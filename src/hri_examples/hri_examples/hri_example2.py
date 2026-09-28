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
from simple_hri_interfaces.srv import Extract
from simple_hri_interfaces.srv import Speech
from std_srvs.srv import SetBool


class State(Enum):
    INIT = auto()
    WAITING_INTRO = auto()
    WAITING_INTRO_DELAY = auto()
    WAITING_USER_RESPONSE = auto()
    WAITING_EXTRACT_DRINK = auto()
    WAITING_ECHO_DRINK_DELAY = auto()
    WAITING_ECHO_DRINK = auto()
    WAITING_EXTRACT_FOOD = auto()
    WAITING_ECHO_FOOD_DELAY = auto()
    WAITING_ECHO_FOOD = auto()
    WAITING_EXTRACT_DESSERT = auto()
    WAITING_ECHO_DESSERT_DELAY = auto()
    WAITING_ECHO_DESSERT = auto()
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
        if self.is_sleeping():
            return

        if self.state == State.INIT:
            self.get_logger().info('🤖 Starting HRI demo with Extract...')

            tts_req = Speech.Request()
            tts_req.text = ('Hola. Vamos a probar la extracción de información. Imagina que soy '
                            'un camarero y tú eres un cliente que va a hacer un pedido. ¿Qué te '
                            'gustaría pedir de beber y de comer?')
            self.current_future = self.tts_client.call_async(tts_req)
            self.state = State.WAITING_INTRO

        elif self.state == State.WAITING_INTRO:
            if self.current_future and self.current_future.done():
                tts_response = self.current_future.result()
                if tts_response.success:
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error(f'❌ TTS error: {tts_response.debug}')

                # Give time to the speech plus a few extra seconds before starting STT
                self.set_sleep(11.0)  # 8.0 base + 3.0 extra delay
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

                self.get_logger().info('🔍 Sending text to the Extract service (drink)...')
                ext_req = Extract.Request()
                ext_req.text = self.user_response
                ext_req.interest = 'bebida'
                self.current_future = None
                self.current_future = self.extract_client.call_async(ext_req)
                self.state = State.WAITING_EXTRACT_DRINK

        # ------------- BEBIDA -------------
        elif self.state == State.WAITING_EXTRACT_DRINK:
            if self.current_future and self.current_future.done():
                extract_response = self.current_future.result()
                self.get_logger().info(f'📝 Extracted (drink): {extract_response.result}')

                if extract_response.result and not extract_response.result.startswith('ERROR'):
                    list_items = extract_response.result.strip('\n').split(';')
                    n = len(list_items)
                    self.get_logger().info(f'✅ {n} items of interest extracted.')
                    self.phrase_to_speak = self.order_to_string(list_items, ('De beber, has '
                                                                             'pedido: '))

                    # Delay so it does not overlap previous speech and sounds natural
                    self.set_sleep(2.0)
                    self.state = State.WAITING_ECHO_DRINK_DELAY
                else:
                    self.get_logger().error(
                        f"❌ Extract error: result '{extract_response.result}'")
                    # If it fails, move on to main courses anyway
                    self.get_logger().info(
                        '🔍 Sending text to the Extract service (main courses)...')
                    ext_req = Extract.Request()
                    ext_req.text = self.user_response
                    ext_req.interest = 'platos principales'
                    self.current_future = None
                    self.current_future = self.extract_client.call_async(ext_req)
                    self.state = State.WAITING_EXTRACT_FOOD

        elif self.state == State.WAITING_ECHO_DRINK_DELAY:
            tts_req = Speech.Request()
            tts_req.text = self.phrase_to_speak
            self.current_future = None
            self.current_future = self.tts_client.call_async(tts_req)
            self.state = State.WAITING_ECHO_DRINK

        elif self.state == State.WAITING_ECHO_DRINK:
            if self.current_future and self.current_future.done():
                tts_response = self.current_future.result()
                if tts_response.success:
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error(f'❌ TTS error: {tts_response.debug}')

                # Move on to the next one
                self.get_logger().info(
                    '🔍 Sending text to the Extract service (main courses)...')
                ext_req = Extract.Request()
                ext_req.text = self.user_response
                ext_req.interest = 'platos principales'
                self.current_future = None
                self.current_future = self.extract_client.call_async(ext_req)
                self.state = State.WAITING_EXTRACT_FOOD

        # ------------- COMIDA -------------
        elif self.state == State.WAITING_EXTRACT_FOOD:
            if self.current_future and self.current_future.done():
                extract_response = self.current_future.result()
                self.get_logger().info(
                    f'📝 Extracted (main courses): {extract_response.result}')

                if extract_response.result and not extract_response.result.startswith('ERROR'):
                    list_items = extract_response.result.strip('\n').split(';')
                    n = len(list_items)
                    self.get_logger().info(f'✅ {n} items of interest extracted.')
                    self.phrase_to_speak = self.order_to_string(list_items, ('Y de comer, has '
                                                                             'pedido: '))

                    self.set_sleep(2.0)
                    self.state = State.WAITING_ECHO_FOOD_DELAY
                else:
                    self.get_logger().error(
                        f"❌ Extract error: result '{extract_response.result}'")
                    self.get_logger().info('🔍 Sending text to the Extract service (desserts)...')
                    ext_req = Extract.Request()
                    ext_req.text = self.user_response
                    ext_req.interest = 'postres'
                    self.current_future = None
                    self.current_future = self.extract_client.call_async(ext_req)
                    self.state = State.WAITING_EXTRACT_DESSERT

        elif self.state == State.WAITING_ECHO_FOOD_DELAY:
            tts_req = Speech.Request()
            tts_req.text = self.phrase_to_speak
            self.current_future = None
            self.current_future = self.tts_client.call_async(tts_req)
            self.state = State.WAITING_ECHO_FOOD

        elif self.state == State.WAITING_ECHO_FOOD:
            if self.current_future and self.current_future.done():
                tts_response = self.current_future.result()
                if tts_response.success:
                    self.get_logger().info('✅ TTS executed successfully')
                else:
                    self.get_logger().error(f'❌ TTS error: {tts_response.debug}')

                # Move on to the last one
                self.get_logger().info('🔍 Sending text to the Extract service (desserts)...')
                ext_req = Extract.Request()
                ext_req.text = self.user_response
                ext_req.interest = 'postres'
                self.current_future = None
                self.current_future = self.extract_client.call_async(ext_req)
                self.state = State.WAITING_EXTRACT_DESSERT

        # ------------- POSTRE -------------
        elif self.state == State.WAITING_EXTRACT_DESSERT:
            if self.current_future and self.current_future.done():
                extract_response = self.current_future.result()
                self.get_logger().info(f'📝 Extracted (desserts): {extract_response.result}')

                if extract_response.result and not extract_response.result.startswith('ERROR'):
                    list_items = extract_response.result.strip('\n').split(';')
                    n = len(list_items)
                    self.get_logger().info(f'✅ {n} items of interest extracted.')
                    self.phrase_to_speak = self.order_to_string(list_items, 'De postre, quieres: ')

                    self.set_sleep(2.0)
                    self.state = State.WAITING_ECHO_DESSERT_DELAY
                else:
                    self.get_logger().error(
                        f"❌ Extract error: result '{extract_response.result}'")
                    self.state = State.DONE

        elif self.state == State.WAITING_ECHO_DESSERT_DELAY:
            tts_req = Speech.Request()
            tts_req.text = self.phrase_to_speak
            self.current_future = None
            self.current_future = self.tts_client.call_async(tts_req)
            self.state = State.WAITING_ECHO_DESSERT

        elif self.state == State.WAITING_ECHO_DESSERT:
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
