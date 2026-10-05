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

# Bump and go for the TurtleBot 4 (iRobot Create 3 base). Same tree as
# bumpgo_bt.py (Kobuki): MoveForward, BackOff and Turn are reused. Only CheckBump
# changes, because the Create 3 has no bumper topic: bumps arrive in
# /hazard_detection, a vector with all the active hazards (bump, cliff...).

from bt_bumpgo.bumpgo_bt import BackOff, MoveForward, Turn
from irobot_create_msgs.msg import HazardDetection, HazardDetectionVector
import py_trees
import py_trees.behaviour
from py_trees.blackboard import Client
import py_trees.common
import py_trees.composites
from rclpy.qos import qos_profile_sensor_data


class CheckBump(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)
        self.blackboard = Client(name=name)
        self.blackboard.register_key(key='node', access=py_trees.common.Access.READ)
        self.bumped = False
        self.in_contact = False
        self.sub = None

    def setup(self, **kwargs):
        node = self.blackboard.node
        # The Create 3 publishes best effort: a reliable subscriber would get nothing
        self.sub = node.create_subscription(
            HazardDetectionVector, '/hazard_detection', self.hazard_callback,
            qos_profile_sensor_data)

    def hazard_callback(self, msg):
        # A bump is a detection of type BUMP
        bump = any(d.type == HazardDetection.BUMP for d in msg.detections)
        # React only to a new contact: the simulator repeats the bump while touching,
        # and an old bump would trigger a second back off after the turn
        if bump and not self.in_contact:
            self.blackboard.node.get_logger().info('Bumper pressed!')
            self.bumped = True
        self.in_contact = bump

    def update(self):
        if self.bumped:
            self.bumped = False
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE


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
