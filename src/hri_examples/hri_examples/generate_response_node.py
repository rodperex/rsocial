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

from enum import auto, Enum

from hri_client.hri_client import HRIClient
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class State(Enum):
    ASK = auto()
    WAITING_ASK = auto()
    WAITING_LISTEN = auto()
    WAITING_EXTRACT = auto()
    WAITING_ANSWER = auto()
    DONE = auto()


class GenerateResponseNode(Node):
    """
    Ask a question, understand the answer with a language model and respond.

    The language model runs inside the simple_hri Extract service: it receives the
    transcribed sentence and the 'interest' (e.g. 'bebida') and returns only the
    relevant information (e.g. 'agua'). The question, the interest and the answer
    are parameters (see config/hri.yaml).
    """

    def __init__(self):
        super().__init__('generate_response_node')

        self.declare_parameter('initial_prompt', '¿Qué quieres beber?')
        self.declare_parameter('interest', 'bebida')
        self.declare_parameter('response_prefix', 'Quieres beber: ')

        self.initial_prompt = self.get_parameter('initial_prompt').value
        self.interest = self.get_parameter('interest').value
        self.response_prefix = self.get_parameter('response_prefix').value

        self.get_logger().info(f'Question: "{self.initial_prompt}". Interest: "{self.interest}"')

        self.hri_client = HRIClient(self)
        if not self.hri_client.wait_for_services(10.0):
            self.get_logger().error(
                'simple_hri services not available. Did you launch simple_hri?')

        self.state = State.ASK
        self.timer = self.create_timer(0.1, self.control_loop)

    def control_loop(self):
        if self.state == State.ASK:
            self.hri_client.start_speaking(self.initial_prompt)
            self.state = State.WAITING_ASK

        elif self.state == State.WAITING_ASK:
            if self.hri_client.is_speaking_done():
                self.hri_client.start_listen()
                self.state = State.WAITING_LISTEN

        elif self.state == State.WAITING_LISTEN:
            if self.hri_client.is_listen_done():
                heard = self.hri_client.get_listened_text()
                if not heard.strip():
                    self.get_logger().warning('No sentence was recognized')
                    self.state = State.DONE
                    return
                self.get_logger().info(f'Heard: "{heard}"')
                self.hri_client.start_extract(self.interest, heard)
                self.state = State.WAITING_EXTRACT

        elif self.state == State.WAITING_EXTRACT:
            if self.hri_client.is_extract_done():
                info = self.hri_client.get_extracted_info()
                if not info or info.startswith('ERROR') or info == 'NONE':
                    self.get_logger().warning(f'Could not extract "{self.interest}": {info}')
                    self.hri_client.start_speaking('Perdona, no te he entendido.')
                else:
                    self.get_logger().info(f'{self.interest}: {info}')
                    self.hri_client.start_speaking(f'{self.response_prefix}{info}')
                self.state = State.WAITING_ANSWER

        elif self.state == State.WAITING_ANSWER:
            if self.hri_client.is_speaking_done():
                self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('Interaction finished')
            self.timer.cancel()
            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = GenerateResponseNode()

    try:
        rclpy.spin(node)
    except SystemExit:
        pass  # Clean exit when State == DONE
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
