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

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool


class ObstacleDetectorNode(Node):
    def __init__(self):
        super().__init__('obstacle_detector_node')

        self.declare_parameter('min_distance', 0.5)
        self.declare_parameter('real_robot', False)

        self.min_distance = self.get_parameter('min_distance').value
        self.real_robot = self.get_parameter('real_robot').value

        self.get_logger().info(f'Obstacle_detector_node set to {self.min_distance:.2f} m')

        self.laser_sub = self.create_subscription(
            LaserScan,
            'input_laser',
            self.laser_callback,
            rclpy.qos.qos_profile_sensor_data)

        self.obstacle_pub = self.create_publisher(Bool, 'obstacle', 10)

    def laser_callback(self, scan: LaserScan):
        if not scan.ranges:
            return

        # Invalid readings (NaN, inf, 0.0 or outside [range_min, range_max], typical
        # of real lasers) are replaced by inf so they are ignored by min()
        ranges = [r if math.isfinite(r) and scan.range_min <= r <= scan.range_max else float('inf')
                  for r in scan.ranges]

        distance_min = min(ranges)
        min_idx = ranges.index(distance_min)

        msg = Bool()
        if distance_min < self.min_distance:
            if not self.real_robot:
                # Kobuki simulator has forward-facing laser
                angle = scan.angle_min + scan.angle_increment * min_idx
            else:
                # Laser faces backward: add pi (180°)
                # Laser upside down: flip angle (multiply by -1)
                angle = -(scan.angle_min + scan.angle_increment * min_idx) + math.pi

            angle_deg = math.degrees(angle)

            self.get_logger().info(
                'Obstacle at {:.2f} m, angle {:.2f} deg'.format(distance_min, angle_deg))
            msg.data = True
        else:
            msg.data = False

        self.obstacle_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetectorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
