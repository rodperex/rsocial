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
Bump and go for the TurtleBot 4 (iRobot Create 3 base).

Same FSM as bumpgo_node.py (Kobuki). Only the bumper input changes: the
Create 3 has no bumper topic; bumps arrive in /hazard_detection, a vector with
all the active hazards (bump, cliff, backup limit...). A bump is a detection of
type HazardDetection.BUMP.
"""

from enum import IntEnum

from geometry_msgs.msg import Twist, TwistStamped
from irobot_create_msgs.msg import HazardDetection, HazardDetectionVector
import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


class State(IntEnum):
    FORWARD = 0
    BACK = 1
    TURN = 2


SPEED_LINEAR = 0.2
SPEED_ANGULAR = 1.0
BACKING_TIME = Duration(seconds=2.0)
TURNING_TIME = Duration(seconds=2.0)


class BumpGoTB4Node(Node):

    def __init__(self):
        super().__init__('bump_go_tb4')

        self.state = State.FORWARD
        self.state_ts = self.get_clock().now()

        self.bumped = False

        # The Create 3 publishes best effort: a reliable subscriber would get nothing
        self.hazard_sub = self.create_subscription(
            HazardDetectionVector,
            '/hazard_detection',
            self.hazard_callback,
            qos_profile_sensor_data
        )

        # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped
        self.declare_parameter('enable_stamped_cmd_vel', False)
        self.stamped = self.get_parameter('enable_stamped_cmd_vel').value
        self.vel_pub = self.create_publisher(
            TwistStamped if self.stamped else Twist, '/out_vel', 10)

        self.timer = self.create_timer(0.05, self.control_cycle)

    def publish_vel(self, twist):
        """Publish a Twist, wrapping it in a TwistStamped if the robot expects it."""
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist = twist
            self.vel_pub.publish(msg)
        else:
            self.vel_pub.publish(twist)

    def hazard_callback(self, msg):
        # Published on every change: bumped while any detection is a bump
        self.bumped = any(d.type == HazardDetection.BUMP for d in msg.detections)

    def control_cycle(self):
        out_vel = Twist()

        if self.state == State.FORWARD:
            out_vel.linear.x = SPEED_LINEAR
            if self.check_forward_2_back():
                self.go_state(State.BACK)

        elif self.state == State.BACK:
            out_vel.linear.x = -SPEED_LINEAR
            if self.check_back_2_turn():
                self.go_state(State.TURN)

        elif self.state == State.TURN:
            out_vel.angular.z = SPEED_ANGULAR
            if self.check_turn_2_forward():
                self.go_state(State.FORWARD)

        self.publish_vel(out_vel)

    def go_state(self, new_state):
        # Log only on transitions (logging in every cycle would print 20 lines/s)
        self.get_logger().info(f'{self.state.name} -> {new_state.name}')
        self.state = new_state
        self.state_ts = self.get_clock().now()

    def check_forward_2_back(self):
        return self.bumped

    def check_back_2_turn(self):
        return (self.get_clock().now() - self.state_ts) > BACKING_TIME

    def check_turn_2_forward(self):
        return (self.get_clock().now() - self.state_ts) > TURNING_TIME


def main(args=None):
    rclpy.init(args=args)
    node = BumpGoTB4Node()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
