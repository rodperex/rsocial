# Instalación con Pixi

Esta guía instala ROS 2 Jazzy y el workspace `rsocial` dentro de Pixi. Los
comandos usan `~/rsocial` como ruta de ejemplo; puedes sustituirla por otra.

## Requisitos

Necesitas una distribución Linux de 64 bits (x86_64), `git`, `curl` y Pixi.
Funciona en cualquier versión de Ubuntu (se ha probado en Ubuntu 26.04), porque
Pixi instala ROS 2 Jazzy y sus dependencias dentro del workspace. No necesitas
instalar ROS 2 en el sistema ni ejecutar `source /opt/ros/jazzy/setup.bash`.

Instala Pixi si no está disponible:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
source "$HOME/.bashrc"
pixi --version
```

## Instalación normal

Esta es la opción por defecto. No incluye Kobuki ni Gazebo.

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

No uses `rosdep` con Pixi. Las dependencias están declaradas en `pixi.toml` y
se instalan con `pixi install`.

## Kobuki: simulador y robot real (opcional)

Esta variante añade el simulador Gazebo y los drivers del Kobuki real: la base
y el láser RPLIDAR (A2 o S2). Como cámara del robot real solo se admite la
OAK-D, incluida en `thirdparty-pixi.repos`. Las cámaras Astra y Xtion
necesitan la [instalación nativa](README.md#instalación-nativa), porque sus
drivers no compilan en Pixi.

Kobuki usa un entorno Pixi aparte, `kobuki`, definido en el mismo
`pixi.toml` (sección `[feature.kobuki.dependencies]`). Añade Gazebo, Nav2 y
las librerías de Kobuki sobre el entorno normal. Todos los comandos se
ejecutan desde la raíz del workspace añadiendo `-e kobuki`.

### 1. Importar Kobuki y sus terceros

```bash
cd ~/rsocial/src
vcs import < kobuki-pixi.repos
cd ..
```

### 2. Instalar el entorno del simulador

```bash
cd ~/rsocial
pixi install -e kobuki
```

### 3. Compilar y lanzar Gazebo

```bash
cd ~/rsocial
pixi run -e kobuki build
pixi shell -e kobuki
source install/setup.bash
ros2 launch kobuki simulation.launch.py
```

Con los repositorios de Kobuki importados, compila siempre con `-e kobuki`:
el entorno normal no tiene sus dependencias. Si cambias de entorno, ejecuta
antes `pixi run clean` para no mezclar compilaciones.

### 4. Usar el robot real

Los dispositivos USB del robot necesitan reglas udev que les den permisos y
nombres fijos (`/dev/kobuki`, `/dev/rplidar`). Se instalan una sola vez en el
sistema, fuera de Pixi (ver también el
[README de Kobuki](https://github.com/IntelligentRoboticsLabs/kobuki/tree/jazzy)):

```bash
cd ~/rsocial/src/thirdparty
sudo cp kobuki_ros/60-kobuki.rules rplidar_ros/scripts/rplidar.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Con el robot conectado, en lugar del simulador lanza sus drivers, indicando el
modelo de láser (`lidar_a2:=true` o `lidar_s2:=true`):

```bash
cd ~/rsocial
pixi shell -e kobuki
source install/setup.bash
ros2 launch kobuki kobuki.launch.py lidar_s2:=true
```

Para la cámara OAK-D, en otra terminal (las reglas udev de la cámara están en
[README-examples.md](README-examples.md#9-sensores-cámara-y-yolo)):

```bash
ros2 launch oak_d_camera camera.launch.py \
  use_disparity:=False use_lr_raw:=False use_pointcloud:=False
```

### Desinstalar Kobuki

```bash
cd ~/rsocial
pixi clean -e kobuki
```

Esto borra solo `.pixi/envs/kobuki`. Para volver al workspace normal, borra
también los repositorios importados con `kobuki-pixi.repos` y recompila con
`pixi run clean && pixi run build`.

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

Si también usas Kobuki, importa de nuevo `kobuki-pixi.repos` y ejecuta
`pixi install -e kobuki` y `pixi run -e kobuki build`.
