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

import math

from geometry_msgs.msg import Twist, TwistStamped
import numpy as np
import rclpy
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener
from tf_transformations import (
    concatenate_matrices,
    euler_from_matrix,
    quaternion_matrix,
    translation_matrix,
)


class TFSquareMover(Node):
    """
    Move the robot along a 1 m square using odometry (TF) and homogeneous matrices.

    Naming convention for transforms: A2B is the result of lookup_transform(A, B), i.e. the
    pose of frame B expressed in frame A (the matrix that maps points from B to A).
    With this convention transforms chain like A2B @ B2C = A2C: the last frame of the first
    term and the first frame of the second term cancel out. Also, inv(A2B) = B2A.

    Why the square is NOT perfect even though TF is used (see tf_square_node3 for a fix):

    1. Errors accumulate. Each side and each turn is measured relative to the pose where
       the PREVIOUS movement ended (the reference is reset in 'init' and before each turn).
       If a turn ends at 93 degrees, the next side starts 3 degrees off and nothing ever
       corrects it: the errors of the 4 sides and 4 turns add up and the square does not
       close.
    2. Overshoot. The speed is constant (bang-bang control) and the robot is only told to
       stop once the goal has been passed, so it always goes a bit too far:
       - Inertia: the robot does not stop instantly when it receives a zero Twist.
       - TF latency: lookup_transform(..., Time()) returns the LATEST available transform,
         which can be tens of milliseconds old. With odometry at 30 Hz, 0.5 rad/s means
         ~1 degree of rotation that we have not seen yet (0.5 m/s means ~1.7 cm).
       - Sampling: the condition is only checked when a new TF arrives, not at the exact
         moment the threshold is crossed.
    3. No heading correction. While moving forward only linear.x is commanded, so any
       lateral drift (uneven wheels, slip) is never corrected, and sqrt(x^2 + y^2) accepts
       the side as done even if the robot went sideways.
    4. 'odom' is not the ground truth. The odom -> base_link transform is estimated from
       the wheel encoders (and maybe an IMU), so it drifts because of wheel slip or a badly
       calibrated wheel radius. Even a perfect square in 'odom' is not perfect in reality.
    """

    def __init__(self):
        super().__init__('tf_square_mover')

        # Some robots (e.g. ros2_control diff_drive_controller) expect TwistStamped
        self.declare_parameter('enable_stamped_cmd_vel', False)
        self.stamped = self.get_parameter('enable_stamped_cmd_vel').value
        self.publisher = self.create_publisher(
            TwistStamped if self.stamped else Twist, '/cmd_vel', 10)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.timer = self.create_timer(0.01, self.control_loop)

        self.state = 'init'
        # Robot pose (base_link) in odom when the movement started, as a 4x4 matrix
        self.T_odom2blref = None
        self.side_count = 0
        # Non-blocking pause between movements (never call time.sleep inside a callback:
        # it blocks the executor and the TF buffer stops updating)
        self.pause_until = self.get_clock().now()

    def publish_vel(self, twist):
        """Publish a Twist, wrapping it in a TwistStamped if the robot expects it."""
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist = twist
            self.publisher.publish(msg)
        else:
            self.publisher.publish(twist)

    def pause(self, seconds):
        self.pause_until = self.get_clock().now() + Duration(seconds=seconds)

    def is_paused(self):
        return self.get_clock().now() < self.pause_until

    def transform_to_matrix(self, transform_stamped):
        """Convert a TransformStamped into a 4x4 homogeneous matrix."""
        t = transform_stamped.transform

        # 1. Translation matrix (4x4)
        trans_mat = translation_matrix([t.translation.x, t.translation.y, t.translation.z])

        # 2. Rotation matrix (4x4) from the quaternion
        rot_mat = quaternion_matrix([t.rotation.x, t.rotation.y, t.rotation.z, t.rotation.w])

        # 3. Combine them: Translation * Rotation
        matrix = concatenate_matrices(trans_mat, rot_mat)
        return matrix

    def matrix_to_pose(self, matrix):
        """Extract x, y, yaw from a 4x4 homogeneous matrix."""
        # In a 4x4 matrix the translation is in the last column (index 3)
        x = matrix[0, 3]
        y = matrix[1, 3]

        # euler_from_matrix returns (roll, pitch, yaw) by default (sxyz axes)
        _, _, yaw = euler_from_matrix(matrix)

        return x, y, yaw

    def control_loop(self):
        try:
            # Current robot pose in odom
            odom2bl = self.tf_buffer.lookup_transform('odom', 'base_link', rclpy.time.Time())
        except TransformException:
            # It is normal to fail at the beginning while the buffer fills up
            return

        if self.is_paused():
            return

        # Current robot pose in odom as a 4x4 homogeneous matrix
        T_odom2bl = self.transform_to_matrix(odom2bl)

        if self.state == 'init':
            # Store the reference pose to start the side
            self.T_odom2blref = T_odom2bl
            self.state = 'forward'
            self.get_logger().info(f'Starting side {self.side_count + 1}')
            return

        elif self.state == 'forward':
            # Where the robot is NOW with respect to where the movement STARTED
            # 1. Invert the reference pose: inv(odom2blref) = blref2odom
            T_blref2odom = np.linalg.inv(self.T_odom2blref)
            # 2. Chain transforms: blref2odom @ odom2bl = blref2bl  ('odom' cancels out)
            T_blref2bl = T_blref2odom @ T_odom2bl
            # 3. Extract the displacement from the reference pose
            x, y, _ = self.matrix_to_pose(T_blref2bl)
            distance = math.sqrt(x**2 + y**2)

            if distance < 1.0:  # move 1 meter
                # [Error 2] Constant speed until the goal: no slowing down near it.
                # [Error 3] Only linear.x: lateral drift is never corrected, and 'distance'
                # counts sideways displacement as progress.
                twist = Twist()
                twist.linear.x = 0.5
                self.publish_vel(twist)
            else:
                # [Error 2] By the time we get here the robot has already passed 1 m (TF
                # latency + sampling), and it will keep moving a bit more due to inertia.
                self.publish_vel(Twist())  # stop
                self.state = 'turn'
                # [Error 1] New relative reference: the turn is measured from here, so any
                # heading error accumulated so far is simply ignored.
                self.T_odom2blref = T_odom2bl  # New reference to measure the turn
                self.get_logger().info(f'Finished side {self.side_count + 1}, starting turn.')
                self.pause(0.5)

        elif self.state == 'turn':
            # Same steps as in 'forward', but now we are interested in the rotation
            T_blref2odom = np.linalg.inv(self.T_odom2blref)
            T_blref2bl = T_blref2odom @ T_odom2bl
            _, _, yaw = self.matrix_to_pose(T_blref2bl)

            # Turn 90 degrees (pi/2)
            if abs(yaw) < math.pi / 2:
                # [Error 2] Constant angular speed until the goal: no slowing down near it.
                twist = Twist()
                twist.angular.z = 0.5  # Slightly lower speed for precision
                self.publish_vel(twist)
            else:
                # [Error 2] The robot has already turned more than 90 degrees, and it keeps
                # turning a bit due to inertia. This overshoot is never corrected.
                self.publish_vel(Twist())  # stop
                self.side_count += 1
                if self.side_count >= 4:
                    self.get_logger().info('Finished square.')
                    self.state = 'done'
                else:
                    # [Error 1] Back to init to take the reference of the next side. The
                    # reference is the CURRENT pose (with the turn overshoot included), not
                    # the ideal one, so the overshoot is carried over to the next side.
                    self.state = 'init'
                self.pause(0.5)

        elif self.state == 'done':
            # Make sure the robot stays stopped
            self.publish_vel(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = TFSquareMover()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
