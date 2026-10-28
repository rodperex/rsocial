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

from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.launch_description import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from rsocial_robots import get_robot, robot_arguments


def launch_setup(context):
    robot = get_robot(context)

    def float_arg(name):
        return float(LaunchConfiguration(name).perform(context))

    return [
        Node(
            package='nav2_example',
            executable='simple_navigation_app',
            name='simple_navigation_app_py_node',
            output='screen',
            parameters=[{
                # In the simulator the node uses its clock, so that the timeout counts
                # robot time (see navigation_client)
                'use_sim_time': robot['use_sim_time'],
                'x': float_arg('x'),
                'y': float_arg('y'),
                'yaw': float_arg('yaw'),
                'goal_timeout': float_arg('goal_timeout'),
            }]
        ),
    ]


def generate_launch_description():
    return LaunchDescription(robot_arguments() + [
        DeclareLaunchArgument('x', default_value='6.0', description='Goal x (m, map frame)'),
        DeclareLaunchArgument('y', default_value='-2.0', description='Goal y (m, map frame)'),
        DeclareLaunchArgument('yaw', default_value='0.0', description='Goal yaw (rad)'),
        DeclareLaunchArgument(
            'goal_timeout', default_value='120.0',
            description='Seconds of robot time to reach the goal before canceling it'),
        OpaqueFunction(function=launch_setup),
    ])
