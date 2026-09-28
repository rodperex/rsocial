import math
import time

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node


class NavigationClient:
    def __init__(self, node: Node):
        self.node_ = node
        self.nav_client_ = ActionClient(self.node_, NavigateToPose, 'navigate_to_pose')
        self.node_.get_logger().debug('Navigation client initialized')

        self.goal_handle_ = None
        self.goal_active_ = False
        self.goal_done_ = False
        self.goal_success_ = False
        self.last_feedback_ = None

    def wait_for_action_server(self, timeout_sec=5.0):
        if not self.nav_client_.wait_for_server(timeout_sec=timeout_sec):
            self.node_.get_logger().error('Navigation server not available after waiting')
            return False
        self.node_.get_logger().debug('Navigation server available')
        return True

    def send_goal(self, target_pose: PoseStamped):
        self.goal_active_ = False
        self.goal_done_ = False
        self.goal_success_ = False
        self.goal_handle_ = None
        self.last_feedback_ = None

        goal_msg = NavigateToPose.Goal()
        # Copy the pose so the caller's object is not modified when changing the header
        goal_msg.pose.pose = target_pose.pose
        goal_msg.pose.header.stamp = self.node_.get_clock().now().to_msg()
        goal_msg.pose.header.frame_id = target_pose.header.frame_id or 'map'

        self.node_.get_logger().debug(
            f'Sending goal: ({target_pose.pose.position.x:.2f}, '
            f'{target_pose.pose.position.y:.2f})')

        send_goal_future = self.nav_client_.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.node_.get_logger().error('Goal rejected by the server')
            self.goal_done_ = True
            self.goal_success_ = False
            return

        self.node_.get_logger().debug('Goal accepted, navigation started')
        self.goal_handle_ = goal_handle
        self.goal_active_ = True

        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        self.last_feedback_ = feedback_msg.feedback
        self.node_.get_logger().debug(
            f'Distance remaining: {self.last_feedback_.distance_remaining:.2f} m | '
            f'Time: {self.last_feedback_.navigation_time.sec} s'
        )

    def result_callback(self, future):
        result = future.result()
        self.goal_active_ = False
        self.goal_done_ = True

        status = result.status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.node_.get_logger().debug('Navigation SUCCEEDED')
            self.goal_success_ = True
        elif status == GoalStatus.STATUS_ABORTED:
            self.node_.get_logger().warn('Navigation ABORTED (obstacle or timeout)')
            self.goal_success_ = False
        elif status == GoalStatus.STATUS_CANCELED:
            self.node_.get_logger().warn('Navigation CANCELED')
            self.goal_success_ = False
        else:
            self.node_.get_logger().error(f'Unknown status: {status}')
            self.goal_success_ = False

    def cancel_goal(self):
        if self.goal_handle_ and self.goal_active_:
            self.node_.get_logger().debug('Canceling navigation goal')
            self.goal_handle_.cancel_goal_async()
            self.goal_active_ = False

    def wait_for_result(self, timeout_sec=300.0):
        # WARNING: this method blocks. It only works if the node is spinning in another
        # thread (e.g. MultiThreadedExecutor or spin in a separate thread). If it is called
        # from a callback with a single-threaded executor, the action callbacks are never
        # processed and it waits until the timeout. In a control_cycle use is_goal_done()
        # instead (see nav2_example).
        start_time = time.time()
        while rclpy.ok():
            if self.goal_done_:
                self.node_.get_logger().debug(
                    f'Goal finished: {"SUCCESS" if self.goal_success_ else "FAILURE"}')
                return self.goal_success_

            elapsed = time.time() - start_time
            if elapsed > timeout_sec:
                self.node_.get_logger().warn(
                    f'Timeout waiting for the goal result ({timeout_sec} s)')
                self.cancel_goal()
                return False

            time.sleep(0.1)

        return False

    def is_goal_active(self):
        return self.goal_active_

    def is_goal_done(self):
        return self.goal_done_

    def was_goal_successful(self):
        return self.goal_success_

    def get_feedback(self):
        return self.last_feedback_

    def create_pose_stamped(self, x, y, yaw):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.node_.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = 0.0

        # Yaw-only rotation (roll = pitch = 0): q = (0, 0, sin(yaw/2), cos(yaw/2))
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = math.sin(yaw * 0.5)
        pose.pose.orientation.w = math.cos(yaw * 0.5)

        return pose
