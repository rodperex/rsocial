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
Bump-and-go behavior implemented as an explicit FSM, for the TurtleBot 4.

Same FSM as bumpgo_fsm_node.py (Kobuki); only the bumper input changes:
bumps arrive in /hazard_detection (iRobot Create 3 base).

Follows the classic FSM anatomy:
  - State: on_entry / on_do / on_exit lifecycle
  - Event: bumper messages and timeouts
  - Guard: boolean condition enabling a transition
  - Action: side effect executed on entry/exit (here: publishing velocity)

Transition = Event + [Guard] / Action
"""

from abc import ABC, abstractmethod
from enum import auto, Enum

from geometry_msgs.msg import Twist, TwistStamped
from irobot_create_msgs.msg import HazardDetection, HazardDetectionVector
import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


SPEED_LINEAR = 0.2
SPEED_ANGULAR = 1.0
BACKING_TIME = Duration(seconds=2.0)
TURNING_TIME = Duration(seconds=2.0)


class Event(Enum):
    """Triggers that can wake up a transition check."""

    BUMP_PRESSED = auto()
    BUMP_RELEASED = auto()
    TIMEOUT = auto()


class State(ABC):
    """Base class for a FSM state, with the on_entry/on_do/on_exit lifecycle."""

    def __init__(self, fsm: 'BumpGoFSM'):
        self.fsm = fsm

    def on_entry(self):
        """Run once when entering the state (initialize resources)."""

    @abstractmethod
    def on_do(self):
        """Run cyclically while in the state (control and evaluation)."""

    def on_exit(self):
        """Run once when leaving the state (safe stop / release)."""

    def check_transition(self):
        """Evaluate guards for this state and return the next State, or None."""
        return None


class ForwardState(State):
    """Robot moves straight ahead until a bumper event fires."""

    def on_entry(self):
        self.fsm.get_logger().info('Entering FORWARD')

    def on_do(self):
        self.fsm.publish_vel(linear=SPEED_LINEAR, angular=0.0)

    def check_transition(self):
        # guard: bumper pressed event received
        if self.fsm.last_event == Event.BUMP_PRESSED:
            return BackState(self.fsm)
        return None


class BackState(State):
    """Robot backs away from the obstacle for a fixed duration."""

    def on_entry(self):
        self.fsm.get_logger().info('Entering BACK')
        self.fsm.reset_state_timer()

    def on_do(self):
        self.fsm.publish_vel(linear=-SPEED_LINEAR, angular=0.0)

    def check_transition(self):
        # guard: enough time has elapsed backing up
        if self.fsm.time_in_state() > BACKING_TIME:
            return TurnState(self.fsm)
        return None


class TurnState(State):
    """Robot turns in place for a fixed duration before resuming forward."""

    def on_entry(self):
        self.fsm.get_logger().info('Entering TURN')
        self.fsm.reset_state_timer()

    def on_do(self):
        self.fsm.publish_vel(linear=0.0, angular=SPEED_ANGULAR)

    def check_transition(self):
        # guard: enough time has elapsed turning
        if self.fsm.time_in_state() > TURNING_TIME:
            return ForwardState(self.fsm)
        return None


class BumpGoFSM(Node):

    def __init__(self):
        super().__init__('bump_go_fsm_tb4')

        self.last_event = None
        self.state_ts = self.get_clock().now()

        # The Create 3 publishes best effort: a reliable subscriber would get nothing
        self.hazard_sub = self.create_subscription(
            HazardDetectionVector, '/hazard_detection', self.hazard_callback,
            qos_profile_sensor_data)
        # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped
        self.declare_parameter('enable_stamped_cmd_vel', True)
        self.stamped = self.get_parameter('enable_stamped_cmd_vel').value
        self.vel_pub = self.create_publisher(
            TwistStamped if self.stamped else Twist, '/out_vel', 10)

        self.current_state = ForwardState(self)
        self.current_state.on_entry()

        self.timer = self.create_timer(0.05, self.control_cycle)

    def hazard_callback(self, msg: HazardDetectionVector):
        # The Create 3 has no bumper topic: a bump is a detection of type BUMP
        if any(d.type == HazardDetection.BUMP for d in msg.detections):
            self.last_event = Event.BUMP_PRESSED
        elif self.last_event != Event.BUMP_PRESSED:
            # Do not overwrite a PRESSED event not yet processed by control_cycle:
            # a short tap (press + release within one cycle) would be lost
            self.last_event = Event.BUMP_RELEASED

    def control_cycle(self):
        # on_do: cyclic action of the current state
        self.current_state.on_do()

        # transition = event + [guard] / action(on_exit, on_entry)
        next_state = self.current_state.check_transition()
        if next_state is not None:
            self.current_state.on_exit()
            self.current_state = next_state
            self.current_state.on_entry()

        self.last_event = None

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
    node = BumpGoFSM()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
