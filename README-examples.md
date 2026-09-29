# Ejemplos de rsocial

Los ejemplos están ordenados de menor a mayor complejidad: cada bloque usa
conceptos de los anteriores. Todos los comandos se ejecutan en una terminal con
ROS 2 y el workspace cargados (ver [README.md](README.md)); cuando un ejemplo
necesita varios procesos, cada comando va en una terminal distinta.

| # | Bloque | Paquetes | Necesita |
| --- | --- | --- | --- |
| 1 | [Nodos, topics y ciclo de vida](#1-nodos-topics-y-ciclo-de-vida) | `node_programming` | Nada |
| 2 | [Servicios y acciones](#2-servicios-y-acciones) | `comms_interfaces`, `comms_demo` | Nada |
| 3 | [Árboles de comportamiento sin robot](#3-árboles-de-comportamiento-sin-robot) | `bt_examples` | Nada |
| 4 | [Movimiento en lazo abierto](#4-movimiento-en-lazo-abierto) | `square_motion` | Simulador |
| 5 | [TF: movimiento con odometría y seguimiento](#5-tf-movimiento-con-odometría-y-seguimiento) | `tf_square_motion`, `tf_seeker` | Simulador |
| 6 | [Sensores: láser](#6-sensores-láser) | `laser` | Simulador |
| 7 | [Máquinas de estados: bump and go](#7-máquinas-de-estados-bump-and-go) | `fsm_bumpgo` | Simulador |
| 8 | [Árboles de comportamiento: bump and go](#8-árboles-de-comportamiento-bump-and-go) | `bt_bumpgo` | Simulador |
| 9 | [Sensores: cámara y YOLO](#9-sensores-cámara-y-yolo) | `camera` | Simulador o cámara OAK-D |
| 10 | [Navegación reactiva con VFF](#10-navegación-reactiva-con-vff) | `vff_control` | Simulador y YOLO |
| 11 | [Navegación con Nav2](#11-navegación-con-nav2) | `navigation_client`, `nav2_example`, `fsm_nav` | Simulador con Nav2 |
| 12 | [Interacción humano-robot](#12-interacción-humano-robot) | `hri_client`, `hri_examples` | `simple_hri` |

## Simulador

Los bloques 4 a 11 usan el simulador del Kobuki (Gazebo). Lánzalo en una
terminal aparte y déjalo abierto:

```bash
ros2 launch kobuki simulation.launch.py
```

El simulador publica los topics que usan los ejemplos: `/cmd_vel` (velocidad),
`/scan_raw` (láser), `/rgbd_camera/*` (cámara RGB-D), `/events/bumper`
(bumper simulado a partir del láser) y las TF `odom` → `base_footprint` →
`base_link`. Con el robot real se usa `ros2 launch kobuki kobuki.launch.py`
(ver el README del paquete `kobuki`).

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

## 3. Árboles de comportamiento sin robot

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

## 4. Movimiento en lazo abierto

Con el simulador en marcha. El robot intenta dibujar un cuadrado de 1 m
controlando solo el tiempo que avanza y gira, sin mirar la odometría: el error
se acumula y el cuadrado no se cierra.

```bash
ros2 run square_motion square_move
```

## 5. TF: movimiento con odometría y seguimiento

Con el simulador en marcha. El mismo cuadrado, pero midiendo con la TF
`odom` → `base_link` cuánto ha avanzado y girado el robot:

```bash
ros2 run tf_square_motion tf_square   # restando posiciones y ángulos (yaw)
ros2 run tf_square_motion tf_square2  # con matrices homogéneas 4x4
```

`tf_square2` sigue el convenio de nombres `A2B` = `lookup_transform(A, B)`.
Así, `A2B @ B2C = A2C`: se tachan el frame final del primer término y el
inicial del segundo.

Seguimiento de un frame: `tf_publisher_node` publica un frame `target` en una
posición aleatoria de `odom`, y `tf_seeker_node` lleva al robot hasta 1 m de
él con dos controladores PID (lineal y angular).

```bash
ros2 launch tf_seeker tf_seeker.launch.py
ros2 launch tf_seeker tf_seeker.launch.py erratic:=True  # PID mal ajustado: oscila
```

## 6. Sensores: láser

Con el simulador en marcha. Detectan el obstáculo más cercano del `LaserScan`
(ignorando lecturas no válidas) y publican `true`/`false` en `/obstacle`.

Versión sin TF: da el ángulo en el frame del láser.

```bash
ros2 run laser obstacle_detector_node_no_tf --ros-args -r input_laser:=/scan_raw
```

En el robot real el láser está montado al revés y hacia atrás; esta versión lo
corrige a mano con `-p real_robot:=true`.

Versión con TF: transforma el obstáculo a `base_footprint`, lo que funciona
con cualquier montaje del láser.

```bash
ros2 launch laser laser.launch.py
ros2 topic echo /obstacle
```

## 7. Máquinas de estados: bump and go

Con el simulador en marcha. El robot avanza; al chocar retrocede, gira y
vuelve a avanzar.

FSM con `if/elif` sobre el estado actual:

```bash
ros2 launch fsm_bumpgo bumpgo.launch.py
```

La misma FSM con una clase por estado (`on_entry`, `on_do`, `on_exit`) y
transiciones explícitas:

```bash
ros2 run fsm_bumpgo bump_go_fsm_node --ros-args \
  -r /bumper:=/events/bumper -r /out_vel:=/cmd_vel
```

## 8. Árboles de comportamiento: bump and go

Con el simulador en marcha. El mismo comportamiento que el bloque 7, con un
árbol de `py_trees`:

```bash
ros2 launch bt_bumpgo bumpgo.launch.py       # árbol construido en Python
ros2 launch bt_bumpgo side_bumpgo.launch.py  # gira hacia el lado contrario al choque
                                             # (usa la blackboard y py_trees_ros)
ros2 launch bt_bumpgo groot_bumpgo.launch.py # árbol cargado desde un XML de Groot
```

`groot_bumpgo.launch.py` carga el árbol desde `src/bt_bumpgo/bt_xml/bumpgo.xml`
(formato BehaviorTree.CPP v4, editable con Groot). El parser está en
`bt_bumpgo/groot_loader.py` y no requiere dependencias externas. Soporta
`Sequence`, `ReactiveSequence`, `Fallback`, `ReactiveFallback`, `Inverter`,
`ForceSuccess`, `ForceFailure`, `Action` y `Condition`. Para cargar otro XML:

```bash
ros2 run bt_bumpgo bumpgo_groot --ros-args -p xml_file:=/ruta/a/arbol.xml \
  -r /out_vel:=/cmd_vel -r /bumper:=/events/bumper
```

## 9. Sensores: cámara y YOLO

YOLO (`yolo_ros`) detecta objetos en la imagen y publica sus propios mensajes;
el paquete `camera` los convierte a los mensajes estándar de `vision_msgs`, que
son los que usan los bloques siguientes.

YOLO usa la GPU por defecto (`device:=cuda:0`). El PyTorch del entorno está
compilado para CUDA 13, que necesita un driver NVIDIA 580 o posterior;
compruébalo con `nvidia-smi`. Sin GPU compatible, añade `device:=cpu` a los
comandos de `yolo.launch.py`; irá mucho más lento.

### Con el simulador

Detecciones 2D (en píxeles), publicadas en `/detections_2d`:

```bash
ros2 launch yolo_bringup yolo.launch.py \
  input_image_topic:=/rgbd_camera/image \
  input_depth_topic:=/rgbd_camera/depth_image \
  input_depth_info_topic:=/rgbd_camera/camera_info \
  target_frame:=camera_link
ros2 launch camera yolo_to_standard2d.launch.py
ros2 topic echo /detections_2d
```

Detecciones 3D (posición en metros usando la profundidad), publicadas en
`/detections_3d`. Hay que lanzar YOLO con `use_3d:=True`. La profundidad de
Gazebo va en metros (`32FC1`), así que también hace falta
`depth_image_units_divisor:=1` (el valor por defecto, 1000, supone milímetros):

```bash
ros2 launch yolo_bringup yolo.launch.py \
  input_image_topic:=/rgbd_camera/image \
  input_depth_topic:=/rgbd_camera/depth_image \
  input_depth_info_topic:=/rgbd_camera/camera_info \
  target_frame:=camera_link use_3d:=True depth_image_units_divisor:=1
ros2 launch camera yolo_to_standard3d.launch.py
ros2 topic echo /detections_3d
```

### Con la cámara OAK-D

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

Para 3D, añade `use_3d:=True` a YOLO y usa `yolo_to_standard3d.launch.py`.

Si al lanzar la cámara hay problemas de permisos de acceso al USB:

```bash
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="03e7", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/80-movidius.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## 10. Navegación reactiva con VFF

Con el simulador en marcha. El robot se dirige hacia un objeto detectado por
YOLO (vector de atracción) mientras esquiva los obstáculos del láser (vector de
repulsión); `vff_controller_node` suma ambos vectores y calcula la velocidad.
Conviene probar las piezas por separado antes de juntarlas.

**Repulsión.** Vector hacia el obstáculo más cercano, en `/repulsive_vector`:

```bash
ros2 launch vff_control obstacle_detector.launch.py
ros2 topic echo /repulsive_vector
```

Como en el bloque 6, también hay una versión sin TF (`-p real_robot:=true` en
el robot real):

```bash
ros2 run vff_control obstacle_detector_node_no_tf --ros-args -r input_laser:=/scan_raw
```

**Atracción.** Vector hacia la clase objetivo, en `/attractive_vector`. Hace
falta YOLO y la conversión del bloque 9 en marcha (2D o 3D, según el caso):

```bash
ros2 launch vff_control yolo_class_2d.launch.py      # 2D: solo dirección (distancia fija de 1 m)
ros2 launch vff_control yolo_class_3d.launch.py      # 3D: posición a partir de /detections_3d
ros2 launch vff_control yolo_class_3d_alt.launch.py  # 3D calculado a mano: detección 2D + imagen de profundidad
ros2 topic echo /attractive_vector
```

**VFF completo** (detector de obstáculos, detector de la clase y controlador),
con YOLO y la conversión del bloque 9 en marcha:

```bash
ros2 launch vff_control vff_2d.launch.py
ros2 launch vff_control vff_3d.launch.py  # además se detiene a 1 m del objetivo
```

**Todo en uno** (también lanza YOLO y la conversión; no hace falta nada más
que el simulador):

```bash
ros2 launch vff_control full_vff_2d.launch.py
ros2 launch vff_control full_vff_3d.launch.py
```

La clase objetivo (`target_class`, p. ej. `cup` o `chair`) y las ganancias se
cambian en los launchers de `src/vff_control/launch/`.

## 11. Navegación con Nav2

Necesita Nav2 con mapa y localización. En simulación:

```bash
ros2 launch kobuki navigation_sim.launch.py
```

Con Nav2 en marcha, en otra terminal:

```bash
ros2 run nav2_example simple_navigation_app  # un objetivo, con feedback de la distancia restante
ros2 launch fsm_nav fsm_nav.launch.py         # FSM que visita dos waypoints seguidos
```

`simple_navigation_app` usa la clase reutilizable `NavigationClient` (paquete
`navigation_client`) y navega a la posición fijada en
`src/nav2_example/nav2_example/simple_navigation_app.py`. Los puntos de la FSM
se configuran en `src/fsm_nav/config/waypoints.yaml`; si un objetivo falla, la
FSM se detiene.

## 12. Interacción humano-robot

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

`nao_hri_example` combina voz, una postura de saludo y los LED del pecho.
Además de `simple_hri`, necesita en marcha los servidores del NAO:
`nao_lola_client` (paquete `nao_lola_client`), `nao_pos_action_server`
(paquete `nao_pos_server`) y `led_action_server` (paquete `nao_led_server`).

```bash
ros2 run hri_examples nao_hri_example
```
