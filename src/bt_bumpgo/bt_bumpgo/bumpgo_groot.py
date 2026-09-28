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

import os
import time

from ament_index_python.packages import get_package_share_directory
from bt_bumpgo import groot_loader
from bt_bumpgo.bumpgo_bt import BackOff, CheckBump, MoveForward, Turn
import py_trees
from py_trees.blackboard import Client
import py_trees.common
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


def main(args=None):
    rclpy.init(args=args)
    ros_node = Node('bump_go')

    blackboard = Client(name='global_blackboard')
    blackboard.register_key(key='node', access=py_trees.common.Access.WRITE)
    blackboard.node = ros_node

    move_forward_bh = MoveForward('MoveForward')
    check_bump_bh = CheckBump('CheckBump')
    back_off_bh = BackOff('BackOff')
    turn_bh = Turn('Turn')

    custom_behaviors = [
        move_forward_bh,
        check_bump_bh,
        back_off_bh,
        turn_bh,
    ]

    # The XML is installed in share/bt_bumpgo/bt_xml (see setup.py). It can be changed
    # with the 'xml_file' parameter to try other trees made with Groot.
    default_xml = os.path.join(get_package_share_directory('bt_bumpgo'), 'bt_xml', 'bumpgo.xml')
    xml_path = ros_node.declare_parameter('xml_file', default_xml).value
    ros_node.get_logger().info(f'Loading tree from: {xml_path}')

    # Load the tree from the Groot XML
    root = groot_loader.load(xml_path, behaviours=custom_behaviors)
    print(py_trees.display.unicode_tree(root))

    # Setup the whole tree
    root.setup_with_descendants()

    try:
        while rclpy.ok():
            rclpy.spin_once(ros_node, timeout_sec=0.1)
            root.tick_once()
            time.sleep(0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ros_node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
