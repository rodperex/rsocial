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

import time

from bt_bumpgo.bumpgo_tb4_bt import BumpGoBT
import py_trees
from py_trees.blackboard import Client
import py_trees.common
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


def main(args=None):
    rclpy.init(args=args)

    # 1. Create a standard ROS node
    ros_node = Node('bump_go')

    # 2. Initialize Blackboard and set the node
    blackboard = Client(name='global_blackboard')
    blackboard.register_key(key='node', access=py_trees.common.Access.WRITE)
    blackboard.node = ros_node

    # 3. Create and Setup the Tree wrapper
    bumpgo = BumpGoBT()
    root = bumpgo.create_tree()

    # OPTION: py_trees_ros (wrapper that manages ticking and ROS integration)
    # tree = py_trees_ros.trees.BehaviourTree(root)

    # # Connect the tree to the ROS node
    # tree.setup(node=ros_node, timeout=15)

    # # Start the tree ticking
    # tree.tick_tock(period_ms=100.0)

    # try:
    #     rclpy.spin(ros_node)
    # except (KeyboardInterrupt, ExternalShutdownException):
    #     pass
    # finally:
    #     tree.shutdown()
    #     ros_node.destroy_node()
    #     rclpy.shutdown()

    # OPTION: Manual ticking
    root.setup_with_descendants()
    try:
        while rclpy.ok():
            rclpy.spin_once(ros_node, timeout_sec=0.1)
            root.tick_once()
            if root.status != py_trees.common.Status.RUNNING:
                break
            time.sleep(0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ros_node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
