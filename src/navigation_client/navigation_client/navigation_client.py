from enum import Enum
import math
import time

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


class NavigationState(Enum):
    # Same states as hri_client.OperationState
    IDLE = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    ERROR = 4
    TIMEOUT = 5
    CANCELED = 6


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

        self.state_ = NavigationState.IDLE
        self.deadline_ = None
        self.cancel_requested_ = False
        # Identifies the current goal: callbacks of a previous goal (e.g. its result arriving
        # after a timeout) must not change the state of the new one
        self.goal_seq_ = 0

    def wait_for_action_server(self, timeout_sec=5.0):
        if not self.nav_client_.wait_for_server(timeout_sec=timeout_sec):
            self.node_.get_logger().error('Navigation server not available after waiting')
            return False
        self.node_.get_logger().debug('Navigation server available')
        return True

    def send_goal(self, target_pose: PoseStamped, timeout_sec=None):
        # timeout_sec: if the goal is not done in that time, is_goal_done() cancels it and the
        # state becomes TIMEOUT (checked when is_goal_done() is called, without blocking)
        self.goal_active_ = False
        self.goal_done_ = False
        self.goal_success_ = False
        self.goal_handle_ = None
        self.last_feedback_ = None

        self.state_ = NavigationState.IN_PROGRESS
        self.deadline_ = None if timeout_sec is None else time.time() + timeout_sec
        self.cancel_requested_ = False
        self.goal_seq_ += 1
        seq = self.goal_seq_

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
            feedback_callback=lambda msg: self.feedback_callback(msg, seq)
        )
        send_goal_future.add_done_callback(lambda future: self.goal_response_callback(future, seq))

    def goal_response_callback(self, future, seq):
        goal_handle = future.result()
        if seq != self.goal_seq_:
            # Goal of a previous send_goal(): cancel it if it was accepted and ignore it
            if goal_handle.accepted:
                goal_handle.cancel_goal_async()
            return

        if not goal_handle.accepted:
            self.node_.get_logger().error('Goal rejected by the server')
            self.goal_done_ = True
            self.goal_success_ = False
            self.state_ = NavigationState.ERROR
            return

        self.goal_handle_ = goal_handle
        if self.cancel_requested_:
            # cancel_goal() or a timeout happened before the server accepted the goal
            goal_handle.cancel_goal_async()
            return

        self.node_.get_logger().debug('Goal accepted, navigation started')
        self.goal_active_ = True

        get_result_future = goal_handle.get_result_async()
        get_result_future.add_done_callback(lambda f: self.result_callback(f, seq))

    def feedback_callback(self, feedback_msg, seq):
        if seq != self.goal_seq_:
            return
        self.last_feedback_ = feedback_msg.feedback
        self.node_.get_logger().debug(
            f'Distance remaining: {self.last_feedback_.distance_remaining:.2f} m | '
            f'Time: {self.last_feedback_.navigation_time.sec} s'
        )

    def result_callback(self, future, seq):
        if seq != self.goal_seq_:
            return
        result = future.result()
        self.goal_active_ = False

        if self.state_ in (NavigationState.TIMEOUT, NavigationState.CANCELED):
            # The client already finished the goal (timeout or cancel_goal())
            return

        self.goal_done_ = True
        status = result.status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.node_.get_logger().debug('Navigation SUCCEEDED')
            self.goal_success_ = True
            self.state_ = NavigationState.COMPLETED
        elif status == GoalStatus.STATUS_ABORTED:
            self.node_.get_logger().warn('Navigation ABORTED (obstacle or timeout)')
            self.goal_success_ = False
            self.state_ = NavigationState.ERROR
        elif status == GoalStatus.STATUS_CANCELED:
            self.node_.get_logger().warn('Navigation CANCELED')
            self.goal_success_ = False
            self.state_ = NavigationState.CANCELED
        else:
            self.node_.get_logger().error(f'Unknown status: {status}')
            self.goal_success_ = False
            self.state_ = NavigationState.ERROR

    def _finish(self, state):
        # Ask Nav2 to cancel (even if the goal has not been accepted yet) and finish the goal
        self.cancel_requested_ = True
        if self.goal_handle_ is not None and self.goal_active_:
            self.goal_handle_.cancel_goal_async()
        self.goal_active_ = False
        self.goal_done_ = True
        self.goal_success_ = False
        self.state_ = state

    def cancel_goal(self):
        if self.state_ == NavigationState.IN_PROGRESS:
            self.node_.get_logger().debug('Canceling navigation goal')
            self._finish(NavigationState.CANCELED)

    def is_goal_done(self):
        if (self.state_ == NavigationState.IN_PROGRESS and self.deadline_ is not None
                and time.time() > self.deadline_):
            self.node_.get_logger().warn('Navigation timed out: canceling the goal')
            self._finish(NavigationState.TIMEOUT)
        return self.goal_done_

    def was_goal_successful(self):
        return self.goal_success_

    def get_goal_state(self):
        """Return how the goal finished: COMPLETED, ERROR, TIMEOUT or CANCELED."""
        return self.state_

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
