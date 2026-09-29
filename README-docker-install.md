# Instalación con Docker

Docker es una alternativa a la [instalación nativa](README.md#instalación-nativa)
y a [Pixi](README-pixi-install.md). La imagen trae todo instalado y compilado,
con un escritorio Linux accesible desde el navegador.

## Qué incluye

La imagen **Jazzy** (la del curso) contiene:

- Ubuntu 24.04 con ROS 2 Jazzy (`desktop`), Gazebo y Nav2.
- El workspace `~/ros2_ws` con `rsocial` y el simulador del Kobuki, ya
  compilados.
- Escritorio XFCE accesible por el navegador (noVNC), con Firefox, VSCodium y
  Terminator.

Con ella funcionan los ejemplos de los bloques 1 a 8 y 11 de
[README-examples.md](README-examples.md). **No incluye** los paquetes de
`src/thirdparty-native.repos` (`simple_hri`, `yolo_ros`, cámara OAK-D, NAO), así que
los ejemplos de cámara y YOLO (bloque 9), VFF (bloque 10) e interacción
humano-robot (bloque 12) necesitan la instalación nativa o Pixi. El contenedor
tampoco tiene acceso a la GPU, al micrófono ni a los altavoces del equipo.

La imagen descarga `rsocial` de GitHub al construirse: los cambios que tengas
en tu copia local y no hayas subido no se incluyen (ver
[Trabajar con tu propio código](#trabajar-con-tu-propio-código)).

## Requisitos

- [Docker Engine](https://docs.docker.com/engine/install/) y permisos para
  usarlo sin `sudo` (usuario en el grupo `docker`).
- Unos 15 GB libres y acceso a Internet durante la construcción, que tarda
  bastante la primera vez.

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
ros2 run square_motion square_move
```

Dentro del contenedor Gazebo no tiene GPU y renderiza por software, así que la
simulación va bastante más lenta que en tiempo real. Para trabajar con fluidez
con el simulador es mejor la instalación nativa o Pixi.

## Recompilar

Dentro del contenedor, tras modificar el código:

```bash
cd ~/ros2_ws
colcon build --symlink-install
```

Si cambian las dependencias de los paquetes, instálalas antes con `rosdep`
(Docker usa ROS 2 del sistema, no Pixi):

```bash
cd ~/ros2_ws
sudo apt update
rosdep update
rosdep install --from-paths src --ignore-src -r -y --skip-keys="ament_python rclpy_lifecycle gazebo_plugins"
colcon build --symlink-install
```

## Trabajar con tu propio código

Para usar dentro del contenedor tu copia local del repositorio (aquí en
`~/rsocial`), sustituye con ella la de la imagen y recompila. El comando copia
solo el código fuente, sin compilaciones ni entornos locales:

```bash
docker exec rsocial-jazzy bash -c "rm -rf ~/ros2_ws/src/rsocial && mkdir ~/ros2_ws/src/rsocial"
tar -C ~/rsocial --exclude=.git --exclude=.pixi --exclude=.venv --exclude=build \
  --exclude=install --exclude=log --exclude=src/thirdparty --exclude=src/kobuki \
  -cf - . | docker exec -i rsocial-jazzy tar -xf - -C /home/ubuntu/ros2_ws/src/rsocial
docker exec rsocial-jazzy bash -ic "cd ~/ros2_ws && colcon build --symlink-install"
```

Para empezar desde cero dentro del contenedor, vuelve a clonar los
repositorios:

```bash
cd ~/ros2_ws
rm -rf src build install log
mkdir src && cd src
git clone https://github.com/rodperex/rsocial.git
git clone -b jazzy https://github.com/IntelligentRoboticsLabs/kobuki.git
vcs import < kobuki/thirdparty.repos
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y --skip-keys="ament_python rclpy_lifecycle gazebo_plugins"
colcon build --symlink-install
```

## Parar, reanudar y borrar

```bash
docker stop rsocial-jazzy      # parar (se conservan los cambios del contenedor)
docker start rsocial-jazzy     # reanudar
docker rm rsocial-jazzy        # borrar el contenedor (se pierden sus cambios)
docker image rm rsocial-jazzy  # borrar la imagen
```

Con Docker Compose: `docker compose -f docker/docker-compose.yaml stop`,
`start` y `down` (borra el contenedor).

## Imagen Lyrical (experimental)

`docker/lyrical/Dockerfile` construye una imagen equivalente con Ubuntu 26.04
y ROS 2 Lyrical. Todavía no incluye el Kobuki, porque no está disponible para
esa versión, así que solo sirven los ejemplos que no usan simulador (bloques 1
a 3 de [README-examples.md](README-examples.md)).

```bash
docker build -f docker/lyrical/Dockerfile -t rsocial-lyrical .
docker run -d --name rsocial-lyrical -p 6081:6080 rsocial-lyrical
```

Se abre en <http://localhost:6081/>.
