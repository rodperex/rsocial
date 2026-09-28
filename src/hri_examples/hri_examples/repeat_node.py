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
    SAY_PROMPT = auto()
    WAITING_PROMPT = auto()
    WAITING_LISTEN = auto()
    WAITING_REPEAT = auto()
    DONE = auto()


class RepeatNode(Node):
    """Ask the user to say something, listen (STT) and repeat it (TTS) using simple_hri."""

    def __init__(self):
        super().__init__('repeat_node')

        self.hri_client = HRIClient(self)
        if not self.hri_client.wait_for_services(10.0):
            self.get_logger().error(
                'simple_hri services not available. Did you launch simple_hri?')

        self.state = State.SAY_PROMPT
        self.transcribed_text = ''
        self.timer = self.create_timer(0.1, self.control_loop)

    def control_loop(self):
        if self.state == State.SAY_PROMPT:
            self.hri_client.start_speaking('¿Qué quieres que repita?')
            self.state = State.WAITING_PROMPT

        elif self.state == State.WAITING_PROMPT:
            if self.hri_client.is_speaking_done():
                self.hri_client.start_listen()
                self.state = State.WAITING_LISTEN

        elif self.state == State.WAITING_LISTEN:
            if self.hri_client.is_listen_done():
                self.transcribed_text = self.hri_client.get_listened_text()
                if not self.transcribed_text.strip():
                    self.get_logger().warning('No sentence was recognized')
                    self.state = State.DONE
                    return
                self.get_logger().info(f'Repeating: "{self.transcribed_text}"')
                self.hri_client.start_speaking(self.transcribed_text)
                self.state = State.WAITING_REPEAT

        elif self.state == State.WAITING_REPEAT:
            if self.hri_client.is_speaking_done():
                self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('Interaction finished')
            self.timer.cancel()
            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = RepeatNode()

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
