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

from setuptools import find_packages, setup

package_name = 'hri_examples'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Package index marker
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        # Package manifest
        ('share/' + package_name, ['package.xml']),
        # Launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Configuration files
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Rodrigo Pérez-Rodríguez',
    maintainer_email='rodrigo.perez@urjc.es',
    description=('Human-robot interaction examples (STT, TTS, information extraction) '
                 'with simple_hri'),
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'say = hri_examples.say_client_node:main',
            'repeat = hri_examples.repeat_node:main',
            'generate_response_node = hri_examples.generate_response_node:main',
            'nao_hri_example = hri_examples.nao_hri_example:main',
            'hri_example = hri_examples.hri_example:main',
            'hri_example2 = hri_examples.hri_example2:main',
            'hri_example3 = hri_examples.hri_example3:main',
            'hri_example_client = hri_examples.hri_example_client:main',
            'hri_example2_client = hri_examples.hri_example2_client:main',
            'hri_example3_client = hri_examples.hri_example3_client:main',
        ],
    },
)
