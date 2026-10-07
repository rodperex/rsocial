# Tareas de Pixi

Resumen de las tareas definidas en [pixi.toml](pixi.toml), para tenerlas a
mano mientras trabajas. Se lanzan desde el directorio del workspace
(`~/rsocial`) con `pixi run <tarea>`. La instalación y los detalles están en
[README-pixi-install.md](README-pixi-install.md) (TurtleBot 4) y
[README-kobuki-pixi.md](README-kobuki-pixi.md) (Kobuki). Lo particular del
TurtleBot 4 físico está en [README-tb4-real.md](README-tb4-real.md).

## Entornos

| Entorno | Para qué | Entrar en él |
| --- | --- | --- |
| `default` | TurtleBot 4 (simulador y robot real), YOLO, HRI y el resto de ejemplos | `pixi shell` |
| `kobuki` | Lo mismo más los drivers y el simulador del Kobuki | `pixi shell -e kobuki` |

Las tareas de la feature `kobuki` solo existen en ese entorno, así que Pixi
lo elige solo (`pixi run kobuki-sim` equivale a `pixi run -e kobuki
kobuki-sim`). Las demás se lanzan en el entorno `kobuki` con
`pixi run -e kobuki <tarea>`.

## Compilar

| Tarea | Qué hace |
| --- | --- |
| `build` | Compila el workspace (`colcon build --symlink-install`). Con el Kobuki, `pixi run -e kobuki build` |
| `test` | Ejecuta los tests (`colcon test`) |
| `clean` | Borra `build`, `install` y `log` |
| `prepare-colcon` | Excluye `nao_lola` de la compilación. La lanza `build` antes de compilar: no hace falta usarla |

## Preparar una terminal

Abren una shell nueva con el entorno, el workspace cargado
(`install/setup.bash`) y las variables del robot. `exit` vuelve a la shell
anterior. Usa la misma en todas las terminales de una sesión.

