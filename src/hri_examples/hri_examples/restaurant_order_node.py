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
Restaurant order: speak, listen and extract information with HRIClient.

The robot is a waiter: it asks for the whole order, listens to the answer and, with
Extract, takes out of it the drink, the main dishes and the dessert, saying each one back.

Speaking and listening are actions of simple_hri (they last seconds and finish when the
audio ends); Extract is a service (a query on the text already heard).
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
# The categories must not overlap: "comida" would also include the dessert (natillas are
# food too), so the main dishes are asked for as "plato". Separating the courses of one
# sentence needs a good LLM (see README-examples.md)
COURSES = [
    ('bebida', 'De beber, has pedido: '),
    ('plato', 'De comer, has pedido: '),
    ('postre', 'De postre, has pedido: '),
]

# Even so, a dessert said alone ("una cerveza y una tarta de queso") can come out both as
# a dish and as a dessert: what Extract finds as a dessert is removed from the other courses
DESSERT = 'postre'


class State(Enum):
    INIT = auto()               # Ask for the order
    SPEAKING_QUESTION = auto()  # Wait until the robot finishes the question
    LISTENING = auto()          # Wait for the transcription
    EXTRACT = auto()            # Ask Extract for the course of this turn
    EXTRACTING = auto()         # Wait for Extract
    SPEAKING_ORDER = auto()     # Wait until the robot repeats the course
    DONE = auto()


class RestaurantOrder(Node):

    def __init__(self):
        super().__init__('restaurant_order_node')
        self.hri_client = HRIClient(self)

        if not self.hri_client.wait_until_ready(10.0):
            self.get_logger().error('simple_hri not available. Did you launch simple_hri?')

        self.state = State.INIT
        self.answer = ''  # What the customer said
        self.course = 0   # Index in COURSES of the course being extracted or said
        self.order = {}   # Items of each course, e.g. {'bebida': ['agua', 'vino'], ...}

        # Run control_loop() every 0.1 seconds (10 Hz)
        self.timer = self.create_timer(0.1, self.control_loop)

    def order_to_string(self, items, prefix):
        """Sentence that repeats the order, e.g. 'De beber, has pedido: agua y cerveza.'."""
        if not items:
            return prefix + 'nada.'
        if len(items) == 1:
            return prefix + items[0] + '.'
        return prefix + ', '.join(items[:-1]) + ' y ' + items[-1] + '.'

    def remove_dessert_from_other_courses(self):
        """Check the LLM answer: a dessert is not also a drink or a dish."""
        desserts = {item.lower() for item in self.order[DESSERT]}
        for interest, _ in COURSES:
            if interest != DESSERT:
                kept = [item for item in self.order[interest] if item.lower() not in desserts]
                if len(kept) != len(self.order[interest]):
                    self.get_logger().info(f'Removed desserts from {interest}: {kept}')
                self.order[interest] = kept

    def speak_course(self):
        """Say the course self.course of the order."""
        interest, prefix = COURSES[self.course]
        self.hri_client.start_speaking(self.order_to_string(self.order[interest], prefix))
        self.state = State.SPEAKING_ORDER

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
                interest, _ = COURSES[self.course]
                self.get_logger().info(f'📝 Extracted ({interest}): {result}')
                if not result or result.startswith('ERROR'):
                    self.get_logger().error(f"❌ Extract error: '{result}'")
                    result = 'NONE'

                # Extract separates the values with ';', e.g. 'agua;cerveza', and answers
                # NONE when it finds nothing
                items = [item.strip() for item in result.split(';') if item.strip()]
                self.order[interest] = [] if items == ['NONE'] else items

                # Next course, or say the whole order once every course is extracted
                self.course += 1
                if self.course < len(COURSES):
                    self.state = State.EXTRACT
                else:
                    self.remove_dessert_from_other_courses()
                    self.course = 0
                    self.speak_course()

        elif self.state == State.SPEAKING_ORDER:
            if self.hri_client.is_speaking_done():
                self.check_speaking()
                # Next course, or the end of the order
                self.course += 1
                if self.course < len(COURSES):
                    self.speak_course()
                else:
                    self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('🎉 Demo finished.')
            self.timer.cancel()
            raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = RestaurantOrder()

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
