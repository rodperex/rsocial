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
Attractive vector towards the person who is calling the robot (arm raised).

It plays the same role as yolo_class_detector_node_3d of vff_control, but instead of
going to any object of a class it chooses one person: the first one who keeps an arm
raised above arm_angle_threshold. YOLO runs with a pose model, which gives the
keypoints of the body of every person (shoulders, elbows, wrists...).

Once a person has called, the node sticks to them (by the YOLO tracking id) and
publishes the attractive vector towards them in every image, even if they lower the
arm. It lets them go only when it receives a message on calling_person_reset, and
then waits for someone to call again. The FSM sends the reset every time it searches
again, both after reaching the person (who usually stays in view) and after losing them.

Topics:
  - input_detections (yolo_msgs/DetectionArray): YOLO detections with 3D positions
  - attractive_vector (geometry_msgs/Vector3): position of the person in base_frame
  - calling_person (std_msgs/String): tracking id of the person, once when they call
  - calling_person_reset (std_msgs/Empty): forget the person and wait for a new call
"""

import math

from geometry_msgs.msg import PointStamped, Vector3
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Empty, String
from tf2_geometry_msgs import do_transform_point
from tf2_ros import Buffer, TransformListener
from yolo_msgs.msg import DetectionArray

# Keypoint ids of yolo_ros: the COCO ones plus 1 (yolo_ros numbers them from 1)
LEFT_SHOULDER, RIGHT_SHOULDER = 6, 7
LEFT_ELBOW, RIGHT_ELBOW = 8, 9
LEFT_WRIST, RIGHT_WRIST = 10, 11
ARMS = [
    (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST),
]


def arm_angle(person):
    """
    Return the angle (degrees) of the most raised arm of a person, or None.

    It is the angle in the image between the arm (shoulder to wrist, or to the elbow
    if the wrist is not visible) and the vertical pointing down: 0 is the arm down,
    90 horizontal and 180 straight up. The image is used instead of the 3D keypoints
    because it does not depend on the depth, which is often missing on thin arms.
    """
    keypoints = {kp.id: kp.point for kp in person.keypoints.data}
    angles = []
    for shoulder_id, elbow_id, wrist_id in ARMS:
        shoulder = keypoints.get(shoulder_id)
        hand = keypoints.get(wrist_id)
        if hand is None:
            hand = keypoints.get(elbow_id)  # Use the elbow if the wrist is not visible
        if shoulder is None or hand is None:
            continue
        # The image y axis points down, so dy > 0 means the hand is below the shoulder
        dx = hand.x - shoulder.x
        dy = hand.y - shoulder.y
        angles.append(math.degrees(math.atan2(abs(dx), dy)))
    return max(angles) if angles else None


class CallingPersonDetectorNode(Node):

    def __init__(self):
        super().__init__('calling_person_detector_node')

        # Parameters
        # Arm angle (degrees, 0 down, 90 horizontal, 180 up) above which a person is calling
        self.declare_parameter('arm_angle_threshold', 120.0)
        # Consecutive images with the arm raised needed to accept that a person is calling.
        # A single image is not enough: while the robot turns, blurred images give wrong
        # keypoints
        self.declare_parameter('frames_to_confirm', 3)
        self.declare_parameter('base_frame', 'base_footprint')
        # Some cameras (e.g. the Kobuki simulator) stamp their images with a frame that is
        # not the optical one, so the 3D positions are relabeled with optical_frame
        self.declare_parameter('fix_image_frame', False)
        self.declare_parameter('optical_frame', 'camera_rgb_optical_frame')

        self.arm_angle_threshold = self.get_parameter('arm_angle_threshold').value
        self.frames_to_confirm = self.get_parameter('frames_to_confirm').value
        self.base_frame = self.get_parameter('base_frame').value
        self.fix_image_frame = self.get_parameter('fix_image_frame').value
        self.optical_frame = self.get_parameter('optical_frame').value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # YOLO detections with 3D positions (/yolo/detections_3d): they keep the 2D
        # keypoints of the pose model and the tracking id of each person.
        # Unlike the other examples, this node reads the yolo_msgs messages directly
        # instead of the standard ones (/detections_3d, vision_msgs/Detection3D):
        # vision_msgs has no field for the keypoints, so the conversion of the camera
        # package drops them (and it does not copy the tracking id either)
        self.detections_sub = self.create_subscription(
            DetectionArray, 'input_detections', self.detections_callback,
            rclpy.qos.qos_profile_sensor_data)
        self.reset_sub = self.create_subscription(
            Empty, 'calling_person_reset', self.reset_callback, 10)

        self.attractive_pub = self.create_publisher(Vector3, 'attractive_vector', 10)
        self.calling_pub = self.create_publisher(String, 'calling_person', 10)

        self.release()

    def release(self):
        """Forget the person who called: wait for someone to call again."""
        # Tracking id of the person who called (None while nobody has called)
        self.target_id = None
        # Consecutive images in which each person has an arm raised, by tracking id
        # (see look_for_caller)
        self.raised_count = {}

    def reset_callback(self, msg: Empty):
        self.get_logger().info('Reset: waiting for someone to call')
        self.release()

    def detections_callback(self, msg: DetectionArray):
        people = [d for d in msg.detections if d.class_name == 'person']

        if self.target_id is None:
            self.look_for_caller(people)
        if self.target_id is not None:
            self.follow_target(people)

    def look_for_caller(self, people):
        """
        Count the images in which each person has an arm raised, and choose one.

        It runs once per YOLO result (one image). self.raised_count is a dictionary
        that maps the tracking id of each person to the number of consecutive images
        in which that person has had an arm raised. For example, with
        frames_to_confirm = 3 and two people, 4 (arm raised) and 9 (arm down):

          image 1: {'4': 1}
          image 2: {'4': 2}
          image 3: {'4': 3}  -> person 4 is calling

        If person 4 lowers the arm in image 2, the count goes back to {} and the
        three images start again. The tracking id is what tells that the person in
        this image is the same one as in the previous image.
        """
        # A new dictionary is built in every image with only the people who have an
        # arm raised in it. Each one gets the count of the previous image plus 1
        # (get(..., 0): 0 if they did not have it raised in the previous image).
        # Whoever lowers the arm, or is no longer seen, is not copied into the new
        # dictionary, so their count starts from 0 again: the images must be
        # consecutive
        raised_count = {}
        for person in people:
            angle = arm_angle(person)
            if angle is not None and angle >= self.arm_angle_threshold:
                raised_count[person.id] = self.raised_count.get(person.id, 0) + 1
        self.raised_count = raised_count

        if people and not raised_count:
            self.get_logger().info(
                'Seen people, but nobody is calling', throttle_duration_sec=2.0)

        # The first person who reaches frames_to_confirm images is the one who called.
        # From now on detections_callback calls follow_target instead of this method
        for person_id, count in raised_count.items():
            if count >= self.frames_to_confirm:
                self.get_logger().info(f'Person {person_id} is calling')
                self.target_id = person_id
                self.calling_pub.publish(String(data=person_id))
                return

    def follow_target(self, people):
        """Publish the attractive vector towards the person who called."""
        # YOLO tracking gives each person the same id in every image while it sees them,
        # so the person is found by id even if they have lowered the arm. If they are not
        # in this image, nothing is published: when the vectors stop, the FSM gives up
        for person in people:
            if person.id == self.target_id:
                position = self.position_in_base(person)
                if position is not None:
                    self.attractive_pub.publish(position)
                return

    def position_in_base(self, detection):
        """Return the position of a detection in base_frame as a Vector3, or None."""
        point = PointStamped()
        point.header.frame_id = (self.optical_frame if self.fix_image_frame
                                 else detection.bbox3d.frame_id)
        point.point = detection.bbox3d.center.position
        try:
            # Latest transform instead of the one at the detection time: on the TurtleBot 4
            # the camera and the base use different clocks (see yolo_class_detector_node_3d)
            transform = self.tf_buffer.lookup_transform(
                self.base_frame, point.header.frame_id, rclpy.time.Time())
        except Exception as e:
            self.get_logger().error(f'Transform error: {e}', throttle_duration_sec=2.0)
            return None
        transformed_point = do_transform_point(point, transform)

        # The attractive vector goes from the robot to the person
        vec = Vector3()
        vec.x = transformed_point.point.x
        vec.y = transformed_point.point.y
        vec.z = transformed_point.point.z
        return vec


def main(args=None):
    rclpy.init(args=args)
    node = CallingPersonDetectorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
