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
Go to the person who is calling the robot: a mission implemented as an explicit FSM.

Each state is a task (searching, approaching, greeting) that uses capabilities.

The FSM only coordinates the other nodes, like the VFF of vff_control:
  - calling_person_detector_node: tells when a person calls (calling_person) and
    publishes the attractive vector towards them (attractive_vector). This node
    tells it to forget the person (calling_person_reset) every time it searches again
  - obstacle_detector_node (vff_control): publishes the repulsive vector
  - vff_controller_node (vff_control): moves the robot with both vectors. It is
    launched disabled, and this node enables it (vff_enable) only to approach the
    person, so only one of them publishes velocities at a time
  - The TTS of simple_hri (tts_action), through HRIClient (hri_client): on entering each
    state the robot says what it is doing, and it greets the person when it reaches them

States:
  - SEARCH: turn in place until a person calls
  - APPROACH: VFF enabled, until the robot is next to the person
  - ARRIVED: greet the person, stay still for a while and search again

Follows the classic FSM anatomy (see fsm_bumpgo):
  - State: on_entry / on_do / on_exit lifecycle
  - Event: a person calling (the only one, stored by its callback)
  - Guard: boolean condition enabling a transition (distance, timeouts)
  - Action: side effect executed on entry/exit (velocity, enabling the VFF...)
