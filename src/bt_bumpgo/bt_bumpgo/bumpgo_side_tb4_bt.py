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

# TurtleBot 4 (iRobot Create 3 base) version of bumpgo_side_bt.py (Kobuki).
# MoveForward and BackOff are the same as in the basic version: reuse them.
# Only CheckBump (stores which side was hit) and Turn (uses it) change.
# The Create 3 has no bumper topic: bumps arrive in /hazard_detection, and the
# side is in the frame_id of the detection (bump_left, bump_front_center...).

from bt_bumpgo.bumpgo_bt import BackOff, create_vel_publisher, MoveForward, publish_vel
from geometry_msgs.msg import Twist
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
        self.blackboard.register_key(key='side', access=py_trees.common.Access.WRITE)
        self.bumped = False
        self.in_contact = False
        self.side = None
        self.sub = None

    def setup(self, **kwargs):
        node = self.blackboard.node
        # The Create 3 publishes best effort: a reliable subscriber would get nothing
        self.sub = node.create_subscription(
            HazardDetectionVector, '/hazard_detection', self.hazard_callback,
            qos_profile_sensor_data)

    def hazard_callback(self, msg):
        bumps = [d for d in msg.detections if d.type == HazardDetection.BUMP]
        # React only to a new contact: the simulator repeats the bump while touching,
        # and an old bump would trigger a second back off after the turn
        new_contact = bumps and not self.in_contact
        self.in_contact = bool(bumps)
        if new_contact:
            # frame_id: bump_left, bump_front_left, bump_front_center, bump_front_right...
            frame = bumps[0].header.frame_id
            if 'left' in frame:
                self.side = 'left'
            elif 'right' in frame:
                self.side = 'right'
            else:
                self.side = 'center'
            self.blackboard.side = self.side
            self.blackboard.node.get_logger().info(f'Bump on the {self.side.upper()} side')
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
        self.cmd_pub = create_vel_publisher(node, '/out_vel')

    def initialise(self):
        self.start_time = None

    def update(self):
        node = self.blackboard.node

        if self.start_time is None:
            if self.blackboard.side == 'left':
                self.blackboard.node.get_logger().info('Turning right...')
                self.rotation_dir = -1  # Turn right
            elif self.blackboard.side == 'right':
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
            publish_vel(self.blackboard.node, self.cmd_pub, msg)
            return py_trees.common.Status.RUNNING
        else:
            self.start_time = None
            stop = Twist()
            publish_vel(self.blackboard.node, self.cmd_pub, stop)
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
