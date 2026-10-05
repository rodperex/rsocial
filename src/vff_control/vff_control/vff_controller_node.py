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
        self.declare_parameter('max_angular_speed', 0.5)
        self.declare_parameter('angular_gain', 1.0)  # angular speed per radian of VFF angle
        self.declare_parameter('repulsive_gain_factor', 0.5)
        self.declare_parameter('repulsive_influence_distance', 0.5)
        self.declare_parameter('stay_distance', -1.0)  # -1.0 means no stay distance (2D case)
        # seconds a received vector is considered valid
        self.declare_parameter('vector_timeout', 0.5)
        # Target search: if the target has not been seen for search_timeout seconds, the
        # robot turns in place at search_angular_speed until it sees it again (0 disables it)
        self.declare_parameter('search_angular_speed', 0.4)
        self.declare_parameter('search_timeout', 2.0)

        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.max_angular_speed = self.get_parameter('max_angular_speed').value
        self.angular_gain = self.get_parameter('angular_gain').value
        self.repulsive_gain_factor = self.get_parameter('repulsive_gain_factor').value
        self.repulsive_influence_distance = self.get_parameter(
            'repulsive_influence_distance').value
        self.stay_distance = self.get_parameter('stay_distance').value
        self.vector_timeout = Duration(seconds=self.get_parameter('vector_timeout').value)
        self.search_angular_speed = self.get_parameter('search_angular_speed').value
        self.search_timeout = Duration(seconds=self.get_parameter('search_timeout').value)

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
        self.searching = False
        # Side where the target was last seen (1 left, -1 right): the search turns that way
        self.search_direction = 1.0
        self.start_time = self.get_clock().now()

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
        if msg.y != 0.0:
            self.search_direction = math.copysign(1.0, msg.y)
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

    def search(self):
        """Turn in place towards the side where the target was last seen."""
        if not self.searching:
            self.get_logger().info('Target lost: turning to search for it')
            self.searching = True
        cmd = Twist()
        cmd.angular.z = self.search_direction * self.search_angular_speed
        self.publish_vel(cmd)
        self.moving = True

    def control_cycle(self):
        if not self.is_fresh(self.attractive_ts):
            # Without a target the VFF has nowhere to go. After a short gap (a missed
            # detection) the robot searches for the target; until then, it stops
            last_seen = self.attractive_ts if self.attractive_ts is not None else self.start_time
            lost_for = self.get_clock().now() - last_seen
            if self.search_angular_speed > 0.0 and lost_for >= self.search_timeout:
                self.search()
            elif self.moving:
                self.stop()
            return

        if self.searching:
            self.get_logger().info('Target found')
            self.searching = False

        attractive = self.attractive_vec
        repulsive = self.repulsive_vec if self.is_fresh(self.repulsive_ts) else Vector3()

        distance = math.hypot(attractive.x, attractive.y)
        if self.stay_distance > 0 and distance < self.stay_distance:
            self.get_logger().debug(f'Target @ {attractive.x:.2f} m, {attractive.y:.2f}. '
                                    f'Within stay distance ({distance:.2f} < '
                                    f'{self.stay_distance}), stopping')
            self.stop()  # Explicitly stop: otherwise the robot keeps the last command
            return

        # Attraction: unit vector towards the target. Only its direction matters, so the
        # same gains work in 2D (fixed 1 m distance) and 3D (real distance)
        attractive_x = attractive.x / distance if distance > 0.0 else 0.0
        attractive_y = attractive.y / distance if distance > 0.0 else 0.0

        # Repulsion: F = k * (1/d - 1/rho_0) away from the obstacle, only while it is
        # closer than rho_0. It is 0 at the edge of the influence area and grows smoothly
        # as the obstacle gets closer. Obstacles behind the robot are ignored: the robot
        # only moves forward, so they cannot be hit
        repulsive_force_x = 0.0
        repulsive_force_y = 0.0
        obstacle_distance = math.hypot(repulsive.x, repulsive.y)
        rho_0 = self.repulsive_influence_distance
        if 0.0 < obstacle_distance <= rho_0 and repulsive.x > 0.0:
            force = self.repulsive_gain_factor * (1.0 / obstacle_distance - 1.0 / rho_0)
            # The repulsive vector points towards the obstacle, so the force is opposite
            repulsive_force_x = -force * repulsive.x / obstacle_distance
            repulsive_force_y = -force * repulsive.y / obstacle_distance

            self.get_logger().debug(
                f'Repulsive magnitude={force:.2f}. '
                f'Angle={math.degrees(math.atan2(repulsive.y, repulsive.x)):.2f} deg')

        vff_x = attractive_x + repulsive_force_x
        vff_y = attractive_y + repulsive_force_y

        self.get_logger().debug(
            f'VFF vector: x={vff_x:.2f}, y={vff_y:.2f}. Magnitude={math.hypot(vff_x, vff_y):.2f} '
            f'Angle={math.degrees(math.atan2(vff_y, vff_x)):.2f} deg')

        angle = math.atan2(vff_y, vff_x)

        cmd = Twist()
        # Only the forward component of the VFF vector moves the robot: if the vector points
        # to the side it turns slower, and if it points backwards (e.g. an obstacle ahead
        # repels more than the target attracts) it turns in place instead of advancing
        forward = math.hypot(vff_x, vff_y) * math.cos(angle)
        cmd.linear.x = max(0.0, min(self.max_linear_speed, forward))
        cmd.angular.z = max(-self.max_angular_speed,
                            min(self.angular_gain * angle, self.max_angular_speed))

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
