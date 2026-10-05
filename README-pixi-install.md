# Instalación con Pixi

Esta guía instala ROS 2 Jazzy y el workspace `rsocial` dentro de Pixi. Los
comandos usan `~/rsocial` como ruta de ejemplo; puedes sustituirla por otra.

## Requisitos

Necesitas una distribución Linux de 64 bits (x86_64), `git`, `curl` y Pixi.
Funciona en cualquier versión de Ubuntu (se ha probado en Ubuntu 26.04), porque
Pixi instala ROS 2 Jazzy y sus dependencias dentro del workspace. No necesitas
instalar ROS 2 en el sistema ni ejecutar `source /opt/ros/jazzy/setup.bash`.

Reserva unos 25 GB libres. La instalación descarga varios GB (ROS 2, PyTorch
y lo que añada cada entorno adicional), así que la primera vez tarda un rato.
Para ejecutar YOLO y Whisper en la GPU hace falta una tarjeta NVIDIA con
driver 580 o posterior (`nvidia-smi` lo muestra); sin ella funcionan en la
CPU, más despacio.

El TTS de `simple_hri` reproduce el audio con `aplay`, que no está en Pixi y
se usa el del sistema. Ubuntu lo trae instalado; si no lo tienes:

```bash
sudo apt install alsa-utils
```

Instala Pixi si no está disponible:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
source "$HOME/.bashrc"
pixi --version
```

## Instalación normal

Esta es la opción por defecto. Incluye el simulador del TurtleBot 4 (Gazebo)
y su navegación (ver [TurtleBot 4](#turtlebot-4-simulador-y-navegación)).

### 1. Clonar e instalar el entorno

```bash
mkdir -p ~/rsocial
cd ~/rsocial
git clone https://github.com/rodperex/rsocial.git .
pixi install
```

### 2. Importar los repositorios

Desde la raíz del workspace, activa la shell de Pixi antes de importar los
repositorios:

```bash
cd ~/rsocial
pixi shell
cd ~/rsocial/src
vcs import < thirdparty-pixi.repos
cd ..
git -C src/thirdparty/nao_lola submodule update --init --recursive
```

`thirdparty-pixi.repos` es el manifiesto completo para Pixi. No ejecutes
`vcs import < thirdparty-native.repos` en este flujo.

### 3. Compilar

Desde la raíz del workspace:

```bash
cd ~/rsocial
pixi run build
```

La tarea crea automáticamente el `COLCON_IGNORE` del paquete legacy
`nao_lola`. Mantiene `nao_lola_client` y los paquetes actuales de mensajes.

La compilación muestra avisos (*stderr output*) de varios paquetes; son
normales mientras el resumen final no indique paquetes fallidos (*failed*).

### 4. Usar el workspace

En nuevas terminales:

```bash
cd ~/rsocial
pixi shell
source install/setup.bash
```

Por ejemplo:

```bash
ros2 launch node_programming pubsub.launch.py
```

Si has instalado un entorno adicional de `pixi.toml` (por ejemplo, el del
[Kobuki](README-kobuki-pixi.md)), compila y abre la shell con ese entorno:
`pixi run -e <entorno> build` y `pixi shell -e <entorno>`.

No uses `rosdep` con Pixi. Las dependencias están declaradas en `pixi.toml` y
se instalan con `pixi install`.

Si compartes red con otros equipos, configura también ROS 2 para no mezclar
tus nodos con los suyos (ver [Varios equipos en la misma red](README.md#varios-equipos-en-la-misma-red)).

## TurtleBot 4: simulador y navegación

El entorno por defecto trae el simulador del TurtleBot 4 (Gazebo), la
navegación (Nav2) y RViz. No hace falta instalar ni compilar nada más.

Vas a usar varias terminales a la vez (simulador, localización, Nav2 y
comandos). Todas tienen que estar preparadas igual; si no, no se ven entre
ellas.

### Preparar cada terminal: simulador o robot real

El TurtleBot 4, real o simulado, necesita dos variables:

- `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`: el middleware de comunicaciones. El
  robot real usa Fast DDS, y el simulador solo funciona bien con él.
- `ROS_DOMAIN_ID`: separa grupos de nodos. Solo se ven los nodos con el mismo
  número. El robot real usa el **0**, así que el simulador tiene que ir en
  otro (por ejemplo, el 1); si no, se mezclan el robot real y el simulado.

| | Robot real | Simulador |
| --- | --- | --- |
| `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` | `rmw_fastrtps_cpp` |
| `ROS_DOMAIN_ID` | `0` | cualquiera del 1 al 100 (no el 0) |

Para no escribirlas cada vez, añade estas dos funciones al final de tu
`~/.bashrc` (solo una vez):

```bash
# TurtleBot 4 real
function tb4() {
    export ROS_DOMAIN_ID=0
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    ros2 daemon stop > /dev/null 2>&1
    echo "TurtleBot 4: ROS_DOMAIN_ID=$ROS_DOMAIN_ID RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
}

