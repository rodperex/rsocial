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
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from rsocial_robots import get_robot, robot_arguments

# RViz configuration of each robot family (for now, only the TurtleBot 4)
RVIZ_CONFIGS = {
    'tb4': 'tb4.rviz',
}


def launch_setup(context):
    robot_name = LaunchConfiguration('robot').perform(context)
    family = robot_name.split('_')[0]
    if family not in RVIZ_CONFIGS:
        raise RuntimeError(f'There is no RViz configuration for robot {robot_name} yet')
    robot = get_robot(context)
    config = os.path.join(
        get_package_share_directory('rsocial_robots'), 'rviz', RVIZ_CONFIGS[family])

    return [
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', config, '-f', LaunchConfiguration('fixed_frame').perform(context)],
            parameters=[{'use_sim_time': robot['use_sim_time']}],
        ),
    ]


def generate_launch_description():
    return LaunchDescription(robot_arguments() + [
        DeclareLaunchArgument(
            'fixed_frame', default_value='odom',
            description='Fixed frame of RViz: odom, or map with localization or Nav2 running'),
        OpaqueFunction(function=launch_setup),
    ])
