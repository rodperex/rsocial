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

from comms_interfaces.action import GenerateInformation
import rclpy
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class GenerateClient(Node):
    def __init__(self):
        super().__init__('generate_information_client')
        self._client = ActionClient(self, GenerateInformation, 'generate_information')

    def send_goal(self, key):
        self._client.wait_for_server()
        goal = GenerateInformation.Goal()
        goal.key = key

        self._client.send_goal_async(goal, feedback_callback=self.feedback_cb)\
            .add_done_callback(self.goal_response_cb)

    def feedback_cb(self, feedback_msg):
        self.get_logger().info(f'Feedback: {feedback_msg.feedback.provisional_content}')

    def goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected')
            return
        self.get_logger().info('Goal accepted')
        goal_handle.get_result_async().add_done_callback(self.result_cb)

    def result_cb(self, future):
        result = future.result().result
        self.get_logger().info(f'Success: {result.success}, Final content: {result.final_content}')
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = GenerateClient()
    node.send_goal('example_key')
    try:
        rclpy.spin(node)  # Returns when result_cb calls rclpy.shutdown()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
