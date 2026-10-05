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
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rsocial_robots import get_robot, robot_arguments


def launch_setup(context):
    robot = get_robot(context)

    return [
        Node(
            package='laser',
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
    ]


def generate_launch_description():
    return LaunchDescription(robot_arguments() + [
        OpaqueFunction(function=launch_setup),
    ])
