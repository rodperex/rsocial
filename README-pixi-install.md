# Instalacion con Pixi

Esta guia instala ROS 2 Jazzy y el workspace `rsocial` dentro de Pixi. Los
comandos usan `~/rsocial` como ruta de ejemplo; puedes sustituirla por otra.

## Requisitos

Necesitas Ubuntu 24.04, `git`, `curl` y Pixi. No necesitas instalar ROS 2 en
el sistema ni ejecutar `source /opt/ros/jazzy/setup.bash`.

Instala Pixi si no esta disponible:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
source "$HOME/.bashrc"
pixi --version
```

## Instalacion normal

Esta es la opcion recomendada. No incluye Kobuki ni Gazebo.

### 1. Clonar e instalar el entorno

```bash
mkdir -p ~/rsocial
cd ~/rsocial
git clone https://github.com/rodperex/rsocial.git .
pixi install
```

### 2. Importar los repositorios

Desde la raiz del workspace, activa la shell de Pixi antes de importar los
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
`vcs import < thirdparty.repos` en este flujo.

### 3. Compilar

Desde la raiz del workspace:

```bash
cd ~/rsocial
pixi run build
```

La tarea crea automaticamente el `COLCON_IGNORE` del paquete legacy
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

No uses `rosdep` con Pixi. Las dependencias estan declaradas en `pixi.toml` y
se instalan con `pixi install`.

## Kobuki/Gazebo opcional

Esta variante es solo para simulacion con Gazebo. No permite usar el Kobuki
real desde Pixi. Para el robot real, sigue el README de Kobuki e instala sus
drivers, librerias del sistema y reglas udev fuera de Pixi.

### 1. Importar Kobuki y sus terceros

```bash
cd ~/rsocial/src
vcs import < kobuki-pixi.repos
```

### 2. Instalar el entorno del simulador

```bash
cd ~/rsocial/kobuki-pixi
pixi install
```

El manifiesto y el lockfile de esta variante son:

```text
kobuki-pixi/pixi.toml
kobuki-pixi/pixi.lock
```

### 3. Compilar y lanzar Gazebo

Desde `kobuki-pixi/`:

```bash
pixi run build
source ../install/setup.bash
ros2 launch kobuki simulation.launch.py
```

Para abrir una shell en la raiz del workspace:

```bash
pixi run shell
```

Despues de usar `pixi run shell`, vuelve a `kobuki-pixi/` para ejecutar tareas
de esa variante:

```bash
cd kobuki-pixi
pixi run build
```

## Reinstalar desde cero

Para repetir la instalacion normal:

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

Si tambien usas Kobuki, importa de nuevo `kobuki-pixi.repos` y ejecuta
`pixi install` y `pixi run build` desde `kobuki-pixi/`.
