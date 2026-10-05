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

# TurtleBot 4 simulator in the AWS RoboMaker small house.
#
# turtlebot4_gz.launch.py cannot load this world: its sim.launch.py overwrites
# GZ_SIM_RESOURCE_PATH with its own folders, so the house and its models are
# never found. This launch file starts Gazebo like sim.launch.py does, adding
# those folders, and then spawns the robot with turtlebot4_spawn.launch.py.

import os
from pathlib import Path
import re
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            SetEnvironmentVariable, SetLaunchConfiguration)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# The world name must match the one inside the SDF file: the TurtleBot 4
# bridges build their Gazebo topics from it (/world/<name>/model/...)
WORLD_NAME = 'small_house'


def make_world_file(house_dir):
    """Write a copy of the house world adapted to the TurtleBot 4 and return its folder."""
    with open(os.path.join(house_dir, 'worlds', 'small_house.world')) as f:
        sdf = f.read()

    sdf = sdf.replace("<world name='default'>", f"<world name='{WORLD_NAME}'>", 1)
    # The robot loads its own Sensors system (with ogre); a second one from the
    # world would clash with it
    sdf = re.sub(r'<plugin\s+filename="gz-sim-sensors-system".*?</plugin>', '', sdf,
                 count=1, flags=re.DOTALL)
    # Same physics step as the TurtleBot 4 worlds
    sdf = sdf.replace('<max_step_size>0.005</max_step_size>',
                      '<max_step_size>0.003</max_step_size>', 1)
    # Contact system, needed by the bumper, as in the TurtleBot 4 worlds
    sdf = sdf.replace(
        '<physics ',
        '<plugin filename="gz-sim-contact-system" name="gz::sim::systems::Contact"/>\n'
        '    <physics ', 1)

    world_dir = tempfile.mkdtemp(prefix='tb4_worlds_')
    with open(os.path.join(world_dir, WORLD_NAME + '.sdf'), 'w') as f:
        f.write(sdf)
    return world_dir


def generate_launch_description():
    pkg_turtlebot4_gz_bringup = get_package_share_directory('turtlebot4_gz_bringup')
    pkg_turtlebot4_gz_gui_plugins = get_package_share_directory('turtlebot4_gz_gui_plugins')
    pkg_turtlebot4_description = get_package_share_directory('turtlebot4_description')
    pkg_irobot_create_description = get_package_share_directory('irobot_create_description')
    pkg_irobot_create_gz_bringup = get_package_share_directory('irobot_create_gz_bringup')
    pkg_irobot_create_gz_plugins = get_package_share_directory('irobot_create_gz_plugins')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_house = get_package_share_directory('aws_robomaker_small_house_world')

    world_dir = make_world_file(pkg_house)

    arguments = [
        DeclareLaunchArgument('namespace', default_value='', description='Robot namespace'),
        DeclareLaunchArgument('rviz', default_value='false', choices=['true', 'false'],
                              description='Start rviz'),
        DeclareLaunchArgument('model', default_value='standard', choices=['standard', 'lite'],
                              description='TurtleBot 4 model'),
        # Default pose: an open spot in the middle of the house, with room for the dock
        DeclareLaunchArgument('x', default_value='0.0', description='Robot x (m)'),
        DeclareLaunchArgument('y', default_value='1.5', description='Robot y (m)'),
        DeclareLaunchArgument('z', default_value='0.0', description='Robot z (m)'),
        DeclareLaunchArgument('yaw', default_value='0.0', description='Robot yaw (rad)'),
    ]

    # Same folders as sim.launch.py, plus the house world and its models
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.pathsep.join([
            world_dir,
            os.path.join(pkg_house, 'models'),
            os.path.join(pkg_turtlebot4_gz_bringup, 'worlds'),
            os.path.join(pkg_irobot_create_gz_bringup, 'worlds'),
            str(Path(pkg_turtlebot4_description).parent.resolve()),
            str(Path(pkg_irobot_create_description).parent.resolve()),
        ]))

    gz_gui_plugin_path = SetEnvironmentVariable(
        name='GZ_GUI_PLUGIN_PATH',
        value=os.pathsep.join([
            os.path.join(pkg_turtlebot4_gz_gui_plugins, 'lib'),
            os.path.join(pkg_irobot_create_gz_plugins, 'lib'),
        ]))

    # The robot bridges read the world name from this launch configuration
    world_name = SetLaunchConfiguration('world', WORLD_NAME)

    gui_config = [os.path.join(pkg_turtlebot4_gz_bringup, 'gui'), '/',
                  LaunchConfiguration('model'), '/gui.config']
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments=[
            ('gz_args', [WORLD_NAME + '.sdf -r -v 4 --gui-config '] + gui_config),
        ])

    clock_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='clock_bridge', output='screen',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'])

    robot_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_turtlebot4_gz_bringup, 'launch', 'turtlebot4_spawn.launch.py')),
        launch_arguments=[
            (name, LaunchConfiguration(name))
            for name in ['namespace', 'rviz', 'model', 'x', 'y', 'z', 'yaw']
        ])

    ld = LaunchDescription(arguments)
    ld.add_action(gz_resource_path)
    ld.add_action(gz_gui_plugin_path)
    ld.add_action(world_name)
    ld.add_action(gazebo)
    ld.add_action(clock_bridge)
    ld.add_action(robot_spawn)
    return ld
