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
from launch_ros.parameter_descriptions import ParameterValue
from rsocial_robots import get_robot, robot_arguments


def launch_setup(context):
    robot = get_robot(context)

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

        # YOLO class detector node (publishes attractive vectors). Needs YOLO to be running
        Node(
            package='vff_control',
            executable='yolo_class_detector_node_2d',
            name='yolo_class_detector_node_2d',
            output='screen',
            parameters=[{
                'use_sim_time': robot['use_sim_time'],
                'target_class': LaunchConfiguration('target_class'),
                'min_confidence': ParameterValue(
                    LaunchConfiguration('min_confidence'), value_type=float),
                'base_frame': 'base_footprint',
                'optical_frame': robot['optical_frame']
            }],
            remappings=[
                ('/input_detection_2d', '/detections_2d'),
                ('/input_image', robot['image_topic']),
                ('/camera_info', robot['camera_info_topic'])
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
                # Starts moving the robot. With False it waits for True on /enable
                # (std_msgs/Bool), as in fsm_calling_person
                'start_enabled': True,
                'max_linear_speed': 0.5,
                'max_angular_speed': 0.7,
                'repulsive_gain_factor': 0.5,
                'repulsive_influence_distance': 0.5,
                'search_angular_speed': 0.4,  # 0.0 disables the target search
                'search_timeout': 2.0,
                'stay_distance': -1.0,  # No stay distance in 2D
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
            'min_confidence',
            default_value='0.6',
            description='Minimum YOLO score for a detection of the target class to be used'
        ),
        OpaqueFunction(function=launch_setup),
    ])
