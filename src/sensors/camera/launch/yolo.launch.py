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
from rsocial_robots import get_robot, load_robots


def launch_setup(context):
    robot = get_robot(context)

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    get_package_share_directory('yolo_bringup'),
                    'launch',
                    'yolo.launch.py'
                )
            ),
            launch_arguments={
                'input_image_topic': robot['image_topic'],
                'input_depth_topic': robot['depth_topic'],
                'input_depth_info_topic': robot['camera_info_topic'],
                'target_frame': robot['camera_frame'],
                'use_3d': LaunchConfiguration('use_3d'),
                'depth_image_units_divisor': str(robot['depth_image_units_divisor']),
                'device': LaunchConfiguration('device'),
            }.items()
        ),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'robot',
            choices=list(load_robots()),
            description=('Robot whose camera feeds YOLO, simulated (kobuki_sim, tb4_sim) '
                         'or real (kobuki, tb4, tb4_rgbd)')
        ),
        DeclareLaunchArgument(
            'use_3d',
            default_value='False',
            description='Set to True to also publish 3D detections (/yolo/detections_3d)'
        ),
        DeclareLaunchArgument(
            'device',
            default_value='cuda:0',
            description='Device YOLO runs on: cuda:0 (GPU) or cpu'
        ),
        OpaqueFunction(function=launch_setup),
    ])
