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


def republisher(name, compressed_topic, output_topic, use_sim_time):
    # The transport is the last part of the compressed topic (compressed or compressedDepth)
    base_topic, transport = compressed_topic.rsplit('/', 1)
    return Node(
        package='image_transport',
        executable='republish',
        name=name,
        output='screen',
        parameters=[{
            'in_transport': transport,
            'out_transport': 'raw',
            'use_sim_time': use_sim_time,
        }],
        remappings=[
            ('in/' + transport, compressed_topic),
            ('out', output_topic),
        ]
    )


def launch_setup(context):
    robot = get_robot(context)

    # Only robots whose images arrive compressed have something to decompress
    nodes = []
    if 'compressed_image_topic' in robot:
        nodes.append(republisher('decompress_image', robot['compressed_image_topic'],
                                 robot['image_topic'], robot['use_sim_time']))
    if 'compressed_depth_topic' in robot:
        nodes.append(republisher('decompress_depth', robot['compressed_depth_topic'],
                                 robot['depth_topic'], robot['use_sim_time']))
    return nodes


def generate_launch_description():
    return LaunchDescription(robot_arguments() + [
        OpaqueFunction(function=launch_setup),
    ])
