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

from enum import IntEnum

from geometry_msgs.msg import Twist
from kobuki_ros_interfaces.msg import BumperEvent
import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class State(IntEnum):
    FORWARD = 0
    BACK = 1
    TURN = 2


SPEED_LINEAR = 0.2
SPEED_ANGULAR = 1.0
BACKING_TIME = Duration(seconds=2.0)
TURNING_TIME = Duration(seconds=2.0)


class BumpGoNode(Node):

    def __init__(self):
        super().__init__('bump_go')

        self.state = State.FORWARD
        self.state_ts = self.get_clock().now()

        self.last_bump = BumperEvent()
        self.last_bump.state = BumperEvent.RELEASED

        self.bumper_sub = self.create_subscription(
            BumperEvent,
            '/bumper',
            self.bumper_callback,
            10
        )

        self.vel_pub = self.create_publisher(Twist, '/out_vel', 10)

        self.timer = self.create_timer(0.05, self.control_cycle)

    def bumper_callback(self, msg):
        self.last_bump = msg

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

        self.vel_pub.publish(out_vel)

    def go_state(self, new_state):
        # Log only on transitions (logging in every cycle would print 20 lines/s)
        self.get_logger().info(f'{self.state.name} -> {new_state.name}')
        self.state = new_state
        self.state_ts = self.get_clock().now()

    def check_forward_2_back(self):
        return self.last_bump.state == BumperEvent.PRESSED

    def check_back_2_turn(self):
        return (self.get_clock().now() - self.state_ts) > BACKING_TIME

    def check_turn_2_forward(self):
        return (self.get_clock().now() - self.state_ts) > TURNING_TIME


def main(args=None):
    rclpy.init(args=args)
    node = BumpGoNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
