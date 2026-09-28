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

from hri_client.hri_client import HRIClient
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class SayClientNode(Node):
    """Minimal example: say a sentence with the simple_hri TTS service and exit."""

    def __init__(self):
        super().__init__('say_client_node')

        self.declare_parameter('text', 'Hola, ¿qué tal estáis?')
        self.text = self.get_parameter('text').value

        self.hri_client = HRIClient(self)
        if not self.hri_client.wait_for_services(10.0):
            self.get_logger().error(
                'simple_hri services not available. Did you launch simple_hri?')

        self.speaking = False
        self.timer = self.create_timer(0.1, self.control_loop)

    def control_loop(self):
        if not self.speaking:
            self.hri_client.start_speaking(self.text)
            self.speaking = True

        elif self.hri_client.is_speaking_done():
            if not self.hri_client.get_speaking_result():
                self.get_logger().error('TTS error')
            self.timer.cancel()
            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = SayClientNode()

    try:
        rclpy.spin(node)
    except SystemExit:
        pass  # Clean exit when speaking is finished
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
