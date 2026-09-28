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
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from simple_hri_interfaces.srv import Speech
from std_srvs.srv import SetBool


class State(Enum):
    INIT = auto()
    WAITING_INTRO = auto()
    WAITING_DELAY = auto()
    WAITING_LISTENING = auto()
    WAITING_ECHO_INTRO = auto()
    WAITING_ECHO_DELAY = auto()
    WAITING_ECHO = auto()
    DONE = auto()


class HRIExample(Node):

    def __init__(self):
        super().__init__('hri_example_node')

        # STT client
        self.stt_client = self.create_client(SetBool, '/stt_service')
        while not self.stt_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/stt_service unavailable...')

        # TTS client
        self.tts_client = self.create_client(Speech, '/tts_service')
        while not self.tts_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/tts_service unavailable...')

        self.get_logger().info('✅ STT and TTS clients ready.')

        self.state = State.INIT
        self.transcribed_text = ''
        self.current_future = None
        self.sleep_until = 0.0

        # Run control_loop() every 0.1 seconds (10 Hz)
        self.timer = self.create_timer(0.1, self.control_loop)

    def is_sleeping(self):
        return time.time() < self.sleep_until

    def set_sleep(self, seconds):
        self.sleep_until = time.time() + seconds

    def control_loop(self):
        if self.is_sleeping():
            return

        if self.state == State.INIT:
            self.get_logger().info('🤖 Starting HRI demo...')

            tts_req = Speech.Request()
            tts_req.text = ('Hola. Vamos a probar el reconocimiento de voz y la síntesis de voz. '
                            'Habla ahora.')
            self.current_future = self.tts_client.call_async(tts_req)
            self.state = State.WAITING_INTRO

        elif self.state == State.WAITING_INTRO:
            if self.current_future and self.current_future.done():
                tts_response = self.current_future.result()
                if tts_response.success:
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error(f'❌ TTS error: {tts_response.debug}')

                # TTS has finished the intro, but the audio might still be playing.
                # Set a non-blocking delay and move to an intermediate state
                self.set_sleep(8.0)
                self.state = State.WAITING_DELAY

        elif self.state == State.WAITING_DELAY:
            # Once the 8 seconds of the sleep have passed, we get here.
            self.get_logger().info('🎤 Starting speech recognition (STT)...')
            stt_req = SetBool.Request()
            stt_req.data = True  # Tell the service to start recording
            self.current_future = None
            self.current_future = self.stt_client.call_async(stt_req)
            self.state = State.WAITING_LISTENING

        elif self.state == State.WAITING_LISTENING:
            if self.current_future and self.current_future.done():
                stt_response = self.current_future.result()
                if not stt_response.success:
                    self.get_logger().error(f'❌ STT error: {stt_response.message}')
                    self.state = State.DONE
                    return

                self.transcribed_text = stt_response.message
                self.get_logger().info(f'📝 Transcription: {self.transcribed_text}')

                tts_req = Speech.Request()
                tts_req.text = 'Ahora voy a repetir lo que has dicho'
                self.current_future = None
                self.current_future = self.tts_client.call_async(tts_req)
                self.state = State.WAITING_ECHO_INTRO

        elif self.state == State.WAITING_ECHO_INTRO:
            if self.current_future and self.current_future.done():
                tts_response = self.current_future.result()
                self.set_sleep(4.0)
                self.state = State.WAITING_ECHO_DELAY

        elif self.state == State.WAITING_ECHO_DELAY:
            # Once the 4 seconds of the sleep in WAITING_ECHO_INTRO have passed
            self.get_logger().info('🔊 Sending text to TTS...')
            tts_req = Speech.Request()
            tts_req.text = self.transcribed_text
            self.current_future = None
            self.current_future = self.tts_client.call_async(tts_req)
            self.state = State.WAITING_ECHO

        elif self.state == State.WAITING_ECHO:
            if self.current_future and self.current_future.done():
                tts_response = self.current_future.result()
                if tts_response.success:
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error(f'❌ TTS error: {tts_response.debug}')

                # self.set_sleep(5.0)
                self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('🎉 Demo finished.')
            self.timer.cancel()

            # Shutting down rclpy from the callback makes rclpy.spin() in main() return
            rclpy.shutdown()
            return


def main(args=None):
    rclpy.init(args=args)
    node = HRIExample()

    try:
        rclpy.spin(node)  # Returns when control_loop calls rclpy.shutdown() in state DONE
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()  # Does not fail if rclpy.shutdown() was already called


if __name__ == '__main__':
    main()
