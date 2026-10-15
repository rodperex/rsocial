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

# Pixi activation script (sourced, not executed): makes the audio of the pixi
# environment go through the PipeWire (or PulseAudio) server of the host system.
#
# Why: the environment ships its own alsa-lib (conda-forge), which only reads
# its own configuration and plugins. Without the PipeWire plugin, the programs
# of the environment (PortAudio, used by sounddevice in the STT of simple_hri)
# only see the raw devices of the sound card (hw:0,0...). Those do not convert
# the sample rate, so the microphone cannot be opened at 16 kHz ("Invalid sample
# rate"), and they ignore the microphone chosen in the desktop settings.
#
# How: point alsa-lib to the configuration and plugins of the system, which
# define the "default" device through PipeWire. Only when the system has the
# ALSA plugin of PipeWire or PulseAudio; otherwise nothing changes.

_pixi_alsa_conf=/usr/share/alsa/alsa.conf
for _pixi_alsa_plugins in /usr/lib/x86_64-linux-gnu/alsa-lib /usr/lib/aarch64-linux-gnu/alsa-lib \
                          /usr/lib64/alsa-lib /usr/lib/alsa-lib; do
  if [ -f "$_pixi_alsa_conf" ] && \
     { [ -f "$_pixi_alsa_plugins/libasound_module_pcm_pipewire.so" ] || \
       [ -f "$_pixi_alsa_plugins/libasound_module_pcm_pulse.so" ]; }; then
    export ALSA_CONFIG_DIR=/usr/share/alsa
    export ALSA_CONFIG_PATH="$_pixi_alsa_conf"
    export ALSA_PLUGIN_DIR="$_pixi_alsa_plugins"
    break
  fi
done

unset _pixi_alsa_conf _pixi_alsa_plugins
