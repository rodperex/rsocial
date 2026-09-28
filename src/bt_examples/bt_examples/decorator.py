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

import random

import py_trees
import py_trees.behaviour
import py_trees.common
import py_trees.composites
import py_trees.decorators


class RandomNumber(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)

    def update(self):
        number = random.randint(0, 10)
        print(f'[{self.name}] Generated number: {number}.')
        if number > 9:
            print(f'[{self.name}] Number {number} is greater than 9. Succeeding.')
            return py_trees.common.Status.SUCCESS
        else:
            print(f'[{self.name}] Number {number} is not greater than 9. Failing.')
            return py_trees.common.Status.FAILURE


def create_root():
    root = py_trees.composites.Sequence('BT example', memory=True)

    r1 = RandomNumber('RandomNumber 1')
    r2 = RandomNumber('RandomNumber 2')
    # Check decorators documentation for more options: https://py-
    # trees.readthedocs.io/en/devel/decorators.html
    failure_is_success = py_trees.decorators.FailureIsSuccess('FailureIsSuccess', child=r1)
    retry = py_trees.decorators.Retry('Retry', child=r2, num_failures=float('inf'))
    root.add_child(failure_is_success)
    root.add_child(retry)

    return root


def main():
    py_trees.logging.level = py_trees.logging.Level.DEBUG
    root = create_root()

    root.setup_with_descendants()

    while True:
        root.tick_once()
        print(f'Root status: {root.status}')
        if root.status in (py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE):
            print(f'Behavior Tree finished with status: {root.status}')
            break


if __name__ == '__main__':
    main()
