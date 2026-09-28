#!/usr/bin/env python3

from navigation_client.navigation_client import NavigationClient
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


class SimpleNavigationApp(Node):
    def __init__(self):
        super().__init__('simple_navigation_app_py_node')
        self.nav_client_ = NavigationClient(self)
        self.target_pose_ = self.nav_client_.create_pose_stamped(6.0, -2.0, 0.0)

        self.server_ready_ = False
        self.goal_sent_ = False

        self.get_logger().info('Navigation application started (Python)')

        self.timer_ = self.create_timer(0.5, self.control_cycle)

    def control_cycle(self):
        if not self.server_ready_:
            if self.nav_client_.wait_for_action_server(1.0):
                self.get_logger().info('Server available, ready to navigate')
                self.server_ready_ = True
            return

        if not self.goal_sent_:
            self.get_logger().info('Sending navigation goal...')
            self.nav_client_.send_goal(self.target_pose_)
            self.goal_sent_ = True
            return

        if not self.nav_client_.is_goal_done():
            feedback = self.nav_client_.get_feedback()
            if feedback:
                t_sec = feedback.navigation_time.sec + feedback.navigation_time.nanosec / 1e9
                self.get_logger().info(
                    f'\t-Distance remaining: {feedback.distance_remaining:.2f} m | '
                    f'Time: {t_sec:.1f} s'
                )
            return

        if self.nav_client_.was_goal_successful():
            self.get_logger().info('Navigation succeeded')
        else:
            self.get_logger().warn('Navigation failed')

        self.timer_.cancel()
        self.get_logger().info('Application finished')


def main(args=None):
    rclpy.init(args=args)

    app_node = SimpleNavigationApp()

    try:
        rclpy.spin(app_node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        app_node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
