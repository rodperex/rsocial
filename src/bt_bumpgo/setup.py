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

from glob import glob
import os

from setuptools import setup

package_name = 'bt_bumpgo'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'bt_xml'), glob('bt_xml/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Rodrigo Pérez-Rodríguez',
    maintainer_email='rodrigo.perez@urjc.es',
    description='Bump-and-go behavior implemented with behavior trees (py_trees)',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'bumpgo = bt_bumpgo.bumpgo:main',
            'bumpgo_side = bt_bumpgo.bumpgo_side:main',
            'bumpgo_groot = bt_bumpgo.bumpgo_groot:main',
            'bumpgo_tb4 = bt_bumpgo.bumpgo_tb4:main',
            'bumpgo_side_tb4 = bt_bumpgo.bumpgo_side_tb4:main',
            'bumpgo_groot_tb4 = bt_bumpgo.bumpgo_groot_tb4:main',
        ],
    },
)
