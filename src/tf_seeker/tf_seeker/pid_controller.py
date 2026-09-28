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


class PIDController:
    def __init__(self, min_output: float, max_output: float,
                 kp: float = 0.41, ki: float = 0.06, kd: float = 0.53):
        self.min_output = min_output
        self.max_output = max_output

        self.KP = kp
        self.KI = ki
        self.KD = kd

        self.prev_error = None  # None until the first call (see derivative term)
        self.int_error = 0.0

    def set_pid(self, kp: float, ki: float, kd: float):
        self.KP = kp
        self.KI = ki
        self.KD = kd

    def get_output(self, error: float, dt: float) -> float:
        """
        Compute the output of a simple standard PID.

        u[n] = Kp*e[n] + Ki*sum(e[k]) + Kd*(e[n]-e[n-1])

        error is the current error (setpoint - current_value) and dt is the time
        between calls (needed for the I and D terms).
        """
        # Proportional term
        p_term = self.KP * error

        # Integral term (with simple saturation)
        self.int_error += error * dt
        # Limit the integral to avoid windup
        max_int = 10.0  # reasonable limit
        self.int_error = max(-max_int, min(self.int_error, max_int))
        i_term = self.KI * self.int_error

        # Derivative term. There is no previous error on the first call: using 0.0 would give
        # a derivative of error/dt (a huge spike, "derivative kick"), so it is skipped.
        if self.prev_error is None or dt <= 0.0:
            d_term = 0.0
        else:
            d_term = self.KD * (error - self.prev_error) / dt
        self.prev_error = error

        # PID output
        output = p_term + i_term + d_term

        # Output saturation
        output = max(self.min_output, min(output, self.max_output))

        return output
