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

import time

from comms_interfaces.action import GenerateInformation
import rclpy
from rclpy.action import ActionServer
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class GenerateServer(Node):
    def __init__(self):
        super().__init__('generate_information_server')
        self._action_server = ActionServer(
            self,
            GenerateInformation,
            'generate_information',
            self.execute_callback
        )

    async def execute_callback(self, goal_handle):
        self.get_logger().info(f'Received key: {goal_handle.request.key}')
        feedback_msg = GenerateInformation.Feedback()

        # Simulate generating the content step by step
        content = ''
        for i in range(3):
            content += f'[fragment {i}] '
            feedback_msg.provisional_content = content
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1)

        goal_handle.succeed()

        result = GenerateInformation.Result()
        result.success = True
        result.final_content = (f"Final content for key '{goal_handle.request.key}': "
                                f'{content.strip()}')
        return result


def main(args=None):
    rclpy.init(args=args)
    node = GenerateServer()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
