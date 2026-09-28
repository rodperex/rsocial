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
from simple_hri_interfaces.srv import YesNo
from std_srvs.srv import SetBool


class State(Enum):
    INIT = auto()
    WAITING_INTRO = auto()
    WAITING_INTRO_DELAY = auto()
    WAITING_USER_RESPONSE = auto()
    WAITING_YESNO = auto()
    WAITING_ECHO_DELAY = auto()
    WAITING_ECHO = auto()
    DONE = auto()


class HRIExample3(Node):

    def __init__(self):
        super().__init__('hri_example3_node')

        # STT client
        self.stt_client = self.create_client(SetBool, '/stt_service')
        while not self.stt_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/stt_service unavailable...')

        # TTS client
        self.tts_client = self.create_client(Speech, '/tts_service')
        while not self.tts_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/tts_service unavailable...')

        # Extract client
        self.extract_client = self.create_client(YesNo, '/yesno_service')
        while not self.extract_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/yesno_service not available, waiting...')

        self.get_logger().info('✅ YesNo, STT and TTS clients ready.')

        self.state = State.INIT
        self.user_response = ''
        self.current_future = None
        self.sleep_until = 0.0
        self.phrase_to_speak = ''

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
            self.get_logger().info('🤖 Starting HRI demo with YesNo...')

            tts_req = Speech.Request()
            tts_req.text = '¿Estás bien?'
            self.current_future = self.tts_client.call_async(tts_req)
            self.state = State.WAITING_INTRO

        elif self.state == State.WAITING_INTRO:
            if self.current_future and self.current_future.done():
                tts_response = self.current_future.result()
                if tts_response.success:
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error(f'❌ TTS error: {tts_response.debug}')

                # Give it time to finish speaking before starting STT
                self.set_sleep(3.0)
                self.state = State.WAITING_INTRO_DELAY

        elif self.state == State.WAITING_INTRO_DELAY:
            self.get_logger().info('🎤 Starting speech recognition (STT)...')
            stt_req = SetBool.Request()
            stt_req.data = True
            self.current_future = None
            self.current_future = self.stt_client.call_async(stt_req)
            self.state = State.WAITING_USER_RESPONSE

        elif self.state == State.WAITING_USER_RESPONSE:
            if self.current_future and self.current_future.done():
                stt_response = self.current_future.result()
                if not stt_response.success:
                    self.get_logger().error(f'❌ STT error: {stt_response.message}')
                    self.user_response = ''
                else:
                    self.user_response = stt_response.message
                    self.get_logger().info(f'📝 Transcription: {self.user_response}')

                self.get_logger().info('🔍 Sending text to the YesNo service...')
                ext_req = YesNo.Request()
                ext_req.text = self.user_response
                self.current_future = None
                self.current_future = self.extract_client.call_async(ext_req)
                self.state = State.WAITING_YESNO

        elif self.state == State.WAITING_YESNO:
            if self.current_future and self.current_future.done():
                extract_response = self.current_future.result()
                extracted_text = extract_response.result
                self.get_logger().info(f'📝 Answer: {extracted_text}')

                if extracted_text and not extracted_text.startswith('ERROR'):
                    self.get_logger().info(f'✅ YesNo service answer: {extracted_text}')
                    if extracted_text.lower() == 'yes':
                        self.phrase_to_speak = 'He entendido: sí'
                        self.set_sleep(2.0)
                        self.state = State.WAITING_ECHO_DELAY
                    elif extracted_text.lower() == 'no':
                        self.phrase_to_speak = 'He entendido: no'
                        self.set_sleep(2.0)
                        self.state = State.WAITING_ECHO_DELAY
                    else:
                        self.get_logger().warn(
                            f'⚠️ Answer not recognized as yes/no: {extracted_text}')
                        self.state = State.DONE
                else:
                    self.get_logger().error(
                        f"❌ YesNo error: result '{extract_response.result}'")
                    self.state = State.DONE

        elif self.state == State.WAITING_ECHO_DELAY:
            tts_req = Speech.Request()
            tts_req.text = self.phrase_to_speak
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

                self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('🎉 Demo finished.')
            self.timer.cancel()
            rclpy.shutdown()
            return


def main(args=None):
    rclpy.init(args=args)
    node = HRIExample3()

    try:
        rclpy.spin(node)  # Returns when control_loop calls rclpy.shutdown() in state DONE
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()  # Does not fail if rclpy.shutdown() was already called


if __name__ == '__main__':
    main()
