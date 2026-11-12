# Ejemplos de rsocial con el Kobuki

Los ejemplos de [README-examples.md](README-examples.md) están escritos para el
TurtleBot 4, el robot del curso, pero funcionan igual con el **Kobuki**: el
mismo código y casi siempre el mismo comando, con `robot:=$ROBOT`. Esta guía
recoge solo lo que cambia: cómo preparar las terminales y lanzar el robot, sus
mundos, la navegación y los ejemplos que leen el bumper. Las explicaciones de
cada bloque están en [README-examples.md](README-examples.md).

La instalación del Kobuki está en [README-kobuki-pixi.md](README-kobuki-pixi.md)
(Pixi), [README.md](README.md#kobuki-real) (nativa) o
[README-docker-install.md](README-docker-install.md) (Docker).

## Preparar cada terminal

Con Pixi, el Kobuki usa su propio entorno, `kobuki`. Prepara **cada terminal
nueva** con una de sus tareas, que abren una shell con el entorno, el workspace
cargado y la variable `ROBOT` puesta:

```bash
cd ~/rsocial
pixi run kobuki-sim   # simulador (ROBOT=kobuki_sim)
pixi run kobuki       # robot real (ROBOT=kobuki)
```

O, a mano, `pixi shell -e kobuki` y `source install/setup.bash` (en este
entorno, `ROBOT` vale `kobuki_sim`). Las funciones `tb4sim` y `tb4` del
TurtleBot 4 no hacen falta.

## Lanzar el robot

Lanza el simulador o los drivers del robot real en una terminal aparte y
déjalo abierto:

```bash
ros2 launch kobuki simulation.launch.py              # simulador, en la casa de AWS RoboMaker
ros2 launch kobuki kobuki.launch.py lidar_s2:=true   # robot real (con el láser A2, lidar_a2:=true)
```

Las reglas udev y la cámara del robot real están en
[README-kobuki-pixi.md](README-kobuki-pixi.md#4-usar-el-robot-real).

La configuración de RViz de `rsocial_robots`
([Ver el robot en RViz](README-examples.md#ver-el-robot-en-rviz)) es, por
ahora, solo para el TurtleBot 4.

### Mundos del simulador

El simulador del Kobuki no tiene tareas de Pixi: se lanza siempre con
`ros2 launch`. Por defecto carga la casa de AWS RoboMaker. Para cambiar de
mundo, `world:=` recibe la **ruta completa** del fichero `.world`, no un nombre
como en el TurtleBot 4:

```bash
# Casa (por defecto)
ros2 launch kobuki simulation.launch.py

# Almacén pequeño
ros2 launch kobuki simulation.launch.py \
  world:=$(ros2 pkg prefix aws_robomaker_small_warehouse_world)/share/aws_robomaker_small_warehouse_world/worlds/small_warehouse/small_warehouse.world

# Librería
ros2 launch kobuki simulation.launch.py \
  world:=$(ros2 pkg prefix aws_robomaker_bookstore_world)/share/aws_robomaker_bookstore_world/worlds/bookstore.world

# Suelo plano, sin obstáculos
ros2 launch kobuki simulation.launch.py \
  world:=$(ros2 pkg prefix kobuki)/share/kobuki/worlds/empty.world
```

`$(ros2 pkg prefix <paquete>)` escribe la ruta donde está instalado el
paquete, así que estos comandos valen en cualquier ordenador. Con
`gui:=false` se lanza sin la ventana de Gazebo (el robot se simula igual).
`ros2 launch kobuki simulation.launch.py --show-args` muestra todas las
opciones.

Los mapas de estos mundos, para la navegación, están en el paquete `kobuki`
(ver [Navegación con Nav2](#10-navegación-con-nav2)):

| Mundo | Mapa (`map:=`) |
| --- | --- |
| Casa | `$(ros2 pkg prefix kobuki)/share/kobuki/maps/aws_house.yaml` (el de por defecto) |
| Almacén pequeño | `$(ros2 pkg prefix kobuki)/share/kobuki/maps/aws_warehouse.yaml` |
| Librería | `$(ros2 pkg prefix kobuki)/share/kobuki/maps/aws_bookstore.yaml` |
| Suelo plano | No tiene: sirve para mover el robot, no para navegar con Nav2 |

## Elegir el robot en los ejemplos

Los launchers de los ejemplos tienen un argumento obligatorio, `robot` (ver
[Elegir el robot en los ejemplos](README-examples.md#elegir-el-robot-en-los-ejemplos)).
Con el Kobuki:

| | Kobuki |
| --- | --- |
| Simulador | `robot:=kobuki_sim` |
| Robot real | `robot:=kobuki` |

Con las tareas de Pixi de arriba, `ROBOT` ya tiene el valor correcto y los
comandos de [README-examples.md](README-examples.md) (`robot:=$ROBOT`) valen
tal cual. En la instalación nativa o en Docker, defínela a mano en cada
terminal:

```bash
export ROBOT=kobuki_sim     # o kobuki, con el robot real
```

### Topics del Kobuki

Están en
[`src/rsocial_robots/config/robots.yaml`](src/rsocial_robots/config/robots.yaml),
igual que los del TurtleBot 4:

| | `kobuki_sim` | `kobuki` |
| --- | --- | --- |
| Láser | `/scan_raw` | `/scan_filtered` |
| Imagen | `/rgbd_camera/image` | `/camera/color/image_raw` |
| Profundidad | `/rgbd_camera/depth_image` (m) | `/camera/depth/image_raw` (mm) |
| Frame óptico | `camera_rgb_optical_frame` | `camera_color_optical_frame` |
| Velocidad (`/cmd_vel`) | `Twist` | `Twist` |
| `use_sim_time` | `true` | `false` |

La entrada del simulador está comprobada. La del robot real supone el láser
RPLIDAR con el filtro de `kobuki.launch.py` y la cámara Astra (`astra:=true`).
Con la OAK-D, cambia sus topics de cámara por los de la OAK-D (`/color/image`,
`/stereo/depth`, `/stereo/camera_info`). Antes de usar el robot real, comprueba
sus topics con `ros2 topic list` y, si no coinciden, cámbialos en el YAML. Con
`--symlink-install` no hace falta recompilar: el cambio se aplica al volver a
lanzar.

### Diferencias con el TurtleBot 4

Los launchers ya las resuelven; solo hay que conocerlas al lanzar los nodos con
`ros2 run` o al escribir nodos nuevos:

| | TurtleBot 4 | Kobuki |
| --- | --- | --- |
| Velocidad | `geometry_msgs/TwistStamped` (parámetro `enable_stamped_cmd_vel:=true` de los nodos) | `geometry_msgs/Twist` |
| Bumper | `/hazard_detection` (`irobot_create_msgs/HazardDetectionVector`) | `/events/bumper` (`kobuki_ros_interfaces/BumperEvent`) |
| TF de la base | `odom` → `base_footprint` → `base_link` | `odom` → `base_footprint` → `base_link` |

## Lo que cambia en cada bloque

Los bloques 1, 2, 11 y 12 no usan el robot. Los bloques 3, 4, 7 y 9 se lanzan
exactamente igual que en [README-examples.md](README-examples.md), con
`robot:=$ROBOT`. En el resto:

### 5. Sensores: láser

Igual, con `robot:=$ROBOT`. En la versión sin TF, el launcher ya corrige la
posición del láser: el del Kobuki real está montado al revés y hacia atrás.

### 6. Sensores: cámara y YOLO

Igual, con `robot:=$ROBOT`. Si la OAK-D está montada en el Kobuki y ya has
lanzado su driver (ver
[README-kobuki-pixi.md](README-kobuki-pixi.md#4-usar-el-robot-real)), en
[Con la cámara OAK-D](README-examples.md#con-la-cámara-oak-d) sáltate la
terminal 1. Recuerda cambiar los topics de la cámara en el YAML (ver
[Topics del Kobuki](#topics-del-kobuki)).

### 8. Máquinas de estados: bump and go

Los bump and go leen el bumper, que es distinto en cada robot, así que el
Kobuki tiene su propio nodo y su propio launcher (sin el `_tb4` del final):

```bash
ros2 launch fsm_bumpgo bumpgo.launch.py       # FSM con if/elif
ros2 launch fsm_bumpgo bumpgo_fsm.launch.py   # una clase por estado
```

`/events/bumper` publica un mensaje cada vez que un bumper se pulsa o se
suelta. En el simulador lo genera un nodo a partir del láser.

### 10. Navegación con Nav2

Con el Kobuki, la localización, Nav2 y RViz se lanzan juntos, en un solo
comando. El resto de [Navegación con Nav2](README-examples.md#10-navegación-con-nav2)
(el mapa con su ruta completa, la posición inicial, los ejemplos) es igual.

**Simulador.** Con el simulador ya lanzado (ver
[Mundos del simulador](#mundos-del-simulador)), en otra terminal:

```bash
# Casa: usa su mapa por defecto
ros2 launch kobuki navigation_sim.launch.py

# Otro mundo: su mapa, por ejemplo el de la librería
ros2 launch kobuki navigation_sim.launch.py \
  map:=$(ros2 pkg prefix kobuki)/share/kobuki/maps/aws_bookstore.yaml
```

Abre su propio RViz (`rviz:=False` para no abrirlo). Su localización ya
arranca en (0, 0), que es donde aparece el robot, así que no hace falta dar la
posición inicial: espera a que Nav2 termine de arrancar.

**Robot real.** En una terminal, los drivers con el láser; en otra, la
navegación con el mapa del sitio donde esté el robot (`map:=` es obligatorio):

```bash
ros2 launch kobuki kobuki.launch.py lidar_s2:=true                  # terminal 1
ros2 launch kobuki navigation.launch.py map:=$HOME/mapas/lab.yaml   # terminal 2
```

`$HOME/mapas/lab.yaml` es un ejemplo: pon la ruta de tu mapa. Los mapas del
paquete `kobuki` son de los mundos simulados y no valen para un sitio real. Da
la posición inicial en RViz con **2D Pose Estimate**.

Los puntos de `fsm_nav` caen en zonas libres del mapa de la casa del Kobuki.

### 13. Árboles de comportamiento: bump and go

Como en el bloque 8, el Kobuki tiene sus propios launchers:

| Árbol | Kobuki |
| --- | --- |
| Construido en Python | `ros2 launch bt_bumpgo bumpgo.launch.py` |
| Gira hacia el lado contrario al choque | `ros2 launch bt_bumpgo side_bumpgo.launch.py` |
| Cargado desde un XML de Groot | `ros2 launch bt_bumpgo groot_bumpgo.launch.py` |

Para cargar otro XML:

```bash
ros2 run bt_bumpgo bumpgo_groot --ros-args -p xml_file:=/ruta/a/arbol.xml \
  -r /out_vel:=/cmd_vel -r /bumper:=/events/bumper
```
