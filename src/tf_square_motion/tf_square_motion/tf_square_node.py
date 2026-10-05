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

import math

from geometry_msgs.msg import Twist, TwistStamped
import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener
from tf_transformations import euler_from_quaternion


class TFSquareMover(Node):
    def __init__(self):
        super().__init__('tf_square_mover')

        # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped
        self.declare_parameter('enable_stamped_cmd_vel', False)
        self.stamped = self.get_parameter('enable_stamped_cmd_vel').value
        self.publisher = self.create_publisher(
            TwistStamped if self.stamped else Twist, '/cmd_vel', 10)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.timer = self.create_timer(0.01, self.control_loop)

        self.state = 'init'
        self.start_x = 0.0
        self.start_y = 0.0
        self.start_yaw = 0.0
        self.side_count = 0
        # Non-blocking pause between movements (never call time.sleep inside a
        # callback: it blocks the executor and the TF buffer stops updating)
        self.pause_until = self.get_clock().now()

    def publish_vel(self, twist):
        """Publish a Twist, wrapping it in a TwistStamped if the robot expects it."""
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist = twist
            self.publisher.publish(msg)
        else:
            self.publisher.publish(twist)

    def pause(self, seconds):
        self.pause_until = self.get_clock().now() + Duration(seconds=seconds)

    def is_paused(self):
        return self.get_clock().now() < self.pause_until

    def control_loop(self):
        try:
            trans = self.tf_buffer.lookup_transform('odom', 'base_link', rclpy.time.Time())

            # Get current pose
            x = trans.transform.translation.x
            y = trans.transform.translation.y
            q = trans.transform.rotation
            _, _, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])

        except TransformException as e:
            self.get_logger().warn(f'TF lookup failed: {e}')
            return

        if self.is_paused():
            return

        if self.state == 'init':
            self.start_x = x
            self.start_y = y
            self.start_yaw = yaw
            self.state = 'forward'
            self.get_logger().info(f'Starting side {self.side_count + 1}')
            return

        elif self.state == 'forward':
            dx = x - self.start_x
            dy = y - self.start_y
            distance = math.sqrt(dx**2 + dy**2)
            self.get_logger().info(
                f'Moving forward on side {self.side_count + 1}. distance: {distance:.2f}')

            if distance < 1.0:  # move 1 meter
                twist = Twist()
                twist.linear.x = 0.5
                self.publish_vel(twist)
            else:
                self.publish_vel(Twist())  # stop
                self.state = 'turn'
                self.start_yaw = yaw
                self.pause(0.5)

        elif self.state == 'turn':
            # Compute angle turned
            yaw_diff = self.normalize_angle(yaw - self.start_yaw)
            self.get_logger().info(
                f'Turning at side {self.side_count + 1}. angle: {math.degrees(yaw_diff):.2f} deg')

            if abs(yaw_diff) < math.pi / 2:
                twist = Twist()
                twist.angular.z = 1.0
                self.publish_vel(twist)
            else:
                self.publish_vel(Twist())  # stop
                self.side_count += 1
                if self.side_count >= 4:
                    self.get_logger().info('Finished square.')
                    self.state = 'done'
                else:
                    self.state = 'init'
                self.pause(0.5)

        elif self.state == 'done':
            self.publish_vel(Twist())

    def normalize_angle(self, angle):
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


def main(args=None):
    rclpy.init(args=args)
    node = TFSquareMover()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
