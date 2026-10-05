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
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        DeclareLaunchArgument(
            'enable_stamped_cmd_vel',
            default_value='false',
            description='Set to true if the robot expects geometry_msgs/TwistStamped on cmd_vel'
        ),

        # Obstacle detector node (publishes raw repulsive vectors)
        Node(
            package='vff_control',
            executable='obstacle_detector_node',
            name='obstacle_detector_node',
            output='screen',
            parameters=[{
                'min_distance': 0.5,
                'base_frame': 'base_footprint'
            }],
            remappings=[
                ('/input_laser', '/scan_raw')
            ]
        ),

        # YOLO class detector node (publishes attractive vectors). Needs YOLO to be running
        Node(
            package='vff_control',
            executable='yolo_class_detector_node_3d',
            name='yolo_class_detector_node_3d',
            output='screen',
            parameters=[{
                'target_class': 'chair',
                'base_frame': 'base_footprint'
            }],
            remappings=[
                ('/input_detection_3d', '/detections_3d'),
            ]
        ),

        # VFF controller node
        Node(
            package='vff_control',
            executable='vff_controller_node',
            name='vff_controller_node',
            output='screen',
            parameters=[{
                'max_linear_speed': 0.1,
                'max_angular_speed': 1.0,
                'repulsive_gain_factor': 0.3,
                'repulsive_influence_distance': 0.5,
                'stay_distance': 1.0,
                'enable_stamped_cmd_vel': LaunchConfiguration('enable_stamped_cmd_vel')
            }],
            remappings=[
                ('/vel', '/cmd_vel')
            ]
        ),
    ])
