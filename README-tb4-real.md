# TurtleBot 4 real

Lo que hay que hacer de forma distinta con el TurtleBot 4 físico respecto al
simulador. Cada punto está resumido aquí y enlaza a la explicación completa
cuando la hay. La instalación y el simulador están en
[README-pixi-install.md](README-pixi-install.md), y los ejemplos en
[README-examples.md](README-examples.md).

## Al empezar cada sesión

1. Enciende el robot y espera a que el display muestre su IP (ver
   [Red y acceso al robot](#red-y-acceso-al-robot)).
2. Conecta el portátil a la misma wifi que el robot.
3. Prepara **cada** terminal con `pixi run tb4` (o con `tb4`, si usas
   `pixi shell` o la instalación nativa), y comprueba que ves el robot:

   ```bash
   ros2 topic list     # deben salir /scan, /odom, /hazard_detection...
   ```

   Si faltan topics o el robot no responde, ver
   [Si el robot deja de responder o desaparecen nodos](#si-el-robot-deja-de-responder-o-desaparecen-nodos).

   Si vas a usar ejemplos 3D, comprueba también que la cámara publica la
   imagen completa y la profundidad (ver
   [Cámara: imagen completa y profundidad](#cámara-imagen-completa-y-profundidad)).

4. Mira la batería (en el display, o con
   `ros2 topic echo --once /battery_state --field percentage`). Con poca
   batería, la base puede negarse a moverse y acaba cortando la alimentación
   del Raspberry Pi, que se reinicia sin avisar.
5. Saca el robot de la base: `pixi run undock`.
6. Si vas a usar los bump and go, desactiva los
   [mecanismos de seguridad de la Create 3](#mecanismos-de-seguridad-de-la-create-3).
7. Al terminar, `pixi run dock` para que se cargue.

## Red y acceso al robot

- **IP del robot:** sale en el display. Desde un equipo preparado con `tb4`,
  también con `ros2 topic echo --once /ip`. Si tu red resuelve mDNS, puedes
  usar el nombre `turtlebot4.local`.
- **SSH al Raspberry Pi:** `ssh ubuntu@<IP del robot>`. Al entrar ya tienes
  ROS cargado.
- **Web de la base Create 3:** `http://<IP del robot>:8080`. El Raspberry Pi
  redirige ese puerto a la base.
- **Si el display muestra `UNKNOWN` en lugar de la IP:** el servicio del robot
  arrancó antes de que hubiera wifi. Si `/ip` ya tiene la IP, el display la
  mostrará al redibujarse. Si no, reinicia el servicio en el robot:
  `turtlebot4-service-restart`.
- **Si el Raspberry Pi no se conecta a la wifi:** su configuración está en
  `/etc/netplan/50-wifis.yaml` y se cambia con `sudo turtlebot4-setup`
  (**Wi-Fi Setup**). Después hay que pulsar **Apply settings**. Comprueba
  luego que se ha guardado lo que esperabas, por ejemplo con
  `grep band /etc/netplan/50-wifis.yaml`. En 5 GHz, el router debe emitir en
  un canal del 36 al 48: en los canales DFS (52 a 144), el Raspberry Pi se
  desconecta o no ve la red.
- **Sin acceso a la red del robot**, puedes conectar el portátil por cable al
  puerto Ethernet del Raspberry Pi. Ese puerto no usa el router: tiene una IP
  fija, definida en `/etc/netplan/40-ethernets.yaml` del robot. Con la
  configuración de fábrica del TurtleBot 4 es `192.168.185.3/24`, pero puede
  estar cambiada; si no responde, mira ese fichero (por ejemplo, desde la wifi
  o con un teclado y una pantalla en el robot). Pon en el portátil, en esa
  conexión de cable, una IP fija libre de esa misma red (con la de fábrica,
  cualquiera de `192.168.185.x` distinta de la del robot, con máscara `/24`),
  sin puerta de enlace, para que internet siga saliendo por tu otra conexión.
  Entra con `ssh ubuntu@<IP del puerto Ethernet>`.

## Terminales: dominio y middleware

El robot usa `ROS_DOMAIN_ID=0` y Fast DDS (`rmw_fastrtps_cpp`). Las tareas
`pixi run tb4` y la función `tb4` dejan la terminal con esos valores y paran
el daemon de `ros2`, que si no podría seguir usando una configuración
anterior. `pixi run tb4` carga además un perfil de Fast DDS con búferes más
grandes, para que las imágenes de la cámara lleguen por la wifi (ver
[Búfer de recepción del portátil](#búfer-de-recepción-del-portátil)).

`pixi run tb4` vuelve a fijar las variables después de cargar tu `~/.bashrc`,
así que valen aunque tu `~/.bashrc` ponga otro dominio u otro middleware. El
mensaje que imprime al empezar muestra los valores con los que se queda la
terminal. Ver
[Preparar una terminal](README-pixi-tasks.md#preparar-una-terminal).

Si no ves los topics del robot:

- Comprueba en esa terminal `echo $ROS_DOMAIN_ID $RMW_IMPLEMENTATION`: debe
  salir `0 rmw_fastrtps_cpp`.
- Si los valores son correctos, para el daemon (`ros2 daemon stop`) o usa
  `ros2 topic list --no-daemon`.
- Comprueba que el portátil llega al robot: `ping <IP del robot>`.
- Si ves algunos topics del robot pero faltan otros (por ejemplo, los de la
  cámara), o sus servicios no responden, limpia la memoria compartida de
  Fast DDS en el robot: ver
  [Si el robot deja de responder o desaparecen nodos](#si-el-robot-deja-de-responder-o-desaparecen-nodos).

## Moverlo

- **`TwistStamped`:** en Jazzy, el robot espera `geometry_msgs/TwistStamped`
  en `/cmd_vel`, no `Twist`. Para mandar `Twist`, usa `/cmd_vel_unstamped`.
- **Ejemplos:** se lanzan con `robot:=tb4` (o `robot:=$ROBOT`, que `tb4` deja
  a `tb4`). Ver
  [Elegir el robot en los ejemplos](README-examples.md#elegir-el-robot-en-los-ejemplos).
- **Bump and go (bloques 6 y 12):** no usan `robot:=`. Tienen sus propios
  launchers, que terminan en `_tb4`. Si lanzas el del Kobuki con `robot:=tb4`,
  `ros2 launch` ignora ese argumento sin avisar, y el robot no se mueve
  (publica `Twist` y escucha un bumper que no existe).
- **Base de carga:** el robot está aparcado de cara a la base. Si arrancas un
  ejemplo sin `pixi run undock`, empuja contra ella. Ver
  [Base de carga del TurtleBot 4](README-pixi-tasks.md#base-de-carga-del-turtlebot-4).

## Bumper

La Create 3 no tiene un topic de bumper. Los golpes llegan en
`/hazard_detection`, y el Raspberry Pi solo lo republica si está descomentado
en su `republisher.yaml`. Si `ros2 topic info /hazard_detection` indica 0
publicadores, ver
[TurtleBot 4 real](README-examples.md#turtlebot-4-real) (bloque 6).

## Mecanismos de seguridad de la Create 3

Con los reflejos y el límite de marcha atrás de la base activados, los bump
and go se mueven a saltos tras cada choque. Se desactivan en el Raspberry Pi
(por SSH; desde el portátil no se puede). El cambio dura hasta que se
reinicie la base, salvo que lo guardes en su web. Comandos para desactivarlos,
volver a activarlos y consultarlos en
[Mecanismos de seguridad de la Create 3](README-examples.md#mecanismos-de-seguridad-de-la-create-3).

## Cámara: imagen completa y profundidad

De fábrica, la cámara OAK-D solo publica una imagen en color pequeña (250x250),
en `/oakd/rgb/preview/image_raw`. No publica ni la imagen en color completa ni
la de profundidad, para no saturar la wifi. Con eso valen los ejemplos 2D
(`robot:=tb4`), pero no los 3D (YOLO 3D, `yolo_class_3d`,
`yolo_class_3d_alt`, `vff_3d` y `full_vff_3d`). El motivo está en
[TurtleBot 4 real: activar la profundidad](README-examples.md#turtlebot-4-real-activar-la-profundidad),
y lo que se ha medido con este robot, más abajo, en
[Por qué 640x360 y 5 imágenes por segundo](#por-qué-640x360-y-5-imágenes-por-segundo).

### Arrancar y parar la cámara y el láser

Con el robot **en la base**, el TurtleBot 4 apaga la cámara y el láser para
ahorrar batería (parámetro `power_saver` de `turtlebot4_node`, activo de
fábrica). Mientras está en la base no hay ningún topic `/oakd` ni `/scan`, y no
sale ningún error. Al sacarlo con `pixi run undock` se encienden solos.

Para usarlos sin sacar el robot de la base, arráncalos a mano desde un equipo
preparado con `tb4`:

| Qué | Arrancar | Parar |
| --- | --- | --- |
| Cámara | `ros2 service call /oakd/start_camera std_srvs/srv/Trigger` | `ros2 service call /oakd/stop_camera std_srvs/srv/Trigger` |
| Láser | `ros2 service call /start_motor std_srvs/srv/Empty` | `ros2 service call /stop_motor std_srvs/srv/Empty` |

La respuesta de la cámara es `success=True`. Tarda unos segundos en volver a
publicar. Si el robot vuelve a entrar en la base, se apagan otra vez.

Para que no se apaguen nunca, cambia `power_saver: true` a `false` en
`/opt/ros/jazzy/share/turtlebot4_bringup/config/turtlebot4.yaml` del robot
(con `sudo`) y reinicia el servicio (`turtlebot4-service-restart`). En la base
gastará algo más de batería mientras se carga.

Parar la cámara también sirve para liberar la wifi y la CPU del Raspberry Pi
cuando no la necesitas.

### Activarlas

En el robot, por SSH:

1. Haz una copia del fichero de configuración de la cámara, para poder
   volver atrás. En el TurtleBot 4 Lite es `oakd_lite.yaml` en lugar de
   `oakd_pro.yaml`, aquí y en los pasos siguientes.

   ```bash
   cd /opt/ros/jazzy/share/turtlebot4_bringup/config
   sudo cp oakd_pro.yaml oakd_pro.yaml.orig
   ```

2. Edítalo (es de `root`, así que con `sudo`):

   ```bash
   sudo nano oakd_pro.yaml
   ```

   Déjalo así. Los valores que cambian respecto al de fábrica están
   comentados:

   ```yaml
   /oakd:
     ros__parameters:
       camera:
         i_enable_imu: false
         i_enable_ir: false
         i_floodlight_brightness: 0
         i_laser_dot_brightness: 100
         i_nn_type: none
         i_pipeline_type: RGBD      # antes RGB: calcula y publica la profundidad
         i_usb_speed: SUPER_PLUS
       rgb:
         i_board_socket_id: 0
         i_fps: 5.0                 # antes 30.0
         i_height: 360              # antes 720
         i_interleaved: false
         i_max_q_size: 10
         i_preview_size: 250
         i_enable_preview: true
         i_low_bandwidth: true
         i_keep_preview_aspect_ratio: true
         i_publish_topic: true      # antes false: publica la imagen en color
         i_resolution: '1080P'
         i_set_isp_scale: true      # nuevo: reduce 1920x1080 a 1/3...
         i_isp_num: 1               # nuevo
         i_isp_den: 3               # nuevo: ...es decir, a 640x360
         i_width: 640               # antes 1280
       left:                        # nuevo: cámaras de la profundidad
         i_fps: 5.0
         i_resolution: '400P'       # de fábrica 720P
         i_width: 640
         i_height: 400
       right:                       # nuevo
         i_fps: 5.0
         i_resolution: '400P'
         i_width: 640
         i_height: 400
       stereo:                      # nuevo: profundidad del tamaño de la imagen en color
         i_width: 640
         i_height: 360
       use_sim_time: false
   ```

3. Reinicia el servicio del robot. Tarda en torno a un minuto, porque
   espera a que se paren todos los procesos:

   ```bash
   turtlebot4-service-restart
   ```

4. Si el robot está en la base, enciende la cámara
   ([ver arriba](#arrancar-y-parar-la-cámara-y-el-láser)). Después, desde tu
   equipo preparado con `tb4`, comprueba que aparecen los topics nuevos (la
   cámara tarda unos segundos en arrancar):

   ```bash
   ros2 topic list | grep oakd
   # /oakd/rgb/image_raw         imagen en color, 640x360
   # /oakd/rgb/camera_info
   # /oakd/stereo/image_raw      profundidad, 640x360, en milímetros
   # /oakd/rgb/preview/image_raw la pequeña sigue publicándose
   ```

5. Lanza los ejemplos con `robot:=tb4_rgbd` en lugar de `robot:=tb4`. Esa
   entrada usa `/oakd/rgb/image_raw` en lugar de la imagen pequeña, porque
   YOLO 3D necesita que la imagen en color y la de profundidad tengan el
   mismo tamaño.

### Por qué 640x360 y 5 imágenes por segundo

Las imágenes viajan sin comprimir del Raspberry Pi al portátil por la wifi.
Medido con este robot y un router en 5 GHz:

| Configuración | En el robot | En el portátil, por wifi |
| --- | --- | --- |
| 1280x720 a 10 fps (y la profundidad a unos 15) | Color a 3,5 Hz y profundidad a 15 Hz: unos 300 Mbit/s entre las dos. La cámara gasta más de un núcleo del Raspberry Pi | Color a 0,2 Hz y profundidad a 0,8 Hz: casi nada |
| 640x360 a 5 fps (la de arriba), búfer de recepción por defecto | Color y profundidad a 5 Hz: unos 46 Mbit/s entre las dos. La cámara gasta un 30 % de un núcleo | Color a 4,1–4,6 Hz y profundidad a 1,5 Hz |
| 640x360 a 5 fps, con el [búfer de recepción ampliado](#búfer-de-recepción-del-portátil) | Igual | **Color y profundidad a 5 Hz: llega todo** |

No subas la resolución ni los fps: con 640x360 a 5 fps ya se usan unos
46 Mbit/s de la wifi, que comparten todos los que estén en esa red. Cada
equipo y cada programa que se suscribe a la cámara (YOLO, RViz, `rqt`...)
recibe su propia copia, así que cierra lo que no uses.

### Búfer de recepción del portátil

Aunque la wifi tenga ancho de banda de sobra, las imágenes se pierden si el
portátil no tiene sitio donde guardarlas al llegar. Fast DDS abre sus sockets
UDP con el búfer de recepción por defecto de Linux (`net.core.rmem_default`,
208 KB). Una imagen de 460–690 KB llega de golpe, desborda el búfer y el
kernel descarta trozos. Basta con perder uno para perder la imagen entera.

`pixi run tb4` lo evita cargando el perfil de Fast DDS
[`pixi/fastdds-tb4.xml`](pixi/fastdds-tb4.xml) (variable
`FASTRTPS_DEFAULT_PROFILES_FILE`), que pide búferes de 4 MB. El kernel no
deja pasar de `net.core.rmem_max`, que en un Ubuntu recién instalado es de
208 KB. Súbelo una vez en tu portátil (necesita `sudo` y queda guardado para
los siguientes arranques):

```bash
echo 'net.core.rmem_max=4194304' | sudo tee /etc/sysctl.d/60-ros2-buffers.conf
sudo sysctl --system
sysctl net.core.rmem_max      # debe salir 4194304
```

Para comprobar si se pierden paquetes por esto, mira este contador antes y
después de recibir imágenes. Si sube, el búfer se está desbordando:

```bash
nstat -az UdpRcvbufErrors
```

Sin Pixi (con la función `tb4` de tu `~/.bashrc`), carga el perfil
añadiendo a esa función:

```bash
export FASTRTPS_DEFAULT_PROFILES_FILE=~/rsocial/pixi/fastdds-tb4.xml
```

### Desactivarlas

Recupera la copia y reinicia el servicio:

```bash
cd /opt/ros/jazzy/share/turtlebot4_bringup/config
sudo cp oakd_pro.yaml.orig oakd_pro.yaml
turtlebot4-service-restart
```

Si actualizas el software del robot (`sudo apt upgrade`), el fichero puede
volver a la versión de fábrica: repite los pasos de activación (ver
[Ficheros del robot que cambian con las actualizaciones](#ficheros-del-robot-que-cambian-con-las-actualizaciones)).

## Si el robot deja de responder o desaparecen nodos

- **El robot no responde a `ping` ni a `ssh` durante un rato:** casi siempre
  es la batería. Con la batería baja, la base corta la alimentación del
  Raspberry Pi y este se reinicia sin avisar (en su log, el arranque anterior
  termina de golpe, sin apagado). Ponlo a cargar antes de seguir.
- **Faltan nodos del robot** (por ejemplo `/oakd` o `/turtlebot4_node`), o sus
  servicios se quedan en `waiting for service to become available...`, aunque
  sus procesos siguen en marcha. Pasa después de que los procesos del robot
  mueran de golpe (cortes de batería, reinicios del servicio que tardan):
  quedan ficheros viejos de la memoria compartida de Fast DDS en `/dev/shm`, y
  los nodos dejan de descubrirse entre sí. En el robot sale el error
  `RTPS_TRANSPORT_SHM Error ... open_and_lock_file failed`. Se arregla
  parando el servicio, limpiando esos ficheros y volviéndolo a arrancar:

  ```bash
  ssh -t ubuntu@<IP del robot> 'sudo systemctl stop turtlebot4.service; source /etc/turtlebot4/setup.bash; ros2 daemon stop; fastdds shm clean; sudo systemctl start turtlebot4.service'
  ```

  `fastdds shm clean` solo borra los ficheros que no usa ningún proceso.
  Después, si el robot está en la base, vuelve a
  [encender la cámara](#arrancar-y-parar-la-cámara-y-el-láser).

## Reloj del robot

Si la red del robot no tiene salida a internet, el Raspberry Pi no puede
poner su reloj en hora y puede ir desfasado días o meses. La base Create 3
toma la hora del Raspberry Pi. Con relojes distintos en el portátil y en el
robot fallan TF, RViz y la navegación, porque comparan marcas de tiempo de
los dos equipos.

Compáralo con `date` en el portátil y en el robot. Si no coinciden, ponle la
hora del portátil (pide la contraseña de `ubuntu`):

```bash
ssh -t ubuntu@<IP del robot> "sudo date -s '$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
```

`$(date ...)` se evalúa en el portátil antes de enviar el comando, así que el
robot recibe la hora del portátil. Hay que repetirlo cada vez que se encienda
el robot sin internet.

## Ficheros del robot que cambian con las actualizaciones

`republisher.yaml` (bumper) y `oakd_pro.yaml` (profundidad) los instala el
paquete `ros-jazzy-turtlebot4-bringup`. Si se actualiza el software del robot
(`sudo apt upgrade`), pueden volver a su versión original y hay que repetir
los cambios.
