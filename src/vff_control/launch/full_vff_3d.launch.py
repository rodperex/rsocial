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

import os

from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from rsocial_robots import get_robot, robot_arguments


def launch_setup(context):
    robot = get_robot(context)

    def float_arg(name):
        return float(LaunchConfiguration(name).perform(context))

    return [
        # Obstacle detector node (publishes raw repulsive vectors)
        Node(
            package='vff_control',
            executable='obstacle_detector_node',
            name='obstacle_detector_node',
            output='screen',
            parameters=[{
                'use_sim_time': robot['use_sim_time'],
                'min_distance': 0.5,
                'base_frame': 'base_footprint'
            }],
            remappings=[
                ('/input_laser', robot['scan_topic'])
            ]
        ),

        # YOLO launcher
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('camera'),
                    'launch',
                    'yolo.launch.py'
                )
            ),
            launch_arguments={
                'robot': LaunchConfiguration('robot'),
                'device': LaunchConfiguration('device'),
                'use_3d': 'True'  # needed to publish /yolo/detections_3d,
            }.items()
        ),

        # YOLO messages to standard
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('camera'),
                    'launch',
                    'yolo_to_standard3d.launch.py'
                )
            ),
            launch_arguments={
                'robot': LaunchConfiguration('robot'),
            }.items()
        ),

        # YOLO class detector node (publishes attractive vectors). Needs YOLO to be running
        Node(
            package='vff_control',
            executable='yolo_class_detector_node_3d',
            name='yolo_class_detector_node_3d',
            output='screen',
            parameters=[{
                'use_sim_time': robot['use_sim_time'],
                'target_class': LaunchConfiguration('target_class'),
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
                'use_sim_time': robot['use_sim_time'],
                'max_linear_speed': 0.5,
                'max_angular_speed': float_arg('max_angular_speed'),
                'angular_gain': float_arg('angular_gain'),
                'repulsive_gain_factor': 0.5,
                'repulsive_influence_distance': 0.5,
                'search_angular_speed': float_arg('search_angular_speed'),
                'search_timeout': float_arg('search_timeout'),
                'stay_distance': 1.0,
                'enable_stamped_cmd_vel': robot['stamped_cmd_vel'],
                'bumper_type': robot['bumper_type'],
                'bumper_topic': robot['bumper_topic']
            }],
            remappings=[
                ('/vel', '/cmd_vel')
            ]
        ),
    ]


def generate_launch_description():
    return LaunchDescription(robot_arguments() + [
        DeclareLaunchArgument(
            'target_class',
            default_value='sports ball',
            description='YOLO class the robot goes to (e.g. person, chair, cup, bottle)'
        ),
        DeclareLaunchArgument(
            'device',
            default_value='cuda:0',
            description='Device YOLO runs on: cuda:0 (GPU) or cpu'
        ),
        DeclareLaunchArgument(
            'angular_gain',
            default_value='2.0',
            description='Angular speed (rad/s) per radian between the robot and the VFF vector'
        ),
        DeclareLaunchArgument(
            'max_angular_speed',
            default_value='1.2',
            description='Maximum angular speed (rad/s)'
        ),
        DeclareLaunchArgument(
            'search_angular_speed',
            default_value='0.8',
            description='Angular speed (rad/s) of the target search (0.0 disables it)'
        ),
        DeclareLaunchArgument(
            'search_timeout',
            default_value='0.5',
            description='Seconds without seeing the target before the search starts'
        ),
        OpaqueFunction(function=launch_setup),
    ])