# TurtleBot 4 simulado: fuera del dominio del robot real
function tb4sim() {
    export ROS_DOMAIN_ID=1
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    ros2 daemon stop > /dev/null 2>&1
    echo "TurtleBot 4 (simulador): ROS_DOMAIN_ID=$ROS_DOMAIN_ID RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
}
```

`ros2 daemon stop` reinicia la caché de `ros2 topic list` y similares, que si
no seguiría mostrando lo del dominio anterior. Si estáis varios en la misma
red, que cada uno ponga en `tb4sim` un número distinto (ver
[Varios equipos en la misma red](README.md#varios-equipos-en-la-misma-red)).

Después, **en cada terminal nueva**:

```bash
cd ~/rsocial
pixi shell
source install/setup.bash
tb4sim     # con el simulador; con el robot real, tb4
```

No mezcles: en todas las terminales de una misma sesión, la misma función.

### 1. Lanzar el simulador (terminal 1)

Antes de lanzarlo, comprueba que no queda ningún Gazebo de una ejecución
anterior (si se cerró mal, su servidor sigue vivo en segundo plano y estropea
el reloj del nuevo):

```bash
pgrep -af "gz sim"         # no debe salir nada
pkill -f "gz sim"          # si ha salido algo
```

Hay tres formas de lanzar el simulador. Hacen lo mismo y solo cambia cómo
dibuja Gazebo la escena, que es también cómo calcula el láser:

| Tarea | Cuándo usarla |
| --- | --- |
| `pixi run sim` | Primera opción en cualquier ordenador: usa la tarjeta gráfica que el sistema tenga por defecto |
| `pixi run sim-nvidia` | Portátiles con dos tarjetas gráficas (integrada + NVIDIA): fuerza la NVIDIA. Es la más rápida |
| `pixi run sim-generic` | Si las otras fallan: dibuja con la CPU. Funciona en cualquier ordenador, pero va varias veces más lento |

A cualquiera de ellas se le pueden añadir opciones detrás (ver
[Elegir el mundo](#elegir-el-mundo)). Para navegar hace falta `rviz:=true`,
que abre RViz con el mapa. Por ejemplo:

```bash
pixi run sim rviz:=true
```

Las tareas solo lanzan `turtlebot4_gz.launch.py` con algunas variables de
entorno ya puestas. Si prefieres lanzarlo a mano, en una terminal preparada
como arriba (`tb4sim` ya pone `RMW_IMPLEMENTATION`), estos comandos equivalen
a cada tarea, con las mismas opciones detrás:

```bash
# pixi run sim
ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py rviz:=true

# pixi run sim-nvidia
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
  __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json \
  ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py rviz:=true

# pixi run sim-generic
LIBGL_ALWAYS_SOFTWARE=1 ros2 launch turtlebot4_gz_bringup turtlebot4_gz.launch.py rviz:=true
```

Espera a que Gazebo muestre el almacén con el robot. La primera vez tarda más.
RViz se abre sin mapa todavía: aparecerá en el paso 3.

**Comprueba el láser** en otra terminal:

```bash
ros2 topic echo --once /scan --field ranges | head -c 300
```

Tienen que salir números distintos (y algunos `inf`). Si **todos** son
`0.164`, la tarjeta gráfica que se está usando no calcula bien el láser (se ha
visto con gráficas Intel integradas): el robot creerá que está rodeado de
obstáculos y no navegará. Cierra el simulador (Ctrl+C) y usa otra de las
tareas de la tabla:

```bash
pixi run sim-nvidia rviz:=true    # si el ordenador tiene NVIDIA
pixi run sim-generic rviz:=true   # si no
```

### 2. Desacoplar el robot (terminal 2)

El robot aparece en su base de carga. Antes de moverlo hay que sacarlo:

```bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
```

El robot retrocede, gira y termina con `Goal finished with status: SUCCEEDED`.

### 3. Localización (terminal 3)

Carga el mapa del almacén y localiza el robot en él (AMCL):

```bash
ros2 launch turtlebot4_navigation localization.launch.py use_sim_time:=true \
  map:=$(ros2 pkg prefix turtlebot4_navigation)/share/turtlebot4_navigation/maps/warehouse.yaml
