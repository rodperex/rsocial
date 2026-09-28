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

"""
Minimal loader for BehaviorTree.CPP / Groot XML files into py_trees.

Supports the subset of nodes used in the course:
  - Control: Sequence, ReactiveSequence, Fallback, ReactiveFallback
  - Decorators: Inverter, ForceSuccess, ForceFailure
  - Leaves: Action, Condition (matched by `name` attribute or, if absent, by `ID`),
    or a custom node written with its own tag (<CheckBump/>)

Semantics follow BehaviorTree.CPP:
  - Sequence / Fallback keep memory (resume from the RUNNING child)
  - ReactiveSequence / ReactiveFallback have no memory (re-tick from the first child)
"""

from xml.etree import ElementTree

import py_trees

CONTROL_NODES = {
    'Sequence': (py_trees.composites.Sequence, True),
    'ReactiveSequence': (py_trees.composites.Sequence, False),
    'Fallback': (py_trees.composites.Selector, True),
    'ReactiveFallback': (py_trees.composites.Selector, False),
}

DECORATOR_NODES = {
    'Inverter': py_trees.decorators.Inverter,
    'ForceSuccess': py_trees.decorators.FailureIsSuccess,
    'ForceFailure': py_trees.decorators.SuccessIsFailure,
}


def load(xml_path: str, behaviours: list) -> py_trees.behaviour.Behaviour:
    """Build the py_trees tree described in `xml_path` using the given behaviour instances."""
    available = {bh.name: bh for bh in behaviours}
    root = ElementTree.parse(xml_path).getroot()

    trees = {bt.get('ID'): bt for bt in root.findall('BehaviorTree')}
    if not trees:
        raise ValueError(f'No <BehaviorTree> found in {xml_path}')

    main_id = root.get('main_tree_to_execute') or next(iter(trees))
    if main_id not in trees:
        raise ValueError(f'main_tree_to_execute="{main_id}" not found in {xml_path}')

    children = list(trees[main_id])
    if len(children) != 1:
        raise ValueError(f'BehaviorTree "{main_id}" must have exactly one root node')

    return _parse(children[0], available)


def _parse(element, available: dict) -> py_trees.behaviour.Behaviour:
    tag = element.tag
    name = element.get('name') or tag

    if tag in CONTROL_NODES:
        composite_class, memory = CONTROL_NODES[tag]
        composite = composite_class(name=name, memory=memory)
        composite.add_children([_parse(child, available) for child in element])
        return composite

    if tag in DECORATOR_NODES:
        children = list(element)
        if len(children) != 1:
            raise ValueError(f'Decorator <{tag}> must have exactly one child')
        return DECORATOR_NODES[tag](name=name, child=_parse(children[0], available))

    # Leaf node: <Action ID="X"/>, <Condition ID="X"/> or <X/>
    if tag in ('Action', 'Condition'):
        leaf_id = element.get('name') or element.get('ID')
    else:
        leaf_id = tag
    if leaf_id not in available:
        # Fail loudly: silently replacing it by a dummy node hides errors in the XML
        raise ValueError(f'Behaviour "{leaf_id}" used in the XML was not provided. '
                         f'Available: {sorted(available)}')
    return available[leaf_id]
