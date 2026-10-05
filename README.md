# rsocial

Workspace docente de ROS 2 Jazzy con ejemplos de nodos, comunicaciones, TF,
sensores, máquinas de estados, árboles de comportamiento, navegación e
interacción humano-robot. Los ejemplos y cómo lanzarlos están en
[README-examples.md](README-examples.md).

## Instalación

Hay tres formas de instalar el workspace. Elige una y no las mezcles en el
mismo directorio:

| Opción | Cuándo usarla | Guía |
| --- | --- | --- |
| Nativa | Ubuntu 24.04 con ROS 2 Jazzy instalado en el sistema. Necesaria para usar el Kobuki real con cámara Astra o Xtion. | Este README |
| Pixi | Cualquier distribución Linux de 64 bits (x86_64), sin instalar ROS 2 en el sistema: todo queda aislado en el directorio del workspace. Incluye el simulador y la navegación del TurtleBot 4. | [README-pixi-install.md](README-pixi-install.md) |
| Docker | Entorno ya preparado en un contenedor, con escritorio en el navegador. | [README-docker-install.md](README-docker-install.md) |

Los comandos usan `~/rsocial` como directorio del workspace; puedes usar otra
sustituyendo esa ruta.

## Instalación nativa

### Requisitos

- Ubuntu 24.04 con [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
  (variante `desktop`).
- Unos 20 GB libres: los modelos de voz y visión usan PyTorch.
- Opcional, para ejecutar YOLO y Whisper en la GPU: tarjeta NVIDIA con driver
  580 o posterior (`nvidia-smi` lo muestra). Sin ella funcionan en la CPU,
  más despacio.

### 1. Herramientas

```bash
sudo apt update
sudo apt install -y git curl python3-rosdep python3-vcstool python3-colcon-common-extensions
[ -e /etc/ros/rosdep/sources.list.d/20-default.list ] || sudo rosdep init  # solo la primera vez
rosdep update
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
```

[`uv`](https://docs.astral.sh/uv/) gestiona los entornos virtuales de Python.
`yolo_ros` también lo usa al compilar para crear su propio entorno.

### 2. Descargar el código

El repositorio es la raíz del workspace. Los paquetes de terceros se
descargan con `vcs` a partir de los manifiestos `.repos` de `src/`:

```bash
git clone https://github.com/rodperex/rsocial.git ~/rsocial
cd ~/rsocial/src
vcs import < thirdparty-native.repos
vcs import < kobuki-native.repos
```

Si algún `vcs import` falla por la red, vuelve a ejecutarlo.

| Manifiesto | Contenido | Instalación |
| --- | --- | --- |
| `thirdparty-native.repos` | Paquetes que usan los ejemplos: `simple_hri`, `yolo_ros`, cámaras, NAO... | Nativa |
| `kobuki-native.repos` | Kobuki (robot y simulador) y sus drivers de láser y cámara | Nativa |
| `thirdparty-pixi.repos` | Lo mismo que `thirdparty-native.repos`, adaptado a Pixi | Pixi |
| `kobuki-pixi.repos` | Kobuki (simulador y robot real con láser RPLIDAR), adaptado a Pixi | Pixi |

Todos descargan en `src/kobuki` y `src/thirdparty`, que Git ignora. No mezcles
los manifiestos de las dos instalaciones en el mismo workspace.

### 3. Dependencias del sistema

```bash
cd ~/rsocial
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y \
  --skip-keys="gazebo gazebo_ros gazebo_plugins python3-torchvision-pip python3-ultralytics-pip"
sudo apt install -y libusb-1.0-0-dev libftdi1-dev libuvc-dev \
  libportaudio2 alsa-utils
```

- `rosdep` instala las dependencias que declaran los `package.xml` de los
  paquetes.
- `sudo apt install` instala lo que ningún paquete declara: las librerías USB
  del Kobuki, PortAudio (para grabar audio) y `alsa-utils` (`aplay`, para
  reproducirlo).
- `--skip-keys` indica a `rosdep` qué dependencias no debe intentar instalar:

  | Clave | Quién la declara | Por qué se omite |
  | --- | --- | --- |
  | `gazebo`, `gazebo_ros` y `gazebo_plugins` | `aws-robomaker-small-house-world` | Son de Gazebo clásico, que no existe en Jazzy; el mundo usa el Gazebo actual (`ros_gz_sim`), que sí se instala |
  | `python3-torchvision-pip` y `python3-ultralytics-pip` | `yolo_ros` | Son dependencias Python que `yolo_ros` instala en su propio entorno al compilar |

### 4. Entorno virtual de Python

Las dependencias Python de la interacción humano-robot (PyTorch, Whisper,
Transformers...) se instalan en un entorno virtual para no interferir con las
del sistema:

```bash
cd ~/rsocial
uv venv --python /usr/bin/python3 --system-site-packages --seed .venv
source .venv/bin/activate
python3 -m pip install colcon-common-extensions \
  -r src/thirdparty/simple_hri/simple_hri/requirements.txt
```

- `--python /usr/bin/python3` usa el Python del sistema, el mismo con el que
  está compilado ROS 2.
- `--system-site-packages` permite ver los paquetes Python que instala `apt`
  (por ejemplo, los que acaba de instalar `rosdep`).
- `colcon` se instala dentro del entorno para que los nodos compilados usen
  su Python y encuentren sus dependencias.

### 5. Compilar

```bash
cd ~/rsocial
source /opt/ros/jazzy/setup.bash
source .venv/bin/activate
python3 -m colcon build --symlink-install
```

La primera compilación tarda un rato: `yolo_ros` crea su propio entorno
(`src/thirdparty/yolo_ros/yolo_ros/.venv`) y descarga sus dependencias. Si el
equipo se queda sin memoria, compila con `--parallel-workers 1`.

### 6. Usar el workspace

En cada terminal nueva, carga ROS 2, el entorno virtual y el workspace, en este
orden:

```bash
source /opt/ros/jazzy/setup.bash
source ~/rsocial/.venv/bin/activate
source ~/rsocial/install/setup.bash
```

Para no repetirlo, puedes añadir esas tres líneas al final de `~/.bashrc`.
Comprueba que todo funciona con el simulador:

```bash
ros2 launch kobuki simulation.launch.py
```

### Kobuki real

Para conectar el Kobuki, su láser o su cámara por USB hacen falta reglas udev
que den permisos a los dispositivos (una sola vez por equipo):

```bash
cd ~/rsocial/src/thirdparty
sudo cp kobuki_ros/60-kobuki.rules rplidar_ros/scripts/rplidar.rules \
  ros_astra_camera/astra_camera/scripts/56-orbbec-usb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Después, en lugar del simulador: `ros2 launch kobuki kobuki.launch.py` (ver
las opciones de láser y cámara en `src/kobuki/README.md`).

## Varios equipos en la misma red

ROS 2 descubre automáticamente los nodos de otros equipos de la red. En un laboratorio eso hace que los robots y simuladores de distintas personas se mezclen. Para
evitarlo, cada persona puede limitar ROS 2 a su propio equipo, o usar un
dominio distinto (un número entre 1 y 101). Añade una de estas líneas a
`~/.bashrc`:

```bash
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST  # solo este equipo
export ROS_DOMAIN_ID=42                         # o un número distinto por persona
```

Para comunicarse con el robot real desde otro equipo, ambos deben tener el
mismo `ROS_DOMAIN_ID` y no usar `LOCALHOST`.

## Interacción humano-robot

Los ejemplos de interacción usan
[`simple_hri`](https://github.com/rodperex/simple_hri), que ofrece
reconocimiento de voz, síntesis de voz y extracción de información con modelos
de lenguaje. Puede usar modelos locales o servicios en la nube (ver
[README-examples.md](README-examples.md#12-interacción-humano-robot)). Los
modelos locales se descargan la primera vez que se lanzan, así que esa vez
necesitan Internet.

Hacen falta micrófono y altavoces accesibles desde el sistema. Si no funciona,
comprueba los dispositivos de audio y las dependencias desde una terminal con
el workspace cargado:

```bash
python3 -c "import sounddevice as sd; print(sd.query_devices())"
python3 -c "import torch, whisper, transformers; print('OK, GPU:', torch.cuda.is_available())"
```

## Actualizar el workspace

```bash
cd ~/rsocial
git pull
vcs pull src/thirdparty src/kobuki
source /opt/ros/jazzy/setup.bash
source .venv/bin/activate
python3 -m colcon build --symlink-install
```

Si tras actualizar la compilación falla por restos antiguos, borra
`build install log` y vuelve a compilar.

## Licencia

Copyright 2026 Rodrigo Pérez-Rodríguez. Distribuido bajo la
[Apache License 2.0](LICENSE) (ver también [NOTICE](NOTICE)).
