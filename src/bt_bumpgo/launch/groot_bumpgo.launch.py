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
        Node(
            package='bt_bumpgo',
            executable='bumpgo_groot',
            name='bt_bumpgo',
            output='screen',
            parameters=[{
                'enable_stamped_cmd_vel': LaunchConfiguration('enable_stamped_cmd_vel')
            }],
            remappings=[
                ('/out_vel', '/cmd_vel'),
                ('/bumper', '/events/bumper')
            ]
        )
    ])