```

Espera a `Managed nodes are active`; el mapa aparece en RViz. Con otro mundo,
cambia `warehouse.yaml` por su mapa (ver [Elegir el mundo](#elegir-el-mundo)).

`use_sim_time:=true` hace que use el reloj del simulador. Sin él descarta los
datos del simulador y no funciona.

### 4. Posición inicial (RViz)

1. Pulsa **2D Pose Estimate** (barra de arriba).
2. Haz clic en el mapa donde está el robot (junto a la base de carga) y, sin
   soltar, arrastra hacia donde mira.
3. Las lecturas del láser (puntos de color) tienen que quedar encima de las
   paredes del mapa. Si no coinciden, repite el paso con más cuidado.

### 5. Navegación (terminal 4)

**Después de dar la posición inicial**:

```bash
ros2 launch turtlebot4_navigation nav2.launch.py use_sim_time:=true
```

Espera a `Managed nodes are active`.

### 6. Enviar objetivos

En RViz, pulsa **Nav2 Goal** y haz clic (y arrastra para la orientación) en un
punto libre del mapa. El robot calcula la ruta y va hasta allí.

También se puede enviar desde una terminal (punto libre del almacén):

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: map}, pose: {position: {x: -2.0, y: -0.5}, orientation: {w: 1.0}}}}"
```

### Si algo no funciona

| Síntoma | Causa y solución |
| --- | --- |
| Las terminales no ven los topics del simulador (`ros2 topic list` casi vacío) | Alguna terminal no está preparada igual. Ejecuta `echo $ROS_DOMAIN_ID $RMW_IMPLEMENTATION` en todas: tiene que salir lo mismo. |
| Se ven topics o nodos raros, o el robot real se mueve | Estás en el dominio 0, el del robot real. Usa `tb4sim`, no `tb4`. |
| La localización repite `Detected jump back in time` | Hay dos Gazebo abiertos (uno de una ejecución anterior). Cierra todo, `pkill -f "gz sim"` y vuelve a empezar. |
| El undock responde `Goal was rejected` | El robot ya no está en la base: puedes seguir. |
| El undock se queda en `Sending goal` | Revisa el dominio (fila anterior) y que solo haya un Gazebo. |
| Nav2 termina con `Failed to bring up all requested nodes` | Lo lanzaste antes de dar la posición inicial. Ciérralo (Ctrl+C), da la posición y vuelve a lanzarlo. |
| Se ve la ruta en RViz pero el robot no se mueve | El láser da `0.164` en todo (ver paso 1), o falta `use_sim_time:=true` en algún comando. |
| Todo va muy lento | Es normal con `sim-generic`: el simulador usa la CPU. |
| Gazebo se cierra nada más arrancar (`[gazebo-1]: process has died ... exit code 255`) y el resto se queda en `Requesting list of world names` | La terminal tiene cargado un ROS 2 del sistema (`source /opt/ros/...`), cuyas librerías de Gazebo se mezclan con las de Pixi. Abre una terminal nueva sin cargarlo; `echo $LD_LIBRARY_PATH` no debe contener `/opt/ros`. |

### Elegir el mundo

Añade `world:=<mundo>` detrás de la tarea, por ejemplo `pixi run sim world:=maze`.

| Mundo | Descripción | Mapa para la localización |
| --- | --- | --- |
| `warehouse` (por defecto) | Almacén con estanterías | `warehouse.yaml` |
| `depot` | Nave industrial. Se descarga de internet la primera vez, así que tarda más | `depot.yaml` |
| `maze` | Recinto cerrado con paredes y obstáculos | `maze.yaml` |
| `empty` | Suelo plano sin nada más (solo la base de carga). Útil para probar movimientos sin obstáculos | No tiene: sirve para mover el robot, no para navegar con Nav2 |

Con otro mundo, en el paso 3 usa su mapa. Por ejemplo, con `maze`:

```bash
pixi run sim world:=maze rviz:=true      # paso 1
ros2 launch turtlebot4_navigation localization.launch.py use_sim_time:=true \
  map:=$(ros2 pkg prefix turtlebot4_navigation)/share/turtlebot4_navigation/maps/maze.yaml   # paso 3
```

