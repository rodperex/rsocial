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

"""Settings of the robots of the course (Kobuki and TurtleBot 4) for the example launchers."""

import os

from ament_index_python import get_package_share_directory
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import yaml


def load_robots():
    """Return the settings of every robot, read from config/robots.yaml."""
    path = os.path.join(get_package_share_directory('rsocial_robots'), 'config', 'robots.yaml')
    with open(path) as f:
        return yaml.safe_load(f)


def get_robot(context):
    """Return the settings of the robot chosen with the robot launch argument."""
    return load_robots()[LaunchConfiguration('robot').perform(context)]


def robot_arguments():
    """Declare the robot launch argument of the examples."""
    return [
        DeclareLaunchArgument(
            'robot',
            choices=list(load_robots()),
            description=('Robot the example runs on, simulated (kobuki_sim, tb4_sim) '
                         'or real (kobuki, tb4, tb4_rgbd)')
        ),
    ]
