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

from geometry_msgs.msg import Twist, TwistStamped, Vector3
import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class VFFControllerNode(Node):
    def __init__(self):
        super().__init__('vff_controller_node')

        # Parameters
        self.declare_parameter('max_linear_speed', 0.3)
        self.declare_parameter('max_angular_speed', 1.0)
        self.declare_parameter('repulsive_gain_factor', 1.0)
        self.declare_parameter('repulsive_influence_distance', 0.5)
        self.declare_parameter('stay_distance', -1.0)  # -1.0 means no stay distance (2D case)
        # seconds a received vector is considered valid
        self.declare_parameter('vector_timeout', 0.5)

        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.max_angular_speed = self.get_parameter('max_angular_speed').value
        self.repulsive_gain_factor = self.get_parameter('repulsive_gain_factor').value
        self.repulsive_influence_distance = self.get_parameter(
            'repulsive_influence_distance').value
        self.stay_distance = self.get_parameter('stay_distance').value
        self.vector_timeout = Duration(seconds=self.get_parameter('vector_timeout').value)

        # Subscribers
        self.attractive_sub = self.create_subscription(
            Vector3,
            'attractive_vector',
            self.attractive_callback,
            10
        )

        self.repulsive_sub = self.create_subscription(
            Vector3,
            'repulsive_vector',
            self.repulsive_callback,
            10
        )

        # Publisher
        # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped
        self.declare_parameter('enable_stamped_cmd_vel', False)
        self.stamped = self.get_parameter('enable_stamped_cmd_vel').value
        self.cmd_pub = self.create_publisher(
            TwistStamped if self.stamped else Twist, 'vel', 10)

        # Internal state: last vector received and when it was received.
        # Callbacks only store data; the control law runs in the timer at a fixed rate,
        # so both vectors are combined even if they arrive at different frequencies.
        self.attractive_vec = None
        self.attractive_ts = None
        self.repulsive_vec = None
        self.repulsive_ts = None
        self.moving = False

        self.timer = self.create_timer(0.05, self.control_cycle)  # 20 Hz

    def publish_vel(self, twist):
        """Publish a Twist, wrapping it in a TwistStamped if the robot expects it."""
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist = twist
            self.cmd_pub.publish(msg)
        else:
            self.cmd_pub.publish(twist)

    def attractive_callback(self, msg: Vector3):
        self.attractive_vec = msg
        self.attractive_ts = self.get_clock().now()
        self.get_logger().debug(
            f'Received Attractive vector: x={msg.x:.2f}, y={msg.y:.2f}. '
            f'Magnitude={math.hypot(msg.x, msg.y):.2f}. '
            f'Angle={math.degrees(math.atan2(msg.y, msg.x)):.2f} deg')

    def repulsive_callback(self, msg: Vector3):
        self.repulsive_vec = msg
        self.repulsive_ts = self.get_clock().now()
        self.get_logger().debug(
            f'Received Repulsive vector: x={msg.x:.2f}, y={msg.y:.2f}. '
            f'Magnitude={math.hypot(msg.x, msg.y):.2f}. '
            f'Angle={math.degrees(math.atan2(msg.y, msg.x)):.2f} deg')

    def is_fresh(self, stamp):
        return stamp is not None and (self.get_clock().now() - stamp) < self.vector_timeout

    def stop(self):
        if self.moving:
            self.get_logger().info('Stopping robot')
        self.publish_vel(Twist())
        self.moving = False

    def control_cycle(self):
        attractive = self.attractive_vec if self.is_fresh(self.attractive_ts) else Vector3()
        repulsive = self.repulsive_vec if self.is_fresh(self.repulsive_ts) else Vector3()

        if not self.is_fresh(self.attractive_ts) and not self.is_fresh(self.repulsive_ts):
            # No recent information: stop once and do not flood /cmd_vel
            if self.moving:
                self.stop()
            return

        if self.stay_distance > 0 and self.is_fresh(self.attractive_ts):
            distance = math.hypot(attractive.x, attractive.y)
            if distance < self.stay_distance:
                self.get_logger().debug(f'Target @ {attractive.x:.2f} m, {attractive.y:.2f}. '
                                        f'Within stay distance ({distance:.2f} < '
                                        f'{self.stay_distance}), stopping')
                self.stop()  # Explicitly stop: otherwise the robot keeps the last command
                return

        obstacle_distance = math.hypot(repulsive.x, repulsive.y)

        # Initialize repulsive force components to zero
        repulsive_force_x = 0.0
        repulsive_force_y = 0.0

        rho_0 = self.repulsive_influence_distance
        if 0.0 < obstacle_distance <= rho_0:  # If within influence distance
            # Normally F_rep is proportional to (1/d - 1/rho_0) but we keep it simple here
            # The closer the obstacle, the stronger the repulsive force
            force_mag_gain = 1.0 / obstacle_distance**2

            unit_x = repulsive.x / obstacle_distance
            unit_y = repulsive.y / obstacle_distance

            repulsive_force_x = self.repulsive_gain_factor * force_mag_gain * unit_x
            repulsive_force_y = self.repulsive_gain_factor * force_mag_gain * unit_y

            self.get_logger().debug(
                f'Repulsive magnitude={math.hypot(repulsive_force_x, repulsive_force_y):.2f}. '
                f'Angle={math.degrees(math.atan2(repulsive.y, repulsive.x)):.2f} deg')

        # The repulsive vector points towards the obstacle, so it is subtracted
        vff_x = attractive.x - repulsive_force_x
        vff_y = attractive.y - repulsive_force_y

        self.get_logger().debug(
            f'VFF vector: x={vff_x:.2f}, y={vff_y:.2f}. Magnitude={math.hypot(vff_x, vff_y):.2f} '
            f'Angle={math.degrees(math.atan2(vff_y, vff_x)):.2f} deg')

        angle = math.atan2(vff_y, vff_x)

        cmd = Twist()
        cmd.linear.x = min(self.max_linear_speed, math.hypot(vff_x, vff_y))
        cmd.angular.z = max(-self.max_angular_speed, min(angle, self.max_angular_speed))

        self.publish_vel(cmd)
        self.moving = True
        self.get_logger().debug(f'Cmd: linear={cmd.linear.x:.2f}, angular={cmd.angular.z:.2f}')


def main(args=None):
    rclpy.init(args=args)
    node = VFFControllerNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