Otras opciones de la tarea:

| Opción | Para qué sirve | Por defecto |
| --- | --- | --- |
| `model:=lite` | TurtleBot 4 Lite (sin torre ni pantalla) | `standard` |
| `x:=`, `y:=`, `yaw:=` | Posición inicial del robot (metros y radianes) | `0.0` |
| `rviz:=true` | RViz con el mapa, para dar la posición inicial y objetivos | `false` |

### Simular en una casa

Para robótica social viene mejor una vivienda que un almacén. El paquete
`tb4_worlds` de este repositorio lanza el TurtleBot 4 en la casa de AWS
RoboMaker (salón, cocina, dormitorio y gimnasio, con muebles). La casa la
descarga `thirdparty-pixi.repos` y se compila con el resto del workspace
(`pixi run build`).

Esta casa no se elige con `world:=`: tiene sus propias tareas, con las mismas
tres variantes que el simulador normal:

| Tarea | Cuándo usarla |
| --- | --- |
| `pixi run sim-house` | Como `sim` |
| `pixi run sim-house-nvidia` | Como `sim-nvidia` |
| `pixi run sim-house-generic` | Como `sim-generic` |

Admiten las mismas opciones que el simulador normal (`rviz:=true`,
`model:=lite`, `x:=`, `y:=`, `yaw:=`), salvo `world:=`. El robot aparece con
su base de carga en el centro de la casa (`x:=0.0 y:=1.5`). Si lo pones en
otro sitio, deja al menos un metro libre alrededor para la base.

Sin tareas de Pixi, el lanzamiento es este (con las variables de
`sim-nvidia` o `sim-generic` delante si las necesitas, como en el paso 1):

```bash
ros2 launch tb4_worlds small_house.launch.py rviz:=true
```

Para navegar, sigue los pasos de arriba cambiando solo el mapa del paso 3:

```bash
pixi run sim-house rviz:=true      # paso 1
ros2 launch turtlebot4_navigation localization.launch.py use_sim_time:=true \
  map:=$(ros2 pkg prefix aws_robomaker_small_house_world)/share/aws_robomaker_small_house_world/maps/turtlebot3_waffle_pi/map.yaml   # paso 3
```

¿Por qué no basta con `world:=small_house`? El lanzamiento del TurtleBot 4
busca el mundo solo en sus propios directorios, y el fichero de la casa no
está preparado para este robot. `small_house.launch.py` hace una copia
adaptada de la casa, le añade sus directorios a Gazebo y lanza el robot igual
que `turtlebot4_gz.launch.py`.

### Mover, quitar y añadir objetos

Para probar los ejemplos a menudo hace falta cambiar la escena: poner una silla
delante del robot, quitar la base de carga o colocar un obstáculo en medio.

**Desde la ventana de Gazebo.** La ventana del TurtleBot 4 trae una disposición
propia sin la herramienta para seleccionar objetos con el ratón. Añádela desde
el menú **⋮** (arriba a la derecha), buscando **Select Entities**. Añade
también **Entity Tree** (la lista de objetos) y, si quieres escribir las
coordenadas a mano, **Component Inspector**. Después:

- **Mover**: haz clic en el objeto (se resalta), pulsa **T** y arrastra la
  flecha roja (x) o la verde (y). No toques la azul (altura). **R** gira el
  objeto y **Esc** sale del modo.
- **Escribir la posición**: con el objeto seleccionado, cambia su **Pose** en
  el Component Inspector.
- **Quitar**: clic derecho sobre el objeto en el Entity Tree → **Remove**.
- **Añadir una forma simple**: los botones de la barra superior (cubo, esfera,
  cilindro...). Para que funcionen hace falta el plugin **Spawn** (menú
  **⋮**), que es el que coloca la forma en la escena. Con él, haz clic en la
  forma, mueve el ratón hasta el sitio y vuelve a hacer clic para soltarla. El
  cubo mide 1 m de lado: es un buen obstáculo, porque llega a la altura del
  láser.
- **Añadir un modelo**: plugin **Resource Spawner** (menú **⋮**), que muestra
  los modelos de Gazebo Fuel (en internet) y los locales para arrastrarlos a la
  escena.

Si en la lista no aparece **Select Entities**, abre en otra terminal (preparada
igual) una segunda ventana con la disposición estándar de Gazebo, que ya trae
todo eso. Muestra la misma simulación:

