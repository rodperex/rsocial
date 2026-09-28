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

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Int32


class SubscriberNode(Node):
    def __init__(self):
        super().__init__('subscriber_node')
        self.subscriber_ = self.create_subscription(
            Int32,
            'int_topic',
            self.callback,
            10
        )

    def callback(self, msg):
        self.get_logger().info(f'Hello {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    subscriber_node = SubscriberNode()
    try:
        rclpy.spin(subscriber_node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        subscriber_node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