"""

from abc import ABC, abstractmethod
from enum import auto, Enum
import math

from geometry_msgs.msg import Twist, TwistStamped, Vector3
from hri_client.hri_client import HRIClient
import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Bool, Empty, String


class Event(Enum):
    """
    Events stored by the callbacks (not states: the states are the State classes).

    Only the call of a person is an event. The other transitions depend on guards
    that check_transition evaluates every cycle (distance, time without vector...).
    """

    # auto() gives each member a different value (1, 2...) without writing it by hand:
    # only the name matters, the events are compared as Event.PERSON_CALLING
    PERSON_CALLING = auto()


# State is a template for the states, not a state itself. As an abstract class (ABC),
# it cannot be instantiated, and each state must implement the methods marked with
# @abstractmethod (otherwise, TypeError when the state is created).
# The states are plain Python classes, not ROS nodes: the node is the robot
class State(ABC):
    """Base class for a FSM state, with the on_entry/on_do/on_exit lifecycle."""

    def __init__(self, robot: 'CallingPersonRobot'):
        # Every state keeps the robot that created it, to read its information (events,
        # times...) in the guards and to use its methods (publish, speak...)
        self.robot = robot

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
        """Evaluate guards and return the next State, created with self.robot, or None."""
        return None


class CallingPersonRobot(Node):
    """
    The robot as the states see it: the state of the world and of the robot, and how to act.

    The guards of the states consult it to decide (a person calling, the attractive
    vector, time in the state...), and the states use its methods to act (move, speak,
    enable the VFF). It is also the ROS node that runs the FSM: it keeps the current
    state and runs it every cycle. The FSM is this node plus the states, which decide
    what to do and which state comes next.
    """

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
        # What the robot says on entering each state ('' = nothing)
        self.declare_parameter('search_text', 'Estoy buscando a alguien que me llame')
        self.declare_parameter(
            'approach_text', 'He visto a una persona con la mano levantada. Voy hacia ella')
        self.declare_parameter(
            'greeting', '¡Hola! Espero que tengas un buen día')
        # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped
        self.declare_parameter('enable_stamped_cmd_vel', False)

        self.search_angular_speed = self.get_parameter('search_angular_speed').value
        self.arrive_distance = self.get_parameter('arrive_distance').value
        self.lost_timeout = Duration(seconds=self.get_parameter('lost_timeout').value)
        self.arrived_wait = Duration(seconds=self.get_parameter('arrived_wait').value)
        self.search_text = self.get_parameter('search_text').value
        self.approach_text = self.get_parameter('approach_text').value
        self.greeting = self.get_parameter('greeting').value
        self.stamped = self.get_parameter('enable_stamped_cmd_vel').value

        # From calling_person_detector_node
        # Who is calling
        self.calling_sub = self.create_subscription(
            String, 'calling_person', self.calling_callback, 10)
        # Attractive vector towards the person who called
        self.attractive_sub = self.create_subscription(
            Vector3, 'attractive_vector', self.attractive_callback, 10)

        self.vel_pub = self.create_publisher(
            TwistStamped if self.stamped else Twist, 'vel', 10)
        self.vff_enable_pub = self.create_publisher(Bool, 'vff_enable', 10)
        self.detector_reset_pub = self.create_publisher(Empty, 'calling_person_reset', 10)

        # Only the TTS of simple_hri is used. wait_until_ready is not called: it also waits
        # for the STT, Extract and Yes/No, which this example does not launch
        self.hri = HRIClient(self)

        self.last_event = None
        self.calling_id = None
        # Last attractive vector and when it arrived. The vector tells how far the person
        # is (ARRIVED guard). The time tells whether the detector still sees them: it
        # only publishes while the person is in view, so if no vector has arrived for
        # lost_timeout seconds, the person is lost (lost guard of APPROACH)
        self.attractive_vec = None
        self.attractive_ts = None
        self.state_ts = self.get_clock().now()

        # Initial state (the states are defined below). The robot passes itself (self)
        # to the state, which keeps it as self.robot; in check_transition each state
        # passes it on to the next one.
        # This first SEARCH does not speak: the TTS starts at the same time as this node
        # and is not ready yet (Piper takes a few seconds to load the voice)
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

    def enable_vff(self):
        self.vff_enable_pub.publish(Bool(data=True))

    def disable_vff(self):
        self.vff_enable_pub.publish(Bool(data=False))

    def reset_detector(self):
        self.detector_reset_pub.publish(Empty())

    def say(self, text: str) -> bool:
        """Start saying text with the TTS; return whether it started (False if text is empty)."""
        if not text:
            return False
        # A sentence of the previous state that has not finished is cut: the robot says
        # what it is doing now. The TTS runs in the background: start_speaking returns at
        # once, and the timeout ends it if simple_hri does not answer
        self.hri.cancel_speaking()
        self.hri.start_speaking(text, timeout_sec=15.0)
        return True

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


class SearchState(State):
    """Robot turns in place until a person calls."""

    def on_entry(self):
        self.robot.get_logger().info('Entering SEARCH')
        # The detector forgets the previous person: otherwise it would stick to them
        # while they are in view and the robot would not notice a new call
        self.robot.reset_detector()
        self.robot.disable_vff()
        # The robot says what it is doing once everything is ready
        self.robot.say(self.robot.search_text)

    def on_do(self):
        self.robot.publish_vel(linear=0.0, angular=self.robot.search_angular_speed)

    def on_exit(self):
        self.robot.publish_vel(linear=0.0, angular=0.0)

    def check_transition(self):
        # last_event is an attribute of the robot, set to None when it is created
        if self.robot.last_event == Event.PERSON_CALLING:
            # The next state is created with the same robot, the one this state keeps
            # in self.robot (the same in all the transitions)
            return ApproachState(self.robot)
        return None


class ApproachState(State):
    """VFF enabled, attracted by the person who called, until the robot is next to them."""

    def on_entry(self):
        self.robot.get_logger().info(
            f'Entering APPROACH: person {self.robot.calling_id} is calling, going towards them')
        # Only the vectors received from now on count. The time is set to now so that
        # the lost guard counts from here until the first vector arrives
        self.robot.attractive_vec = None
        self.robot.attractive_ts = self.robot.get_clock().now()
        # The robot says what it is going to do before it starts moving
        self.robot.say(self.robot.approach_text)
        self.robot.enable_vff()

    def on_do(self):
        # Nothing to do: the VFF moves the robot with the vectors of the detectors
        pass

    def on_exit(self):
        # Both when it arrives and when it loses the person
        self.robot.disable_vff()

    def check_transition(self):
        # Distance to the person on the floor (x, y in base_frame). Until the first vector
        # arrives it is infinite: the robot cannot have arrived yet
        vector = self.robot.attractive_vec
        distance = math.inf
        if vector is not None:
            distance = math.hypot(vector.x, vector.y)

        time_without_vector = self.robot.get_clock().now() - self.robot.attractive_ts

        # guard: close enough to the person
        if distance <= self.robot.arrive_distance:
            return ArrivedState(self.robot)
        # guard: no attractive vector for a while, the detector does not see the person
        # (the VFF already turns towards the side where it was last seen)
        if time_without_vector > self.robot.lost_timeout:
            self.robot.get_logger().info(f'Person {self.robot.calling_id} lost')
            return SearchState(self.robot)
        return None


class ArrivedState(State):
    """Robot greets the person and stays still next to them before searching again."""

    def on_entry(self):
        self.robot.get_logger().info('Entering ARRIVED: next to the person')
        self.robot.reset_state_timer()
        self.speaking = self.robot.say(self.robot.greeting)

    def on_do(self):
        self.robot.publish_vel(linear=0.0, angular=0.0)
        if self.speaking and self.robot.hri.is_speaking_done():
            self.speaking = False

    def check_transition(self):
        # guard: it has finished speaking and enough time has elapsed next to the person,
        # so that it does not start turning in the middle of the sentence
        if not self.speaking and self.robot.time_in_state() > self.robot.arrived_wait:
            return SearchState(self.robot)
        return None


def main(args=None):
    rclpy.init(args=args)
    node = CallingPersonRobot()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