```bash
gz sim -g
```

**Desde la terminal.** El mundo de la casa se llama `small_house` (con otros
mundos, `gz service -l | grep set_pose` muestra el nombre), la base de carga
`standard_dock` y los objetos tienen nombres como `ChairA_01_001`
(`gz model --list` los lista todos):

```bash
# Quitar la base de carga
gz service -s /world/small_house/remove --reqtype gz.msgs.Entity --reptype gz.msgs.Boolean \
  --timeout 3000 --req 'name: "standard_dock" type: MODEL'

# Poner una silla 1,5 m delante del punto de aparición del robot (x=0, y=1.5, mirando a +x)
gz service -s /world/small_house/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean \
  --timeout 3000 --req 'name: "ChairA_01_001" position: {x: 1.5, y: 1.5, z: 0}'

# Añadir una caja de 0,4 x 0,4 x 0,5 m en (x=0.8, y=1.5), como obstáculo
gz service -s /world/small_house/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean \
  --timeout 3000 --req 'sdf: "<sdf version=\"1.9\"><model name=\"caja\"><static>true</static><pose>0.8 1.5 0.25 0 0 0</pose><link name=\"link\"><collision name=\"c\"><geometry><box><size>0.4 0.4 0.5</size></box></geometry></collision><visual name=\"v\"><geometry><box><size>0.4 0.4 0.5</size></box></geometry></visual></link></model></sdf>"'

# Ver dónde está un objeto
gz model -m turtlebot4 -p
```

Los cambios se pierden al cerrar el simulador.

Ten en cuenta que el láser del robot está a unos 20 cm del suelo y solo ve lo
que corta ese plano: la base de carga y los objetos bajos (una pesa, por
ejemplo) pueden no verse, y el robot chocará con ellos aunque el ejemplo
esquive obstáculos.

### Moverlo sin navegación

El robot espera velocidades `geometry_msgs/TwistStamped` en `/cmd_vel`, igual
que el TurtleBot 4 real. También acepta `geometry_msgs/Twist` en
`/cmd_vel_unstamped`. Por ejemplo, para avanzar 3 segundos:

```bash
timeout 3 ros2 topic pub -r 10 /cmd_vel_unstamped geometry_msgs/msg/Twist "{linear: {x: 0.2}}"
```

### Ejemplos del curso

Los ejemplos de [README-examples.md](README-examples.md) se lanzan con el
simulador del TurtleBot 4 añadiendo `robot:=tb4_sim` (ver
[Elegir el robot en los ejemplos](README-examples.md#elegir-el-robot-en-los-ejemplos)).
Lanza el simulador en la casa (`pixi run sim-house`): es el mundo para el que
están preparados.

### Robot real

Con el TurtleBot 4 real no se lanza el simulador: el robot ya ejecuta sus
drivers. Prepara cada terminal con `tb4` en lugar de `tb4sim` (dominio 0) y
comprueba que lo ves:

```bash
ros2 topic list     # deben salir /scan, /odom, /hazard_detection...
```

En Jazzy, el robot real también espera `TwistStamped` en `/cmd_vel`. Los
ejemplos se lanzan con `robot:=tb4` en lugar de `robot:=tb4_sim` (ver
[README-examples.md](README-examples.md#elegir-el-robot-en-los-ejemplos)). Su
cámara no publica profundidad de fábrica: para los ejemplos 3D hay que
activarla (ver
[README-examples.md](README-examples.md#turtlebot-4-real-activar-la-profundidad)). Los
ajustes que necesitan los bump and go (topic del bumper, límites de la base
Create 3) están en [README-examples.md](README-examples.md#turtlebot-4-real).

## Kobuki (alternativa)

Si prefieres usar el Kobuki en lugar del TurtleBot 4 (su simulador o el robot
real), sigue [README-kobuki-pixi.md](README-kobuki-pixi.md) después de la
instalación normal.

## Reinstalar desde cero

Para repetir la instalación normal:

```bash
cd ~/rsocial
rm -rf src/thirdparty build install log
pixi install
pixi shell
cd src
vcs import < thirdparty-pixi.repos
cd ..
git -C src/thirdparty/nao_lola submodule update --init --recursive
pixi run build
```

Si también usas el Kobuki, repite después los pasos de
[README-kobuki-pixi.md](README-kobuki-pixi.md).
