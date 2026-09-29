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

from action_msgs.msg import GoalStatus
from rclpy.action import ActionClient
from rclpy.node import Node
from simple_hri_interfaces.action import Listen, Say
from simple_hri_interfaces.srv import Extract, YesNo
from std_msgs.msg import String


class OperationState(Enum):
    IDLE = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    ERROR = 4
    TIMEOUT = 5
    CANCELED = 6


FINISHED_STATES = (OperationState.COMPLETED, OperationState.ERROR,
                   OperationState.TIMEOUT, OperationState.CANCELED)


class _ActionCall:
    """Non-blocking tracking of one action goal: poll() it on each control cycle."""

    def __init__(self, client, goal, feedback_callback):
        self._goal_future = client.send_goal_async(goal, feedback_callback=feedback_callback)
        self._handle = None
        self._result_future = None
        self._cancel_sent = False

    def poll(self):
        """Return None while running, or (status, result) when finished."""
        if self._result_future is None:
            if not self._goal_future.done():
                return None
            self._handle = self._goal_future.result()
            if not self._handle.accepted:
                return GoalStatus.STATUS_ABORTED, None
            self._result_future = self._handle.get_result_async()
        if not self._result_future.done():
            return None
        response = self._result_future.result()
        return response.status, response.result

    def cancel(self):
        """Ask the server to cancel the goal, even if it has not been accepted yet."""
        if self._cancel_sent:
            return
        self._cancel_sent = True
        if self._goal_future.done():
            self._cancel_when_accepted(self._goal_future)
        else:
            self._goal_future.add_done_callback(self._cancel_when_accepted)

    @staticmethod
    def _cancel_when_accepted(goal_future):
        handle = goal_future.result()
        if handle.accepted:
            handle.cancel_goal_async()


