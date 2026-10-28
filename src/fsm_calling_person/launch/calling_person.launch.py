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
        # YOLO with a pose model and 3D positions (publishes /yolo/detections_3d)
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
                'model': LaunchConfiguration('model'),
                # The detector needs the tracking id to follow the same person between
                # images (it is the default of yolo_bringup, set here to make it explicit)
                'use_tracking': 'True',
                'use_3d': 'True'
            }.items()
        ),

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

        # VFF controller node, the same one as in vff_control. It starts disabled: the FSM
        # enables it on /vff_enable when a person calls the robot
        Node(
            package='vff_control',
            executable='vff_controller_node',
            name='vff_controller_node',
            output='screen',
            parameters=[{
                'use_sim_time': robot['use_sim_time'],
                'start_enabled': False,
                'max_linear_speed': 0.3,
                'max_angular_speed': 1.0,
                'angular_gain': 1.5,
                'repulsive_gain_factor': 0.5,
                'repulsive_influence_distance': 0.5,
                # Same distance as the FSM: the VFF stops there even if the FSM is late
                'stay_distance': float_arg('arrive_distance'),
                'enable_stamped_cmd_vel': robot['stamped_cmd_vel'],
                'bumper_type': robot['bumper_type'],
                'bumper_topic': robot['bumper_topic']
            }],
            remappings=[
                ('/vel', '/cmd_vel'),
                ('/enable', '/vff_enable')
            ]
        ),

        # Calling person detector node (publishes attractive vectors towards the person who
        # raised an arm). It takes the place of yolo_class_detector_node_3d of full_vff_3d
        Node(
            package='fsm_calling_person',
            executable='calling_person_detector_node',
            name='calling_person_detector_node',
            output='screen',
            parameters=[{
                'use_sim_time': robot['use_sim_time'],
                'arm_angle_threshold': float_arg('arm_angle_threshold'),
                'base_frame': 'base_footprint',
                'fix_image_frame': robot['fix_image_frame'],
                'optical_frame': robot['optical_frame']
            }],
            remappings=[
                ('/input_detections', '/yolo/detections_3d')
            ]
        ),

        # FSM: turns until a person calls, enables the VFF and resets the detector
        Node(
            package='fsm_calling_person',
            executable='calling_person_fsm_node',
            name='calling_person_fsm',
            output='screen',
            parameters=[{
                'use_sim_time': robot['use_sim_time'],
                'arrive_distance': float_arg('arrive_distance'),
                'search_angular_speed': float_arg('search_angular_speed'),
                'enable_stamped_cmd_vel': robot['stamped_cmd_vel']
            }],
            remappings=[
                ('/vel', '/cmd_vel')
            ]
        ),
    ]


def generate_launch_description():
    return LaunchDescription(robot_arguments() + [
        DeclareLaunchArgument(
            'device',
            default_value='cuda:0',
            description='Device YOLO runs on: cuda:0 (GPU) or cpu'
        ),
        DeclareLaunchArgument(
            'model',
            default_value='yolov8m-pose.pt',
            description='YOLO pose model (e.g. yolov8n-pose.pt, faster without GPU)'
        ),
        DeclareLaunchArgument(
            'arm_angle_threshold',
            default_value='120.0',
            description='Arm angle (degrees, 0 down, 90 horizontal, 180 up) to call the robot'
        ),
        DeclareLaunchArgument(
            'arrive_distance',
            default_value='1.0',
            description='Distance (m) to the person at which the robot stops'
        ),
        DeclareLaunchArgument(
            'search_angular_speed',
            default_value='0.5',
            description='Angular speed (rad/s) at which the FSM turns while nobody is calling'
        ),
        OpaqueFunction(function=launch_setup),
    ])
