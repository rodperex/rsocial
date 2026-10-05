# Kobuki con Pixi

El robot por defecto de `rsocial` es el TurtleBot 4 (ver
[README-pixi-install.md](README-pixi-install.md#turtlebot-4-simulador-y-navegación)).
Esta guía es la alternativa si prefieres trabajar con el Kobuki: su simulador
y el robot real.

Parte de la [instalación normal con Pixi](README-pixi-install.md#instalación-normal)
ya hecha. El Kobuki usa un entorno Pixi aparte, `kobuki`, definido en el mismo
`pixi.toml` (sección `[feature.kobuki.dependencies]`), que añade sobre el
normal su simulador y los drivers del robot real: la base y el láser RPLIDAR
(A2 o S2). Todos los comandos se ejecutan desde la raíz del workspace añadiendo
`-e kobuki`.

Como cámara del robot real solo se admite la OAK-D, incluida en
`thirdparty-pixi.repos`. Las cámaras Astra y Xtion necesitan la
[instalación nativa](README.md#instalación-nativa), porque sus drivers no
compilan en Pixi.

## 1. Instalar el entorno del simulador

```bash
cd ~/rsocial
pixi install -e kobuki
```

## 2. Importar Kobuki y sus terceros

Desde la raíz del workspace, activa la shell de Pixi del entorno `kobuki`
antes de importar los repositorios:

```bash
cd ~/rsocial
pixi shell -e kobuki
cd ~/rsocial/src
vcs import < kobuki-pixi.repos
cd ..
```

## 3. Compilar y lanzar Gazebo

Si ya habías compilado con el entorno normal (`pixi run build`), ejecuta
antes `pixi run clean` para no mezclar compilaciones de los dos entornos.

Desde la raíz del workspace, en la misma shell:

```bash
cd ~/rsocial
pixi run -e kobuki build
source install/setup.bash
ros2 launch kobuki simulation.launch.py
```

Con los repositorios de Kobuki importados, compila y abre la shell siempre con
`-e kobuki`: el entorno normal no tiene sus dependencias. En cada terminal
nueva:

```bash
cd ~/rsocial
pixi shell -e kobuki
source install/setup.bash
```

El `source` va siempre después de `pixi shell -e kobuki`. Sin él, Gazebo no
encuentra los modelos del mundo y termina enseguida (`process has died ...
exit code 255`).

## 4. Usar el robot real

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

## Desinstalar Kobuki

```bash
cd ~/rsocial
pixi clean -e kobuki
```

Esto borra solo `.pixi/envs/kobuki`. Para volver al workspace normal, borra
también los repositorios importados con `kobuki-pixi.repos` y recompila con
`pixi run clean && pixi run build`.