class HRIClient:
    def __init__(self, node: Node):
        self._node = node

        # Listening and speaking are actions (feedback, cancellation, real end of playback);
        # extraction and yes/no detection are services
        self._listen_action = ActionClient(self._node, Listen, '/stt_action')
        self._say_action = ActionClient(self._node, Say, '/tts_action')
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
        self._stt_call = None
        self._stt_feedback = ''

        self._tts_state = OperationState.IDLE
        self._tts_result = False
        self._tts_deadline = None
        self._tts_call = None
        self._tts_remaining = -1.0

        self._extract_state = OperationState.IDLE
        self._extracted_info = ''
        self._extract_future = None
        self._extract_deadline = None

        self._yesno_state = OperationState.IDLE
        self._yesno_result = ''
        self._yesno_future = None
        self._yesno_deadline = None

        self._node.get_logger().debug('HRI client initialized')

    def wait_for_services(self, timeout_sec: float = 5.0) -> bool:
        """Wait for the simple_hri actions (listen, speak) and services (extract, yes/no)."""
        all_ready = True

        if not self._listen_action.wait_for_server(timeout_sec=timeout_sec):
            self._node.get_logger().error('STT action (/stt_action) not available')
            all_ready = False

        if not self._say_action.wait_for_server(timeout_sec=timeout_sec):
            self._node.get_logger().error('TTS action (/tts_action) not available')
            all_ready = False

        if not self._extract_client.wait_for_service(timeout_sec):
            self._node.get_logger().error('Extract service not available')
            all_ready = False

        if not self._yesno_client.wait_for_service(timeout_sec):
            self._node.get_logger().error('YesNo service not available')
            all_ready = False

        if all_ready:
            self._node.get_logger().debug('All HRI actions and services available')

        return all_ready

    # ============ TIMEOUT AND CANCELLATION HELPERS ============

    def _deadline(self, timeout_sec):
        return None if timeout_sec is None else time.time() + timeout_sec

    def _expired(self, deadline) -> bool:
        return deadline is not None and time.time() > deadline

    def _abandon(self, client, future):
        # A service call cannot be canceled: forget the request so a late response is ignored
        if future is not None and not future.done():
            client.remove_pending_request(future)

    # ============ ASYNCHRONOUS METHODS ============

    def start_listen(self, timeout_sec: float = None):
        # timeout_sec: time for the person to START speaking (the server stops recording
        # if nobody speaks); once they speak, it waits until they finish
        if self._stt_state == OperationState.IN_PROGRESS:
            self._node.get_logger().debug('STT already in progress, ignoring new request')
            return

        self._node.get_logger().info('Starting to listen (STT)...')

        self._stt_state = OperationState.IN_PROGRESS
        self._stt_text = ''
        self._stt_feedback = ''

        goal = Listen.Goal()
        goal.max_wait = float(timeout_sec) if timeout_sec is not None else 0.0
        self._stt_call = _ActionCall(self._listen_action, goal, self._listen_feedback_callback)

    def is_listen_done(self) -> bool:
        if self._stt_state != OperationState.IN_PROGRESS:
            return self._stt_state in FINISHED_STATES

        finished = self._stt_call.poll()
        if finished is None:
            return False
        status, result = finished
        if status == GoalStatus.STATUS_SUCCEEDED and result.success:
            self._stt_text = result.text
            self._stt_state = OperationState.COMPLETED
            self._node.get_logger().info(f"STT completed: '{self._stt_text}'")
        elif status == GoalStatus.STATUS_CANCELED:
            self._stt_state = OperationState.CANCELED
        elif result is not None and result.timed_out:
            self._stt_state = OperationState.TIMEOUT
            self._node.get_logger().warning('STT timed out: nobody spoke')
        else:
            self._stt_state = OperationState.ERROR
            error_msg = result.message if result is not None else 'goal rejected'
            self._node.get_logger().warning(f'STT failed: {error_msg}')
        return True

    def get_listened_text(self) -> str:
        return self._stt_text

    def start_speaking(self, text: str, timeout_sec: float = None):
        # The action finishes when playback really ends; timeout_sec cancels it (stopping
        # the audio) if it takes longer
        if self._tts_state == OperationState.IN_PROGRESS:
            self._node.get_logger().debug('TTS already in progress, ignoring new request')
            return

        self._node.get_logger().info(f"Starting TTS: '{text}'")

        self._tts_state = OperationState.IN_PROGRESS
        self._tts_result = False
        self._tts_remaining = -1.0
        self._tts_deadline = self._deadline(timeout_sec)

        goal = Say.Goal()
        goal.text = text
        self._tts_call = _ActionCall(self._say_action, goal, self._say_feedback_callback)

    def is_speaking_done(self) -> bool:
        if self._tts_state != OperationState.IN_PROGRESS:
            return self._tts_state in FINISHED_STATES

        finished = self._tts_call.poll()
        if finished is None:
            if self._expired(self._tts_deadline):
                self._tts_call.cancel()  # The server stops the audio
                self._tts_state = OperationState.TIMEOUT
                self._node.get_logger().warning('TTS timed out')
                return True
            return False
        status, result = finished
        if status == GoalStatus.STATUS_SUCCEEDED and result.success:
            self._tts_result = True
            self._tts_state = OperationState.COMPLETED
            self._node.get_logger().info('TTS completed')
        elif status == GoalStatus.STATUS_CANCELED:
            self._tts_state = OperationState.CANCELED
        else:
            self._tts_state = OperationState.ERROR
            self._node.get_logger().error('TTS failed')
        return True

    def get_speaking_result(self) -> bool:
        return self._tts_result

    def start_extract(self, interest: str, text: str = '', timeout_sec: float = None):
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
        self._extract_deadline = self._deadline(timeout_sec)
        self._extract_future = self._extract_client.call_async(request)

    def is_extract_done(self) -> bool:
        if self._extract_state != OperationState.IN_PROGRESS:
            return self._extract_state in FINISHED_STATES

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

        if self._expired(self._extract_deadline):
            self._abandon(self._extract_client, self._extract_future)
            self._extract_state = OperationState.TIMEOUT
            self._node.get_logger().warning('Extract timed out')
            return True

        return False

    def get_extracted_info(self) -> str:
        return self._extracted_info

    def start_yesno(self, text: str = '', timeout_sec: float = None):
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
        self._yesno_result = ''
        self._yesno_deadline = self._deadline(timeout_sec)
        self._yesno_future = self._yesno_client.call_async(request)

    def is_yesno_done(self) -> bool:
        if self._yesno_state != OperationState.IN_PROGRESS:
            return self._yesno_state in FINISHED_STATES

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

        if self._expired(self._yesno_deadline):
            self._abandon(self._yesno_client, self._yesno_future)
            self._yesno_state = OperationState.TIMEOUT
            self._node.get_logger().warning('YesNo timed out')
            return True

        return False

    def get_yesno_result(self) -> str:
        return self._yesno_result

    # ============ CANCELLATION AND STATE ============

    def cancel_listen(self):
        if self._stt_state == OperationState.IN_PROGRESS:
            self._stt_call.cancel()  # The server stops recording
            self._stt_state = OperationState.CANCELED
            self._node.get_logger().info('STT canceled')

    def cancel_speaking(self):
        if self._tts_state == OperationState.IN_PROGRESS:
            self._tts_call.cancel()  # The server stops the audio
            self._tts_result = False
            self._tts_state = OperationState.CANCELED
            self._node.get_logger().info('TTS canceled')

    def cancel_extract(self):
        if self._extract_state == OperationState.IN_PROGRESS:
            self._abandon(self._extract_client, self._extract_future)
            self._extract_state = OperationState.CANCELED
            self._node.get_logger().info('Extract canceled')

    def cancel_yesno(self):
        if self._yesno_state == OperationState.IN_PROGRESS:
            self._abandon(self._yesno_client, self._yesno_future)
            self._yesno_state = OperationState.CANCELED
            self._node.get_logger().info('YesNo canceled')

    def get_listen_state(self) -> OperationState:
        return self._stt_state

    def get_speaking_state(self) -> OperationState:
        return self._tts_state

    def get_extract_state(self) -> OperationState:
        return self._extract_state

    def get_yesno_state(self) -> OperationState:
        return self._yesno_state

    def get_listen_feedback(self) -> str:
        """Stage of the current listening: 'listening', 'speech_detected', 'transcribing'."""
        return self._stt_feedback

    def get_speaking_feedback(self) -> float:
        """Seconds of playback left, or -1.0 before the first feedback."""
        return self._tts_remaining

    def _listen_feedback_callback(self, feedback_msg):
        self._stt_feedback = feedback_msg.feedback.status

    def _say_feedback_callback(self, feedback_msg):
        self._tts_remaining = feedback_msg.feedback.remaining

    def _listened_text_callback(self, msg: String):
        self._last_listened_text = msg.data
        self._node.get_logger().debug(f'Texto escuchado recibido: {self._last_listened_text}')

    def get_last_listened_text(self) -> str:
        return self._last_listened_text
