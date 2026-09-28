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

from geometry_msgs.msg import Twist
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
    """

    def __init__(self):
        super().__init__('tf_square_mover')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.timer = self.create_timer(0.01, self.control_loop)

        self.state = 'init'
        self.odom2blref = None  # Robot pose (base_link) in odom when the movement started
        self.side_count = 0
        # Non-blocking pause between movements (never call time.sleep inside a callback:
        # it blocks the executor and the TF buffer stops updating)
        self.pause_until = self.get_clock().now()

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

    def relative_motion(self, odom2bl):
        """Return blref2bl: current robot pose expressed in the reference (start) pose."""
        T_odom2blref = self.transform_to_matrix(self.odom2blref)
        T_odom2bl = self.transform_to_matrix(odom2bl)

        T_blref2odom = np.linalg.inv(T_odom2blref)  # inv(A2B) = B2A

        # blref2odom @ odom2bl = blref2bl  ('odom' cancels out)
        return T_blref2odom @ T_odom2bl

    def control_loop(self):
        try:
            # Current robot pose in odom
            odom2bl = self.tf_buffer.lookup_transform('odom', 'base_link', rclpy.time.Time())
        except TransformException:
            # It is normal to fail at the beginning while the buffer fills up
            return

        if self.is_paused():
            return

        if self.state == 'init':
            # Store the reference pose to start the side
            self.odom2blref = odom2bl
            self.state = 'forward'
            self.get_logger().info(f'Starting side {self.side_count + 1}')
            return

        elif self.state == 'forward':
            # Where the robot is NOW with respect to where the movement STARTED
            x, y, _ = self.matrix_to_pose(self.relative_motion(odom2bl))
            distance = math.sqrt(x**2 + y**2)

            if distance < 1.0:  # move 1 meter
                twist = Twist()
                twist.linear.x = 0.5
                self.publisher.publish(twist)
            else:
                self.publisher.publish(Twist())  # stop
                self.state = 'turn'
                self.odom2blref = odom2bl  # New reference to measure the turn
                self.get_logger().info(f'Finished side {self.side_count + 1}, starting turn.')
                self.pause(0.5)

        elif self.state == 'turn':
            _, _, yaw = self.matrix_to_pose(self.relative_motion(odom2bl))

            # Turn 90 degrees (pi/2)
            if abs(yaw) < math.pi / 2:
                twist = Twist()
                twist.angular.z = 0.5  # Slightly lower speed for precision
                self.publisher.publish(twist)
            else:
                self.publisher.publish(Twist())  # stop
                self.side_count += 1
                if self.side_count >= 4:
                    self.get_logger().info('Finished square.')
                    self.state = 'done'
                else:
                    self.state = 'init'  # Back to init to take the reference of the next side
                self.pause(0.5)

        elif self.state == 'done':
            # Make sure the robot stays stopped
            self.publisher.publish(Twist())


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
