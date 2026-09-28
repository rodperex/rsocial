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
    INIT = auto()
    WAITING_INTRO = auto()
    WAITING_USER_RESPONSE = auto()
    WAITING_YESNO = auto()
    WAITING_ECHO = auto()
    DONE = auto()


class HRIExample3Client(Node):

    def __init__(self):
        super().__init__('hri_example3_client_node')
        self.hri_client = HRIClient(self)

        if not self.hri_client.wait_for_services(10.0):
            self.get_logger().info('Services not available, waiting...')

        self.get_logger().info('✅ YesNo, STT and TTS clients ready.')

        self.state = State.INIT
        self.user_response = ''

        self.timer = self.create_timer(0.1, self.control_loop)

    def control_loop(self):
        if self.state == State.INIT:
            self.get_logger().info('🤖 Starting HRI demo with YesNo...')
            self.hri_client.start_speaking('¿Estás bien?')
            self.state = State.WAITING_INTRO

        elif self.state == State.WAITING_INTRO:
            if self.hri_client.is_speaking_done():
                if self.hri_client.get_speaking_result():
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error('❌ TTS error')

                self.get_logger().info('🎤 Starting speech recognition (STT)...')
                self.hri_client.start_listen()
                self.state = State.WAITING_USER_RESPONSE

        elif self.state == State.WAITING_USER_RESPONSE:
            if self.hri_client.is_listen_done():
                self.user_response = self.hri_client.get_listened_text()
                if not self.user_response:
                    self.get_logger().error('❌ STT error')
                    self.user_response = ''
                else:
                    self.get_logger().info(f'📝 Transcription: {self.user_response}')

                self.get_logger().info('🔍 Sending text to the YesNo service...')
                self.hri_client.start_yesno(self.user_response)
                self.state = State.WAITING_YESNO

        elif self.state == State.WAITING_YESNO:
            if self.hri_client.is_yesno_done():
                extracted_response = self.hri_client.get_yesno_result()
                self.get_logger().info(f'📝 Answer: {extracted_response}')

                if extracted_response and not extracted_response.startswith('ERROR'):
                    self.get_logger().info(f'✅ YesNo service answer: {extracted_response}')
                    if extracted_response.lower() == 'yes':
                        self.hri_client.start_speaking('He entendido: sí')
                        self.state = State.WAITING_ECHO
                    elif extracted_response.lower() == 'no':
                        self.hri_client.start_speaking('He entendido: no')
                        self.state = State.WAITING_ECHO
                    else:
                        self.state = State.DONE
                else:
                    self.get_logger().error('❌ YesNo error')
                    self.state = State.DONE

        elif self.state == State.WAITING_ECHO:
            if self.hri_client.is_speaking_done():
                if self.hri_client.get_speaking_result():
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error('❌ TTS error')
                self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('🎉 Demo finished.')
            self.timer.cancel()
            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = HRIExample3Client()

    try:
        rclpy.spin(node)  # This blocks main while processing callbacks
    except SystemExit:
        pass  # Clean exit when State == DONE
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # Clean exit with Ctrl+C
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
