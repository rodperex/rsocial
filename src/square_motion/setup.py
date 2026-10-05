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

package_name = 'square_motion'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/square_move.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    extras_require={'test': ['pytest']},
    maintainer='Rodrigo Pérez-Rodríguez',
    maintainer_email='rodrigo.perez@urjc.es',
    description='Open-loop square motion (time-based control)',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'square_move = square_motion.square_move_node:main',
        ],
    },
)
