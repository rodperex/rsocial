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
    # Command line argument to toggle between normal and erratic PID constants
    erratic_arg = DeclareLaunchArgument(
        'erratic',
        default_value='False',
        description='Set to True to use erratic PID constants that cause oscillation'
    )

    # Node for publishing TF
    publisher_cmd = Node(
        package='tf_seeker',
        executable='tf_publisher_node',
        name='tf_publisher_node',
        output='screen',
        parameters=[{'use_sim_time': True,
                     'tf_update_time': 60.0}],
    )

    # Node for seeking TF
    seeker_cmd = Node(
        package='tf_seeker',
        executable='tf_seeker_node',
        name='tf_seeker_node',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'erratic': LaunchConfiguration('erratic')
        }],
    )

    ld = LaunchDescription()
    ld.add_action(erratic_arg)
    ld.add_action(publisher_cmd)
    ld.add_action(seeker_cmd)

    return ld
