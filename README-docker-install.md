# Instalacion con Docker

Docker es una alternativa a la instalacion nativa y a Pixi. La imagen Jazzy
incluye ROS 2 Jazzy, `rsocial`, Kobuki y el entorno grafico noVNC.

## Requisitos

- Docker Engine.
- Permisos para ejecutar Docker sin `sudo`.
- Acceso a Internet durante la construccion.

## Construir la imagen Jazzy

Desde la raiz del repositorio:

```bash
docker build -f docker/jazzy/Dockerfile -t rsocial-jazzy .
```

## Ejecutar Jazzy

```bash
docker run -d --name rsocial-jazzy \
  -p 6080:6080 \
  rsocial-jazzy
```

Abre `http://localhost:6080/` en el navegador. Para entrar en una terminal:

```bash
docker exec -it rsocial-jazzy bash
```

El workspace esta en `~/ros2_ws` y ROS 2 se carga automaticamente.

## Recompilar

Dentro del contenedor:

```bash
cd ~/ros2_ws
colcon build --symlink-install
```

Si cambian las dependencias, resuelvelas con ROS 2 del sistema:

```bash
sudo apt update
rosdep update
sudo rosdep install --from-paths src --ignore-src -r -y \
  --skip-keys="ament_python rclpy_lifecycle"
colcon build --symlink-install
```

Docker usa ROS 2 del sistema, no Pixi. Por eso aqui si se utiliza `rosdep`.

## Lyrical

La imagen Lyrical no incluye Kobuki. Para construirla y ejecutarla:

```bash
docker build -f docker/lyrical/Dockerfile -t rsocial-lyrical .
docker run -d --name rsocial-lyrical \
  -p 6081:6080 \
  rsocial-lyrical
```

Abre `http://localhost:6081/`.

## Ciclo de vida

```bash
docker stop rsocial-jazzy
docker start rsocial-jazzy
docker rm rsocial-jazzy
docker image rm rsocial-jazzy
```

## Repositorios thirdparty

La imagen Docker usa la instalacion de ROS 2 del sistema. Para importar repositorios
manualmente, usa el manifiesto de la instalacion estandar:

```bash
cd ~/ros2_ws/src
vcs import < thirdparty.repos
```

No uses `thirdparty-pixi.repos` dentro de Docker. Para Pixi, consulta
[README-pixi-install.md](README-pixi-install.md).
