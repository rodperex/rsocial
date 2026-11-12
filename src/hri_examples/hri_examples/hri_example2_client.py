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
Restaurant order with HRIClient: the same as hri_example2, without calling the services.

The robot is a waiter: it asks for the whole order, listens to the answer and, with
Extract, takes out of it the drink, the food and the dessert, saying each one back.

HRIClient speaks and listens with the actions of simple_hri, which finish when the audio
ends, so here there is no need to estimate how long the robot takes to say each sentence.
"""

from enum import auto, Enum

from hri_client.hri_client import HRIClient, OperationState
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

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


class State(Enum):
    INIT = auto()               # Ask for the order
    SPEAKING_QUESTION = auto()  # Wait until the robot finishes the question
    LISTENING = auto()          # Wait for the transcription
    EXTRACT = auto()            # Ask Extract for the course of this turn
    EXTRACTING = auto()         # Wait for Extract
    SPEAKING_ORDER = auto()     # Wait until the robot repeats the course
    DONE = auto()


class HRIExample2Client(Node):

    def __init__(self):
        super().__init__('hri_example2_client_node')
        self.hri_client = HRIClient(self)

        if not self.hri_client.wait_until_ready(10.0):
            self.get_logger().info('Services not available, waiting...')

        self.get_logger().info('✅ Extract, STT and TTS clients ready.')

        self.state = State.INIT
        self.answer = ''  # What the customer said
        self.course = 0   # Index in COURSES of the course being extracted

        # Run control_loop() every 0.1 seconds (10 Hz)
        self.timer = self.create_timer(0.1, self.control_loop)

    def order_to_string(self, order_list, prefix):
        """Sentence that repeats the order, e.g. 'De beber, has pedido: agua y cerveza.'."""
        # Extract answers NONE when it finds nothing
        if not order_list or order_list[0] == 'NONE':
            return prefix + 'nada.'
        if len(order_list) == 1:
            return prefix + order_list[0] + '.'
        return prefix + ', '.join(order_list[:-1]) + ' y ' + order_list[-1] + '.'

    def check_speaking(self):
        """Log an error if the robot could not say the last sentence."""
        if self.hri_client.get_speaking_state() != OperationState.COMPLETED:
            self.get_logger().error('❌ TTS error')

    def control_loop(self):
        if self.state == State.INIT:
            self.get_logger().info('🤖 Starting HRI demo with Extract...')
            self.hri_client.start_speaking(QUESTION)
            self.state = State.SPEAKING_QUESTION

        elif self.state == State.SPEAKING_QUESTION:
            # Listen only when the robot has finished the question, or the microphone
            # would record the robot's own voice
            if self.hri_client.is_speaking_done():
                self.check_speaking()
                self.get_logger().info('🎤 Starting speech recognition (STT)...')
                self.hri_client.start_listening()
                self.state = State.LISTENING

        elif self.state == State.LISTENING:
            if self.hri_client.is_listening_done():
                self.answer = self.hri_client.get_listened_text()
                if self.answer:
                    self.get_logger().info(f'📝 Transcription: {self.answer}')
                else:
                    # Nothing heard: Extract answers NONE for an empty text
                    self.get_logger().error('❌ STT error')
                self.state = State.EXTRACT

        elif self.state == State.EXTRACT:
            # Look for the category of this course in the whole answer
            interest, _ = COURSES[self.course]
            self.get_logger().info(f'🔍 Sending text to the Extract service ({interest})...')
            self.hri_client.start_extract(interest, self.answer)
            self.state = State.EXTRACTING

        elif self.state == State.EXTRACTING:
            if self.hri_client.is_extract_done():
                result = self.hri_client.get_extracted_info()
                self.get_logger().info(f'📝 Extracted: {result}')
                if not result or result.startswith('ERROR'):
                    self.get_logger().error(f"❌ Extract error: '{result}'")
                    result = 'NONE'

                # Extract separates the values with ';', e.g. 'agua;cerveza'
                items = result.strip().split(';')
                _, prefix = COURSES[self.course]
                self.hri_client.start_speaking(self.order_to_string(items, prefix))
                self.state = State.SPEAKING_ORDER

        elif self.state == State.SPEAKING_ORDER:
            if self.hri_client.is_speaking_done():
                self.check_speaking()
                # Next course, or the end of the order
                self.course += 1
                if self.course < len(COURSES):
                    self.state = State.EXTRACT
                else:
                    self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('🎉 Demo finished.')
            self.timer.cancel()
            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = HRIExample2Client()

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
