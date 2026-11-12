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

"""
Restaurant order with the services of simple_hri: TTS, STT and Extract.

The robot is a waiter: it asks for the whole order, listens to the answer and, with
Extract, takes out of it the drink, the food and the dessert, saying each one back.

The services are called with call_async(), so the node is never blocked: control_loop()
runs 10 times per second and, in each state, only checks whether the pending answer
(the future) has arrived. hri_example2_client does the same with HRIClient.
"""

from enum import auto, Enum
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from simple_hri_interfaces.srv import Extract
from simple_hri_interfaces.srv import Speech
from std_srvs.srv import SetBool

# The robot asks for the whole order in one question...
QUESTION = ('Hola. Vamos a probar la extracción de información. Imagina que soy un camarero y '
            'tú eres un cliente. ¿Qué te gustaría pedir de beber, de comer y de postre?')

# ...and then calls Extract once per course on the same answer. For each course: the
# category (interest) that Extract looks for, and the start of the sentence that repeats it.
# Separating the courses of one sentence needs a good LLM (see README-examples.md):
# with a small one, the drink also comes out as food
COURSES = [
    ('bebida', 'De beber, has pedido: '),
    ('comida', 'De comer, has pedido: '),
    ('postre', 'De postre, has pedido: '),
]

# How long does the robot take to say a sentence?
# The TTS service answers as soon as the audio starts playing, so its answer does not tell
# us when the robot stops talking. We estimate it from the number of words: the voices of
# simple_hri (Piper and MMS-TTS) take between 0.3 and 0.4 s per word.
# (The TTS action, used by hri_example2_client, does finish when the audio ends.)
SECONDS_PER_WORD = 0.35


class State(Enum):
    INIT = auto()               # Ask for the order
    SPEAKING_QUESTION = auto()  # Wait for the TTS service
    LISTEN = auto()             # Start the STT service
    LISTENING = auto()          # Wait for the transcription
    EXTRACT = auto()            # Ask Extract for the course of this turn
    EXTRACTING = auto()         # Wait for the Extract service
    SPEAKING_ORDER = auto()     # Wait for the TTS service that repeats the course
    DONE = auto()


class HRIExample2(Node):

    def __init__(self):
        super().__init__('hri_example2_node')

        # STT client
        self.stt_client = self.create_client(SetBool, '/stt_service')
        while not self.stt_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/stt_service unavailable...')

        # TTS client
        self.tts_client = self.create_client(Speech, '/tts_service')
        while not self.tts_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/tts_service unavailable...')

        # Extract client
        self.extract_client = self.create_client(Extract, '/extract_service')
        while not self.extract_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('/extract_service not available, waiting...')

        self.get_logger().info('✅ Extract, STT and TTS clients ready.')

        self.state = State.INIT
        self.answer = ''            # What the customer said
        self.course = 0             # Index in COURSES of the course being extracted
        self.current_future = None  # Answer of the service called last
        self.sleep_until = 0.0
        self.phrase_to_speak = ''   # Last sentence sent to the TTS

        # Run control_loop() every 0.1 seconds (10 Hz)
        self.timer = self.create_timer(0.1, self.control_loop)

    def is_sleeping(self):
        return time.time() < self.sleep_until

    def set_sleep(self, seconds):
        self.sleep_until = time.time() + seconds

    def speech_duration(self, text):
        """Estimate the seconds that the robot takes to say a text."""
        words = len(text.split())
        return words * SECONDS_PER_WORD + 0.5  # + 0.5 s of margin

    def speak(self, text):
        """Call the TTS service; its answer arrives in self.current_future."""
        self.phrase_to_speak = text  # Kept to estimate how long it lasts
        tts_req = Speech.Request()
        tts_req.text = text
        self.current_future = self.tts_client.call_async(tts_req)

    def wait_until_spoken(self):
        """
        Check the TTS answer, and do not go on until the robot stops talking.

        Otherwise the next sentence would overlap this one or, if the robot listens next,
        the microphone would record the robot's own voice.
        """
        tts_response = self.current_future.result()
        if not tts_response.success:
            self.get_logger().error(f'❌ TTS error: {tts_response.debug}')
        self.set_sleep(self.speech_duration(self.phrase_to_speak))

    def order_to_string(self, order_list, prefix):
        """Sentence that repeats the order, e.g. 'De beber, has pedido: agua y cerveza.'."""
        # Extract answers NONE when it finds nothing
        if not order_list or order_list[0] == 'NONE':
            return prefix + 'nada.'
        if len(order_list) == 1:
            return prefix + order_list[0] + '.'
        return prefix + ', '.join(order_list[:-1]) + ' y ' + order_list[-1] + '.'

    def control_loop(self):
        if self.is_sleeping():
            return

        if self.state == State.INIT:
            self.get_logger().info('🤖 Starting HRI demo with Extract...')
            self.speak(QUESTION)
            self.state = State.SPEAKING_QUESTION

        elif self.state == State.SPEAKING_QUESTION:
            if self.current_future.done():
                self.wait_until_spoken()  # Listen only after the question
                self.state = State.LISTEN

        elif self.state == State.LISTEN:
            self.get_logger().info('🎤 Starting speech recognition (STT)...')
            stt_req = SetBool.Request()
            stt_req.data = True
            self.current_future = self.stt_client.call_async(stt_req)
            self.state = State.LISTENING

        elif self.state == State.LISTENING:
            if self.current_future.done():
                stt_response = self.current_future.result()
                if stt_response.success:
                    self.answer = stt_response.message
                    self.get_logger().info(f'📝 Transcription: {self.answer}')
                else:
                    # Nothing heard: Extract answers NONE for an empty text
                    self.get_logger().error(f'❌ STT error: {stt_response.message}')
                    self.answer = ''
                self.state = State.EXTRACT

        elif self.state == State.EXTRACT:
            # Look for the category of this course in the whole answer
            interest, _ = COURSES[self.course]
            self.get_logger().info(f'🔍 Sending text to the Extract service ({interest})...')
            ext_req = Extract.Request()
            ext_req.text = self.answer
            ext_req.interest = interest
            self.current_future = self.extract_client.call_async(ext_req)
            self.state = State.EXTRACTING

        elif self.state == State.EXTRACTING:
            if self.current_future.done():
                result = self.current_future.result().result
                self.get_logger().info(f'📝 Extracted: {result}')
                if result.startswith('ERROR'):
                    self.get_logger().error(f"❌ Extract error: '{result}'")
                    result = 'NONE'

                # Extract separates the values with ';', e.g. 'agua;cerveza'
                items = result.strip().split(';')
                _, prefix = COURSES[self.course]
                self.speak(self.order_to_string(items, prefix))
                self.state = State.SPEAKING_ORDER

        elif self.state == State.SPEAKING_ORDER:
            if self.current_future.done():
                self.wait_until_spoken()
                # Next course, or the end of the order
                self.course += 1
                if self.course < len(COURSES):
                    self.state = State.EXTRACT
                else:
                    self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('🎉 Demo finished.')
            self.timer.cancel()
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = HRIExample2()

    try:
        rclpy.spin(node)  # Returns when control_loop calls rclpy.shutdown() in state DONE
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()  # Does not fail if rclpy.shutdown() was already called


if __name__ == '__main__':
    main()
