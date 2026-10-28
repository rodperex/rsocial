# Ejemplos de rsocial

Los ejemplos están ordenados de menor a mayor complejidad: cada bloque usa
conceptos de los anteriores. Todos los comandos se ejecutan en una terminal con
ROS 2 y el workspace cargados (ver [README.md](README.md)); cuando un ejemplo
necesita varios procesos, cada comando va en una terminal distinta.

| # | Bloque | Paquetes | Necesita |
| --- | --- | --- | --- |
| 1 | [Nodos, topics y ciclo de vida](#1-nodos-topics-y-ciclo-de-vida) | `node_programming` | Nada |
| 2 | [Servicios y acciones](#2-servicios-y-acciones) | `comms_interfaces`, `comms_demo` | Nada |
| 3 | [Movimiento en lazo abierto](#3-movimiento-en-lazo-abierto) | `square_motion` | Simulador o robot real |
| 4 | [TF: movimiento con odometría y seguimiento](#4-tf-movimiento-con-odometría-y-seguimiento) | `tf_square_motion`, `tf_seeker` | Simulador o robot real |
| 5 | [Sensores: láser](#5-sensores-láser) | `laser` | Simulador o robot real |
| 6 | [Sensores: cámara y YOLO](#6-sensores-cámara-y-yolo) | `camera` | Cámara OAK-D, simulador o robot real |
| 7 | [Navegación reactiva con VFF](#7-navegación-reactiva-con-vff) | `vff_control` | Simulador o robot real, y YOLO |
| 8 | [Máquinas de estados: bump and go](#8-máquinas-de-estados-bump-and-go) | `fsm_bumpgo` | Simulador o robot real |
| 9 | [Máquinas de estados: ir hacia la persona que llama](#9-máquinas-de-estados-ir-hacia-la-persona-que-llama) | `fsm_calling_person` | Robot real con profundidad, y YOLO |
| 10 | [Navegación con Nav2](#10-navegación-con-nav2) | `navigation_client`, `nav2_example`, `fsm_nav` | Simulador o robot real, con Nav2 |
| 11 | [Interacción humano-robot](#11-interacción-humano-robot) | `hri_client`, `hri_examples` | `simple_hri` |
| 12 | [Árboles de comportamiento sin robot](#12-árboles-de-comportamiento-sin-robot) | `bt_examples` | Nada |
| 13 | [Árboles de comportamiento: bump and go](#13-árboles-de-comportamiento-bump-and-go) | `bt_bumpgo` | Simulador o robot real |

## Robots

Los bloques 3 a 10 y el 13 necesitan un robot, real o simulado. Todos funcionan
con los dos robots del curso: el **Kobuki** y el **TurtleBot 4**.

Con el TurtleBot 4 físico hay que hacer algunas cosas más (sacarlo de la base,
desactivar la seguridad de la base para los bump and go, activar la
profundidad de la cámara…). Están resumidas en
[README-tb4-real.md](README-tb4-real.md).

Además, el bloque 11 tiene un ejemplo para el robot **NAO**. Es el único: el
NAO no es uno de los robots del curso y el resto de ejemplos no funciona con
él.

### TurtleBot 4: preparar cada terminal con `tb4sim` o `tb4`

> **Importante:** con el TurtleBot 4, ejecuta `tb4sim` (simulador) o `tb4` (robot real) **en
> cada terminal nueva**, antes de lanzar nada: la del simulador y todas las de
> los ejemplos. Sin ellas, las terminales no se ven entre sí o, peor, una
> terminal del simulador acaba en el dominio del robot real y lo mueve.

```bash
tb4sim     # con el simulador (ROS_DOMAIN_ID=1)
tb4        # con el robot real (ROS_DOMAIN_ID=0)
```

O, desde `~/rsocial` y sin `pixi shell` previo, con las tareas de Pixi que
abren una shell ya preparada (entorno, workspace y variables):

```bash
pixi run tb4-sim   # simulador
pixi run tb4       # robot real
```

Usa la misma en todas las terminales de una sesión. Si aún no tienes estas
funciones en tu `~/.bashrc`, añádelas como se explica en
[Preparar cada terminal](README-pixi-install.md#preparar-cada-terminal-simulador-o-robot-real).
Con el Kobuki no hacen falta (aunque también tiene sus tareas, `pixi run
kobuki-sim` y `pixi run kobuki`, que ponen `ROBOT`; ver
[Elegir el robot en los ejemplos](#elegir-el-robot-en-los-ejemplos)).

### Lanzar el robot

Lanza el simulador (o los drivers del robot real) en una terminal aparte y
déjalo abierto.

| | Kobuki | TurtleBot 4 |
| --- | --- | --- |
| Simulador en la casa de AWS RoboMaker | `ros2 launch kobuki simulation.launch.py` | `pixi run sim-house` (o `ros2 launch tb4_worlds small_house.launch.py`), con el paquete `tb4_worlds` de este repositorio |
| Simulador en otros mundos | Con `world:=` (ver [Mundos del Kobuki](#mundos-del-kobuki)) | `pixi run sim` (o `ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py`) |
| Robot real | `ros2 launch kobuki kobuki.launch.py` | Ya ejecuta sus drivers: no se lanza nada |
| Instalación y detalles | [README-kobuki-pixi.md](README-kobuki-pixi.md) (Pixi) o [README.md](README.md#kobuki-real) (nativa) | [README-pixi-install.md](README-pixi-install.md#turtlebot-4-simulador-y-navegación) |

Recuerda `tb4sim` o `tb4` en cada terminal (ver
[arriba](#turtlebot-4-preparar-cada-terminal-con-tb4sim-o-tb4)). El TurtleBot 4
empieza en su base de carga: desacóplalo antes de moverlo (ver
[README-pixi-install.md](README-pixi-install.md#2-desacoplar-el-robot-terminal-2)).

#### Ver el robot en RViz

Para ver el robot, sus TF y el láser en 3D, lanza RViz con la configuración de
este repositorio (por ahora, solo para el TurtleBot 4):

```bash
ros2 launch rsocial_robots rviz.launch.py robot:=$ROBOT
ros2 launch rsocial_robots rviz.launch.py robot:=$ROBOT fixed_frame:=map  # con localización o Nav2
```

Abre la vista 3D (Orbit) con las TF visibles. El ratón: botón izquierdo para
girar, central (o Mayús + izquierdo) para desplazar y rueda para acercar. El
frame fijo es `odom`; con localización o Nav2 usa `fixed_frame:=map`, que es el
que necesitan las herramientas *2D Pose Estimate* y *Nav2 Goal*. Úsalo en
lugar de `rviz:=true` del simulador, que abre una vista 2D desde arriba.

#### Mundos del TurtleBot 4

El simulador del TurtleBot 4 trae sus propios mundos, que se eligen añadiendo
`world:=<mundo>` (por defecto, `warehouse`):

```bash
pixi run sim                    # almacén con estanterías (warehouse)
pixi run sim world:=maze        # recinto cerrado con paredes y obstáculos
pixi run sim world:=empty       # suelo plano, sin obstáculos
pixi run sim world:=depot       # nave industrial (se descarga la primera vez)

# Sin Pixi, el mismo lanzamiento:
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py world:=maze
```

Además del mundo, el simulador admite otras opciones, como el modelo del robot
o su posición inicial (`x:=`, `y:=`, `yaw:=`). Se añaden igual detrás de la
tarea de Pixi que detrás de `ros2 launch`: ver
[Opciones del simulador](README-pixi-install.md#opciones-del-simulador).

Si el láser no funciona bien con tu gráfica, usa `sim-nvidia` o `sim-generic`
en lugar de `sim` (ver
[README-pixi-install.md](README-pixi-install.md#turtlebot-4-simulador-y-navegación)).

Los bloques 3 a 5, el 8 y el 13 funcionan en cualquiera de ellos: `empty` es el más
cómodo para los de movimiento y `maze` o `warehouse` para los que usan el láser
(bump and go, obstáculos).

Para los bloques 6, 7 y 10 (cámara, VFF y Nav2) viene mejor una casa con muebles,
como la del simulador del Kobuki. Este repositorio incluye el paquete
`tb4_worlds`, que lanza el TurtleBot 4 en esa misma casa de AWS RoboMaker
(necesita el workspace compilado; ver
[Simular en una casa](README-pixi-install.md#simular-en-una-casa)):

```bash
pixi run sim-house                              # o sim-house-nvidia, sim-house-generic
ros2 launch tb4_worlds small_house.launch.py    # sin Pixi
```

Para los ejemplos de cámara conviene además preparar la escena (ver el
[bloque 7](#7-navegación-reactiva-con-vff)).

#### Mundos del Kobuki

El simulador del Kobuki no tiene tareas de Pixi: se lanza siempre con
`ros2 launch`, en una terminal del entorno `kobuki` (`pixi run kobuki-sim`, o
`pixi shell -e kobuki` y `source install/setup.bash`). Por defecto carga la
casa de AWS RoboMaker. Para cambiar de mundo, `world:=` recibe la **ruta
completa** del fichero `.world`, no un nombre como en el TurtleBot 4:

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
(ver el [bloque 10](#10-navegación-con-nav2)):

| Mundo | Mapa (`map:=`) |
| --- | --- |
| Casa | `$(ros2 pkg prefix kobuki)/share/kobuki/maps/aws_house.yaml` (el de por defecto) |
| Almacén pequeño | `$(ros2 pkg prefix kobuki)/share/kobuki/maps/aws_warehouse.yaml` |
| Librería | `$(ros2 pkg prefix kobuki)/share/kobuki/maps/aws_bookstore.yaml` |
| Suelo plano | No tiene: sirve para mover el robot, no para navegar con Nav2 |

### Elegir el robot en los ejemplos

Casi todos los ejemplos usan el mismo código con dos robots. Sus
launchers tienen un argumento obligatorio, `robot`, que indica el robot y si
es el simulado o el real:

| | Kobuki | TurtleBot 4 |
| --- | --- | --- |
| Simulador | `robot:=kobuki_sim` | `robot:=tb4_sim` |
| Robot real | `robot:=kobuki` | `robot:=tb4`, o `robot:=tb4_rgbd` con la profundidad de la cámara activada (`robot:=tb4_rgbd_c` si las imágenes viajan comprimidas; ver [bloque 6](#turtlebot-4-real-activar-la-profundidad)) |

Con él, el launcher elige los topics del robot, el tipo de mensaje de
velocidad y si los nodos usan el reloj del simulador (`use_sim_time`), que es
necesario en simulación.

Para no escribir el robot en cada comando, los comandos de esta guía usan la
variable `ROBOT`. Con Pixi ya viene puesta según el entorno y la función de
preparación de la terminal:

| Terminal preparada con | `ROBOT` |
| --- | --- |
| `pixi run tb4-sim`, o `pixi shell` y `tb4sim` | `tb4_sim` |
| `pixi run tb4`, o `pixi shell` y `tb4` | `tb4` |
| `pixi run tb4-rgbd` | `tb4_rgbd` |
| `pixi run tb4-rgbd-c` | `tb4_rgbd_c` |
| `pixi run kobuki-sim`, o `pixi shell -e kobuki` | `kobuki_sim` |
| `pixi run kobuki` | `kobuki` |

Las tareas `kobuki` y `kobuki-sim` abren una shell del entorno `kobuki` con el
workspace cargado, igual que `tb4` y `tb4-sim`.

Para el resto de casos (por ejemplo, la instalación nativa sin Pixi), defínela
a mano en cada terminal en la que lances ejemplos, después de preparar la
terminal:

```bash
export ROBOT=tb4     # o tb4_sim, tb4_rgbd, tb4_rgbd_c, kobuki_sim, kobuki
```

Compruébala con `echo $ROBOT` antes de lanzar un ejemplo.

Así, `ros2 launch square_motion square_move.launch.py robot:=$ROBOT` vale para
todos los casos.

Los bump and go (bloques 8 y 13) son la excepción: leen el bumper, que es
distinto en cada robot, así que tienen un nodo y un launcher para cada uno. Los
del TurtleBot 4 terminan en `_tb4`.

### Topics de cada robot

Los topics y frames de cada caso están en un único fichero,
[`src/rsocial_robots/config/robots.yaml`](src/rsocial_robots/config/robots.yaml)
(paquete `rsocial_robots`), con una entrada para cada valor de `robot`. Un
mismo robot no publica siempre en los mismos topics en el simulador y en el
robot real, por eso tienen entradas distintas:

| | `kobuki_sim` | `kobuki` | `tb4_sim` | `tb4` | `tb4_rgbd` | `tb4_rgbd_c` |
| --- | --- | --- | --- | --- | --- | --- |
| Láser | `/scan_raw` | `/scan_filtered` | `/scan` | `/scan` | `/scan` | `/scan` |
| Imagen | `/rgbd_camera/image` | `/camera/color/image_raw` | `/oakd/rgb/preview/image_raw` | `/oakd/rgb/preview/image_raw` | `/oakd/rgb/image_raw` | `/oakd/rgb/image_local` (descomprimida en el portátil) |
| Profundidad | `/rgbd_camera/depth_image` (m) | `/camera/depth/image_raw` (mm) | `/oakd/rgb/preview/depth` (m) | No hay | `/oakd/stereo/image_raw` (mm) | `/oakd/stereo/image_local` (mm, descomprimida en el portátil) |
| Frame óptico | `camera_rgb_optical_frame` | `camera_color_optical_frame` | `oakd_rgb_camera_optical_frame` | `oakd_rgb_camera_optical_frame` | `oakd_rgb_camera_optical_frame` | `oakd_rgb_camera_optical_frame` |
| Velocidad (`/cmd_vel`) | `Twist` | `Twist` | `TwistStamped` | `TwistStamped` | `TwistStamped` | `TwistStamped` |
| `use_sim_time` | `true` | `false` | `true` | `false` | `false` | `false` |

Las entradas de los simuladores están comprobadas. Las de los robots reales
dependen de los sensores montados y de cómo se lanzan sus drivers: la del
Kobuki supone el láser RPLIDAR con el filtro de `kobuki.launch.py` y la cámara
Astra (`astra:=true`). Las del TurtleBot 4 dependen de cómo esté configurada
su cámara: `tb4` es la configuración de fábrica, que no publica profundidad,
`tb4_rgbd` la configuración con profundidad y `tb4_rgbd_c` la misma con las
imágenes comprimidas en la wifi (ver
[TurtleBot 4 real: activar la profundidad](#turtlebot-4-real-activar-la-profundidad)).
Antes de usar un robot real,
comprueba sus topics con `ros2 topic list` y, si no coinciden, cámbialos en el
YAML. Con `--symlink-install` no hace falta recompilar: el cambio se aplica al
volver a lanzar.

Otras diferencias, que los launchers ya resuelven y solo hay que conocer al
lanzar los nodos con `ros2 run` o escribir nodos nuevos:

| | Kobuki | TurtleBot 4 |
| --- | --- | --- |
| Velocidad | `geometry_msgs/Twist` | `geometry_msgs/TwistStamped` (parámetro `enable_stamped_cmd_vel:=true` de los nodos) |
| Bumper | `/events/bumper` (`kobuki_ros_interfaces/BumperEvent`) | `/hazard_detection` (`irobot_create_msgs/HazardDetectionVector`) |
| TF de la base | `odom` → `base_footprint` → `base_link` | `odom` → `base_footprint` → `base_link` |

## 1. Nodos, topics y ciclo de vida

Ejemplos mínimos, en este orden: crear un nodo, escribir en el log, publicar y
suscribirse. Primero con funciones y bucles, después con clases y timers, que
es la forma recomendada.

```bash
ros2 run node_programming simple_node_creation    # nodo vacío (ver con: ros2 node list)
ros2 run node_programming simple_node_logging     # log en un bucle con Rate
ros2 run node_programming logger_node             # log con un timer (clase Node)
ros2 run node_programming simple_node_publishing  # publica en /int_topic en un bucle
ros2 run node_programming publisher_node          # publica en /int_topic con un timer
ros2 run node_programming simple_callback         # se suscribe a /int_topic (función)
ros2 run node_programming subscriber_node         # se suscribe a /int_topic (clase)
```

Para probar un publicador y un suscriptor a la vez, lanza cada uno en una
terminal o usa el launcher, que arranca ambos:

```bash
ros2 launch node_programming pubsub.launch.py
```

Nodo con ciclo de vida (*lifecycle*): solo publica mientras está activo.

```bash
ros2 launch node_programming lc_pubsub.launch.py
```

Con el launcher en marcha, en otra terminal:

```bash
ros2 lifecycle get /lifecycle_publisher_node          # estado actual
ros2 lifecycle set /lifecycle_publisher_node deactivate  # deja de publicar
ros2 lifecycle set /lifecycle_publisher_node activate    # vuelve a publicar
```

## 2. Servicios y acciones

`comms_interfaces` define un mensaje, un servicio (`GetInformation`) y una
acción (`GenerateInformation`); `comms_demo` los usa. Arranca primero el
servidor y después el cliente, cada uno en su terminal.

Servicio (petición y respuesta):

```bash
ros2 run comms_demo service_server
ros2 run comms_demo service_client
```

Acción (petición, *feedback* periódico y resultado final):

```bash
ros2 run comms_demo action_server
ros2 run comms_demo action_client
```

Las interfaces se pueden inspeccionar con
`ros2 interface show comms_interfaces/action/GenerateInformation`.

## 3. Movimiento en lazo abierto

Con el robot en marcha. El robot intenta dibujar un cuadrado de 1 m
controlando solo el tiempo que avanza y gira, sin mirar la odometría: el error
se acumula y el cuadrado no se cierra.

```bash
ros2 launch square_motion square_move.launch.py robot:=$ROBOT
```

## 4. TF: movimiento con odometría y seguimiento

Con el robot en marcha. El mismo cuadrado, pero midiendo con la TF
`odom` → `base_link` cuánto ha avanzado y girado el robot:

```bash
ros2 launch tf_square_motion tf_square.launch.py robot:=$ROBOT   # restando posiciones y ángulos (yaw)
ros2 launch tf_square_motion tf_square2.launch.py robot:=$ROBOT  # con matrices homogéneas 4x4
```

`tf_square2` sigue el convenio de nombres `A2B` = `lookup_transform(A, B)`.
Así, `A2B @ B2C = A2C`: se tachan el frame final del primer término y el
inicial del segundo.

Seguimiento de un frame: `tf_publisher_node` publica un frame `target` en una
posición aleatoria de `odom`, y `tf_seeker_node` lleva al robot hasta 1 m de
él con dos controladores PID (lineal y angular).

```bash
ros2 launch tf_seeker tf_seeker.launch.py robot:=$ROBOT
ros2 launch tf_seeker tf_seeker.launch.py robot:=$ROBOT erratic:=True  # PID angular mal ajustado: avanza haciendo eses
ros2 launch tf_seeker tf_seeker.launch.py robot:=$ROBOT tf_update_time:=10.0  # objetivo nuevo cada 10 s
```

El objetivo `target` se publica en `odom` 20 veces por segundo y cambia a una
posición aleatoria cada `tf_update_time` segundos (20 por defecto). En
simulación son segundos del simulador: si va más lento que el tiempo real (lo
muestra Gazebo abajo a la derecha, *RTF*), el objetivo tarda más en cambiar.
Si el robot no se mueve y el nodo repite `Waiting for transform`, comprueba que
llega el reloj del simulador (`ros2 topic hz /clock`).

## 5. Sensores: láser

Con el robot en marcha. Detectan el obstáculo más cercano del `LaserScan`
(ignorando lecturas no válidas) y publican `true`/`false` en `/obstacle`.

Versión sin TF: corrige el ángulo a mano con la posición del láser en el
robot (`laser_yaw` y `laser_flipped` en `src/rsocial_robots/config/robots.yaml`,
que el launcher pasa según `robot:=`): 0° es el frente y los positivos la
izquierda. El láser del TurtleBot 4 está girado 90° y el del Kobuki real
está al revés y hacia atrás.

```bash
ros2 launch laser laser_no_tf.launch.py robot:=$ROBOT
```

Versión con TF: transforma el obstáculo a `base_footprint`, lo que funciona
con cualquier montaje del láser.

```bash
ros2 launch laser laser.launch.py robot:=$ROBOT
```

Lanza solo una de las dos y, en otra terminal, mira el resultado:

```bash
ros2 topic echo /obstacle
```

## 6. Sensores: cámara y YOLO

YOLO (`yolo_ros`) detecta objetos en la imagen y publica sus propios mensajes;
el paquete `camera` los convierte a los mensajes estándar de `vision_msgs`, que
son los que usan los bloques siguientes.

YOLO usa la GPU por defecto (`device:=cuda:0`). El PyTorch del entorno está
compilado para CUDA 13, que necesita un driver NVIDIA 580 o posterior;
compruébalo con `nvidia-smi`. Sin GPU compatible, añade `device:=cpu` a los
comandos que lanzan YOLO: `yolo.launch.py` (de `camera` o de `yolo_bringup`),
los `full_vff_*.launch.py` del bloque 7 y `calling_person.launch.py` del
bloque 9. Irá mucho más lento: en CPU, YOLO da unas pocas detecciones por
segundo, y el robot puede avanzar a tirones porque el controlador del VFF
descarta los vectores de más de 0,5 s.

### Con la cámara OAK-D

Lo más sencillo para empezar: una OAK-D conectada por USB al portátil, sin
robot. Con el simulador o un robot real (también el TurtleBot 4, cuya OAK-D la
lanza el propio robot) se usa el apartado
[Con la cámara del robot](#con-la-cámara-del-robot).

Aquí nadie lanza la cámara, así que hacen falta tres launchers, cada uno en su
terminal: el driver de la cámara, YOLO con los topics de la OAK-D y la
conversión a `vision_msgs`. Si la OAK-D está montada en el Kobuki y ya has
lanzado su driver (ver [README-kobuki-pixi.md](README-kobuki-pixi.md)),
sáltate la terminal 1:

```bash
# Terminal 1: driver de la cámara
ros2 launch oak_d_camera camera.launch.py \
  use_disparity:=False use_lr_raw:=False use_pointcloud:=False

# Terminal 2: YOLO
ros2 launch yolo_bringup yolo.launch.py \
  input_image_topic:=/color/image \
  input_depth_topic:=/stereo/depth \
  input_depth_info_topic:=/stereo/camera_info \
  target_frame:=oak-d_frame

# Terminal 3: conversión a /detections_2d
ros2 launch camera yolo_to_standard2d.launch.py

# Terminal 4: ver las detecciones
ros2 topic echo /detections_2d
```

Para 3D, añade `use_3d:=True` a YOLO (terminal 2) y, en la terminal 3, lanza
`ros2 launch camera yolo_to_standard3d.launch.py` en lugar de la conversión 2D.

Si al lanzar la cámara hay problemas de permisos de acceso al USB:

```bash
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/80-movidius.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Detección, segmentación y pose

YOLO usa por defecto el modelo `yolov8m.pt`, que solo detecta: la caja y la
clase de cada objeto. El argumento `model` elige otro modelo, tanto en
`yolo_bringup yolo.launch.py` como en `camera yolo.launch.py`:

| `model` | Qué añade |
| --- | --- |
| `yolov8m.pt` (por defecto) | Detección: caja y clase de cada objeto |
| `yolov8m-seg.pt` | Segmentación: además, la máscara (silueta) de cada objeto |
| `yolov8m-pose.pt` | Pose: solo personas, con los 17 puntos del cuerpo (ojos, hombros, codos...) |

Con la OAK-D, cambia el comando de la terminal 2:

```bash
# Segmentación
ros2 launch yolo_bringup yolo.launch.py \
  input_image_topic:=/color/image \
  input_depth_topic:=/stereo/depth \
  input_depth_info_topic:=/stereo/camera_info \
  target_frame:=oak-d_frame \
  model:=yolov8m-seg.pt

# Pose
ros2 launch yolo_bringup yolo.launch.py \
  input_image_topic:=/color/image \
  input_depth_topic:=/stereo/depth \
  input_depth_info_topic:=/stereo/camera_info \
  target_frame:=oak-d_frame \
  model:=yolov8m-pose.pt
```

Con la cámara del robot:

```bash
ros2 launch camera yolo.launch.py robot:=$ROBOT model:=yolov8m-seg.pt   # segmentación
ros2 launch camera yolo.launch.py robot:=$ROBOT model:=yolov8m-pose.pt  # pose
```

La primera vez, YOLO descarga el modelo al directorio desde el que lo lanzas.
La conversión a `vision_msgs` (`/detections_2d` y `/detections_3d`) solo se
queda con la caja y la clase; las máscaras y los puntos del cuerpo están en
`/yolo/detections` (campos `mask` y `keypoints`). La forma más rápida de
verlos es la imagen que dibuja YOLO, en otra terminal:

```bash
ros2 run rqt_image_view rqt_image_view /yolo/dbg_image
```

La `m` del nombre es el tamaño del modelo: `n`, `s`, `m`, `l` o `x`, de más
rápido a más preciso. Sin GPU, `yolov8n.pt` (o `yolov8n-seg.pt`,
`yolov8n-pose.pt`) va bastante más fluido.

### Con la cámara del robot

Con el simulador o el robot real en marcha, la cámara ya está publicando: solo
hay que lanzar YOLO y la conversión. `camera yolo.launch.py` lanza YOLO con los
topics de la cámara de cada robot (ver
[Topics de cada robot](#topics-de-cada-robot)).

Detecciones 2D (en píxeles), publicadas en `/detections_2d` (cada comando en
su terminal):

```bash
ros2 launch camera yolo.launch.py robot:=$ROBOT
ros2 launch camera yolo_to_standard2d.launch.py
ros2 topic echo /detections_2d
```

Detecciones 3D (posición en metros usando la profundidad), publicadas en
`/detections_3d`. Hay que lanzar YOLO con `use_3d:=True` (cada comando en su
terminal):

```bash
ros2 launch camera yolo.launch.py robot:=$ROBOT use_3d:=True
ros2 launch camera yolo_to_standard3d.launch.py robot:=$ROBOT
ros2 topic echo /detections_3d
```

La profundidad de los simuladores va en metros y la de las cámaras reales en
milímetros. El launcher le indica a YOLO las unidades según la entrada del YAML
(`depth_image_units_divisor`).

### TurtleBot 4 real: activar la profundidad

La cámara del TurtleBot 4 (OAK-D) puede medir profundidad, pero el robot viene
configurado para no hacerlo: solo publica una imagen en color pequeña (250x250).
Con esa configuración (`robot:=tb4`) funcionan los ejemplos 2D, pero no los
3D (YOLO 3D, `yolo_class_3d`, `yolo_class_3d_alt`, `vff_3d` y `full_vff_3d`),
porque no hay imagen de profundidad. Por qué viene así está en
[Cámara: imagen completa y profundidad](README-tb4-real.md#cámara-imagen-completa-y-profundidad).

Para los ejemplos 3D hay que cambiar la configuración de la cámara en el
robot: activar la profundidad y publicar la imagen en color, ambas a 640x360 y
5 imágenes por segundo. A 1280x720 casi no llegan por la WiFi. Los pasos, el
fichero completo y lo que se ha medido están en
[README-tb4-real.md](README-tb4-real.md#cámara-imagen-completa-y-profundidad).

Después lanza los ejemplos con `robot:=tb4_rgbd`. Esta entrada usa
`/oakd/rgb/image_raw` en lugar de la imagen pequeña, porque YOLO 3D necesita
que la imagen en color y la de profundidad tengan el mismo tamaño, y el robot
alinea la profundidad con esa imagen. La imagen pequeña se sigue publicando,
así que `robot:=tb4` sigue funcionando para los ejemplos 2D.

Para gastar menos WiFi, usa `robot:=tb4_rgbd_c` (terminal con
`pixi run tb4-rgbd-c`). El robot envía las imágenes comprimidas y
`yolo.launch.py` arranca también dos nodos que las descomprimen en el
portátil, en `/oakd/rgb/image_local` y `/oakd/stereo/image_local`. Con esta
entrada no te suscribas a los topics `image_raw` del robot (por ejemplo, desde
RViz), porque esas imágenes volverían a viajar sin comprimir. Los detalles
están en
[README-tb4-real.md](README-tb4-real.md#imágenes-comprimidas).

Con el robot en la base, la cámara está apagada para ahorrar batería. Ver
[Arrancar y parar la cámara y el láser](README-tb4-real.md#arrancar-y-parar-la-cámara-y-el-láser).

## 7. Navegación reactiva con VFF

Con el robot en marcha. El robot se dirige hacia un objeto detectado por
YOLO (vector de atracción) mientras esquiva los obstáculos del láser (vector de
repulsión); `vff_controller_node` suma ambos vectores y calcula la velocidad.
Conviene probar las piezas por separado antes de juntarlas.

**Repulsión.** Vector hacia el obstáculo más cercano, en `/repulsive_vector`:

```bash
ros2 launch vff_control obstacle_detector.launch.py robot:=$ROBOT
```

Como en el bloque 5, también hay una versión sin TF:

```bash
ros2 launch vff_control obstacle_detector_no_tf.launch.py robot:=$ROBOT
```

Lanza solo una de las dos y, en otra terminal, mira el resultado:

```bash
ros2 topic echo /repulsive_vector
```

En todos estos launchers, `target_class` es la clase de YOLO hacia la que va
el robot. Los comandos de abajo usan `person`; cámbiala por la que quieras
(ver más abajo). Si no la pones, cada launcher usa su propia clase por
defecto (`sports ball`, `cup` o `chair`), y el robot no va hacia ti aunque
YOLO te detecte. La excepción es `full_vff_3d.launch.py`, que por defecto va
hacia una persona (`person`).

**Atracción.** Vector hacia la clase objetivo, en `/attractive_vector`. Hace
falta YOLO y la conversión del bloque 6 en marcha (2D o 3D, según el caso):

```bash
# target_class:=person -> cámbiala por la clase que quieras (chair, cup...)
ros2 launch vff_control yolo_class_2d.launch.py robot:=$ROBOT target_class:=person      # 2D: solo dirección (distancia fija de 1 m)
ros2 launch vff_control yolo_class_3d.launch.py robot:=$ROBOT target_class:=person      # 3D: posición a partir de /detections_3d
ros2 launch vff_control yolo_class_3d_alt.launch.py robot:=$ROBOT target_class:=person  # 3D calculado a mano: detección 2D + imagen de profundidad
ros2 topic echo /attractive_vector
```

**VFF completo** (detector de obstáculos, detector de la clase y controlador),
con YOLO y la conversión del bloque 6 en marcha:

```bash
# target_class:=person -> cámbiala por la clase que quieras (chair, cup...)
ros2 launch vff_control vff_2d.launch.py robot:=$ROBOT target_class:=person
ros2 launch vff_control vff_3d.launch.py robot:=$ROBOT target_class:=person  # además se detiene a 1 m del objetivo
```

**Todo en uno** (también lanza YOLO y la conversión; no hace falta nada más
que el robot):

```bash
# target_class:=person -> cámbiala por la clase que quieras (chair, cup...)
ros2 launch vff_control full_vff_2d.launch.py robot:=$ROBOT target_class:=person
# Por defecto, target_class:=person; añádelo para cambiarla
ros2 launch vff_control full_vff_3d.launch.py robot:=$ROBOT
```

Sin GPU, añade `device:=cpu` (ver el [bloque 6](#6-sensores-cámara-y-yolo)).

`target_class` admite cualquier clase que detecte YOLO (las de COCO: `person`,
`chair`, `cup`, `bottle`, `dog`...). La clase por defecto de cada launcher sale
con `--show-args` (por ejemplo,
`ros2 launch vff_control full_vff_3d.launch.py --show-args`). Las clases con
espacios van entre comillas:

```bash
ros2 launch vff_control full_vff_3d.launch.py robot:=$ROBOT target_class:='sports ball'
```

Para ver qué clases está detectando YOLO en cada momento:
`ros2 topic echo /yolo/detections --field detections | grep class_name`.

**Preparar la escena.** El robot solo se mueve si la cámara ve un objeto de la
clase objetivo; si no, se queda quieto. En simulación, coloca el objeto delante
del robot y, para probar la repulsión, un obstáculo en medio (ver
[Mover, quitar y añadir objetos](README-pixi-install.md#mover-quitar-y-añadir-objetos)).
Con el TurtleBot 4, ten en cuenta la base de carga: es más baja que el láser,
así que el VFF no la ve ni la esquiva. Si queda entre el robot y el objetivo,
apártala, quítala o coloca el objetivo en otra dirección. Por la misma razón,
usa obstáculos que lleguen a la altura del láser (otra silla o una caja), no
objetos bajos.

**Cómo se comporta.** En las versiones 3D, el robot deja de avanzar a
`stay_distance` (1 m) del objetivo, pero sigue girando hacia él: si el objetivo
se mueve a su alrededor, el robot gira sobre sí mismo para no perderlo.
En las 2D no hay distancia, así que sigue avanzando hasta que la repulsión lo
frena delante del objeto.

Si el objetivo deja de verse (por ejemplo, porque al esquivar un obstáculo sale
de la imagen), el robot se para y, si pasan 2 s (`search_timeout`) sin
volver a verlo, gira sobre sí mismo hacia el lado donde lo vio por última vez
hasta encontrarlo (`search_angular_speed`; 0 desactiva la búsqueda).
`full_vff_3d.launch.py` empieza a buscar antes (a los 0,5 s) y se orienta más
rápido hacia el objetivo, para seguir a alguien que rodea al robot (ver más
abajo).

El controlador combina un vector unitario hacia el objetivo (solo importa su
dirección) con una repulsión `k·(1/d − 1/ρ₀)` que solo actúa con obstáculos
delante y a menos de `repulsive_influence_distance`. Solo avanza con la
componente de la resultante que apunta hacia delante: si apunta hacia atrás,
gira sin avanzar. El giro es proporcional al ángulo de la resultante
(`angular_gain`, en rad/s por radián). Avanza a 0,3 m/s y gira a 0,5 rad/s como
máximo; estos valores y las ganancias se cambian en los launchers de
`src/vff_control/launch/`.

En `full_vff_3d.launch.py`, el giro y la búsqueda son argumentos del launcher,
para probar valores sin tocar el fichero:

| Argumento | Por defecto | Qué hace |
| --- | --- | --- |
| `angular_gain` | 2,0 | Velocidad de giro por radián de ángulo hacia el objetivo |
| `max_angular_speed` | 1,2 rad/s | Velocidad de giro máxima |
| `search_angular_speed` | 0,7 rad/s | Velocidad de giro al buscar el objetivo (0 la desactiva) |
| `search_timeout` | 0,5 s | Tiempo sin ver el objetivo antes de empezar a buscarlo |

```bash
ros2 launch vff_control full_vff_3d.launch.py robot:=$ROBOT target_class:=person angular_gain:=1.5
```

Si al girar hacia el objetivo el robot se pasa y oscila a un lado y a otro,
baja `angular_gain`.

## 8. Máquinas de estados: bump and go

Con el robot en marcha. El robot avanza; al chocar retrocede, gira y
vuelve a avanzar.

FSM con `if/elif` sobre el estado actual:

```bash
ros2 launch fsm_bumpgo bumpgo_tb4.launch.py  # TurtleBot 4
ros2 launch fsm_bumpgo bumpgo.launch.py      # Kobuki
```

La misma FSM con una clase por estado (`on_entry`, `on_do`, `on_exit`) y
transiciones explícitas:

```bash
ros2 launch fsm_bumpgo bumpgo_fsm_tb4.launch.py  # TurtleBot 4
ros2 launch fsm_bumpgo bumpgo_fsm.launch.py      # Kobuki
```

Cada robot tiene su propio nodo y su propio launcher (los del TurtleBot 4
terminan en `_tb4`). La FSM es la misma; solo cambia la entrada del bumper:

- **Kobuki**: `/events/bumper` publica un mensaje cada vez que un bumper se
  pulsa o se suelta. En el simulador lo genera un nodo a partir del láser.
- **TurtleBot 4**: la base iRobot Create 3 no tiene un topic de bumper. Los
  golpes llegan en `/hazard_detection`, un vector con todos los peligros
  activos (golpe, precipicio, límite de marcha atrás…). Un golpe es una
  detección de tipo `BUMP`. Sus launchers publican además `TwistStamped`, que
  es lo que espera el TurtleBot 4.

### TurtleBot 4 real

Antes de lanzar los bump and go en el robot real, comprueba dos cosas en
[README-tb4-real.md](README-tb4-real.md):

- Que el robot republica el bumper: si `ros2 topic info /hazard_detection`
  indica 0 publicadores, ver [Bumper](README-tb4-real.md#bumper).
- Que están desactivados los reflejos y el límite de marcha atrás de la base:
  si no, el robot va a saltos al retroceder y al girar tras cada choque. Ver
  [Mecanismos de seguridad de la Create 3](README-tb4-real.md#mecanismos-de-seguridad-de-la-create-3).

## 9. Máquinas de estados: ir hacia la persona que llama

Con el robot en marcha. Junta los tres bloques anteriores: el modelo de pose de
YOLO ([bloque 6](#detección-segmentación-y-pose)), el VFF (bloque 7) y una
máquina de estados con una clase por estado, como la de bump and go (bloque 8).
El robot gira sobre sí mismo hasta ver a una persona con el brazo levantado y
entonces va hacia ella, esquivando los obstáculos. Además, va diciendo en voz
alta lo que hace, con el TTS de `simple_hri` (bloque 11): así se oye en qué
estado está la máquina de estados.

```bash
ros2 launch fsm_calling_person calling_person.launch.py robot:=$ROBOT
ros2 launch fsm_calling_person calling_person.launch.py robot:=$ROBOT arm_angle_threshold:=90.0  # basta con el brazo en horizontal
```

El launcher arranca YOLO, el TTS y todos los nodos: solo hace falta el robot.
El TTS suena en el portátil. La primera vez, Piper descarga la voz al
directorio `models/`, así que esa vez necesita internet. Es 3D,
porque el robot necesita saber a qué distancia está la persona, así que con el
TurtleBot 4 real hace falta `robot:=tb4_rgbd` o `tb4_rgbd_c` (ver
[TurtleBot 4 real: activar la profundidad](#turtlebot-4-real-activar-la-profundidad)).
Los mundos del simulador no tienen personas: se prueba con el robot real.

| Argumento | Por defecto | Qué hace |
| --- | --- | --- |
| `arm_angle_threshold` | 120,0 | Ángulo del brazo (grados) a partir del cual la persona llama |
| `arrive_distance` | 1,0 m | Distancia a la persona a la que el robot se para |
| `search_angular_speed` | 0,5 rad/s | Velocidad de giro de la FSM mientras nadie llama (estado `SEARCH`) |
| `search_text` | «Estoy buscando a alguien que me llame» | Lo que dice al entrar en `SEARCH` |
| `approach_text` | «He visto a una persona con la mano levantada. Voy hacia ella» | Lo que dice al entrar en `APPROACH` |
| `greeting` | «¡Hola! Espero que tengas un buen día» | Lo que dice al llegar junto a la persona (`ARRIVED`) |
| `tts` | `piper` | TTS de `simple_hri`: `piper` o `mms` (los dos locales, en la CPU) |
| `model` | `yolov8m-pose.pt` | Modelo de pose (`yolov8n-pose.pt` va más fluido sin GPU) |
| `device` | `cuda:0` | `cpu` sin GPU (ver el [bloque 6](#6-sensores-cámara-y-yolo)) |

### Los nodos

Tiene la misma estructura que `full_vff_3d` (bloque 7): un nodo publica el
vector de repulsión, otro el de atracción y el controlador del VFF mueve el
robot con los dos. Cambian dos cosas: el vector de atracción lo publica un
detector nuevo, que apunta a la persona que llama, y hay una máquina de estados
que decide cuándo se mueve el VFF.

| Nodo | Paquete | Qué hace |
| --- | --- | --- |
| `obstacle_detector_node` | `vff_control` | Vector de repulsión (`/repulsive_vector`), el mismo del bloque 7 |
| `calling_person_detector_node` | `fsm_calling_person` | Vector de atracción (`/attractive_vector`) hacia la persona que llama; en `full_vff_3d` lo publica `yolo_class_detector_node_3d` |
| `vff_controller_node` | `vff_control` | Mueve el robot con los dos vectores, el mismo del bloque 7 |
| `calling_person_fsm_node` | `fsm_calling_person` | Máquina de estados: activa y desactiva el VFF, resetea el detector y dice lo que hace |
| `tts_service_node` | `simple_hri` | TTS (acción `/tts_action`). Solo el TTS: el launcher de `simple_hri` arrancaría también Whisper y un modelo de lenguaje, que aquí no hacen falta y le quitarían la GPU a YOLO |

### El detector: quién llama

El detector mide el ángulo del brazo de cada persona en la imagen, entre la
recta del hombro a la muñeca y la vertical hacia abajo: 0° con el brazo bajado,
90° en horizontal y 180° hacia arriba. Una persona llama cuando supera
`arm_angle_threshold` (120° por defecto) en 3 imágenes seguidas; con una sola
imagen habría falsos avisos, porque mientras el robot gira las imágenes salen
movidas. Si ve personas pero ninguna llama, lo dice en el log (`Seen people,
but nobody is calling`).

Cuando alguien llama, el detector avisa una vez en `/calling_person` y desde
entonces publica en `/attractive_vector` la posición de esa persona, aunque baje
el brazo. Sabe que es la misma persona en cada imagen por el identificador que
le da el tracking de YOLO, que el launcher activa (`use_tracking:=True`).

El detector se queda con esa persona hasta que recibe un reset
(`/calling_person_reset`, `std_msgs/Empty`), que le hace olvidarla y volver a
esperar a que alguien llame. Hace falta porque la persona suele seguir delante
del robot después de que llegue: sin el reset, el detector seguiría con ella y
no se enteraría de una llamada nueva.

A diferencia del resto de ejemplos, el detector no usa los mensajes estándar
(`/detections_3d`, de `vision_msgs`), sino directamente los de YOLO
(`/yolo/detections_3d`, de `yolo_msgs`): `vision_msgs` no tiene un campo para
los puntos del cuerpo, así que la conversión del bloque 6 los pierde, y
tampoco copia el identificador de tracking.

### La máquina de estados

En la arquitectura del tema 4 (misión, tarea y capacidad), este ejemplo es
una **tarea**, no una misión: ir hacia la persona que llama es un único
objetivo, y la máquina de estados decide **cómo** cumplirlo, ordenando y
supervisando las capacidades (el detector, el VFF y el TTS). La misión
decidiría **qué** objetivo toca, y aquí no hay nada que elegir. La frontera es
difusa porque, con un solo objetivo, la tarea es todo lo que hace el robot.
En un robot real habría una misión por encima: por ejemplo, una que decide
cuándo atender llamadas y cuándo ir a cargar. `SEARCH`, `APPROACH` y `ARRIVED`
no son tareas, sino las fases de esta tarea.

La tarea está modelada con una máquina de estados, como bump and go (bloque
8). También podría haberse hecho con un árbol de comportamiento (bloque 13).

La máquina de estados no sabe nada de YOLO: solo escucha al detector.

| Estado | Al entrar | Mientras está | Pasa a |
| --- | --- | --- | --- |
| `SEARCH` | Dice «Estoy buscando a alguien que me llame», desactiva el VFF y resetea el detector | Gira despacio (0,5 rad/s) | `APPROACH` cuando el detector avisa en `/calling_person` |
| `APPROACH` | Dice «He visto a una persona con la mano levantada. Voy hacia ella» y activa el VFF | Nada: el VFF mueve el robot hacia la persona | `ARRIVED` cuando el vector de atracción mide menos de `arrive_distance`; `SEARCH` si no llega ningún vector en 5 s |
| `ARRIVED` | Saluda: «¡Hola! Espero que tengas un buen día» | Se queda quieto | `SEARCH` cuando ha terminado de hablar y han pasado 5 s |

Al salir de `APPROACH` (al llegar o al perder a la persona) desactiva el VFF.

El aviso de `/calling_person` es un evento, como el golpe del bumper en bump
and go: el callback solo lo apunta, y el único estado que lo comprueba es
`SEARCH`. Si alguien levanta el brazo mientras el robot va hacia otra persona,
se ignora.

La máquina de estados habla con `HRIClient` (paquete `hri_client`, bloque 11),
sin esperar: `start_speaking` empieza la frase y vuelve enseguida, y `ARRIVED`
comprueba en cada ciclo si ha terminado (`is_speaking_done`). Si el robot
cambia de estado a mitad de una frase, la corta y dice la del estado nuevo. Las
frases son argumentos del launcher (`search_text`, `approach_text` y `greeting`);
con una frase vacía, ese estado no dice nada. Por ejemplo:

```bash
ros2 launch fsm_calling_person calling_person.launch.py robot:=$ROBOT \
  greeting:='Hola, ¿en qué te puedo ayudar?' search_text:=''
```

El VFF es el mismo nodo del bloque 7, con un topic `enable` (`std_msgs/Bool`)
para activarlo y desactivarlo. En este launcher arranca desactivado
(`start_enabled:=False`) y la máquina de estados lo activa en `/vff_enable`
solo en `APPROACH`. Desactivado no publica velocidades, así que el VFF y la
máquina de estados nunca mueven el robot a la vez. En los launchers del bloque 7
arranca activado.

El topic `enable` se usa **por sencillez**. En la arquitectura del tema 4, una
capacidad como el VFF se activa y se desactiva como *lifecycle node*: la tarea
le pide las transiciones `activate` y `deactivate`, y el nodo sabe en todo
momento en qué estado está (`inactive` o `active`). Aquí basta con un `Bool`,
que hace lo mismo con menos código; convertir `vff_controller_node` en
*lifecycle node* sería la versión fiel a la teoría.

### Ver qué está pasando

Los logs de `calling_person_detector_node` y `calling_person_fsm` cuentan cada
aviso y cada cambio de estado. Además, en otras terminales:

```bash
ros2 run rqt_image_view rqt_image_view /yolo/dbg_image   # puntos del cuerpo que detecta YOLO
ros2 topic echo /calling_person                          # avisos del detector
ros2 topic echo /attractive_vector                       # posición de la persona que llamó
```

El robot gira despacio para que YOLO llegue a ver a la persona: en el
TurtleBot 4 real, YOLO 3D da unas 3 imágenes por segundo. Si no reacciona,
comprueba en `/yolo/dbg_image` que YOLO ve los hombros y las muñecas, y no te
pongas demasiado cerca: la persona tiene que salir entera en la imagen.

## 10. Navegación con Nav2

Nav2 necesita dos cosas: un mapa del sitio y saber dónde está el robot en
él (localización con AMCL). El mapa se indica con `map:=` y la **ruta
completa** de su fichero `.yaml` (el `.pgm` tiene que estar al lado). Escribe
la ruta con `$HOME` o `$(ros2 pkg prefix ...)`: en `map:=~/...` la terminal no
cambia `~` por tu directorio personal.

La navegación no se lanza con el simulador ni con los drivers: va **aparte**,
en otras terminales y con el robot ya en marcha. Lo que cambia entre robots es
cuántos lanzamientos son:

| | Kobuki | TurtleBot 4 |
| --- | --- | --- |
| Lanzamientos | Uno: localización, Nav2 y RViz juntos | Dos: localización y, después de dar la posición inicial, Nav2 |
| Simulador | `ros2 launch kobuki navigation_sim.launch.py` | `localization.launch.py` y `nav2.launch.py` (paquete `turtlebot4_navigation`), con `use_sim_time:=true` |
| Robot real | `ros2 launch kobuki navigation.launch.py map:=...` | Los mismos, sin `use_sim_time` |
| Mapa por defecto | Simulador: la casa. Robot real: ninguno, `map:=` es obligatorio | `warehouse` |

Al arrancar hay que dar en RViz la posición inicial del robot con **2D Pose
Estimate**: clic donde está el robot y arrastrar hacia donde mira. Las
lecturas del láser tienen que quedar encima de las paredes del mapa. La
excepción es el Kobuki en el simulador: su localización ya arranca en (0, 0),
que es donde aparece el robot.

### Kobuki en el simulador

Con el simulador ya lanzado (ver [Mundos del Kobuki](#mundos-del-kobuki)), en
otra terminal:

```bash
# Casa: usa su mapa por defecto
ros2 launch kobuki navigation_sim.launch.py

# Otro mundo: su mapa, por ejemplo el de la librería
ros2 launch kobuki navigation_sim.launch.py \
  map:=$(ros2 pkg prefix kobuki)/share/kobuki/maps/aws_bookstore.yaml
```

Abre su propio RViz (`rviz:=False` para no abrirlo). Da la posición inicial y
espera a que Nav2 termine de arrancar.

### Kobuki real

En una terminal, los drivers con el láser (ver
[Lanzar el robot](#lanzar-el-robot)); en otra, la navegación con el mapa del
sitio donde esté el robot:

```bash
ros2 launch kobuki kobuki.launch.py lidar_s2:=true                  # terminal 1
ros2 launch kobuki navigation.launch.py map:=$HOME/mapas/lab.yaml   # terminal 2
```

`$HOME/mapas/lab.yaml` es un ejemplo: pon la ruta de tu mapa. Los mapas del
paquete `kobuki` son de los mundos simulados y no valen para un sitio real.

### TurtleBot 4 en el simulador

Los ejemplos de navegación se prueban en la casa, que se parece más a los
sitios donde trabajan los robots sociales que el almacén. Cada comando en su
terminal (preparadas con `tb4sim` o `pixi run tb4-sim`):

```bash
# 1. Simulador de la casa (sim-house-nvidia con la GPU NVIDIA, ver README-pixi-install.md)
pixi run sim-house

# 2. Sacar el robot de la base
pixi run undock

# 3. Localización, con el mapa de la casa
ros2 launch turtlebot4_navigation localization.launch.py use_sim_time:=true \
  map:=$(ros2 pkg prefix aws_robomaker_small_house_world)/share/aws_robomaker_small_house_world/maps/turtlebot3_waffle_pi/map.yaml

# 4. RViz, para dar la posición inicial y objetivos
ros2 launch rsocial_robots rviz.launch.py robot:=$ROBOT fixed_frame:=map

# 5. Nav2, después de dar la posición inicial
ros2 launch turtlebot4_navigation nav2.launch.py use_sim_time:=true
```

En la casa, el robot aparece en la habitación central, en (0, 1,5), mirando
hacia la derecha del mapa (+x), con la base de carga delante; al sacarlo de la
base retrocede un poco. Da la posición inicial ahí, con **2D Pose Estimate**,
antes de lanzar Nav2.

Con otro mundo, cambia el simulador y el mapa (ver la tabla de abajo y
[README-pixi-install.md](README-pixi-install.md#3-localización-terminal-3),
que usa el almacén).

Los mapas de cada mundo:

| Mundo | Mapa (`map:=`) |
| --- | --- |
| `warehouse`, `maze`, `depot` | `$(ros2 pkg prefix turtlebot4_navigation)/share/turtlebot4_navigation/maps/<mundo>.yaml` |
| Casa (`sim-house`) | `$(ros2 pkg prefix aws_robomaker_small_house_world)/share/aws_robomaker_small_house_world/maps/turtlebot3_waffle_pi/map.yaml` |
| `empty` | No tiene |

Sin `use_sim_time:=true`, la localización y Nav2 descartan los datos del
simulador y no funcionan. El simulador también admite `localization:=true`,
`map:=...` y `nav2:=true` para lanzarlo todo junto, pero Nav2 arrancaría antes
de dar la posición inicial y fallaría (ver
[Opciones del simulador](README-pixi-install.md#opciones-del-simulador)).

### TurtleBot 4 real: mapa y navegación

Los mismos lanzamientos, sin `use_sim_time` (el robot real usa el reloj del
sistema), en terminales preparadas con `tb4` o `pixi run tb4`. Antes:

- El robot tiene que estar fuera de la base: acoplado, el láser está apagado
  (ver [README-tb4-real.md](README-tb4-real.md#arrancar-y-parar-la-cámara-y-el-láser)).
- El reloj del robot tiene que coincidir con el del portátil; si no, fallan
  TF y la navegación (ver
  [Reloj del robot](README-tb4-real.md#reloj-del-robot)).
- Hace falta un mapa del sitio. Se hace una vez con SLAM, moviendo el robot
  por todo el sitio (ver [Moverlo](README-tb4-real.md#moverlo)) mientras se
  construye el mapa, y después se guarda:

  ```bash
  ros2 launch turtlebot4_navigation slam.launch.py                  # mientras mueves el robot
  ros2 launch rsocial_robots rviz.launch.py robot:=$ROBOT fixed_frame:=map   # para ver el mapa
  mkdir -p $HOME/mapas
  ros2 run nav2_map_server map_saver_cli -f $HOME/mapas/lab         # crea lab.yaml y lab.pgm
  ```

  Cierra el SLAM (Ctrl+C) antes de lanzar la localización.

Después, cada comando en su terminal:

```bash
ros2 launch turtlebot4_navigation localization.launch.py map:=$HOME/mapas/lab.yaml
ros2 launch rsocial_robots rviz.launch.py robot:=$ROBOT fixed_frame:=map
ros2 launch turtlebot4_navigation nav2.launch.py    # después de dar la posición inicial
```

### Ejemplos

Con Nav2 en marcha, en otra terminal:

```bash
ros2 launch nav2_example simple_navigation_app.launch.py robot:=$ROBOT  # un objetivo, con feedback de la distancia restante
ros2 launch fsm_nav fsm_nav.launch.py robot:=$ROBOT                     # FSM que visita dos puntos seguidos
```

Los dos usan la clase reutilizable `NavigationClient` (paquete
`navigation_client`), que manda el objetivo a Nav2 sin bloquear el nodo y dice
cómo terminó: `COMPLETED`, `ERROR` (Nav2 lo abortó), `TIMEOUT` o `CANCELED`.
Los dos terminan solos al acabar.

- `simple_navigation_app` va a un objetivo, (6, −2) por defecto, y muestra la
  distancia que le queda. Otro objetivo, en metros y radianes en el frame
  `map`: `ros2 launch nav2_example simple_navigation_app.launch.py
  robot:=$ROBOT x:=4.0 y:=0.0 yaw:=1.57`.
- `fsm_nav` es una **tarea**, modelada con una máquina de estados: espera a
  Nav2 (`WAIT_NAV2`), va al primer punto (`NAV1`), después al segundo (`NAV2`)
  y termina (`DONE`). Si un objetivo no se completa (`ERROR` o `TIMEOUT`), la
  tarea se aborta. Es una tarea y no una misión, como `fsm_calling_person`
  (bloque 9): tiene un solo objetivo, visitar los dos puntos, y decide cómo
  cumplirlo con la capacidad de navegar. Podría haberse hecho también con un
  árbol de comportamiento (bloque 13).
  Los puntos, (−1, 0) y (4, 0), y el tiempo máximo se configuran en
  `src/fsm_nav/config/waypoints.yaml`.

El tiempo máximo de cada objetivo es de 2 minutos (`goal_timeout`, 120 s) y
cuenta **tiempo de robot**: en el simulador, el tiempo simulado. Por eso los
dos se lanzan con `robot:=$ROBOT`, que les dice si están en el simulador
(`use_sim_time`): el simulador suele ir más despacio que el tiempo real (en un
portátil, la casa puede ir a la cuarta parte), y con el reloj de la pared un
objetivo se cancelaría antes de que el robot pudiera llegar.

Sus puntos caen en zonas libres de los mapas de la casa (del Kobuki y del
TurtleBot 4) y del almacén del TurtleBot 4. En otro mundo, comprueba en RViz
que los puntos caen en zonas libres y, si no, cámbialos: en `depot`, por
ejemplo, el de `simple_navigation_app` cae fuera de la zona conocida.

## 11. Interacción humano-robot

Los ejemplos usan los servicios de `simple_hri`: STT (voz a texto), TTS (texto
a voz), Extract (extraer información de una frase con un LLM) y YesNo
(detectar si una respuesta es sí o no). Lánzalo y déjalo en marcha. El
argumento `backend` elige qué hay por debajo:

- `local` (por defecto): todo en tu ordenador y gratuito; descarga los modelos
  la primera vez y necesita Internet para ello. Extract y YesNo son sencillos
  y fallan con frases complicadas.
- `ollama`: STT y TTS locales, y Extract y YesNo con un LLM servido por
  [Ollama](https://ollama.com), en tu GPU o en un servidor. Gratuito y mucho
  mejor que el local; requiere tener Ollama instalado con el modelo
  descargado.
- `hf`: STT y TTS locales, y Extract y YesNo con la API de Hugging Face;
  requiere `HF_TOKEN` y créditos de pago en Hugging Face.
- `cloud`: servicios en la nube; requiere `OPENAI_API_KEY` con créditos y
  `GOOGLE_APPLICATION_CREDENTIALS` (proyecto de Google Cloud con
  facturación).

El idioma por defecto es el español; `language:=en` cambia a inglés el STT, la
voz del TTS y los prompts. El [README de `simple_hri`](src/thirdparty/simple_hri/README.md)
explica qué necesita cada uno, todos los argumentos, cómo combinarlos, cómo
montar Ollama y cómo probar los servicios.

```bash
ros2 launch simple_hri simple_hri.launch.py
```

o, con Ollama en tu ordenador (`ollama pull qwen2.5:3b` la primera vez) o en
un servidor (`ollama_host:=servidor`):

```bash
ros2 launch simple_hri simple_hri.launch.py backend:=ollama
```

o, con servicios en la nube:

```bash
export OPENAI_API_KEY="..."
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/las-credenciales.json"
ros2 launch simple_hri simple_hri.launch.py backend:=cloud
```

Con cualquier `backend`, el STT y el TTS locales (Whisper y MMS-TTS) se pueden
cambiar por faster-whisper y Piper, más rápidos y con voces más naturales:

```bash
ros2 launch simple_hri simple_hri.launch.py stt:=faster_whisper tts:=piper
ros2 launch simple_hri simple_hri.launch.py backend:=ollama stt:=faster_whisper tts:=piper whisper_model:=small
```

La primera vez descargan el modelo de faster-whisper y la voz de Piper al
directorio `models/` y Silero VAD a `~/.cache/torch/hub`. Piper funciona en la
CPU. En Pixi, faster-whisper usa la GPU solo si el sistema tiene CUDA 12
(`/usr/local/cuda`); si no, avisa (`GPU unavailable ... using the CPU`) y
funciona en la CPU, donde va bien con `tiny`, `base` o `small`. Si el nodo
falla al cargar Silero VAD con `No module named 'torchaudio'`, tienes una
copia antigua en la caché; bórrala y se descarga la actual:

```bash
rm -rf ~/.cache/torch/hub/snakers4_silero-vad_master
```

`simple_hri` ofrece escuchar (STT) y hablar (TTS) de dos formas, que hacen lo
mismo por dentro, y extraer información y detectar sí/no solo como servicio:

| Capacidad | Servicio | Acción |
| --- | --- | --- |
| Escuchar | `/stt_service` (`std_srvs/SetBool`) | `/stt_action` (`Listen`) |
| Hablar | `/tts_service` (`Speech`) | `/tts_action` (`Say`) |
| Extraer información | `/extract_service` (`Extract`) | No hay |
| Sí o no | `/yesno_service` (`YesNo`) | No hay |

El servicio es lo más sencillo: se pide y la respuesta llega al final, sin
saber nada mientras tanto. La acción añade lo que un servicio no puede dar:
*feedback* (en qué fase está la escucha, cuánto audio queda), cancelación
(cortar la grabación o el audio) y, al hablar, que no termina hasta que acaba
de sonar. Es la regla del tema 4: servicios para consultas puntuales, acciones
para actividades largas, y escuchar y hablar lo son.

La clase `HRIClient` (paquete `hri_client`) envuelve todo esto con el contrato
de una capacidad del tema 4, el mismo que `NavigationClient` para navegar:
`wait_for_services()` como precondición, `start_listen()` y
`start_speaking(texto)` para empezar, `is_listen_done()` e
`is_speaking_done()` para saber si ha terminado sin bloquear el nodo, el estado
final (`COMPLETED`, `ERROR`, `TIMEOUT` o `CANCELED`), el *feedback*, la
cancelación y un tiempo máximo (`timeout_sec`). Para escuchar y hablar usa las
acciones, y para extraer y para sí/no, los servicios.

`hri_example`, `hri_example2` y `hri_example3` vienen por parejas para comparar
las dos formas. Sin sufijo, llaman a los servicios directamente (`call_async`)
y gestionan ellos mismos cada respuesta pendiente (el *future*), sin *feedback*
ni cancelación. Los `*_client` hacen lo mismo con `HRIClient`: el ciclo de
control solo pregunta si ha terminado y qué ha pasado. `say`, `repeat` y
`generate_response` usan también `HRIClient`.

Con `simple_hri` en marcha, en otra terminal:

```bash
ros2 run hri_examples say                  # dice una frase (TTS)
ros2 run hri_examples repeat               # escucha (STT) y repite lo que has dicho
ros2 run hri_examples hri_example          # STT + TTS llamando a los servicios
ros2 run hri_examples hri_example_client
ros2 run hri_examples hri_example2         # pedido en un restaurante (Extract)
ros2 run hri_examples hri_example2_client
ros2 run hri_examples hri_example3         # respuesta sí/no (YesNo)
ros2 run hri_examples hri_example3_client
ros2 launch hri_examples generate_response.launch.py  # pregunta y responde con lo extraído
```

`say` admite `--ros-args -p text:="..."`. La pregunta y la información que
extrae `generate_response` se configuran en `src/hri_examples/config/hri.yaml`.

### Con el robot NAO

Es el único ejemplo para el NAO (ver [Robots](#robots)).

`nao_hri_example` combina voz, una postura de saludo y los LED del pecho.
Además de `simple_hri`, necesita en marcha los servidores del NAO:
`nao_lola_client` (paquete `nao_lola_client`), `nao_pos_action_server`
(paquete `nao_pos_server`) y `led_action_server` (paquete `nao_led_server`).

```bash
ros2 run hri_examples nao_hri_example
```

## 12. Árboles de comportamiento sin robot

Árboles pequeños con `py_trees` y acciones que generan números aleatorios.
Sirven para entender cada tipo de nodo sin robot ni simulador. Ejecútalos
varias veces: el resultado cambia en cada ejecución.

```bash
ros2 run bt_examples sequence           # Sequence con memoria
ros2 run bt_examples fallback           # Fallback (Selector) con memoria
ros2 run bt_examples reactive_sequence  # Sequence sin memoria (reactiva)
ros2 run bt_examples reactive_fallback  # Fallback sin memoria (reactivo)
ros2 run bt_examples decorator          # decoradores FailureIsSuccess y Retry
```

## 13. Árboles de comportamiento: bump and go

Con el robot en marcha. El mismo comportamiento que el bloque 8, con un
árbol de `py_trees`:

| Árbol | TurtleBot 4 | Kobuki |
| --- | --- | --- |
| Construido en Python | `ros2 launch bt_bumpgo bumpgo_tb4.launch.py` | `ros2 launch bt_bumpgo bumpgo.launch.py` |
| Gira hacia el lado contrario al choque (usa la blackboard y `py_trees_ros`) | `ros2 launch bt_bumpgo side_bumpgo_tb4.launch.py` | `ros2 launch bt_bumpgo side_bumpgo.launch.py` |
| Cargado desde un XML de Groot | `ros2 launch bt_bumpgo groot_bumpgo_tb4.launch.py` | `ros2 launch bt_bumpgo groot_bumpgo.launch.py` |

Como en el bloque 8, cada robot tiene su propio nodo y launcher. Entre las dos
versiones solo cambia `CheckBump` (y `Turn` en la versión side); el resto de
comportamientos se reutilizan.

En el TurtleBot 4 real, desactiva antes los reflejos y el límite de marcha
atrás de la base, o se moverá a saltos tras cada choque. Ver
[Mecanismos de seguridad de la Create 3](README-tb4-real.md#mecanismos-de-seguridad-de-la-create-3).

`groot_bumpgo.launch.py` carga el árbol desde `src/bt_bumpgo/bt_xml/bumpgo.xml`
(formato BehaviorTree.CPP v4, editable con Groot). El parser está en
`bt_bumpgo/groot_loader.py` y no requiere dependencias externas. Soporta
`Sequence`, `ReactiveSequence`, `Fallback`, `ReactiveFallback`, `Inverter`,
`ForceSuccess`, `ForceFailure`, `Action` y `Condition`. Para cargar otro XML:

```bash
# TurtleBot 4
ros2 run bt_bumpgo bumpgo_groot_tb4 --ros-args -p xml_file:=/ruta/a/arbol.xml \
  -r /out_vel:=/cmd_vel -p enable_stamped_cmd_vel:=true
# Kobuki
ros2 run bt_bumpgo bumpgo_groot --ros-args -p xml_file:=/ruta/a/arbol.xml \
  -r /out_vel:=/cmd_vel -r /bumper:=/events/bumper
```
