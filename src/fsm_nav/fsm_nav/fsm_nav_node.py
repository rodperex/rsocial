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

from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class FSMNavNode(Node):
    def __init__(self):
        super().__init__('fsm_nav_node')
        self.state = 'INIT'
        # Declare parameters for each waypoint
        self.declare_parameter('nav1.x', 0.0)
        self.declare_parameter('nav1.y', 0.0)
        self.declare_parameter('nav2.x', 0.0)
        self.declare_parameter('nav2.y', 0.0)
        # Read the waypoints from the parameters
        self.waypoints = [
            {
                'x': self.get_parameter('nav1.x').get_parameter_value().double_value,
                'y': self.get_parameter('nav1.y').get_parameter_value().double_value
            },
            {
                'x': self.get_parameter('nav2.x').get_parameter_value().double_value,
                'y': self.get_parameter('nav2.y').get_parameter_value().double_value
            }
        ]
        self.current_index = 0
        self.nav_action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.timer = self.create_timer(1.0, self.state_machine)
        self.get_logger().info('fsm_nav_node started')

    def state_machine(self):
        if self.state == 'INIT':
            self.get_logger().info('State: INIT -> NAV1')
            self.state = 'NAV1'
            self.current_index = 0
            self.send_goal(self.current_index)
        # Transitions NAV1->NAV2 and NAV2->DONE are handled in goal_result_callback

    def send_goal(self, index):
        self.nav_action_client.wait_for_server()
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = self.waypoints[index]['x']
        goal_msg.pose.pose.position.y = self.waypoints[index]['y']
        goal_msg.pose.pose.orientation.w = 1.0

        self.get_logger().info(f'Sending goal: {self.waypoints[index]}')
        send_goal_future = self.nav_action_client.send_goal_async(goal_msg)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected')
            self.state = 'DONE'
            return

        self.get_logger().info('Goal accepted')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.goal_result_callback)

    def goal_result_callback(self, future):
        status = future.result().status
        if status != GoalStatus.STATUS_SUCCEEDED:
            # An aborted or canceled goal is not a success: do not move to the next waypoint
            self.get_logger().error(f'Navigation failed in state {self.state} (status {status})')
            self.state = 'DONE'
            return

        if self.state == 'NAV1':
            self.get_logger().info('State: NAV1 -> NAV2')
            self.state = 'NAV2'
            self.current_index = 1
            self.send_goal(self.current_index)
        elif self.state == 'NAV2':
            self.get_logger().info('State: NAV2 -> DONE')
            self.state = 'DONE'


def main(args=None):
    rclpy.init(args=args)
    node = FSMNavNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
