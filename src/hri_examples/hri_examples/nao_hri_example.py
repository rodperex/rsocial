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
Listen and repeat with Nao: greeting gesture, chest LED and HRIClient.

The chest LED tells the person when to speak: red while the robot talks, blue while
it listens, green while it repeats what it heard.
"""

from enum import auto, Enum

from hri_client.hri_client import HRIClient, OperationState
from nao_led_interfaces.action import LedsPlay
from nao_led_interfaces.msg import LedIndexes, LedModes
from nao_lola_command_msgs.msg import ChestLed
from nao_pos_interfaces.action import PosPlay
import rclpy
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import ColorRGBA

RED = (1.0, 0.0, 0.0)
GREEN = (0.0, 1.0, 0.0)
BLUE = (0.0, 0.0, 1.0)
OFF = (0.0, 0.0, 0.0)


class State(Enum):
    INIT = auto()                 # Greeting gesture and introduction
    SPEAKING_INTRO = auto()       # Wait until the robot finishes the introduction
    LISTENING = auto()            # Wait for the transcription
    SPEAKING_ECHO_INTRO = auto()  # Wait for 'Ahora voy a repetir...'
    SPEAKING_ECHO = auto()        # Wait until the robot repeats what it heard
    DONE = auto()


class NaoHRIExample(Node):

    def __init__(self):
        super().__init__('nao_hri_example_node')

        self.hri_client = HRIClient(self)
        if not self.hri_client.wait_until_ready(10.0):
            self.get_logger().error('simple_hri not available. Did you launch simple_hri?')

        # Position action client
        self.pos_client = ActionClient(self, PosPlay, '/nao_pos_action')
        while not self.pos_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('/nao_pos_action unavailable...')

        # Publisher to change chest led color
        self.chest_led_pub = self.create_publisher(ChestLed, '/effectors/chest_led', 10)

        self.leds_client = ActionClient(self, LedsPlay, '/leds_play')
        while not self.leds_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('/leds_play unavailable...')
        self.switch_off_all_leds()

        self.state = State.INIT
        self.transcribed_text = ''

        # Run control_loop() every 0.1 seconds (10 Hz)
        self.timer = self.create_timer(0.1, self.control_loop)

    def set_chest(self, color):
        chest_led_msg = ChestLed()
        chest_led_msg.color.r, chest_led_msg.color.g, chest_led_msg.color.b = color
        self.chest_led_pub.publish(chest_led_msg)

    def check_speaking(self):
        """Log an error if the robot could not say the last sentence."""
        if self.hri_client.get_speaking_state() != OperationState.COMPLETED:
            self.get_logger().error('❌ TTS error')

    def control_loop(self):
        if self.state == State.INIT:
            self.get_logger().info('🤖 Starting HRI demo with Nao...')
            pos_goal = PosPlay.Goal()
            pos_goal.action_name = 'hello'
            self.pos_client.send_goal_async(pos_goal).add_done_callback(
                self.goal_response_callback)

            self.set_chest(RED)
            self.hri_client.start_speaking(
                'Hola, soy Nao. Vamos a probar el reconocimiento de voz y la síntesis de '
                'voz. Habla cuando la luz de mi pecho esté azul.')
            self.state = State.SPEAKING_INTRO

        elif self.state == State.SPEAKING_INTRO:
            # Listen only when the robot has finished, or the microphone would record
            # the robot's own voice
            if self.hri_client.is_speaking_done():
                self.check_speaking()
                self.set_chest(BLUE)
                self.get_logger().info('🎤 Starting speech recognition (STT)...')
                self.hri_client.start_listening()
                self.state = State.LISTENING

        elif self.state == State.LISTENING:
            if self.hri_client.is_listening_done():
                self.transcribed_text = self.hri_client.get_listened_text()
                if not self.transcribed_text:
                    self.get_logger().error('❌ STT error')
                    self.set_chest(OFF)
                    self.state = State.DONE
                    return

                self.get_logger().info(f'📝 Transcription: {self.transcribed_text}')
                self.set_chest(RED)
                self.hri_client.start_speaking('Ahora voy a repetir lo que has dicho')
                self.state = State.SPEAKING_ECHO_INTRO

        elif self.state == State.SPEAKING_ECHO_INTRO:
            if self.hri_client.is_speaking_done():
                self.check_speaking()
                self.set_chest(GREEN)
                self.get_logger().info('🔊 Sending text to TTS...')
                self.hri_client.start_speaking(self.transcribed_text)
                self.state = State.SPEAKING_ECHO

        elif self.state == State.SPEAKING_ECHO:
            if self.hri_client.is_speaking_done():
                self.check_speaking()
                self.set_chest(OFF)  # One cycle before exiting, so the message goes out
                self.state = State.DONE

        elif self.state == State.DONE:
            self.get_logger().info('🎉 Demo finished.')
            self.timer.cancel()
            raise SystemExit

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Success: {result.success}')

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected')
            return

        self.get_logger().info('Goal accepted :)')

        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def switch_off_all_leds(self):
        N_COLORS = 8
        N_INTENS = 12

        for leds in ([LedIndexes.REYE, LedIndexes.LEYE],
                     [LedIndexes.CHEST],
                     [LedIndexes.REAR, LedIndexes.LEAR]):
            goal_msg = LedsPlay.Goal()
            goal_msg.leds = leds
            goal_msg.mode = LedModes.STEADY
            goal_msg.frequency = 0.0
            # Independent instances (not [ColorRGBA()] * n, which would repeat the same object)
            goal_msg.colors = [ColorRGBA(r=0.0, g=0.0, b=0.0, a=1.0) for _ in range(N_COLORS)]
            goal_msg.intensities = [0.0] * N_INTENS
            goal_msg.duration = 0.0
            send_goal_future = self.leds_client.send_goal_async(goal_msg)
            send_goal_future.add_done_callback(self.goal_response_callback)


def main(args=None):
    rclpy.init(args=args)
    node = NaoHRIExample()

    try:
        rclpy.spin(node)
    except SystemExit:
        pass  # Clean exit when State == DONE
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
