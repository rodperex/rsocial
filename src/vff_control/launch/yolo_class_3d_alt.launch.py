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

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from rsocial_robots import get_robot, robot_arguments


def launch_setup(context):
    robot = get_robot(context)

    return [
        Node(
            package='vff_control',
            executable='yolo_class_detector_node_3d_alt',
            name='yolo_class_detector_node_3d_alt',
            output='screen',
            parameters=[{
                'use_sim_time': robot['use_sim_time'],
                'target_class': LaunchConfiguration('target_class'),
                'base_frame': 'base_footprint',
                'optical_frame': robot['optical_frame']
            }],
            remappings=[
                ('/input_detection_2d', '/detections_2d'),
                ('/input_depth_image', robot['depth_topic']),
                ('/camera_info', robot['camera_info_topic'])
            ]
        ),
    ]


def generate_launch_description():
    return LaunchDescription(robot_arguments() + [
        DeclareLaunchArgument(
            'target_class',
            default_value='chair',
            description='YOLO class the robot goes to (e.g. person, chair, cup, bottle)'
        ),
        OpaqueFunction(function=launch_setup),
    ])
