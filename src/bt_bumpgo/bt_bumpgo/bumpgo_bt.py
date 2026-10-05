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

from geometry_msgs.msg import Twist, TwistStamped
from kobuki_ros_interfaces.msg import BumperEvent
import py_trees
import py_trees.behaviour
from py_trees.blackboard import Client
import py_trees.common
import py_trees.composites


def create_vel_publisher(node, topic):
    """Create a Twist or TwistStamped publisher depending on 'enable_stamped_cmd_vel'."""
    # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped.
    # Several behaviours share the node, so the parameter is declared only once.
    if not node.has_parameter('enable_stamped_cmd_vel'):
        node.declare_parameter('enable_stamped_cmd_vel', False)
    stamped = node.get_parameter('enable_stamped_cmd_vel').value
    return node.create_publisher(TwistStamped if stamped else Twist, topic, 10)


def publish_vel(node, publisher, twist):
    """Publish a Twist, wrapping it in a TwistStamped if the publisher expects it."""
    if publisher.msg_type is TwistStamped:
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist = twist
        publisher.publish(msg)
    else:
        publisher.publish(twist)


class MoveForward(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)
        self.blackboard = Client(name=name)
        self.blackboard.register_key(key='node', access=py_trees.common.Access.READ)
        self.cmd_pub = None

    def setup(self, **kwargs):
        node = self.blackboard.node
        self.cmd_pub = create_vel_publisher(node, '/out_vel')

    def update(self):
        self.blackboard.node.get_logger().debug('Moving forward...')
        msg = Twist()
        msg.linear.x = 0.2
        publish_vel(self.blackboard.node, self.cmd_pub, msg)
        return py_trees.common.Status.RUNNING


class CheckBump(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)
        self.blackboard = Client(name=name)
        self.blackboard.register_key(key='node', access=py_trees.common.Access.READ)
        self.bumped = False
        self.sub = None

    def setup(self, **kwargs):
        node = self.blackboard.node
        self.sub = node.create_subscription(BumperEvent, '/bumper', self.bumper_callback, 10)

    def bumper_callback(self, msg):
        if msg.state == BumperEvent.PRESSED:
            self.blackboard.node.get_logger().info('Bumper pressed!')
            self.bumped = True

    def update(self):
        if self.bumped:
            self.bumped = False
            return py_trees.common.Status.SUCCESS
        else:
            return py_trees.common.Status.FAILURE


class BackOff(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)
        self.blackboard = Client(name=name)
        self.blackboard.register_key(key='node', access=py_trees.common.Access.READ)
        self.cmd_pub = None
        self.start_time = None
        self.duration_sec = 2.0

    def setup(self, **kwargs):
        node = self.blackboard.node
        self.cmd_pub = create_vel_publisher(node, '/out_vel')

    def initialise(self):
        self.blackboard.node.get_logger().info('Backing off...')
        self.start_time = None

    def update(self):
        self.blackboard.node.get_logger().debug('Backing off...')
        node = self.blackboard.node

        if self.start_time is None:
            self.start_time = node.get_clock().now()

        now = node.get_clock().now()
        elapsed = (now - self.start_time).nanoseconds / 1e9

        if elapsed < self.duration_sec:
            msg = Twist()
            msg.linear.x = -0.2
            publish_vel(self.blackboard.node, self.cmd_pub, msg)
            return py_trees.common.Status.RUNNING
        else:
            self.start_time = None
            stop = Twist()
            publish_vel(self.blackboard.node, self.cmd_pub, stop)
            return py_trees.common.Status.SUCCESS


class Turn(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)
        self.blackboard = Client(name=name)
        self.blackboard.register_key(key='node', access=py_trees.common.Access.READ)
        self.cmd_pub = None
        self.duration_sec = 2.0

    def setup(self, **kwargs):
        node = self.blackboard.node
        self.cmd_pub = create_vel_publisher(node, '/out_vel')

    def initialise(self):
        self.blackboard.node.get_logger().info('Turning...')
        self.start_time = None

    def update(self):
        self.blackboard.node.get_logger().debug('Turning...')
        node = self.blackboard.node

        if self.start_time is None:
            self.start_time = node.get_clock().now()

        now = node.get_clock().now()
        elapsed = (now - self.start_time).nanoseconds / 1e9

        if elapsed < self.duration_sec:
            msg = Twist()
            msg.angular.z = 0.5
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