| Tarea | Entorno | Variables | Cuándo |
| --- | --- | --- | --- |
| `tb4-sim` | `default` | `ROS_DOMAIN_ID=1`, `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, `ROBOT=tb4_sim` | Simulador del TurtleBot 4. Otro dominio: `TB4_SIM_DOMAIN_ID=7 pixi run tb4-sim` |
| `tb4` | `default` | `ROS_DOMAIN_ID=0`, `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, `ROBOT=tb4`, `FASTRTPS_DEFAULT_PROFILES_FILE=pixi/fastdds-tb4.xml` | TurtleBot 4 real. El perfil de Fast DDS amplía los búferes para recibir la cámara por la wifi ([ver](README-tb4-real.md#búfer-de-recepción-del-portátil)) |
| `kobuki-sim` | `kobuki` | `ROBOT=kobuki_sim` | Simulador del Kobuki |
| `kobuki` | `kobuki` | `ROBOT=kobuki` | Kobuki real |
| `source-local` | `default` | Ninguna | Solo carga el workspace, sin elegir robot |

`tb4-sim` y `tb4` equivalen a `pixi shell` + `source install/setup.bash` + las
funciones `tb4sim` y `tb4` (ver
[Preparar cada terminal](README-pixi-install.md#preparar-cada-terminal-simulador-o-robot-real)).

Estas variables se fijan después de cargar tu `~/.bashrc`. Así mandan las de la
tarea, aunque tu `~/.bashrc` defina otro `ROS_DOMAIN_ID` u otro
`RMW_IMPLEMENTATION`. El mensaje que imprime la tarea al empezar muestra los
valores con los que se queda la shell.

## Simulador del TurtleBot 4

Lanzan Gazebo con el TurtleBot 4 en su base de carga. Hazlo en una terminal
preparada con `tb4-sim` y deja el simulador abierto.

| Tarea | Mundo | Render |
| --- | --- | --- |
| `sim` | Los del simulador (`warehouse` por defecto) | GPU por defecto |
| `sim-nvidia` | Los del simulador | GPU NVIDIA (portátiles con gráfica híbrida) |
| `sim-generic` | Los del simulador | CPU: más lento, pero el láser siempre funciona |
| `sim-house` | Casa de AWS RoboMaker (paquete `tb4_worlds`; necesita `build`) | GPU por defecto |
| `sim-house-nvidia` | Casa de AWS RoboMaker | GPU NVIDIA |
| `sim-house-generic` | Casa de AWS RoboMaker | CPU |

Las opciones se añaden detrás de la tarea:

| Opción | Para qué | Por defecto |
| --- | --- | --- |
| `world:=<mundo>` | Mundo: `warehouse`, `maze`, `depot` o `empty`. Solo en `sim*`, no en `sim-house*` | `warehouse` |
| `rviz:=true` | Abre RViz | `false` |
| `model:=lite` | TurtleBot 4 Lite | `standard` |
| `x:=`, `y:=`, `yaw:=` | Posición inicial del robot (m y rad) | `0.0` (en la casa, `x:=0.0 y:=1.5`) |

Por ejemplo: `pixi run sim-nvidia world:=maze rviz:=true`. Ver
[Elegir el mundo](README-pixi-install.md#elegir-el-mundo) y
[Simular en una casa](README-pixi-install.md#simular-en-una-casa).

## Base de carga del TurtleBot 4

Sacan al robot de su base de carga y lo devuelven a ella. Sirven para el robot
real y para el simulador.

| Tarea | Qué hace | Comando equivalente |
| --- | --- | --- |
| `undock` | Retrocede para salir de la base y gira hacia fuera | `ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'` |
| `dock` | Busca la base delante de él y se acopla | `ros2 action send_goal --feedback /dock irobot_create_msgs/action/Dock '{}'` |

Lánzalas en una terminal preparada con `tb4` (robot real) o `tb4-sim`
(simulador). Las tareas no fijan el dominio ni el middleware: usan los de la
terminal, para valer con los dos. En una terminal sin preparar se quedan
esperando con `Waiting for an action server to become available...`, porque
buscan al robot en otro dominio. En ese caso, corta con `Ctrl+C` y prepara la
terminal.

```bash
pixi run tb4       # o tb4-sim
pixi run undock
# ... ejemplos ...
pixi run dock
```

Cuándo usarlas:

- **Antes de un ejemplo que mueve el robot.** El robot está aparcado de cara a
  la base. Si arrancas un ejemplo sin desacoplarlo (por ejemplo, el bump and
  go), empuja contra ella. El simulador también arranca con el robot en la
  base.
- **Al terminar,** para que se cargue. `dock` solo funciona si el robot ve la
  base: delante de él y cerca. Si está lejos o detrás, acerca el robot antes
  (a mano o con la navegación) y oriéntalo hacia ella.

Al acabar, cada una muestra el resultado. `is_docked: false` tras `undock`, o
`is_docked: true` tras `dock`, indica que ha salido bien. Con `dock` se ve
además el feedback mientras se acerca (`sees_dock`: si ve la base).

Lo mismo se puede hacer desde el display del robot real, con las opciones
**Dock** y **Undock** del menú.

Los reflejos y el límite de marcha atrás de la base no tienen tarea: sus
parámetros solo se pueden cambiar desde el Raspberry Pi del robot. Ver
[Mecanismos de seguridad de la Create 3](README-examples.md#mecanismos-de-seguridad-de-la-create-3).

## Comandos de Pixi útiles

| Comando | Qué hace |
| --- | --- |
| `pixi install` / `pixi install -e kobuki` | Instala o actualiza el entorno |
| `pixi shell` / `pixi shell -e kobuki` | Entra en el entorno (sin cargar el workspace) |
| `pixi run <tarea>` | Lanza una tarea sin entrar antes en el entorno |
| `pixi task list` | Lista las tareas con su descripción |
