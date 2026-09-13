# rsocial

Workspace docente de ROS 2 con ejemplos de nodos, sensores, navegación,
máquinas de estados, árboles de comportamiento e interacción humano-robot.

## Instalación

Elige una de estas instalaciones:

- **Nativa:** Ubuntu 24.04 con ROS 2 Jazzy. Es la opción descrita en este
	README.
- **Pixi:** ROS 2 Jazzy aislado en Pixi. Sigue [README-pixi-install.md](README-pixi-install.md).
- **Docker:** entorno preparado en un contenedor. Sigue [README-docker-install.md](README-docker-install.md).

Los comandos de este README usan `~/rsocial` como ruta de ejemplo. Puedes
usar otra ubicación sustituyendo esa ruta en los comandos.

La instalación nativa usa `src/thirdparty.repos`; la instalación Pixi usa
`src/thirdparty-pixi.repos` y no deben mezclarse.

## Requisitos para la instalación nativa

- Ubuntu 24.04 con ROS 2 Jazzy instalado.
- `git`, `python3`, `python3-rosdep`, `python3-vcstool`, `python3-colcon-common-extensions` y [`uv`](https://docs.astral.sh/uv/).
- Para movimiento y navegación: un robot Kobuki o una simulación que publique
	los topics y TF necesarios. El simulador recomendado es
	[Kobuki](https://github.com/IntelligentRoboticsLabs/kobuki). Sigue su README
	para instalarlo. La configuración USB/udev del robot real siempre se hace en
	el sistema anfitrión.

En cada terminal desde la que se ejecute ROS hay que cargar ROS y este workspace:

```bash
source /opt/ros/jazzy/setup.bash
source ~/rsocial/install/setup.bash
```

## Instalación nativa desde cero

```bash
mkdir -p ~/rsocial/src
git clone https://github.com/rodperex/rsocial.git ~/rsocial/src/rsocial
cd ~/rsocial/src
vcs import < rsocial/src/thirdparty.repos
cd ~/rsocial

# Cargar ROS antes de continuar.
source /opt/ros/jazzy/setup.bash

curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"

rosdep update
rosdep install --from-paths src --ignore-src -r -y \
	--skip-keys="ament_python rclpy_lifecycle"

uv venv --seed .venv
source .venv/bin/activate

# Dependencias de audio de sound_play.
sudo apt update && sudo apt install -y libportaudio2 gstreamer1.0-tools gstreamer1.0-alsa gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly python3-gi python3-gst-1.0

python3 -m pip install colcon-common-extensions
python3 -m pip install -r src/thirdparty/simple_hri/simple_hri/requirements.txt
python3 -m colcon build --symlink-install
source install/setup.bash
```

Activa `.venv` antes de compilar y en cada terminal desde la que ejecutes
nodos ROS. `colcon-common-extensions` se instala dentro del entorno virtual
para que `python3 -m colcon` use el mismo intérprete que `simple_hri`.

En cada terminal que ejecute nodos hay que activar también `.venv` después de
cargar ROS y el workspace:

```bash
source /opt/ros/jazzy/setup.bash
source ~/rsocial/.venv/bin/activate
source ~/rsocial/install/setup.bash
```

`yolo_ros` no usa `requirements.txt` en su versión actual. Sus dependencias
están declaradas en `yolo_ros/pyproject.toml` y `colcon build` ejecuta `uv sync`
automáticamente para crear o actualizar `src/thirdparty/yolo_ros/yolo_ros/.venv`.
Si se quiere preparar ese entorno antes de compilar, se puede ejecutar:

```bash
cd src/thirdparty/yolo_ros/yolo_ros
uv venv --python python3 --system-site-packages .venv
uv sync --no-install-project --no-dev
cd ../../../..
```

La restricción `numpy<2` de `yolo_ros` es intencionada: evita
incompatibilidades entre `cv_bridge`/ROS 2 Jazzy y NumPy 2. No se debe
sustituir por la versión global de NumPy sin comprobar antes que la cámara y
la conversión de imágenes siguen funcionando.

### Portabilidad de `simple_hri`

`simple_hri` incluye servicios locales y servicios que requieren credenciales.
El entorno virtual aísla sus dependencias Python de las versiones instaladas
en el sistema, incluido el wheel de WebRTC VAD. Los launchers
locales no necesitan claves, pero sí descargan modelos la primera
vez y requieren micrófono y salida de audio accesibles desde el sistema:

El extractor local usa `google/flan-t5-small` con la tarea
`text2text-generation`. El requirements fija una versión compatible de
`transformers` y de NumPy para que todos los servicios funcionen dentro del
entorno virtual y declara una versión de Numba que no hereda una copia
incompatible del sistema.

```bash
ros2 launch simple_hri local_simple_hri.launch.py
```

Si el nodo no arranca fuera del equipo original, comprueba primero el
dispositivo de audio y las importaciones desde la misma terminal donde se
cargaron ROS y el entorno virtual:

```bash
python3 -c "import numpy, torch, transformers, whisper, sounddevice, webrtcvad; print('Dependencias Python OK')"
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

En sistemas sin micrófono o servidor de audio, se pueden probar los servicios
de texto, pero los servicios STT/TTS locales no podrán grabar o reproducir
audio hasta configurar ALSA/PulseAudio o el equivalente del sistema.

## Ejemplos y uso

Consulta [README-examples.md](README-examples.md) para los comandos de nodos,
sensores, navegación, árboles de comportamiento e interacción humano-robot.

## Docker

Para trabajar con el entorno Docker, sigue la guía específica [README-docker-install.md](README-docker-install.md). La documentación histórica y las variantes de la imagen siguen disponibles en [docker/howto.md](docker/howto.md). Ahí se explica cómo:

- construir y arrancar las imágenes Jazzy y Lyrical;
- acceder al escritorio ROS 2 desde el navegador;
- usar el workspace que ya viene compilado;
- clonar el workspace desde cero o copiar tus repositorios al contenedor;
- recompilar y detener/eliminar el contenedor.

La guía Docker es la referencia para todo lo relacionado con contenedores; el resto de este README describe los ejemplos y sus comandos ROS 2.

## Licencia

[Apache License 2.0](LICENSE)