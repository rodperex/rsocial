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
6. Si vas a usar los bump and go, comprueba que están desactivados los
   [mecanismos de seguridad de la Create 3](#mecanismos-de-seguridad-de-la-create-3)
   y, si no lo están, desactívalos.
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

La Create 3 no tiene un topic de bumper: los golpes llegan en
`/hazard_detection`. En el TurtleBot 4 con Jazzy, la Create 3 publica bajo
`/_do_not_use` y el Raspberry Pi solo republica los topics de
`/opt/ros/jazzy/share/turtlebot4_bringup/config/republisher.yaml`.
`hazard_detection` viene comentado: si `ros2 topic info /hazard_detection`
indica 0 publicadores, descoméntalo en el robot y reinicia el servicio
(`turtlebot4-service-restart`). Ese fichero lo instala el paquete
`ros-jazzy-turtlebot4-bringup`: si se actualiza el software del robot
(`sudo apt upgrade`), puede volver a escribirse el original y habrá que
descomentar la línea de nuevo.

## Mecanismos de seguridad de la Create 3

La base tiene dos mecanismos de seguridad que interfieren con los bump and go
(bloques 6 y 12 de [README-examples.md](README-examples.md)):

- **Reflejos** (`reflexes_enabled`): al chocar, la base retrocede y gira un
  poco por su cuenta, ignorando `/cmd_vel` durante un instante. Después la FSM
  o el árbol recuperan el control.
- **Límite de marcha atrás** (`safety_override`): sin sensores traseros, la
  base solo deja retroceder unos centímetros. Al pasar de ahí, publica el
  hazard `BACKUP_LIMIT` y se para.

El resultado es que el robot se mueve a saltos al retroceder y al girar
después del choque. El giro en sí no es el problema: sin choques, la base gira
de forma uniforme.

Los comandos de abajo funcionan desde una terminal del portátil preparada con
`pixi run tb4`. Si la llamada se queda en
`waiting for service to become available...`, el portátil no ve el servicio de
la base: entra por SSH en el Raspberry Pi (con la IP del display, o
`turtlebot4.local` si tu red resuelve mDNS) y ejecútalo allí:

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
edita desde su servidor web. Hazlo con el robot quieto: al reiniciar la
aplicación de la base, el robot se queda sin control durante un minuto.

1. Abre en el navegador `http://<IP del robot>:8080` (la IP del display; el
   Raspberry Pi redirige ese puerto a la base).
2. Entra en **Application → Configuration**. Arriba, en **ROS 2 Namespace**,
   sale `/_do_not_use`: es el namespace de todos los nodos de la base. No lo
   cambies.
3. Más abajo, el cuadro **Application ROS 2 Parameters File** trae de fábrica
   un bloque `motion_control:` con `safety_override: "none"`. Ese bloque no se
   aplica: como el namespace no está vacío, el nombre del nodo tiene que
   llevarlo delante (lo avisa la nota de la página). Sustituye todo el
   contenido del cuadro por esto:

   ```yaml
   /_do_not_use/motion_control:
     ros__parameters:
       # safety_override: "none" (fábrica), "backup_only" o "full"
       safety_override: "backup_only"
       reflexes_enabled: false
   ```

   No uses `safety_override: "full"`: desactiva también los sensores de
   escalón de delante.
4. Pulsa **Save**. Al recargar la página, el cuadro debe mostrar el fichero
   nuevo.
5. Reinicia la aplicación de la base: **Restart application**, debajo del
   cuadro, o **Application → Restart Application**. Tarda en torno a un minuto
   y suena al terminar.
6. Reinicia el servicio del Raspberry Pi, por SSH:

   ```bash
   turtlebot4-service-restart
   ```

   Hace falta: después de reiniciar la base, el Raspberry Pi deja de
   republicar sus datos (`/odom`, `/tf`, `/hazard_detection`...) hasta que se
   reinicia su servicio. Hazlo con el robot fuera de la base (ver
   [Arrancar y parar la cámara y el láser](#arrancar-y-parar-la-cámara-y-el-láser)).
7. Comprueba que la base arranca con los valores nuevos con `get_parameters`,
   como arriba: deben salir `string_value='backup_only'` y
   `bool_value=False`. Comprueba también que llega la odometría:
   `ros2 topic hz /odom` (unos 20 Hz).

Para volver a la configuración de fábrica, deja en el cuadro el bloque
original (`motion_control:` con `safety_override: "none"`, sin
`reflexes_enabled`) y repite los pasos 4 a 7.

Con la seguridad desactivada, el robot puede caer marcha atrás por un escalón
y no se aparta solo al chocar: úsalo en suelo plano y despejado, y vuelve a
activarla al terminar si el robot lo van a usar otros.

## Cámara: imagen completa y profundidad

De fábrica, la cámara OAK-D solo publica una imagen en color pequeña (250x250),
en `/oakd/rgb/preview/image_raw`. No publica ni la imagen en color completa ni
la de profundidad, para no saturar la wifi. Con eso valen los ejemplos 2D
(`robot:=tb4`), pero no los 3D (YOLO 3D, `yolo_class_3d`,
`yolo_class_3d_alt`, `vff_3d` y `full_vff_3d`). Lo que se ha medido con este
robot está más abajo, en
[Por qué 640x360 y pocas imágenes por segundo](#por-qué-640x360-y-pocas-imágenes-por-segundo).

> **¿Por qué no se publica por defecto?** Calcular la profundidad no es el
> problema: lo hace la propia cámara. El problema es mover las imágenes. La
> Raspberry Pi del robot tiene que recibirlas por USB y publicarlas en ROS 2, y
> los nodos que las usan (YOLO, RViz...) suelen estar en otro equipo, así que
> viajan por la WiFi. Una imagen en color de 1280x720 ocupa unos 2,8 MB y una de
> profundidad del mismo tamaño unos 1,8 MB: a 30 imágenes por segundo son más de
> 1 Gbit/s, mucho más de lo que da una WiFi. La imagen de 250x250 ocupa unos
> 190 KB (unos 45 Mbit/s), y la navegación del robot no necesita la cámara, así
> que los fabricantes dejan solo esa para que el robot vaya fluido.

Para gastar menos wifi, las imágenes pueden viajar comprimidas (ver
[Imágenes comprimidas](#imágenes-comprimidas)).

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

**Con la profundidad activada, la cámara puede quedarse bloqueada al volver a
encenderse.** Pasa al sacar el robot de la base, después de que la base la
haya apagado: `turtlebot4_node` pide encenderla, pero el nodo `/oakd` no
responde, y su proceso (`component_container` de `oakd_container`) se queda
al 100 % de CPU. Solo se ve `/oakd/rgb/preview/image_raw`, sin
`/oakd/rgb/image_raw` ni `/oakd/stereo/image_raw`, y YOLO no recibe imágenes.
Llamar a mano a `/oakd/start_camera` tampoco recibe respuesta. Se arregla
reiniciando el servicio **con el robot fuera de la base**, para que la cámara
arranque directamente.

Para que no pase, desactiva el `power_saver`, así la cámara y el láser no se
apagan nunca. En el robot, por SSH:

```bash
sudo sed -i 's/power_saver: true/power_saver: false/' /opt/ros/jazzy/share/turtlebot4_bringup/config/turtlebot4.yaml
grep -n power_saver /opt/ros/jazzy/share/turtlebot4_bringup/config/turtlebot4.yaml   # power_saver: false
turtlebot4-service-restart
```

En la base gastará algo más de batería mientras se carga. Las actualizaciones
del robot pueden devolver el fichero a su versión de fábrica (ver
[Ficheros del robot que cambian con las actualizaciones](#ficheros-del-robot-que-cambian-con-las-actualizaciones)).

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
         i_fps: 3.0                 # antes 30.0
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
         i_fps: 3.0
         i_resolution: '400P'       # de fábrica 720P
         i_width: 640
         i_height: 400
       right:                       # nuevo
         i_fps: 3.0
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

5. Abre la terminal con `pixi run tb4-rgbd` (deja `ROBOT=tb4_rgbd`) y lanza los
   ejemplos con `robot:=$ROBOT`, en lugar de `robot:=tb4`. Esa
   entrada usa `/oakd/rgb/image_raw` en lugar de la imagen pequeña, porque
   YOLO 3D necesita que la imagen en color y la de profundidad tengan el
   mismo tamaño. Si quieres que las imágenes viajen comprimidas, usa
   `pixi run tb4-rgbd-c` (ver [Imágenes comprimidas](#imágenes-comprimidas)).

### Por qué 640x360 y pocas imágenes por segundo

Las imágenes viajan sin comprimir del Raspberry Pi al portátil por la wifi.
Medido con este robot y un router en 5 GHz (la tabla usa 5 fps; para YOLO 3D
baja a 3 fps, como se explica debajo de la tabla):

| Configuración | En el robot | En el portátil, por wifi |
| --- | --- | --- |
| 1280x720 a 10 fps (y la profundidad a unos 15) | Color a 3,5 Hz y profundidad a 15 Hz: unos 300 Mbit/s entre las dos. La cámara gasta más de un núcleo del Raspberry Pi | Color a 0,2 Hz y profundidad a 0,8 Hz: casi nada |
| 640x360 a 5 fps (la de arriba), búfer de recepción por defecto | Color y profundidad a 5 Hz: unos 46 Mbit/s entre las dos. La cámara gasta un 30 % de un núcleo | Color a 4,1–4,6 Hz y profundidad a 1,5 Hz |
| 640x360 a 5 fps, con el [búfer de recepción ampliado](#búfer-de-recepción-del-portátil) | Igual | **Color y profundidad a 5 Hz: llega todo** |

**Usa 3 fps si vas a usar YOLO 3D.** `detect_3d_node` empareja la profundidad,
el `camera_info` y las detecciones, y solo acepta 0,5 s de diferencia entre sus
sellos. A 5 fps, el color y el `camera_info` llegaban por wifi a unos 3 Hz
mientras la profundidad seguía a 5 Hz, así que el retraso del color crecía
(hasta unos 3 s) y `/yolo/detections_3d` nunca se publicaba. Con `i_fps: 3.0`
en `rgb`, `left` y `right` (en `oakd_pro.yaml`), los sellos difieren como
mucho un fotograma (0,33 s) y el 3D funciona. Para comprobarlo mide con YOLO
en marcha la diferencia entre los sellos de `/oakd/stereo/image_raw`,
`/oakd/rgb/image_raw`, `/oakd/rgb/camera_info` y `/yolo/tracking`: debe quedar
por debajo de 0,5 s y no crecer.

Sin comprimir, no subas la resolución ni los fps: con 640x360 a 5 fps ya se
usan unos 46 Mbit/s de la wifi, que comparten todos los que estén en esa red
(comprimidas sí se pueden subir, ver [Subir los fps](#subir-los-fps)). Cada
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

### Imágenes comprimidas

El driver de la cámara publica cada imagen en varios formatos con
`image_transport`: sin comprimir (`/oakd/rgb/image_raw`) y comprimida
(`/oakd/rgb/image_raw/compressed`, en JPEG). Para la profundidad, el formato
comprimido es `/oakd/stereo/image_raw/compressedDepth`, en PNG, que no pierde
información. YOLO solo admite imágenes sin comprimir, así que hay que
descomprimirlas en el portátil:

```text
robot                                             portátil
/oakd/rgb/image_raw/compressed         ──wifi──►  decompress_image ──► /oakd/rgb/image_local
/oakd/stereo/image_raw/compressedDepth ──wifi──►  decompress_depth ──► /oakd/stereo/image_local
```

La entrada `tb4_rgbd_c` de
[`robots.yaml`](src/rsocial_robots/config/robots.yaml) hace esto:

- `ros2 launch camera yolo.launch.py robot:=tb4_rgbd_c` arranca además los dos
  nodos `republish` de `image_transport` del dibujo
  ([`decompress.launch.py`](src/sensors/camera/launch/decompress.launch.py)).
  Con las demás entradas no arranca nada.
- Todos los ejemplos usan las imágenes descomprimidas, `/oakd/rgb/image_local`
  y `/oakd/stereo/image_local`. El `camera_info` no cambia: es pequeño y viaja
  tal cual.
- Los sellos de tiempo se conservan, así que YOLO 3D empareja la profundidad y
  las detecciones igual que sin comprimir.

Para usarla:

1. Configura la cámara del robot como en [Activarlas](#activarlas). Para
   comprimir no hay que cambiar nada más en `oakd_pro.yaml`: los topics
   comprimidos los añaden los plugins de `image_transport` instalados en el
   robot, y el Raspberry Pi solo comprime mientras alguien está suscrito a
   ellos. No actives `i_publish_compressed` en el fichero: deja de publicar
   la imagen sin comprimir, cambia los topics y comprimiría la profundidad
   en JPEG, que pierde información.
2. Comprueba que el robot publica las imágenes comprimidas:

   ```bash
   ros2 topic list | grep -E 'compressed$|compressedDepth$'
   # /oakd/rgb/image_raw/compressed
   # /oakd/stereo/image_raw/compressedDepth
   ```

   Si no salen, en el robot faltan los plugins de compresión. Instálalos por
   SSH y reinicia el servicio:

   ```bash
   sudo apt install ros-jazzy-image-transport-plugins
   turtlebot4-service-restart
   ```

3. Abre las terminales con `pixi run tb4-rgbd-c` (deja `ROBOT=tb4_rgbd_c`) y
   lanza los ejemplos con `robot:=$ROBOT`.

Para ver las imágenes sin YOLO (en RViz o `rqt_image_view`), arranca los
descompresores solos:

```bash
ros2 launch camera decompress.launch.py robot:=$ROBOT
```

No lo hagas con YOLO en marcha, porque YOLO ya los arranca y cada imagen
llegaría dos veces.

**No te suscribas desde el portátil a `/oakd/rgb/image_raw` ni a
`/oakd/stereo/image_raw`.** El robot sigue publicando esas imágenes sin
comprimir, pero solo las envía por la wifi si alguien está suscrito a ellas:
en DDS, cada mensaje se envía solo a los suscriptores de su topic, así que sin
suscriptores no sale nada del robot. Si en RViz, `rqt` o un
`ros2 topic hz` eliges uno de esos topics, vuelven a viajar sin comprimir
mientras siga abierto. Para comprobar que no viajan, mira que no tengan
suscriptores:

```bash
ros2 topic info /oakd/rgb/image_raw        # Subscription count: 0
ros2 topic info /oakd/stereo/image_raw     # Subscription count: 0
```

Los descompresores tampoco piden nada al robot si nadie usa sus imágenes:
solo se suscriben a los topics comprimidos mientras alguien está suscrito a
`/oakd/rgb/image_local` o a `/oakd/stereo/image_local`.

#### Subir los fps

Sin comprimir, los 3 fps vienen de la wifi (ver
[Por qué 640x360 y pocas imágenes por segundo](#por-qué-640x360-y-pocas-imágenes-por-segundo)).
El color en JPEG ocupa en torno a la décima parte que sin comprimir y la
profundidad se comprime bastante menos, porque PNG no pierde información, así
que comprimidas caben más imágenes por segundo. El límite pasa a ser la CPU
del Raspberry Pi, que tiene que comprimirlas, sobre todo la profundidad.

Los fps se cambian en el mismo `oakd_pro.yaml` del robot, en `i_fps` de
`rgb`, `left` y `right` (los tres con el mismo valor), y después se reinicia
el servicio con `turtlebot4-service-restart`. Empieza por 5:

```yaml
rgb:
  i_fps: 5.0
left:
  i_fps: 5.0
right:
  i_fps: 5.0
```

Todavía no está medido con este robot. Antes de pasar a 6, mide con 5:

- El ancho de banda de los topics comprimidos, con
  `ros2 topic bw /oakd/rgb/image_raw/compressed` y
  `ros2 topic bw /oakd/stereo/image_raw/compressedDepth`. No uses
  `ros2 topic bw` con los topics sin comprimir, porque se suscribe a ellos y
  los hace viajar.
- La CPU del proceso de la cámara en el robot, con `top`.
- La diferencia entre sellos con YOLO 3D en marcha, como en
  [Por qué 640x360 y pocas imágenes por segundo](#por-qué-640x360-y-pocas-imágenes-por-segundo):
  debe quedar por debajo de 0,5 s y no crecer.

#### Calidad de la compresión

Cada imagen tiene su propio ajuste, y los dos funcionan de forma distinta:

| | Color: `jpeg_quality` | Profundidad: `png_level` |
| --- | --- | --- |
| Formato | JPEG, pierde calidad | PNG, no pierde nada |
| Valores | 1 a 100 (de fábrica, 95) | 1 a 9 (de fábrica, 3) |
| Número más alto | Más calidad y ocupa más | Ocupa algo menos y gasta más CPU |
| CPU | Casi no cambia con el valor | Crece con el nivel |

Medido en un portátil con una imagen de 640x360, comprimiendo con un solo
núcleo. La profundidad es sintética, con un ruido como el de una cámara
estéreo:

| Ajuste | Tiempo por imagen | Tamaño | Frente a sin comprimir |
| --- | --- | --- | --- |
| JPEG 95 (de fábrica) | 2,2 ms | 111 KB | 6 veces menos |
| **JPEG 80** | 1,6 ms | 52 KB | 13 veces menos |
| JPEG 60 | 1,5 ms | 34 KB | 20 veces menos |
| **PNG 1** | 21 ms | 269 KB | 1,7 veces menos |
| PNG 3 (de fábrica) | 25 ms | 266 KB | 1,7 veces menos |
| PNG 9 | 52 ms | 263 KB | 1,7 veces menos |

La profundidad es la que gasta CPU y la que menos se comprime: el ruido
apenas deja comprimir, y subir el nivel del PNG dobla la CPU sin reducir casi
el tamaño. Con esas medidas, a 5 fps queda así (la CPU del Raspberry Pi 4 es
una estimación: un núcleo suyo es unas 4 o 5 veces más lento que el del
portátil):

| Imágenes a 5 fps | Wifi | CPU para comprimir en el Raspberry Pi |
| --- | --- | --- |
| Sin comprimir | 46 Mbit/s | Nada |
| Color en JPEG 80, profundidad sin comprimir | unos 20 Mbit/s | Muy poca (en torno al 5 % de un núcleo) |
| Color en JPEG 80 y profundidad en PNG 1 | unos 13 Mbit/s | En torno a la mitad de un núcleo |

Comprimir el color sale casi gratis y es lo que más ayuda por cada punto de
CPU. Comprimir también la profundidad ahorra otros 7 Mbit/s, pero es lo que
carga el Raspberry Pi. Con las dos comprimidas debería llegar todo a 5 fps
con margen. Si el Raspberry Pi no da, la alternativa es comprimir solo el
color.

Valores recomendados:

- **`png_level: 1`** para la profundidad. Ocupa lo mismo que con 3 y gasta
  menos CPU, y la profundidad llega exacta con cualquier nivel. No lo subas.
- **`jpeg_quality: 80`** para el color. Ocupa la mitad que con 95 y no se nota
  ni a la vista ni en YOLO. Por debajo de 60 aparecen defectos en la imagen
  que pueden empeorar las detecciones.

Son parámetros del nodo de la cámara. Su nombre sale del topic, así que
deberían ser `stereo.image_raw.compressedDepth.png_level` y
`rgb.image_raw.compressed.jpeg_quality`. Comprueba los nombres exactos en el
robot, con la cámara en marcha:

```bash
ros2 param list /oakd | grep -iE 'png_level|jpeg_quality'
```

Pruébalos en marcha:

```bash
ros2 param set /oakd stereo.image_raw.compressedDepth.png_level 1
ros2 param set /oakd rgb.image_raw.compressed.jpeg_quality 80
```

Para que no se pierdan al reiniciar, añádelos a `oakd_pro.yaml`, dentro de
`rgb` y `stereo`:

```yaml
rgb:
  image_raw:
    compressed:
      jpeg_quality: 80
stereo:
  image_raw:
    compressedDepth:
      png_level: 1
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

`republisher.yaml` (bumper), `oakd_pro.yaml` (profundidad) y
`turtlebot4.yaml` (`power_saver`) los instala el paquete
`ros-jazzy-turtlebot4-bringup`. Si se actualiza el software del robot
(`sudo apt upgrade`), pueden volver a su versión original y hay que repetir
los cambios.
