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

from setuptools import find_packages, setup

package_name = 'vff_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/vff_2d.launch.py']),
        ('share/' + package_name + '/launch', ['launch/vff_3d.launch.py']),
        ('share/' + package_name + '/launch', ['launch/yolo_class_3d.launch.py']),
        ('share/' + package_name + '/launch', ['launch/yolo_class_2d.launch.py']),
        ('share/' + package_name + '/launch', ['launch/yolo_class_3d_alt.launch.py']),
        ('share/' + package_name + '/launch', ['launch/obstacle_detector.launch.py']),
        ('share/' + package_name + '/launch', ['launch/full_vff_2d.launch.py']),
        ('share/' + package_name + '/launch', ['launch/full_vff_3d.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Rodrigo Pérez-Rodríguez',
    maintainer_email='rodrigo.perez@urjc.es',
    description=('Reactive navigation with Virtual Force Field: laser (repulsion) and '
                 'YOLO (attraction)'),
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'vff_controller_node = vff_control.vff_controller_node:main',
            'obstacle_detector_node = vff_control.obstacle_detector_node:main',
            'obstacle_detector_node_no_tf = vff_control.obstacle_detector_node_no_tf:main',
            'yolo_class_detector_node_2d = vff_control.yolo_class_detector_node_2d:main',
            'yolo_class_detector_node_3d = vff_control.yolo_class_detector_node_3d:main',
            'yolo_class_detector_node_3d_alt = vff_control.yolo_class_detector_node_3d_alt:main',
        ],
    },
)
