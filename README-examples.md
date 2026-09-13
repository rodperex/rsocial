# Ejemplos de rsocial

Los comandos se ejecutan en una shell con ROS 2 y el workspace ya cargados.
Cuando se lancen varios nodos, usa terminales separadas.

## Publicacion, suscripcion y ciclo de vida

```bash
ros2 launch node_programming pubsub.launch.py
ros2 launch node_programming lc_pubsub.launch.py
```

Tambien estan disponibles `publisher_node`, `subscriber_node`, `logger_node`,
`lifecycle_publisher_node`, `lifecycle_subscriber_node`, `simple_node_creation`,
`simple_node_logging`, `simple_node_publishing` y `simple_callback`.

## Servicios y acciones

Ejecuta cada servidor y cliente en terminales distintas:

```bash
ros2 run comms_demo service_server
ros2 run comms_demo service_client
ros2 run comms_demo action_server
ros2 run comms_demo action_client
```

## Movimiento y TF

Estos ejemplos necesitan un robot o simulador que acepte `cmd_vel`:

```bash
ros2 run square_motion square_move
ros2 run tf_square_motion tf_square
ros2 run tf_square_motion tf_square2
ros2 launch tf_seeker tf_seeker.launch.py
```

## Sensores

### Laser

Con un `LaserScan` publicado:

```bash
ros2 launch laser laser.launch.py
```

### Camara y YOLO

Para una camara OAK-D:

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

Para detecciones 3D usa `yolo_to_standard3d.launch.py` y adapta los topics y
`target_frame` a la camara utilizada.

## Control y navegacion

```bash
ros2 launch vff_control full_vff_2d.launch.py
ros2 launch vff_control full_vff_3d.launch.py
ros2 run nav2_example simple_navigation_app
ros2 launch fsm_nav fsm_nav.launch.py
```

La navegacion requiere Nav2, mapa, localizacion y los topics/TF del robot.
Los puntos de la FSM se configuran en `src/fsm_nav/config/waypoints.yaml`.

## Maquinas de estados y arboles de comportamiento

```bash
ros2 launch fsm_bumpgo bumpgo.launch.py
ros2 launch bt_bumpgo bumpgo.launch.py
ros2 launch bt_bumpgo side_bumpgo.launch.py
ros2 launch bt_bumpgo groot_bumpgo.launch.py
```

Ejemplos de `py_trees`:

```bash
ros2 run bt_examples sequence
ros2 run bt_examples reactive_sequence
ros2 run bt_examples fallback
ros2 run bt_examples reactive_fallback
ros2 run bt_examples decorator
```

Para editar arboles con Groot:

```bash
python3 -m pip install --user \
  git+https://github.com/narcispr/py_trees_meet_groot.git
```

## Interaccion humano-robot

Launchers disponibles:

- `simple_hri.launch.py`: servicios cloud; requiere `OPENAI_API_KEY` y
  `GOOGLE_APPLICATION_CREDENTIALS`.
- `local_simple_hri.launch.py`: servicios locales; descarga modelos la primera
  vez y necesita Internet.
- `free_simple_hri.launch.py`: servicios locales y API gratuita de Hugging Face;
  requiere `HF_TOKEN`.

Ejemplo local:

```bash
ros2 launch simple_hri local_simple_hri.launch.py
```

Ejemplo cloud:

```bash
export OPENAI_API_KEY="..."
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/a/las-credenciales.json"
ros2 launch simple_hri simple_hri.launch.py
ros2 run hri_examples hri_example
```

El ejemplo completo de NAO requiere que esten ejecutándose los servidores de
NAO y sus interfaces correspondientes.
