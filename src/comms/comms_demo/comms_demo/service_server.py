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


class ServerNode(Node):
    def __init__(self):
        super().__init__('server_node')
        self.srv = self.create_service(GetInformation, 'get_information', self.handle_request)

    def handle_request(self, request, response):
        response.content = f'Content for key: {request.key}'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ServerNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
