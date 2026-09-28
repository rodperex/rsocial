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

import rclpy
from rclpy.executors import ExternalShutdownException


def main(args=None):
    rclpy.init(args=args)
    node = rclpy.create_node('logger_node')
    rate = node.create_rate(2)  # 2 Hz
    counter = 1
    # Note: in rclpy the Rate is driven by a timer that is executed by spin_once().
    # spin_once() blocks until that timer fires, and rate.sleep() then returns
    # immediately. For periodic work the idiomatic way is a timer (see logger_node.py).
    try:
        while rclpy.ok():
            rclpy.spin_once(node)
            node.get_logger().info(f'Counter: {counter}')
            counter += 1
            rate.sleep()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
