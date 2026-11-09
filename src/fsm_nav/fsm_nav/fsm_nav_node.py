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
Mission modeled as an FSM on Nav2: visit two waypoints one after the other.

Each state is a task (going to a waypoint) that uses the navigation capability.

States:
  - WAIT_NAV2: wait until the Nav2 action server is available
  - GO_TO_WP1: navigate to the first waypoint
  - GO_TO_WP2: navigate to the second waypoint
  - DONE: the mission is over (both waypoints reached, or a goal failed)

The navigation goes through NavigationClient (navigation_client), like
simple_navigation_app of nav2_example. start_navigation() returns at once, and each cycle
asks is_navigation_done(): the FSM never blocks. When a goal finishes, its state is the
event of the transition: COMPLETED goes to the next waypoint, and ERROR (Nav2
aborted it), TIMEOUT (it took longer than goal_timeout) or CANCELED end the mission.
"""

import time

from navigation_client.navigation_client import NavigationClient, NavigationState
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class FSMNavNode(Node):
    def __init__(self):
        super().__init__('fsm_nav_node')

        # Waypoints (map frame) and the time allowed to reach each one
        self.declare_parameter('waypoint1.x', 0.0)
        self.declare_parameter('waypoint1.y', 0.0)
        self.declare_parameter('waypoint2.x', 0.0)
        self.declare_parameter('waypoint2.y', 0.0)
        self.declare_parameter('goal_timeout', 120.0)
        self.waypoint1 = (self.get_parameter('waypoint1.x').value,
                          self.get_parameter('waypoint1.y').value)
        self.waypoint2 = (self.get_parameter('waypoint2.x').value,
                          self.get_parameter('waypoint2.y').value)
        self.goal_timeout = self.get_parameter('goal_timeout').value

        self.nav_client = NavigationClient(self)
        self.state = 'WAIT_NAV2'
        self.nav_ready_time = None  # When the Nav2 server was found
        self.get_logger().info('fsm_nav_node started: waiting for Nav2')

        self.timer = self.create_timer(0.5, self.control_cycle)

    def control_cycle(self):
        if self.state == 'WAIT_NAV2':
            # Waits at most 1 s per cycle, so the node keeps running while Nav2 starts
            if self.nav_ready_time is None:
                if self.nav_client.wait_until_ready(1.0):
                    self.get_logger().info('Nav2 available')
                    self.nav_ready_time = time.time()
            # The first goal is sent a little later: right after this node connects, the
            # discovery traffic can make Nav2 miss its internal timeouts (on a loaded
            # computer it then aborts the goal at once)
            elif time.time() - self.nav_ready_time > 2.0:
                self.navigate_to(self.waypoint1)
                self.go_to_state('GO_TO_WP1')

        elif self.state == 'GO_TO_WP1':
            if not self.nav_client.is_navigation_done():
                return
            result = self.nav_client.get_navigation_state()
            if result == NavigationState.COMPLETED:
                self.get_logger().info('First waypoint reached')
                self.navigate_to(self.waypoint2)
                self.go_to_state('GO_TO_WP2')
            else:
                self.get_logger().error(f'GO_TO_WP1 failed ({result.name}): mission aborted')
                self.finish()

        elif self.state == 'GO_TO_WP2':
            if not self.nav_client.is_navigation_done():
                return
            result = self.nav_client.get_navigation_state()
            if result == NavigationState.COMPLETED:
                self.get_logger().info('Second waypoint reached')
            else:
                self.get_logger().error(f'GO_TO_WP2 failed ({result.name}): mission aborted')
            self.finish()

    def navigate_to(self, waypoint):
        x, y = waypoint
        self.get_logger().info(f'Going to ({x:.2f}, {y:.2f})')
        self.nav_client.start_navigation(
            self.nav_client.create_pose_stamped(x, y, 0.0), timeout_sec=self.goal_timeout)

    def go_to_state(self, new_state):
        self.get_logger().info(f'State: {self.state} -> {new_state}')
        self.state = new_state

    def finish(self):
        self.go_to_state('DONE')
        self.timer.cancel()
        raise SystemExit


def main(args=None):
    rclpy.init(args=args)
    node = FSMNavNode()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass  # Clean exit when the mission is over
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
