# Instalación con Docker

Docker es una alternativa a la [instalación nativa](README.md#instalación-nativa)
y a [Pixi](README-pixi-install.md). La imagen trae todo instalado y compilado,
con un escritorio Linux accesible desde el navegador.

## Qué incluye

La imagen contiene:

- Ubuntu 24.04 con ROS 2 Jazzy (`desktop`), Gazebo y Nav2.
- El workspace `~/rsocial` ya compilado, con los mismos paquetes que la
  [instalación nativa](README.md#instalación-nativa): los de
  `thirdparty-native.repos` (`simple_hri`, `yolo_ros`, cámaras, NAO) y los de
  `kobuki-native.repos` (Kobuki y su simulador).
- El entorno de Python `~/rsocial/.venv` con las dependencias de `simple_hri` y
  `yolo_ros` (PyTorch, Whisper, Transformers, Ultralytics...).
- Escritorio XFCE accesible por el navegador (noVNC), con Firefox, VSCodium y
  Terminator.

El contenedor no usa la GPU: PyTorch está instalado solo para CPU, así que
Whisper y YOLO van más despacio que en una instalación nativa con GPU. Por
defecto tampoco tiene acceso al micrófono ni a los altavoces del equipo (ver
[Micrófono y altavoces](#micrófono-y-altavoces)).

La imagen descarga `rsocial` de GitHub al construirse: los cambios que tengas
en tu copia local y no hayas subido no se incluyen (ver
[Trabajar con tu propio código](#trabajar-con-tu-propio-código)).

## Requisitos

- [Docker Engine](https://docs.docker.com/engine/install/) y permisos para
  usarlo sin `sudo` (usuario en el grupo `docker`).
- Unos 40 GB libres y acceso a Internet durante la construcción, que tarda
  bastante la primera vez. La imagen final ocupa unos 17 GB; el resto es caché
  de construcción, que puedes borrar después con `docker builder prune -a`.

## Construir y arrancar

Desde la raíz del repositorio:

```bash
docker build -f docker/jazzy/Dockerfile -t rsocial-jazzy .
docker run -d --name rsocial-jazzy -p 6080:6080 rsocial-jazzy
```

O, equivalente, con Docker Compose (además comparte el directorio
`docker/shared` del repositorio con `~/shared` en el contenedor):

```bash
docker compose -f docker/docker-compose.yaml up -d --build
```

## Usar el contenedor

Abre <http://localhost:6080/> en el navegador. El escritorio arranca con el
usuario `ubuntu` (contraseña `ubuntu`, que también sirve para `sudo`) y abre
una terminal automáticamente.

También puedes abrir una terminal desde el equipo:

```bash
docker exec -it rsocial-jazzy bash
```

ROS 2 y el workspace se cargan solos en cada terminal. Por ejemplo, lanza el
simulador (se ve en el escritorio del navegador) y, en otra terminal, un
ejemplo:

```bash
ros2 launch kobuki simulation.launch.py
ros2 launch square_motion square_move.launch.py
```

Dentro del contenedor Gazebo no tiene GPU y renderiza por software, así que la
simulación va bastante más lenta que en tiempo real. Para trabajar con fluidez
con el simulador es mejor la instalación nativa o Pixi.

## Micrófono y altavoces

Solo en equipos Linux con PipeWire o PulseAudio (lo habitual en Ubuntu). El
contenedor usa el servidor de sonido del equipo a través de su socket, así que
el sonido del equipo sigue funcionando a la vez. Arranca el contenedor con el
socket montado:

```bash
docker run -d --name rsocial-jazzy -p 6080:6080 \
  -v /run/user/$(id -u)/pulse/native:/run/pulse/native \
  -e PULSE_SERVER=unix:/run/pulse/native \
  rsocial-jazzy
```

O con Docker Compose:

```bash
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.audio.yaml up -d --build
```

Si el contenedor ya existía, bórralo antes (`docker rm -f rsocial-jazzy`): el
socket solo se puede montar al crearlo. Para comprobarlo, dentro del
contenedor:

```bash
aplay /usr/share/sounds/alsa/Front_Center.wav   # debe sonar en el equipo
python3 -c "import sounddevice as sd; print(sd.query_devices())"
```

Limitaciones:

- El sonido sale por los altavoces del equipo que ejecuta Docker, no por el
  navegador: noVNC no transmite audio.
- No funciona con Docker Desktop en macOS o Windows.
- Con PulseAudio (no PipeWire) puede hacer falta montar también la cookie de
  autenticación: `-v ~/.config/pulse/cookie:/home/ubuntu/.config/pulse/cookie:ro`.

## Recompilar

Dentro del contenedor, tras modificar el código:

```bash
cd ~/rsocial
colcon build --symlink-install
```

Si cambian las dependencias de los paquetes, instálalas antes con `rosdep`
(Docker usa ROS 2 del sistema, no Pixi):

```bash
cd ~/rsocial
sudo apt update
rosdep update
rosdep install --from-paths src --ignore-src -r -y \
  --skip-keys="gazebo gazebo_ros gazebo_plugins python3-torchvision-pip python3-ultralytics-pip"
colcon build --symlink-install
```

El significado de cada clave de `--skip-keys` está en el
[README](README.md#3-dependencias-del-sistema).

## Trabajar con tu propio código

Para usar dentro del contenedor tu copia local del repositorio (aquí en
`~/rsocial`), copia su código fuente sobre el de la imagen y recompila. El
comando copia solo tus ficheros, sin compilaciones, entornos ni paquetes de
terceros; los de la imagen se conservan:

```bash
tar -C ~/rsocial --exclude=.git --exclude=.pixi --exclude=.venv --exclude=build \
  --exclude=install --exclude=log --exclude=src/thirdparty --exclude=src/kobuki \
  -cf - . | docker exec -i rsocial-jazzy tar -xf - -C /home/ubuntu/rsocial
docker exec rsocial-jazzy bash -ic "cd ~/rsocial && colcon build --symlink-install"
```

Los ficheros que hayas borrado en tu copia siguen en el contenedor. Para
empezar desde cero, lo más sencillo es crear un contenedor nuevo a partir de
la imagen (ver [Parar, reanudar y borrar](#parar-reanudar-y-borrar)).

## Parar, reanudar y borrar

```bash
docker stop rsocial-jazzy      # parar (se conservan los cambios del contenedor)
docker start rsocial-jazzy     # reanudar
docker rm rsocial-jazzy        # borrar el contenedor (se pierden sus cambios)
docker image rm rsocial-jazzy  # borrar la imagen
```

Con Docker Compose: `docker compose -f docker/docker-compose.yaml stop`,
`start` y `down` (borra el contenedor).
