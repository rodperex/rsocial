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

from comms_interfaces.srv import GetInformation
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class ClientNode(Node):
    def __init__(self):
        super().__init__('client_node')
        self.cli = self.create_client(GetInformation, 'get_information')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for service...')
        self.req = GetInformation.Request()

    def send_request(self, key):
        self.req.key = key
        self.future = self.cli.call_async(self.req)
        self.future.add_done_callback(self.callback_response)

    def callback_response(self, future):
        try:
            response = future.result()
            self.get_logger().info(f'Response received: {response.content}')
        except Exception as e:
            self.get_logger().error(f'Error receiving the response: {e}')
        finally:
            rclpy.shutdown()  # Finish the node once the response is received


def main(args=None):
    rclpy.init(args=args)
    node = ClientNode()
    node.send_request('example_key')
    try:
        rclpy.spin(node)  # Returns when callback_response calls rclpy.shutdown()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
