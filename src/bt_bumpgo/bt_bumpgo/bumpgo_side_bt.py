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

# MoveForward and BackOff are the same as in the basic version: reuse them.
# Only CheckBump (stores which side was hit) and Turn (uses it) change.

from bt_bumpgo.bumpgo_bt import BackOff, MoveForward
from geometry_msgs.msg import Twist
from kobuki_ros_interfaces.msg import BumperEvent
import py_trees
import py_trees.behaviour
from py_trees.blackboard import Client
import py_trees.common
import py_trees.composites


class CheckBump(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)
        self.blackboard = Client(name=name)
        self.blackboard.register_key(key='node', access=py_trees.common.Access.READ)
        self.blackboard.register_key(key='side', access=py_trees.common.Access.WRITE)
        self.bumped = False
        self.side = None
        self.sub = None

    def setup(self, **kwargs):
        node = self.blackboard.node
        self.sub = node.create_subscription(BumperEvent, '/bumper', self.bumper_callback, 10)

    def bumper_callback(self, msg):
        if msg.state == BumperEvent.PRESSED:
            self.side = msg.bumper
            self.blackboard.side = msg.bumper
            if self.side == BumperEvent.LEFT:
                self.blackboard.node.get_logger().info('Bump on the LEFT side')
            elif self.side == BumperEvent.RIGHT:
                self.blackboard.node.get_logger().info('Bump on the RIGHT side')
            elif self.side == BumperEvent.CENTER:
                self.blackboard.node.get_logger().info('Bump on the CENTER side')
            self.bumped = True

    def update(self):
        if self.bumped:
            self.bumped = False
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE


class Turn(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)
        self.blackboard = Client(name=name)
        self.blackboard.register_key(key='node', access=py_trees.common.Access.READ)
        self.blackboard.register_key(key='side', access=py_trees.common.Access.READ)
        self.cmd_pub = None
        self.duration_sec = 2.0
        self.rotation_dir = 1  # 1 for left, -1 for right

    def setup(self, **kwargs):
        node = self.blackboard.node
        self.cmd_pub = node.create_publisher(Twist, '/out_vel', 10)

    def initialise(self):
        self.start_time = None

    def update(self):
        node = self.blackboard.node

        if self.start_time is None:
            if self.blackboard.side == BumperEvent.LEFT:
                self.blackboard.node.get_logger().info('Turning right...')
                self.rotation_dir = -1  # Turn right
            elif self.blackboard.side == BumperEvent.RIGHT:
                self.blackboard.node.get_logger().info('Turning left...')
                self.rotation_dir = 1   # Turn left
            else:
                # CENTER bump: always turn left (otherwise the previous direction would be reused)
                self.blackboard.node.get_logger().info('Turning left...')
                self.rotation_dir = 1
            self.start_time = node.get_clock().now()

        now = node.get_clock().now()
        elapsed = (now - self.start_time).nanoseconds / 1e9

        if elapsed < self.duration_sec:
            msg = Twist()
            msg.angular.z = self.rotation_dir * 0.5
            self.cmd_pub.publish(msg)
            return py_trees.common.Status.RUNNING
        else:
            self.start_time = None
            stop = Twist()
            self.cmd_pub.publish(stop)
            return py_trees.common.Status.SUCCESS


class BumpGoBT():
    def create_tree(self):
        check_bump = CheckBump('check_bump')
        back_off = BackOff('back_off')
        turn = Turn('turn')
        move_forward = MoveForward('forward')

        invert_bump = py_trees.decorators.Inverter('invert_bump', child=check_bump)

        back_and_turn = py_trees.composites.Sequence('back_and_turn', memory=True)
        back_and_turn.add_children([back_off, turn])

        react_to_bump = py_trees.composites.Selector('bumpgo_seq', memory=True)
        react_to_bump.add_children([invert_bump, back_and_turn])

        root = py_trees.composites.Sequence('bumpgo_root', memory=False)
        root.add_children([react_to_bump, move_forward])

        return root
