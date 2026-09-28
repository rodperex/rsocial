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
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose
from yolo_msgs.msg import DetectionArray


class YoloToStandardNode(Node):
    def __init__(self):
        super().__init__('yolo_to_standard_node')

        self.detection_sub = self.create_subscription(
            DetectionArray,
            'input_detection',
            self.detection_callback,
            rclpy.qos.qos_profile_sensor_data
        )

        self.detection_pub = self.create_publisher(
            Detection2DArray,
            'output_detection_2d',
            rclpy.qos.qos_profile_sensor_data
        )

    def detection_callback(self, msg: DetectionArray):
        detection_array_msg = Detection2DArray()
        detection_array_msg.header = msg.header

        for detection in msg.detections:
            detection_msg = Detection2D()
            detection_msg.header = msg.header

            detection_msg.bbox.center.position.x = detection.bbox.center.position.x
            detection_msg.bbox.center.position.y = detection.bbox.center.position.y
            detection_msg.bbox.size_x = detection.bbox.size.x
            detection_msg.bbox.size_y = detection.bbox.size.y

            obj_msg = ObjectHypothesisWithPose()
            obj_msg.hypothesis.class_id = detection.class_name
            obj_msg.hypothesis.score = detection.score

            detection_msg.results.append(obj_msg)
            detection_array_msg.detections.append(detection_msg)

        self.detection_pub.publish(detection_array_msg)


def main(args=None):
    rclpy.init(args=args)
    node = YoloToStandardNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
