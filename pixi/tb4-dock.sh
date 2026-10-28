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

# Docks and undocks the TurtleBot 4 (pixi run dock / undock), and stops the lidar motor
# while it is docked. With power_saver disabled in turtlebot4.yaml the robot keeps the
# camera and the lidar on when docked; this script stops only the lidar, so that it does
# not spin while the robot charges (see README-tb4-real.md).
#
# Usage: bash pixi/tb4-dock.sh dock | undock

# Start or stop the lidar motor ($1: start_motor or stop_motor). Only the real robot has
# these services, so nothing is done in the simulator. It is told apart by /clock, which
# only the simulator publishes: ROBOT cannot be used, because pixi run activates the
# environment again and sets it to tb4_sim, whatever the terminal had. The first call of
# a new ros2 process takes a few seconds to discover the service; the timeout keeps the
# task from waiting forever if the service is not there
lidar_motor() {
    if timeout 10 ros2 topic info /clock 2> /dev/null | grep -q "Publisher count: [1-9]"; then
        return
    fi
    if timeout 30 ros2 service call "/$1" std_srvs/srv/Empty > /dev/null; then
        echo "Lidar: $1"
    else
        echo "Lidar: /$1 did not answer (is the lidar running?)"
    fi
}

case "$1" in
    dock)
        # The output is shown as it arrives (tee) and kept to read the result of the action
        result=$(timeout 120 ros2 action send_goal --feedback /dock \
            irobot_create_msgs/action/Dock '{}' | tee /dev/stderr)
        docked=false
        if grep -q 'is_docked: true' <<< "$result"; then
            docked=true
        # The result sometimes does not reach this computer although the base has docked
        # (right after the robot service restarts): then dock_status is asked. Its type is
        # given because a new ros2 process does not know the topic yet, and without it
        # ros2 topic echo gives up at once instead of waiting for a message
        elif timeout 30 ros2 topic echo --once /dock_status irobot_create_msgs/msg/DockStatus \
                --field is_docked 2> /dev/null | grep -q True; then
            docked=true
        fi
        if $docked; then
            lidar_motor stop_motor
        else
            echo "Not docked: the lidar keeps running"
        fi
        ;;
    undock)
        # The lidar is started first, so that it is already spinning when the robot moves
        lidar_motor start_motor
        timeout 60 ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
        ;;
    *)
        echo "Usage: bash pixi/tb4-dock.sh dock | undock"
        exit 1
        ;;
esac
