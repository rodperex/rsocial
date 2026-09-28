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

import random

from geometry_msgs.msg import TransformStamped
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class TFPublisherNode(Node):

    def __init__(self):
        super().__init__('tf_producer')

        self.declare_parameter('tf_update_time', 20.0)
        self.tf_update_time = self.get_parameter(
            'tf_update_time').get_parameter_value().double_value

        self.get_logger().info(
            f'TFPublisherNode initialized with tf_update_time={self.tf_update_time} seconds')

        self.tf_broadcaster = TransformBroadcaster(self)

        self.transform = TransformStamped()
        self.generate_tf()

        self.create_timer(self.tf_update_time, self.generate_tf)
        self.create_timer(0.05, self.publish_tf)

    def generate_tf(self):
        self.transform.header.stamp = self.get_clock().now().to_msg()
        self.transform.header.frame_id = 'odom'
        self.transform.child_frame_id = 'target'

        self.transform.transform.translation.x = random.uniform(-5.0, 5.0)
        self.transform.transform.translation.y = random.uniform(-5.0, 5.0)
        self.transform.transform.translation.z = 0.0

        # No rotation (identity quaternion)
        self.transform.transform.rotation.x = 0.0
        self.transform.transform.rotation.y = 0.0
        self.transform.transform.rotation.z = 0.0
        self.transform.transform.rotation.w = 1.0

        self.get_logger().info(
            f'Generated transform to ({self.transform.transform.translation.x:.2f}, '
            f'{self.transform.transform.translation.y:.2f})')

    def publish_tf(self):
        self.transform.header.stamp = self.get_clock().now().to_msg()
        self.tf_broadcaster.sendTransform(self.transform)


def main(args=None):
    rclpy.init(args=args)
    node = TFPublisherNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
