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

from setuptools import setup

package_name = 'node_programming'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    install_requires=['setuptools'],
    zip_safe=True,
    extras_require={'test': ['pytest']},
    package_data={
        package_name: ['resource/*', 'launch/*'],
    },
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch',
            ['launch/pubsub.launch.py', 'launch/lc_pubsub.launch.py']),
    ],
    entry_points={
        'console_scripts': [
            'publisher_node = node_programming.publisher_node:main',
            'subscriber_node = node_programming.subscriber_node:main',
            'logger_node = node_programming.logger_node:main',
            'lifecycle_publisher_node = node_programming.lifecycle_publisher_node:main',
            'simple_node_creation = node_programming.simple_node_creation:main',
            'simple_node_logging = node_programming.simple_node_logging:main',
            'simple_node_publishing = node_programming.simple_node_publishing:main',
            'simple_callback = node_programming.simple_callback:main',
        ],
    },
)
