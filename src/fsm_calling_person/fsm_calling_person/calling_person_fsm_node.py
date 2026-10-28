# Copyright 2026 Rodrigo Pérez-Rodríguez
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Go to the person who is calling the robot, implemented as an explicit FSM.

The FSM only coordinates the other nodes, like the VFF of vff_control:
  - calling_person_detector_node: tells when a person calls (calling_person) and
    publishes the attractive vector towards them (attractive_vector). This node
    tells it to forget the person (calling_person_reset) every time it searches again
  - obstacle_detector_node (vff_control): publishes the repulsive vector
  - vff_controller_node (vff_control): moves the robot with both vectors. It is
    launched disabled, and this node enables it (vff_enable) only to approach the
    person, so only one of them publishes velocities at a time

States:
  - SEARCH: turn in place until a person calls
  - APPROACH: VFF enabled, until the robot is next to the person
  - ARRIVED: stay still for a while and search again

Follows the classic FSM anatomy (see fsm_bumpgo):
  - State: on_entry / on_do / on_exit lifecycle
  - Event: a person calling, attractive vectors and timeouts
  - Guard: boolean condition enabling a transition
  - Action: side effect executed on entry/exit (velocity, enabling the VFF...)
"""

from abc import ABC, abstractmethod
from enum import auto, Enum
import math

from geometry_msgs.msg import Twist, TwistStamped, Vector3
import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Bool, Empty, String


class Event(Enum):
    """Triggers that can wake up a transition check."""

    PERSON_CALLING = auto()


# State is an abstract base class (ABC, from the standard abc module): a template that
# says which methods a state has, not a state itself. Inheriting from ABC makes Python
# enforce the methods marked with @abstractmethod: State cannot be instantiated, and
# neither can a subclass that does not implement them (TypeError when it is created,
# naming the missing method). Without ABC, @abstractmethod is ignored. The states are
# plain Python classes, not ROS nodes: the only node is the FSM, reachable as self.fsm
class State(ABC):
    """Base class for a FSM state, with the on_entry/on_do/on_exit lifecycle."""

    def __init__(self, fsm: 'CallingPersonFSM'):
        self.fsm = fsm

    def on_entry(self):
        """Run once when entering the state (initialize resources)."""

    # Mandatory: every state does something while it is active. The other methods
    # do nothing by default, so each state only overrides the ones it needs
    @abstractmethod
    def on_do(self):
        """Run cyclically while in the state (control and evaluation)."""

    def on_exit(self):
        """Run once when leaving the state (safe stop / release)."""

    def check_transition(self):
        """Evaluate guards for this state and return the next State, or None."""
        return None


class SearchState(State):
    """Robot turns in place until a person calls."""

    def on_entry(self):
        self.fsm.get_logger().info('Entering SEARCH')
        self.fsm.enable_vff(False)
        # The detector forgets the previous person: otherwise it would stick to them
        # while they are in view and the robot would not notice a new call
        self.fsm.reset_detector()

    def on_do(self):
        self.fsm.publish_vel(linear=0.0, angular=self.fsm.search_angular_speed)

    def on_exit(self):
        self.fsm.publish_vel(linear=0.0, angular=0.0)

    def check_transition(self):
        # guard: the detector says that a person is calling. Only SEARCH checks this
        # event: a call while approaching another person or while ARRIVED is ignored
        if self.fsm.last_event == Event.PERSON_CALLING:
            return ApproachState(self.fsm)
        return None


class ApproachState(State):
    """VFF enabled, attracted by the person who called, until the robot is next to them."""

    def on_entry(self):
        self.fsm.get_logger().info(
            f'Entering APPROACH: person {self.fsm.calling_id} is calling, going towards them')
        self.fsm.enable_vff(True)
        # Only the vectors received from now on count. The time is set to now so that
        # the lost guard counts from here until the first vector arrives
        self.fsm.attractive_vec = None
        self.fsm.attractive_ts = self.fsm.get_clock().now()

    def on_do(self):
        # Nothing to do: the VFF moves the robot with the vectors of the detectors
        pass

    def on_exit(self):
        # Both when it arrives and when it loses the person
        self.fsm.enable_vff(False)

    def check_transition(self):
        # Distance to the person on the floor (x, y in base_frame). Until the first vector
        # arrives it is infinite: the robot cannot have arrived yet
        vector = self.fsm.attractive_vec
        distance = math.inf
        if vector is not None:
            distance = math.hypot(vector.x, vector.y)

        time_without_vector = self.fsm.get_clock().now() - self.fsm.attractive_ts

        # guard: close enough to the person
        if distance <= self.fsm.arrive_distance:
            return ArrivedState(self.fsm)
        # guard: no attractive vector for a while, the detector does not see the person
        # (the VFF already turns towards the side where it was last seen)
        if time_without_vector > self.fsm.lost_timeout:
            self.fsm.get_logger().info(f'Person {self.fsm.calling_id} lost')
            return SearchState(self.fsm)
        return None


class ArrivedState(State):
    """Robot stays still next to the person for a while before searching again."""

    def on_entry(self):
        self.fsm.get_logger().info('Entering ARRIVED: next to the person')
        self.fsm.reset_state_timer()

    def on_do(self):
        self.fsm.publish_vel(linear=0.0, angular=0.0)

    def check_transition(self):
        # guard: enough time has elapsed next to the person
        if self.fsm.time_in_state() > self.fsm.arrived_wait:
            return SearchState(self.fsm)
        return None


class CallingPersonFSM(Node):

    def __init__(self):
        super().__init__('calling_person_fsm')

        # Parameters
        self.declare_parameter('search_angular_speed', 0.3)
        # Distance (m) to the person at which the robot considers it has arrived
        self.declare_parameter('arrive_distance', 1.0)
        # Seconds without attractive vectors before going back to SEARCH
        self.declare_parameter('lost_timeout', 5.0)
        # Seconds the robot stays next to the person before searching again
        self.declare_parameter('arrived_wait', 5.0)
        # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped
        self.declare_parameter('enable_stamped_cmd_vel', False)

        self.search_angular_speed = self.get_parameter('search_angular_speed').value
        self.arrive_distance = self.get_parameter('arrive_distance').value
        self.lost_timeout = Duration(seconds=self.get_parameter('lost_timeout').value)
        self.arrived_wait = Duration(seconds=self.get_parameter('arrived_wait').value)
        self.stamped = self.get_parameter('enable_stamped_cmd_vel').value

        # From calling_person_detector_node
        self.calling_sub = self.create_subscription(
            String, 'calling_person', self.calling_callback, 10)
        self.attractive_sub = self.create_subscription(
            Vector3, 'attractive_vector', self.attractive_callback, 10)

        self.vel_pub = self.create_publisher(
            TwistStamped if self.stamped else Twist, 'vel', 10)
        self.vff_enable_pub = self.create_publisher(Bool, 'vff_enable', 10)
        self.detector_reset_pub = self.create_publisher(Empty, 'calling_person_reset', 10)

        self.last_event = None
        self.calling_id = None
        # Last attractive vector and when it arrived. The vector tells how far the person
        # is (ARRIVED guard). The time tells whether the detector still sees them: it
        # only publishes while the person is in view, so if no vector has arrived for
        # lost_timeout seconds, the person is lost (lost guard of APPROACH)
        self.attractive_vec = None
        self.attractive_ts = None
        self.state_ts = self.get_clock().now()

        self.current_state = SearchState(self)
        self.current_state.on_entry()

        self.timer = self.create_timer(0.05, self.control_cycle)

    def calling_callback(self, msg: String):
        # The callback only stores the event; it does not change the state. The
        # transitions are decided in check_transition of the current state, so all the
        # transitions of a state are together and only the states that care about the
        # event check it (as BUMP_PRESSED in fsm_bumpgo)
        self.calling_id = msg.data
        self.last_event = Event.PERSON_CALLING

    def attractive_callback(self, msg: Vector3):
        self.attractive_vec = msg
        # Arrival time (the Vector3 message has no header with a stamp of its own)
        self.attractive_ts = self.get_clock().now()

    def control_cycle(self):
        # on_do: cyclic action of the current state
        self.current_state.on_do()

        # transition = event + [guard] / action(on_exit, on_entry)
        next_state = self.current_state.check_transition()
        if next_state is not None:
            self.current_state.on_exit()
            self.current_state = next_state
            self.current_state.on_entry()

        # The event is consumed in this cycle, whether the current state used it or not.
        # Otherwise it would stay stored and a later SEARCH would take an old call as new
        self.last_event = None

    def enable_vff(self, enabled: bool):
        self.vff_enable_pub.publish(Bool(data=enabled))

    def reset_detector(self):
        self.detector_reset_pub.publish(Empty())

    def publish_vel(self, linear: float, angular: float):
        vel = Twist()
        vel.linear.x = linear
        vel.angular.z = angular
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist = vel
            self.vel_pub.publish(msg)
        else:
            self.vel_pub.publish(vel)

    def reset_state_timer(self):
        self.state_ts = self.get_clock().now()

    def time_in_state(self) -> Duration:
        return self.get_clock().now() - self.state_ts


def main(args=None):
    rclpy.init(args=args)
    node = CallingPersonFSM()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
