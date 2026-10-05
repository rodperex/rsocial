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

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Header
from vision_msgs.msg import Detection3D, Detection3DArray, ObjectHypothesisWithPose
from yolo_msgs.msg import DetectionArray


class YoloToStandardNode3D(Node):

    def __init__(self):
        super().__init__('yolo_to_standard_node_3d')

        self.declare_parameter('fix_image_frame', False)
        self.declare_parameter('optical_frame', 'camera_rgb_optical_frame')
        self.fix_image_frame = self.get_parameter('fix_image_frame').value
        self.optical_frame = self.get_parameter('optical_frame').get_parameter_value().string_value

        self.detection_sub = self.create_subscription(
            DetectionArray,
            'input_detection',
            self.detection_callback,
            rclpy.qos.qos_profile_sensor_data
        )

        self.detection_pub = self.create_publisher(
            Detection3DArray,
            'output_detection_3d',
            rclpy.qos.qos_profile_sensor_data
        )

    def detection_callback(self, msg: DetectionArray):
        detection_array_msg = Detection3DArray()
        detection_array_msg.header = msg.header

        for detection in msg.detections:
            detection_msg = Detection3D()
            # Build a new Header: assigning msg.header and then changing frame_id would
            # modify the same object shared by every detection and by the array
            detection_msg.header = Header()
            detection_msg.header.stamp = msg.header.stamp
            # Some cameras (e.g. the Kobuki simulator) stamp their images with a frame that
            # is not the optical one, so the 3D points would be read in the wrong axes
            if self.fix_image_frame:
                detection_msg.header.frame_id = self.optical_frame
            else:
                detection_msg.header.frame_id = detection.bbox3d.frame_id

            detection_msg.bbox.center.position.x = detection.bbox3d.center.position.x
            detection_msg.bbox.center.position.y = detection.bbox3d.center.position.y
            detection_msg.bbox.center.position.z = detection.bbox3d.center.position.z

            detection_msg.bbox.size.x = detection.bbox3d.size.x
            detection_msg.bbox.size.y = detection.bbox3d.size.y
            detection_msg.bbox.size.z = detection.bbox3d.size.z

            self.get_logger().debug(f'Detected {detection.class_name} at '
                                    f'x={detection.bbox3d.center.position.x:.2f}, '
                                    f'y={detection.bbox3d.center.position.y:.2f}, '
                                    f'z={detection.bbox3d.center.position.z:.2f} '
                                    f'({detection.bbox3d.frame_id})')

            obj_msg = ObjectHypothesisWithPose()
            obj_msg.hypothesis.class_id = detection.class_name
            obj_msg.hypothesis.score = detection.score

            obj_msg.pose.pose.position.x = detection.bbox3d.center.position.x
            obj_msg.pose.pose.position.y = detection.bbox3d.center.position.y
            obj_msg.pose.pose.position.z = detection.bbox3d.center.position.z

            detection_msg.results.append(obj_msg)
            detection_array_msg.detections.append(detection_msg)

        self.detection_pub.publish(detection_array_msg)


def main(args=None):
    rclpy.init(args=args)
    node = YoloToStandardNode3D()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
