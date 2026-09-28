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
    WAITING_EXTRACT_DRINK = auto()
    WAITING_ECHO_DRINK = auto()
    WAITING_EXTRACT_FOOD = auto()
    WAITING_ECHO_FOOD = auto()
    WAITING_EXTRACT_DESSERT = auto()
    WAITING_ECHO_DESSERT = auto()
    DONE = auto()


class HRIExample2Client(Node):

    def __init__(self):
        super().__init__('hri_example2_client_node')
        self.hri_client = HRIClient(self)

        if not self.hri_client.wait_for_services(10.0):
            self.get_logger().info('Services not available, waiting...')

        self.get_logger().info('✅ Extract, STT and TTS clients ready.')

        self.state = State.INIT
        self.user_response = ''

        # Run control_loop() every 0.1 seconds (10 Hz)
        self.timer = self.create_timer(0.1, self.control_loop)

    def order_to_string(self, order_list, prefix):
        n = len(order_list)
        phrase = prefix

        if not order_list:
            return phrase + 'nada.'

        if order_list[0] == 'NONE':
            phrase += 'nada.'
            return phrase
        elif len(order_list) == 1:
            phrase += order_list[0] + '.'
            return phrase

        for i in range(n):
            if i == n - 1 and n > 1:  # Last item
                phrase += 'y ' + order_list[i] + '.'
            else:
                phrase += order_list[i] + ', '

        return phrase

    def control_loop(self):
        if self.state == State.INIT:
            self.get_logger().info('🤖 Starting HRI demo with Extract...')
            self.hri_client.start_speaking(
                'Hola. Vamos a probar la extracción de información. Imagina que soy un camarero '
                'y tú eres un cliente que va a hacer un pedido. ¿Qué te gustaría pedir de beber y '
                'de comer?'
            )
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

                self.get_logger().info('🔍 Sending text to the Extract service (drink)...')
                self.hri_client.start_extract('bebida', self.user_response)
                self.state = State.WAITING_EXTRACT_DRINK

        elif self.state == State.WAITING_EXTRACT_DRINK:
            if self.hri_client.is_extract_done():
                extracted_text = self.hri_client.get_extracted_info()
                self.get_logger().info(f'📝 Extracted (drink): {extracted_text}')

                if extracted_text and not extracted_text.startswith('ERROR'):
                    list_items = extracted_text.strip('\n').split(';')
                    n = len(list_items)
                    self.get_logger().info(f'✅ {n} items of interest extracted.')
                    phrase = self.order_to_string(list_items, 'De beber, has pedido: ')
                    self.hri_client.start_speaking(phrase)
                    self.state = State.WAITING_ECHO_DRINK
                else:
                    # If it fails, go straight to the food
                    self.get_logger().info(
                        '🔍 Sending text to the Extract service (main courses)...')
                    self.hri_client.start_extract('platos principales', self.user_response)
                    self.state = State.WAITING_EXTRACT_FOOD

        elif self.state == State.WAITING_ECHO_DRINK:
            if self.hri_client.is_speaking_done():
                # Pasamos a procesar platos principales
                self.get_logger().info(
                    '🔍 Sending text to the Extract service (main courses)...')
                self.hri_client.start_extract('platos principales', self.user_response)
                self.state = State.WAITING_EXTRACT_FOOD

        elif self.state == State.WAITING_EXTRACT_FOOD:
            if self.hri_client.is_extract_done():
                extracted_text = self.hri_client.get_extracted_info()
                self.get_logger().info(
                    f'📝 Extracted (main courses): {extracted_text}')

                if extracted_text and not extracted_text.startswith('ERROR'):
                    list_items = extracted_text.strip('\n').split(';')
                    n = len(list_items)
                    self.get_logger().info(f'✅ {n} items of interest extracted.')
                    phrase = self.order_to_string(list_items, 'Y de comer, has pedido: ')
                    self.hri_client.start_speaking(phrase)
                    self.state = State.WAITING_ECHO_FOOD
                else:
                    # If it fails, go straight to the desserts
                    self.get_logger().info('🔍 Sending text to the Extract service (desserts)...')
                    self.hri_client.start_extract('postres', self.user_response)
                    self.state = State.WAITING_EXTRACT_DESSERT

        elif self.state == State.WAITING_ECHO_FOOD:
            if self.hri_client.is_speaking_done():
                # Pasamos a procesar postres
                self.get_logger().info('🔍 Sending text to the Extract service (desserts)...')
                self.hri_client.start_extract('postres', self.user_response)
                self.state = State.WAITING_EXTRACT_DESSERT

        elif self.state == State.WAITING_EXTRACT_DESSERT:
            if self.hri_client.is_extract_done():
                extracted_text = self.hri_client.get_extracted_info()
                self.get_logger().info(f'📝 Extracted (desserts): {extracted_text}')

                if extracted_text and not extracted_text.startswith('ERROR'):
                    list_items = extracted_text.strip('\n').split(';')
                    n = len(list_items)
                    self.get_logger().info(f'✅ {n} items of interest extracted.')
                    phrase = self.order_to_string(list_items, 'De postre, quieres: ')
                    self.hri_client.start_speaking(phrase)
                    self.state = State.WAITING_ECHO_DESSERT
                else:
                    self.state = State.DONE

        elif self.state == State.WAITING_ECHO_DESSERT:
            if self.hri_client.is_speaking_done():
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
