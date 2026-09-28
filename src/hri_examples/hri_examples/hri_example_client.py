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
    WAITING_LISTENING = auto()
    WAITING_ECHO_INTRO = auto()
    WAITING_ECHO = auto()
    DONE = auto()


class HRIExampleClient(Node):

    def __init__(self):
        super().__init__('hri_example_client_node')
        self.hri_client = HRIClient(self)

        if not self.hri_client.wait_for_services(10.0):
            self.get_logger().error('Services not available.')

        self.get_logger().info('✅ STT and TTS clients ready.')

        self.state = State.INIT
        self.transcribed_text = ''

        self.timer = self.create_timer(0.1, self.control_loop)

    def control_loop(self):
        if self.state == State.INIT:
            self.get_logger().info('🤖 Starting HRI demo...')
            self.hri_client.start_speaking(
                'Hola. Vamos a probar el reconocimiento de voz y la síntesis de voz. Habla ahora.')
            self.state = State.WAITING_INTRO

        elif self.state == State.WAITING_INTRO:
            if self.hri_client.is_speaking_done():
                if self.hri_client.get_speaking_result():
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error('❌ TTS error')

                self.get_logger().info('🎤 Starting speech recognition (STT)...')
                self.hri_client.start_listen()
                self.state = State.WAITING_LISTENING

        elif self.state == State.WAITING_LISTENING:
            if self.hri_client.is_listen_done():
                self.transcribed_text = self.hri_client.get_listened_text()
                if not self.transcribed_text:
                    self.get_logger().error('❌ STT error')
                    self.state = State.DONE
                    return

                self.get_logger().info(f'📝 Transcription: {self.transcribed_text}')
                self.hri_client.start_speaking('Ahora voy a repetir lo que has dicho')
                self.state = State.WAITING_ECHO_INTRO

        elif self.state == State.WAITING_ECHO_INTRO:
            if self.hri_client.is_speaking_done():
                self.get_logger().info('🔊 Sending text to TTS...')
                self.hri_client.start_speaking(self.transcribed_text)
                self.state = State.WAITING_ECHO

        elif self.state == State.WAITING_ECHO:
            if self.hri_client.is_speaking_done():
                if self.hri_client.get_speaking_result():
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error('❌ TTS error')
                self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('🎉 Demo finished.')
            self.timer.cancel()  # Stop the control loop

            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = HRIExampleClient()

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
