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
| 6 | [Máquinas de estados: bump and go](#6-máquinas-de-estados-bump-and-go) | `fsm_bumpgo` | Simulador o robot real |
| 7 | [Sensores: cámara y YOLO](#7-sensores-cámara-y-yolo) | `camera` | Simulador, robot real o cámara OAK-D |
| 8 | [Navegación reactiva con VFF](#8-navegación-reactiva-con-vff) | `vff_control` | Simulador o robot real, y YOLO |
| 9 | [Navegación con Nav2](#9-navegación-con-nav2) | `navigation_client`, `nav2_example`, `fsm_nav` | Simulador o robot real, con Nav2 |
| 10 | [Interacción humano-robot](#10-interacción-humano-robot) | `hri_client`, `hri_examples` | `simple_hri` |
| 11 | [Árboles de comportamiento sin robot](#11-árboles-de-comportamiento-sin-robot) | `bt_examples` | Nada |
| 12 | [Árboles de comportamiento: bump and go](#12-árboles-de-comportamiento-bump-and-go) | `bt_bumpgo` | Simulador o robot real |

## Robots

Los bloques 3 a 9 y el 12 necesitan un robot, real o simulado. Todos funcionan
con los dos robots del curso: el **Kobuki** y el **TurtleBot 4**.

Con el TurtleBot 4 físico hay que hacer algunas cosas más (sacarlo de la base,
desactivar la seguridad de la base para los bump and go, activar la
profundidad de la cámara…). Están resumidas en
[README-tb4-real.md](README-tb4-real.md).

Además, el bloque 10 tiene un ejemplo para el robot **NAO**. Es el único: el
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
| Simulador en los mundos propios del TurtleBot 4 | — | `pixi run sim` (o `ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py`) |
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

Si el láser no funciona bien con tu gráfica, usa `sim-nvidia` o `sim-generic`
en lugar de `sim` (ver
[README-pixi-install.md](README-pixi-install.md#turtlebot-4-simulador-y-navegación)).

Los bloques 3 a 6 y el 12 funcionan en cualquiera de ellos: `empty` es el más
cómodo para los de movimiento y `maze` o `warehouse` para los que usan el láser
(bump and go, obstáculos).

Para los bloques 7 a 9 (cámara, VFF y Nav2) viene mejor una casa con muebles,
como la del simulador del Kobuki. Este repositorio incluye el paquete
`tb4_worlds`, que lanza el TurtleBot 4 en esa misma casa de AWS RoboMaker
(necesita el workspace compilado; ver
[Simular en una casa](README-pixi-install.md#simular-en-una-casa)):

```bash
pixi run sim-house                              # o sim-house-nvidia, sim-house-generic
ros2 launch tb4_worlds small_house.launch.py    # sin Pixi
```

Para los ejemplos de cámara conviene además preparar la escena (ver el
[bloque 8](#8-navegación-reactiva-con-vff)).

### Elegir el robot en los ejemplos

Casi todos los ejemplos usan el mismo código con dos robots. Sus
launchers tienen un argumento obligatorio, `robot`, que indica el robot y si
es el simulado o el real:

| | Kobuki | TurtleBot 4 |
| --- | --- | --- |
| Simulador | `robot:=kobuki_sim` | `robot:=tb4_sim` |
| Robot real | `robot:=kobuki` | `robot:=tb4`, o `robot:=tb4_rgbd` con la profundidad de la cámara activada (ver [bloque 7](#turtlebot-4-real-activar-la-profundidad)) |

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
| `pixi run kobuki-sim`, o `pixi shell -e kobuki` | `kobuki_sim` |
| `pixi run kobuki` | `kobuki` |

Las tareas `kobuki` y `kobuki-sim` abren una shell del entorno `kobuki` con el
workspace cargado, igual que `tb4` y `tb4-sim`.

Para el resto de casos (TurtleBot 4 real con profundidad o instalación nativa
sin Pixi), defínela a mano en cada terminal en la que lances ejemplos, después
de preparar la terminal:

```bash
export ROBOT=kobuki     # o kobuki_sim, tb4_sim, tb4, tb4_rgbd
```

Compruébala con `echo $ROBOT` antes de lanzar un ejemplo.

Así, `ros2 launch square_motion square_move.launch.py robot:=$ROBOT` vale para
todos los casos.

Los bump and go (bloques 6 y 12) son la excepción: leen el bumper, que es
distinto en cada robot, así que tienen un nodo y un launcher para cada uno. Los
del TurtleBot 4 terminan en `_tb4`.

### Topics de cada robot

Los topics y frames de cada caso están en un único fichero,
[`src/rsocial_robots/config/robots.yaml`](src/rsocial_robots/config/robots.yaml)
(paquete `rsocial_robots`), con una entrada para cada valor de `robot`. Un
mismo robot no publica siempre en los mismos topics en el simulador y en el
robot real, por eso tienen entradas distintas:

| | `kobuki_sim` | `kobuki` | `tb4_sim` | `tb4` | `tb4_rgbd` |
| --- | --- | --- | --- | --- | --- |
| Láser | `/scan_raw` | `/scan_filtered` | `/scan` | `/scan` | `/scan` |
| Imagen | `/rgbd_camera/image` | `/camera/color/image_raw` | `/oakd/rgb/preview/image_raw` | `/oakd/rgb/preview/image_raw` | `/oakd/rgb/image_raw` |
| Profundidad | `/rgbd_camera/depth_image` (m) | `/camera/depth/image_raw` (mm) | `/oakd/rgb/preview/depth` (m) | No hay | `/oakd/stereo/image_raw` (mm) |
| Frame óptico | `camera_rgb_optical_frame` | `camera_color_optical_frame` | `oakd_rgb_camera_optical_frame` | `oakd_rgb_camera_optical_frame` | `oakd_rgb_camera_optical_frame` |
| Velocidad (`/cmd_vel`) | `Twist` | `Twist` | `TwistStamped` | `TwistStamped` | `TwistStamped` |
| `use_sim_time` | `true` | `false` | `true` | `false` | `false` |

Las entradas de los simuladores están comprobadas. Las de los robots reales
dependen de los sensores montados y de cómo se lanzan sus drivers: la del
Kobuki supone el láser RPLIDAR con el filtro de `kobuki.launch.py` y la cámara
Astra (`astra:=true`). Las del TurtleBot 4 dependen de cómo esté configurada
su cámara: `tb4` es la configuración de fábrica, que no publica profundidad, y
`tb4_rgbd` la configuración con profundidad (ver
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

Versión sin TF: da el ángulo en el frame del láser. Se lanza con `ros2 run`,
así que hay que indicar el topic del láser (ver
[Topics de cada robot](#topics-de-cada-robot)) y, en simulación,
`use_sim_time`. Por ejemplo, en los simuladores:

```bash
ros2 run laser obstacle_detector_node_no_tf --ros-args -r input_laser:=/scan_raw -p use_sim_time:=true  # Kobuki
ros2 run laser obstacle_detector_node_no_tf --ros-args -r input_laser:=/scan -p use_sim_time:=true      # TurtleBot 4
```

En el Kobuki real el láser está montado al revés y hacia atrás; esta versión lo
corrige a mano con `-p real_robot:=true`.

Versión con TF: transforma el obstáculo a `base_footprint`, lo que funciona
con cualquier montaje del láser.

```bash
ros2 launch laser laser.launch.py robot:=$ROBOT
ros2 topic echo /obstacle
```

## 6. Máquinas de estados: bump and go

Con el robot en marcha. El robot avanza; al chocar retrocede, gira y
vuelve a avanzar.

FSM con `if/elif` sobre el estado actual:

```bash
ros2 launch fsm_bumpgo bumpgo.launch.py      # Kobuki
ros2 launch fsm_bumpgo bumpgo_tb4.launch.py  # TurtleBot 4
```

La misma FSM con una clase por estado (`on_entry`, `on_do`, `on_exit`) y
transiciones explícitas:

```bash
ros2 launch fsm_bumpgo bumpgo_fsm.launch.py      # Kobuki
ros2 launch fsm_bumpgo bumpgo_fsm_tb4.launch.py  # TurtleBot 4
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

En el TurtleBot 4 con Jazzy, la Create 3 publica bajo `/_do_not_use` y el
Raspberry Pi solo republica los topics de
`/opt/ros/jazzy/share/turtlebot4_bringup/config/republisher.yaml`.
`hazard_detection` viene comentado: si `ros2 topic info /hazard_detection`
indica 0 publicadores, descoméntalo en el robot y reinicia el servicio
(`turtlebot4-service-restart`). Ese fichero lo instala el paquete
`ros-jazzy-turtlebot4-bringup`: si se actualiza el software del robot
(`sudo apt upgrade`), puede volver a escribirse el original y habrá que
descomentar la línea de nuevo.

#### Mecanismos de seguridad de la Create 3

La Create 3 tiene dos mecanismos de seguridad que interfieren con el bump and
go:

- **Reflejos** (`reflexes_enabled`): al chocar, la base retrocede y gira un
  poco por su cuenta, ignorando `/cmd_vel` durante un instante. Después la FSM
  o el árbol recuperan el control.
- **Límite de marcha atrás** (`safety_override`): sin sensores traseros, la
  base solo deja retroceder unos centímetros. Al pasar de ahí, publica el
  hazard `BACKUP_LIMIT` y se para.

El resultado es que el robot se mueve a saltos al retroceder y al girar
después del choque. El giro en sí no es el problema: sin choques, la base gira
de forma uniforme.

Sus parámetros solo son accesibles **desde el Raspberry Pi del robot**. La
Create 3 está en una red USB privada con él, y `create3_repub` no republica el
servicio de parámetros. Desde el portátil, la llamada se queda en
`waiting for service to become available...`. Entra por SSH (con la IP del
display, o `turtlebot4.local` si tu red resuelve mDNS) y ejecútalo allí:

```bash
ssh ubuntu@turtlebot4.local
```

Para **desactivarlos**:

```bash
ros2 service call /_do_not_use/motion_control/set_parameters rcl_interfaces/srv/SetParameters \
  "{parameters: [{name: safety_override, value: {type: 4, string_value: backup_only}},
                 {name: reflexes_enabled, value: {type: 1, bool_value: false}}]}"
```

Para **volver a activarlos** (valores de fábrica):

```bash
ros2 service call /_do_not_use/motion_control/set_parameters rcl_interfaces/srv/SetParameters \
  "{parameters: [{name: safety_override, value: {type: 4, string_value: none}},
                 {name: reflexes_enabled, value: {type: 1, bool_value: true}}]}"
```

Las dos llamadas responden con `successful=True` por cada parámetro. Para ver
cómo están:

```bash
ros2 service call /_do_not_use/motion_control/get_parameters rcl_interfaces/srv/GetParameters \
  "{names: [safety_override, reflexes_enabled]}"
```

En la respuesta, el primer valor es `safety_override` (`string_value`) y el
segundo, `reflexes_enabled` (`bool_value`). Con la seguridad activa salen
`string_value='none'` y `bool_value=True`.

El cambio dura **hasta que se reinicie la base**. Al apagar el robot o al
reiniciar la aplicación de la Create 3, vuelven los valores de fábrica, y el
bump and go vuelve a ir a saltos. Compruébalo al empezar cada sesión.

Para que el cambio sea **permanente**, guárdalo en el fichero de parámetros de
la Create 3. Ese fichero está dentro de la base, no en el Raspberry Pi, y se
edita desde su servidor web:

1. Abre en el navegador `http://<IP del robot>:8080` (la IP del display; el
   Raspberry Pi redirige ese puerto a la base).
2. Entra en **Application → Configuration**. El cuadro **ROS 2 Parameters
   File** ya trae un bloque `motion_control` con `safety_override: "none"`.
   Cambia ese valor y añade `reflexes_enabled` debajo, dentro del mismo
   bloque. No añadas un segundo bloque `motion_control`: quedaría duplicado.

   ```yaml
   motion_control:
     ros__parameters:
       # (comentarios del fichero original)
       safety_override: "backup_only"
       reflexes_enabled: false
   ```

3. Pulsa **Save** y reinicia la aplicación (**Application → Restart
   Application**).

Tras el reinicio, compruébalo en el Raspberry Pi con `get_parameters`, como
arriba. Para volver a la configuración de fábrica, deja
`safety_override: "none"`, borra la línea de `reflexes_enabled`, guarda y
reinicia la aplicación.

Con la seguridad desactivada, el robot puede caer marcha atrás por un escalón
y no se aparta solo al chocar: úsalo en suelo plano y despejado, y vuelve a
activarla al terminar si el robot lo van a usar otros.

## 7. Sensores: cámara y YOLO

YOLO (`yolo_ros`) detecta objetos en la imagen y publica sus propios mensajes;
el paquete `camera` los convierte a los mensajes estándar de `vision_msgs`, que
son los que usan los bloques siguientes.

YOLO usa la GPU por defecto (`device:=cuda:0`). El PyTorch del entorno está
compilado para CUDA 13, que necesita un driver NVIDIA 580 o posterior;
compruébalo con `nvidia-smi`. Sin GPU compatible, añade `device:=cpu` a los
comandos que lanzan YOLO: `yolo.launch.py` (de `camera` o de `yolo_bringup`) y
los `full_vff_*.launch.py` del bloque 8. Irá mucho más lento: en CPU, YOLO da
unas pocas detecciones por segundo, y el robot puede avanzar a tirones porque
el controlador del VFF descarta los vectores de más de 0,5 s.

### Con la cámara del robot

`camera yolo.launch.py` lanza YOLO con los topics de la cámara de cada robot
(ver [Topics de cada robot](#topics-de-cada-robot)).

Detecciones 2D (en píxeles), publicadas en `/detections_2d`:

```bash
ros2 launch camera yolo.launch.py robot:=$ROBOT
ros2 launch camera yolo_to_standard2d.launch.py
ros2 topic echo /detections_2d
```

Detecciones 3D (posición en metros usando la profundidad), publicadas en
`/detections_3d`. Hay que lanzar YOLO con `use_3d:=True`:

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

> **¿Por qué no se publica por defecto?** Calcular la profundidad no es el
> problema: lo hace la propia cámara. El problema es mover las imágenes. La
> Raspberry Pi del robot tiene que recibirlas por USB y publicarlas en ROS 2, y
> los nodos que las usan (YOLO, RViz...) suelen estar en otro equipo, así que
> viajan por la WiFi. Una imagen en color de 1280x720 ocupa unos 2,8 MB y una de
> profundidad del mismo tamaño unos 1,8 MB: a 30 imágenes por segundo son más de
> 1 Gbit/s, mucho más de lo que da una WiFi. La imagen de 250x250 ocupa unos
> 190 KB (unos 45 Mbit/s), y la navegación del robot no necesita la cámara, así
> que los fabricantes dejan solo esa para que el robot vaya fluido.

Con esa
configuración (`robot:=tb4`) funcionan los ejemplos 2D, pero no los 3D (YOLO
3D, `yolo_class_3d`, `yolo_class_3d_alt`, `vff_3d` y `full_vff_3d`), porque no
hay imagen de profundidad.

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

Con el robot en la base, la cámara está apagada para ahorrar batería. Ver
[Arrancar y parar la cámara y el láser](README-tb4-real.md#arrancar-y-parar-la-cámara-y-el-láser).

### Con la cámara OAK-D

Sirve sin robot o con una OAK-D montada en el robot real:

```bash
ros2 launch oak_d_camera camera.launch.py \
  use_disparity:=False use_lr_raw:=False use_pointcloud:=False
ros2 launch yolo_bringup yolo.launch.py \
  input_image_topic:=/color/image \
  input_depth_topic:=/stereo/depth \
  input_depth_info_topic:=/stereo/camera_info \
  target_frame:=oak-d_frame
ros2 launch camera yolo_to_standard2d.launch.py
```

Para 3D, añade `use_3d:=True` a YOLO y usa
`ros2 launch camera yolo_to_standard3d.launch.py robot:=kobuki`. Con la OAK-D
vale cualquier entrada de robot real: de ella solo se usa que no hay que
corregir el frame de la imagen (ver `fix_image_frame` en el YAML).

Si al lanzar la cámara hay problemas de permisos de acceso al USB:

```bash
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/80-movidius.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## 8. Navegación reactiva con VFF

Con el robot en marcha. El robot se dirige hacia un objeto detectado por
YOLO (vector de atracción) mientras esquiva los obstáculos del láser (vector de
repulsión); `vff_controller_node` suma ambos vectores y calcula la velocidad.
Conviene probar las piezas por separado antes de juntarlas.

**Repulsión.** Vector hacia el obstáculo más cercano, en `/repulsive_vector`:

```bash
ros2 launch vff_control obstacle_detector.launch.py robot:=$ROBOT
ros2 topic echo /repulsive_vector
```

Como en el bloque 5, también hay una versión sin TF (`-p real_robot:=true` en
el Kobuki real). En los simuladores:

```bash
ros2 run vff_control obstacle_detector_node_no_tf --ros-args -r input_laser:=/scan_raw -p use_sim_time:=true  # Kobuki
ros2 run vff_control obstacle_detector_node_no_tf --ros-args -r input_laser:=/scan -p use_sim_time:=true      # TurtleBot 4
```

**Atracción.** Vector hacia la clase objetivo, en `/attractive_vector`. Hace
falta YOLO y la conversión del bloque 7 en marcha (2D o 3D, según el caso):

```bash
ros2 launch vff_control yolo_class_2d.launch.py robot:=$ROBOT       # 2D: solo dirección (distancia fija de 1 m)
ros2 launch vff_control yolo_class_3d.launch.py robot:=$ROBOT       # 3D: posición a partir de /detections_3d
ros2 launch vff_control yolo_class_3d_alt.launch.py robot:=$ROBOT   # 3D calculado a mano: detección 2D + imagen de profundidad
ros2 topic echo /attractive_vector
```

**VFF completo** (detector de obstáculos, detector de la clase y controlador),
con YOLO y la conversión del bloque 7 en marcha:

```bash
ros2 launch vff_control vff_2d.launch.py robot:=$ROBOT
ros2 launch vff_control vff_3d.launch.py robot:=$ROBOT  # además se detiene a 1 m del objetivo
```

**Todo en uno** (también lanza YOLO y la conversión; no hace falta nada más
que el robot):

```bash
ros2 launch vff_control full_vff_2d.launch.py robot:=$ROBOT
ros2 launch vff_control full_vff_3d.launch.py robot:=$ROBOT
```

Sin GPU, añade `device:=cpu` (ver el [bloque 7](#7-sensores-cámara-y-yolo)).

La clase objetivo se elige con el argumento `target_class`, que admite
cualquier clase que detecte YOLO (las de COCO: `person`, `chair`, `cup`,
`bottle`, `dog`...). Por defecto es `chair` en los launchers 3D y `cup` en los
2D. Por ejemplo:

```bash
ros2 launch vff_control full_vff_3d.launch.py robot:=$ROBOT target_class:=person
ros2 launch vff_control full_vff_3d.launch.py robot:=$ROBOT target_class:='sports ball'  # con espacios, entre comillas
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

**Cómo se comporta.** El robot se detiene a `stay_distance` (1 m) del objetivo
en las versiones 3D.
En las 2D no hay distancia, así que sigue avanzando hasta que la repulsión lo
frena delante del objeto.

Si el objetivo deja de verse (por ejemplo, porque al esquivar un obstáculo sale
de la imagen), el robot se para y, si pasan 2 s (`search_timeout`) sin
volver a verlo, gira sobre sí mismo hacia el lado donde lo vio por última vez
hasta encontrarlo (`search_angular_speed`; 0 desactiva la búsqueda).

El controlador combina un vector unitario hacia el objetivo (solo importa su
dirección) con una repulsión `k·(1/d − 1/ρ₀)` que solo actúa con obstáculos
delante y a menos de `repulsive_influence_distance`. Solo avanza con la
componente de la resultante que apunta hacia delante: si apunta hacia atrás,
gira sin avanzar. Avanza a 0,3 m/s y gira a 0,5 rad/s como máximo; estos valores
y las ganancias se cambian en los launchers de `src/vff_control/launch/`.

## 9. Navegación con Nav2

Necesita Nav2 con el mapa de la casa y el robot localizado en él:

- **Kobuki** (simulador): `ros2 launch kobuki navigation_sim.launch.py`.
- **TurtleBot 4**: lanza la localización con el mapa del mundo que estés
  usando y después Nav2, como en los pasos 3 a 5 de
  [README-pixi-install.md](README-pixi-install.md#turtlebot-4-simulador-y-navegación).
  Los mundos del simulador traen su mapa (ver
  [Elegir el mundo](README-pixi-install.md#elegir-el-mundo)); el de la casa
  está en [Simular en una casa](README-pixi-install.md#simular-en-una-casa).

Con Nav2 en marcha, en otra terminal:

```bash
ros2 run nav2_example simple_navigation_app  # un objetivo, con feedback de la distancia restante
ros2 launch fsm_nav fsm_nav.launch.py         # FSM que visita dos waypoints seguidos
```

`simple_navigation_app` usa la clase reutilizable `NavigationClient` (paquete
`navigation_client`) y navega a la posición fijada en
`src/nav2_example/nav2_example/simple_navigation_app.py`. Los puntos de la FSM
se configuran en `src/fsm_nav/config/waypoints.yaml`; si un objetivo falla, la
FSM se detiene. Estos ejemplos solo hablan con Nav2, así que no necesitan
`robot`.

Las posiciones están pensadas para el mapa del Kobuki. Con el TurtleBot 4 (en
la casa, cuyo mapa tiene otro origen, o en otro mundo) comprueba en RViz que los
puntos caen en zonas libres y, si no, cámbialos.

## 10. Interacción humano-robot

Los ejemplos usan los servicios de `simple_hri`: STT (voz a texto), TTS (texto
a voz), Extract (extraer información de una frase con un LLM) y YesNo
(detectar si una respuesta es sí o no). Lanza uno de sus launchers y déjalo en
marcha:

- `local_simple_hri.launch.py`: servicios locales; descarga los modelos la
  primera vez y necesita Internet para ello.
- `simple_hri.launch.py`: servicios en la nube; requiere `OPENAI_API_KEY` y
  `GOOGLE_APPLICATION_CREDENTIALS`.
- `free_simple_hri.launch.py`: servicios locales y API gratuita de Hugging Face;
  requiere `HF_TOKEN`.

```bash
ros2 launch simple_hri local_simple_hri.launch.py
```

o, con servicios en la nube:

```bash
export OPENAI_API_KEY="..."
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/las-credenciales.json"
ros2 launch simple_hri simple_hri.launch.py
```

Con `simple_hri` en marcha, en otra terminal. Los ejemplos `*_client` hacen lo
mismo que su pareja sin sufijo, pero usando la clase reutilizable `HRIClient`
(paquete `hri_client`) en lugar de llamar a los servicios directamente:

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

## 11. Árboles de comportamiento sin robot

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

## 12. Árboles de comportamiento: bump and go

Con el robot en marcha. El mismo comportamiento que el bloque 6, con un
árbol de `py_trees`:

| Árbol | Kobuki | TurtleBot 4 |
| --- | --- | --- |
| Construido en Python | `ros2 launch bt_bumpgo bumpgo.launch.py` | `ros2 launch bt_bumpgo bumpgo_tb4.launch.py` |
| Gira hacia el lado contrario al choque (usa la blackboard y `py_trees_ros`) | `ros2 launch bt_bumpgo side_bumpgo.launch.py` | `ros2 launch bt_bumpgo side_bumpgo_tb4.launch.py` |
| Cargado desde un XML de Groot | `ros2 launch bt_bumpgo groot_bumpgo.launch.py` | `ros2 launch bt_bumpgo groot_bumpgo_tb4.launch.py` |

Como en el bloque 6, cada robot tiene su propio nodo y launcher. Entre las dos
versiones solo cambia `CheckBump` (y `Turn` en la versión side); el resto de
comportamientos se reutilizan.

En el TurtleBot 4 real, desactiva antes los reflejos y el límite de marcha
atrás de la base, o se moverá a saltos tras cada choque. Ver
[Mecanismos de seguridad de la Create 3](#mecanismos-de-seguridad-de-la-create-3).

`groot_bumpgo.launch.py` carga el árbol desde `src/bt_bumpgo/bt_xml/bumpgo.xml`
(formato BehaviorTree.CPP v4, editable con Groot). El parser está en
`bt_bumpgo/groot_loader.py` y no requiere dependencias externas. Soporta
`Sequence`, `ReactiveSequence`, `Fallback`, `ReactiveFallback`, `Inverter`,
`ForceSuccess`, `ForceFailure`, `Action` y `Condition`. Para cargar otro XML:

```bash
# Kobuki
ros2 run bt_bumpgo bumpgo_groot --ros-args -p xml_file:=/ruta/a/arbol.xml \
  -r /out_vel:=/cmd_vel -r /bumper:=/events/bumper
# TurtleBot 4
ros2 run bt_bumpgo bumpgo_groot_tb4 --ros-args -p xml_file:=/ruta/a/arbol.xml \
  -r /out_vel:=/cmd_vel -p enable_stamped_cmd_vel:=true
```
