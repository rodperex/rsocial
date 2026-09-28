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


class RandomNumber(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)

    def update(self):
        number = random.randint(0, 10)
        print(f'[{self.name}] Generated number: {number}.')
        if number < 3:
            print(f'[{self.name}] Number {number} is less than 3. Succeeding.')
            return py_trees.common.Status.SUCCESS
        elif number < 8:
            print(
                f'[{self.name}] Number {number} is greater than or equal to 3 and less than 8. '
                'Running.')
            return py_trees.common.Status.RUNNING
        else:
            print(f'[{self.name}] Number {number} is greater than or equal to 8. Failing.')
            return py_trees.common.Status.FAILURE


class FiftyFifty(py_trees.behaviour.Behaviour):
    def __init__(self, name):
        super().__init__(name)

    def update(self):
        number = random.randint(0, 1)
        print(f'[{self.name}] Generated number: {number}.')
        if number == 1:
            print(f'[{self.name}] Number {number}. Succeeding.')
            return py_trees.common.Status.SUCCESS
        else:
            print(f'[{self.name}] Number {number}. Failing.')
            return py_trees.common.Status.FAILURE


def create_root():
    root = py_trees.composites.Selector('BT example', memory=False)
    printer_action_1 = FiftyFifty('FiftyFifty_1')
    random_action = RandomNumber('RandomNumber')
    printer_action_2 = FiftyFifty('FiftyFifty_2')
    root.add_child(printer_action_1)
    root.add_child(random_action)
    root.add_child(printer_action_2)

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
