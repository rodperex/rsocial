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

from enum import Enum
import time

from rclpy.node import Node
from simple_hri_interfaces.srv import Extract, Speech, YesNo
from std_msgs.msg import String
from std_srvs.srv import SetBool


class OperationState(Enum):
    IDLE = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    ERROR = 4


class HRIClient:
    def __init__(self, node: Node):
        self._node = node

        # Create service clients
        self._stt_client = self._node.create_client(SetBool, '/stt_service')
        self._tts_client = self._node.create_client(Speech, '/tts_service')
        self._extract_client = self._node.create_client(Extract, '/extract_service')
        self._yesno_client = self._node.create_client(YesNo, '/yesno_service')

        # Subscribe to listened text topic
        self._listened_text_sub = self._node.create_subscription(
            String,
            '/listened_text',
            self._listened_text_callback,
            10
        )

        self._last_listened_text = ''

        # States for async operations
        self._stt_state = OperationState.IDLE
        self._stt_text = ''
        self._stt_future = None

        self._tts_state = OperationState.IDLE
        self._tts_result = False
        self._tts_start_time = 0.0
        self._tts_expected_duration = 0.0
        self._tts_service_responded = False
        self._tts_future = None

        self._extract_state = OperationState.IDLE
        self._extracted_info = ''
        self._extract_future = None

        self._yesno_state = OperationState.IDLE
        self._yesno_result = ''
        self._yesno_future = None

        self._node.get_logger().debug('HRI client initialized')

    def wait_for_services(self, timeout_sec: float = 5.0) -> bool:
        all_ready = True

        if not self._stt_client.wait_for_service(timeout_sec):
            self._node.get_logger().error('STT service not available')
            all_ready = False

        if not self._tts_client.wait_for_service(timeout_sec):
            self._node.get_logger().error('TTS service not available')
            all_ready = False

        if not self._extract_client.wait_for_service(timeout_sec):
            self._node.get_logger().error('Extract service not available')
            all_ready = False

        if not self._yesno_client.wait_for_service(timeout_sec):
            self._node.get_logger().error('YesNo service not available')
            all_ready = False

        if all_ready:
            self._node.get_logger().debug('All HRI services available')

        return all_ready

    # ============ ASYNCHRONOUS METHODS ============

    def start_listen(self):
        if self._stt_state == OperationState.IN_PROGRESS:
            self._node.get_logger().debug('STT already in progress, ignoring new request')
            return

        request = SetBool.Request()
        request.data = True

        self._node.get_logger().info('Starting to listen (STT)...')

        self._stt_state = OperationState.IN_PROGRESS
        self._stt_text = ''
        self._stt_future = self._stt_client.call_async(request)

    def is_listen_done(self) -> bool:
        if self._stt_state != OperationState.IN_PROGRESS:
            return self._stt_state in (OperationState.COMPLETED, OperationState.ERROR)

        if self._stt_future is not None and self._stt_future.done():
            response = self._stt_future.result()
            if response is not None and response.success:
                self._stt_text = response.message
                self._stt_state = OperationState.COMPLETED
                self._node.get_logger().info(f"STT completed: '{self._stt_text}'")
            else:
                self._stt_state = OperationState.ERROR
                error_msg = response.message if response else 'Unknown error'
                self._node.get_logger().warning(f'STT failed: {error_msg}')
            return True

        return False

    def get_listened_text(self) -> str:
        return self._stt_text

    def start_speaking(self, text: str):
        if self._tts_state == OperationState.IN_PROGRESS:
            self._node.get_logger().debug('TTS already in progress, ignoring new request')
            return

        request = Speech.Request()
        request.text = text

        self._node.get_logger().info(f"Starting TTS: '{text}'")

        self._tts_state = OperationState.IN_PROGRESS
        self._tts_start_time = time.time()
        self._tts_service_responded = False

        # Estimate duration based on text length: ~10 chars per second + 500ms margin
        text_length = len(text)
        self._tts_expected_duration = (text_length * 0.1) + 0.5

        self._node.get_logger().debug(
            f'Estimated TTS duration: {self._tts_expected_duration * 1000} ms')

        self._tts_future = self._tts_client.call_async(request)

    def is_speaking_done(self) -> bool:
        if self._tts_state != OperationState.IN_PROGRESS:
            return self._tts_state in (OperationState.COMPLETED, OperationState.ERROR)

        if (not self._tts_service_responded and self._tts_future is not None
                and self._tts_future.done()):
            response = self._tts_future.result()
            if response is None or not response.success:
                self._tts_result = False
                self._tts_state = OperationState.ERROR
                self._node.get_logger().error('TTS failed')
                return True

            self._tts_result = True
            self._tts_service_responded = True
            self._node.get_logger().debug('TTS service responded, waiting for playback...')

        elapsed = time.time() - self._tts_start_time

        if elapsed >= self._tts_expected_duration and self._tts_service_responded:
            self._tts_state = OperationState.COMPLETED
            self._node.get_logger().info(f'TTS completed (duration: {int(elapsed * 1000)} ms)')
            return True

        return False

    def get_speaking_result(self) -> bool:
        return self._tts_result

    def start_extract(self, interest: str, text: str = ''):
        if self._extract_state == OperationState.IN_PROGRESS:
            self._node.get_logger().debug('Extract already in progress, ignoring new request')
            return

        request = Extract.Request()
        request.interest = interest
        request.text = text

        if not text:
            # simple_hri does not record audio in Extract: with an empty text it returns "NONE".
            # Get the text first with start_listen()/get_listened_text().
            self._node.get_logger().warning(f"Extraction of '{interest}' with empty text")
        else:
            self._node.get_logger().info(f"Starting extraction from text '{text}': {interest}")

        self._extract_state = OperationState.IN_PROGRESS
        self._extracted_info = ''
        self._extract_future = self._extract_client.call_async(request)

    def is_extract_done(self) -> bool:
        if self._extract_state != OperationState.IN_PROGRESS:
            return self._extract_state in (OperationState.COMPLETED, OperationState.ERROR)

        if self._extract_future is not None and self._extract_future.done():
            response = self._extract_future.result()
            if response is not None:
                self._extracted_info = response.result
                # simple_hri returns "ERROR..." on failure and "NONE" if nothing is found
                if self._extracted_info and not self._extracted_info.startswith('ERROR'):
                    self._extract_state = OperationState.COMPLETED
                    self._node.get_logger().info(f'Extraction completed: {self._extracted_info}')
                else:
                    self._extract_state = OperationState.ERROR
                    self._node.get_logger().warning(
                        f"Extraction could not get the information: '{self._extracted_info}'")
            else:
                self._extract_state = OperationState.ERROR
                self._node.get_logger().warning('Call to the extract service failed')
            return True

        return False

    def get_extracted_info(self) -> str:
        return self._extracted_info

    def start_yesno(self, text: str = ''):
        if self._yesno_state == OperationState.IN_PROGRESS:
            self._node.get_logger().debug('YesNo already in progress, ignoring new request')
            return

        request = YesNo.Request()
        request.text = text

        if not text:
            # simple_hri does not record audio in YesNo:
            # with an empty text it returns "ERROR: Empty text"
            self._node.get_logger().warning('Yes/no detection with empty text')
        else:
            self._node.get_logger().info(f"Starting yes/no detection from text '{text}'")

        self._yesno_state = OperationState.IN_PROGRESS
        self._yesno_future = self._yesno_client.call_async(request)

    def is_yesno_done(self) -> bool:
        if self._yesno_state != OperationState.IN_PROGRESS:
            return self._yesno_state in (OperationState.COMPLETED, OperationState.ERROR)

        if self._yesno_future is not None and self._yesno_future.done():
            response = self._yesno_future.result()
            if response is not None:
                self._yesno_result = response.result
                answer_lower = response.result.lower()
                if answer_lower in ('yes', 'no'):
                    self._yesno_state = OperationState.COMPLETED
                    self._node.get_logger().info(f'YesNo completed: {response.result}')
                else:
                    self._yesno_state = OperationState.ERROR
                    self._node.get_logger().warning(
                        f'YesNo could not get a valid answer: {response.result}')
            else:
                self._yesno_state = OperationState.ERROR
                self._node.get_logger().warning('Call to the yes/no service failed')
            return True

        return False

    def get_yesno_result(self) -> str:
        return self._yesno_result

    def _listened_text_callback(self, msg: String):
        self._last_listened_text = msg.data
        self._node.get_logger().debug(f'Texto escuchado recibido: {self._last_listened_text}')

    def get_last_listened_text(self) -> str:
        return self._last_listened_text
