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
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener

from .pid_controller import PIDController


class TFSeekerNode(Node):

    def __init__(self):
        super().__init__('tf_seeker')

        self.declare_parameter('erratic', False)
        self.erratic = self.get_parameter('erratic').get_parameter_value().bool_value

        self.get_logger().info(f'TFSeekerNode initialized with erratic={self.erratic}')

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped
        self.declare_parameter('enable_stamped_cmd_vel', False)
        self.stamped = self.get_parameter('enable_stamped_cmd_vel').value
        self.vel_publisher = self.create_publisher(
            TwistStamped if self.stamped else Twist, '/cmd_vel', 10)

        if not self.erratic:
            # PID gains tuned to avoid overshoot and oscillation:
            # low kp to avoid overreacting, zero (or very low) ki to avoid windup, kd for damping
            self.vlin_pid = PIDController(-0.5, 0.5, kp=0.3, ki=0.0, kd=0.15)
            self.vrot_pid = PIDController(-0.5, 0.5, kp=0.6, ki=0.0, kd=0.25)
        else:
            # Angular PID badly tuned on purpose so the robot weaves towards the target:
            # a high ki keeps accumulating the angle error and overshoots it on every
            # swing, and without kd nothing damps it (raise ki for wider swings). The
            # faster turn limit makes the swings wide enough to see. With a high kp
            # instead, the speed limit would hide it: the robot would only shake
            # slightly. The linear PID is the normal one, so that the robot still
            # stops 1 m from the target.
            self.vlin_pid = PIDController(-0.5, 0.5, kp=0.3, ki=0.0, kd=0.15)
            self.vrot_pid = PIDController(-0.8, 0.8, kp=0.8, ki=2.0, kd=0.0)

        self.timer_period = 0.05  # 20 Hz
        self.last_cycle_time = None
        self.timer = self.create_timer(self.timer_period, self.control_cycle)

    def publish_vel(self, twist):
        """Publish a Twist, wrapping it in a TwistStamped if the robot expects it."""
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist = twist
            self.vel_publisher.publish(msg)
        else:
            self.vel_publisher.publish(twist)

    def control_cycle(self):

        # Check if the transform is available
        if not self.tf_buffer.can_transform('base_footprint', 'target', rclpy.time.Time()):
            self.get_logger().warn('Waiting for transform base_footprint -> target')
            return
        try:
            tf = self.tf_buffer.lookup_transform(
                'base_footprint', 'target', rclpy.time.Time())

            x = tf.transform.translation.x
            y = tf.transform.translation.y

            angle = math.atan2(y, x)
            dist = math.sqrt(x ** 2 + y ** 2)

            # Measured dt: the timer does not guarantee exactly 0.05 s between cycles
            now = self.get_clock().now()
            if self.last_cycle_time is None:
                dt = self.timer_period
            else:
                dt = (now - self.last_cycle_time).nanoseconds / 1e9
            self.last_cycle_time = now

            vel_rot = self.vrot_pid.get_output(angle, dt)
            vel_lin = self.vlin_pid.get_output(dist - 1.0, dt)

            self.get_logger().debug(f'Angle error: {angle:.2f}. Angular speed: {vel_rot:.2f}')
            self.get_logger().info(f'Distance error: {dist - 1:.2f}. Linear speed: {vel_lin:.2f}')

            twist = Twist()
            twist.linear.x = vel_lin
            twist.angular.z = vel_rot

            self.publish_vel(twist)

            if abs(angle) < 0.2 and dist < 1.3:
                self.get_logger().info('Target reached!')

        except TransformException as e:
            self.get_logger().warn(f'Error in TF base_footprint -> target: {str(e)}')


def main(args=None):
    rclpy.init(args=args)
    node = TFSeekerNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
