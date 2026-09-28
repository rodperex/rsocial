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
from rclpy.lifecycle import LifecycleNode
from rclpy.lifecycle import LifecycleState
from rclpy.lifecycle import TransitionCallbackReturn
from std_msgs.msg import Int32


class LifeCyclePublisherNode(LifecycleNode):
    def __init__(self):
        super().__init__('publisher_node')
        self.publisher_ = None
        self.timer_ = None
        self.message_ = Int32()

    def on_configure(self, state: LifecycleState):
        self.get_logger().info(f'[{self.get_name()}] Configuring')
        # Lifecycle publisher: only publishes while the node is ACTIVE
        self.publisher_ = self.create_lifecycle_publisher(Int32, 'int_topic', 10)
        self.get_logger().info(f'[{self.get_name()}] Configured')
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: LifecycleState):
        self.get_logger().info(f'[{self.get_name()}] Activating...')
        self.timer_ = self.create_timer(0.1, self.timer_callback)
        self.get_logger().info(f'[{self.get_name()}] Activated')
        # The base class activates the lifecycle publishers
        return super().on_activate(state)

    def on_deactivate(self, state: LifecycleState):
        self.get_logger().info(f'[{self.get_name()}] Deactivating...')
        # Setting the attribute to None is not enough: the node keeps a reference
        # to the timer and it would keep firing. It has to be destroyed.
        self.stop_timer()
        self.get_logger().info(f'[{self.get_name()}] Deactivated')
        # The base class deactivates the lifecycle publishers
        return super().on_deactivate(state)

    def on_cleanup(self, state: LifecycleState):
        self.get_logger().info(f'[{self.get_name()}] Cleaning Up...')
        if self.publisher_ is not None:
            self.destroy_lifecycle_publisher(self.publisher_)
            self.publisher_ = None
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: LifecycleState):
        self.get_logger().info(f'[{self.get_name()}] Shutting Down...')
        self.stop_timer()
        return TransitionCallbackReturn.SUCCESS

    def on_error(self, state: LifecycleState):
        self.get_logger().error(f'[{self.get_name()}] Error State')
        return TransitionCallbackReturn.SUCCESS

    def stop_timer(self):
        if self.timer_ is not None:
            self.destroy_timer(self.timer_)
            self.timer_ = None

    def timer_callback(self):
        self.message_.data += 1
        self.publisher_.publish(self.message_)


def main(args=None):
    rclpy.init(args=args)
    node = LifeCyclePublisherNode()

    node.trigger_configure()
    node.trigger_activate()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
