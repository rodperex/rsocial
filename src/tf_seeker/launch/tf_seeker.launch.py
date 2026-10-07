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
    tf_update_time = float(LaunchConfiguration('tf_update_time').perform(context))

    # Node for publishing TF
    publisher_cmd = Node(
        package='tf_seeker',
        executable='tf_publisher_node',
        name='tf_publisher_node',
        output='screen',
        parameters=[{'use_sim_time': robot['use_sim_time'],
                     'tf_update_time': tf_update_time}],
    )

    # Node for seeking TF
    seeker_cmd = Node(
        package='tf_seeker',
        executable='tf_seeker_node',
        name='tf_seeker_node',
        output='screen',
        parameters=[{
            'use_sim_time': robot['use_sim_time'],
            'erratic': LaunchConfiguration('erratic'),
            'enable_stamped_cmd_vel': robot['stamped_cmd_vel']
        }],
    )

    return [publisher_cmd, seeker_cmd]


def generate_launch_description():
    return LaunchDescription(robot_arguments() + [
        # Command line argument to toggle between normal and erratic PID constants
        DeclareLaunchArgument(
            'erratic',
            default_value='False',
            description='Set to True to use erratic PID constants that cause oscillation'
        ),
        # Seconds between targets (simulated time in the simulators, slower than real time)
        DeclareLaunchArgument(
            'tf_update_time',
            default_value='20.0',
            description='Seconds between new random targets'
        ),
        OpaqueFunction(function=launch_setup),
    ])
