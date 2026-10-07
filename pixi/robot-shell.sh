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

# Opens the interactive shell of the robot tasks (tb4, tb4-sim, kobuki...):
# the workspace sourced and the robot variables set by the task.
#
# Usage: bash pixi/robot-shell.sh <label> <variable>...
#   e.g. bash pixi/robot-shell.sh "TurtleBot 4" ROS_DOMAIN_ID RMW_IMPLEMENTATION ROBOT
#
# Why: an interactive bash reads ~/.bashrc, and ROS users often set
# ROS_DOMAIN_ID or RMW_IMPLEMENTATION there. A plain `exec bash` would let
# ~/.bashrc override the values of the task (e.g. domain 1 and CycloneDDS
# instead of domain 0 and Fast DDS), and the robot topics would not show up.
#
# How: the shell starts with a temporary rcfile that sources ~/.bashrc first
# and then sets the given variables again with the values received from the
# task, so they always win.

label=$1
shift

rcfile=$(mktemp)
{
  echo '[ -f ~/.bashrc ] && source ~/.bashrc'
  for var in "$@"; do
    if [ -n "${!var+x}" ]; then
      printf 'export %s=%q\n' "$var" "${!var}"
    fi
  done
  echo '[ -f install/setup.bash ] && source install/setup.bash'
  # A daemon started with other DDS settings would hide the robot topics
  echo 'ros2 daemon stop > /dev/null 2>&1'
  printf 'echo %q' "$label:"
  for var in "$@"; do
    printf ' %s=$%s' "$var" "$var"
  done
  echo
  printf 'rm -f %q\n' "$rcfile"
} > "$rcfile"

exec bash --rcfile "$rcfile"
