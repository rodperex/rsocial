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

setup(
    name='comms_demo',
    version='0.0.1',
    packages=['comms_demo'],  # <- MUST match the package folder
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/comms_demo']),
        ('share/comms_demo', ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    extras_require={'test': ['pytest']},
    maintainer='Rodrigo Pérez-Rodríguez',
    maintainer_email='rodrigo.perez@urjc.es',
    description='Service and action client/server examples using comms_interfaces',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'action_client = comms_demo.action_client:main',
            'action_server = comms_demo.action_server:main',
            'service_client = comms_demo.service_client:main',
            'service_server = comms_demo.service_server:main'
        ],
    },
)
