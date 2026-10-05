# Base image: Ubuntu 24.04 LTS (required by ROS 2 Jazzy)
FROM ubuntu:24.04 AS system
ARG TARGETPLATFORM
LABEL maintainer="Jose Miguel Guerrero <josemiguel.guerrero@urjc.es>"

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

# 1. Update the OS
RUN apt update -q && \
    apt full-upgrade -y && \
    apt autoclean -y && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# 2. Install XFCE4 (desktop and icons)
RUN apt update -q && \
    apt install -y xfce4 xfce4-goodies xfce4-terminal xfdesktop4 && \
    apt autoclean -y && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# 3. System and network tools, video servers and D-Bus
RUN apt update -q && \
    apt install -y \
        xvfb x11vnc dbus-x11 x11-xserver-utils \
        tigervnc-standalone-server tigervnc-common \
        supervisor wget curl gosu git sudo python3-full python3-pip tini \
        build-essential vim bash-completion tzdata terminator locales lsb-release && \
    apt autoclean -y && \
    apt autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# 4. Locale
RUN locale-gen es_ES.UTF-8
ENV LANG=es_ES.UTF-8
ENV LANGUAGE=es_ES:es
ENV LC_ALL=es_ES.UTF-8

# 5. noVNC web desktop (vnc.html copied as index.html)
# websockify from apt (same 0.10.0 version): installing it with pip would pull NumPy 2
# into the system Python and break ROS 2 packages built against NumPy 1 (tf_transformations)
RUN git clone https://github.com/AtsushiSaito/noVNC.git -b add_clipboard_support /usr/lib/novnc && \
    apt update -q && apt install -y websockify && rm -rf /var/lib/apt/lists/* && \
    cp /usr/lib/novnc/vnc.html /usr/lib/novnc/index.html

RUN sed -i "s/UI.initSetting('resize', 'off');/UI.initSetting('resize', 'remote');/g" /usr/lib/novnc/app/ui.js

# 6. Firefox from the official Mozilla repository
RUN wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O /etc/apt/keyrings/packages.mozilla.org.asc && \
    echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" | tee -a /etc/apt/sources.list.d/mozilla-apt.list && \
    echo -e "Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1000" | tee /etc/apt/preferences.d/mozilla > /dev/null && \
    apt update -q && \
    apt install -y --allow-downgrades firefox && \
    rm -rf /var/lib/apt/lists/*
    
# 7. VSCodium
RUN wget https://gitlab.com/paulcarroty/vscodium-deb-rpm-repo/raw/master/pub.gpg -O /usr/share/keyrings/vscodium-archive-keyring.asc && \
    echo 'deb [ signed-by=/usr/share/keyrings/vscodium-archive-keyring.asc ] https://paulcarroty.gitlab.io/vscodium-deb-rpm-repo/debs vscodium main' | tee /etc/apt/sources.list.d/vscodium.list && \
    apt update -q && \
    apt install -y codium && \
    sed -i 's|/usr/share/codium/codium |/usr/share/codium/codium --no-sandbox --disable-gpu |g' /usr/share/applications/codium.desktop /usr/share/applications/codium-url-handler.desktop && \
    printf '%s\n' '#!/bin/sh' 'exec /usr/share/codium/bin/codium --no-sandbox --disable-gpu "$@"' > /usr/local/bin/codium && \
    chmod +x /usr/local/bin/codium && \
    rm -rf /var/lib/apt/lists/*

# 8. ROS 2 Jazzy Jalisco + Gazebo simulation (noble repository)
ENV ROS_DISTRO=jazzy
ARG INSTALL_PACKAGE=desktop

RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu noble main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null && \
    apt update -q && \
    apt install -y ros-${ROS_DISTRO}-${INSTALL_PACKAGE} \
    ros-${ROS_DISTRO}-ros-gz \
    python3-argcomplete \
    python3-colcon-common-extensions \
    python3-rosdep python3-vcstool

# 9. rsocial and Kobuki dependencies
RUN apt install -y \
    ros-dev-tools \
    libusb-1.0-0-dev libftdi1-dev libuvc-dev \
    libportaudio2 alsa-utils libasound2-plugins \
    ros-${ROS_DISTRO}-ament-cmake-clang-format \
    ros-${ROS_DISTRO}-ament-mypy \
    ros-${ROS_DISTRO}-camera-info-manager \
    ros-${ROS_DISTRO}-depth-image-proc \
    ros-${ROS_DISTRO}-depthai-ros \
    ros-${ROS_DISTRO}-diagnostic-updater \
    ros-${ROS_DISTRO}-ecl-build \
    ros-${ROS_DISTRO}-ecl-license \
    ros-${ROS_DISTRO}-image-publisher \
    ros-${ROS_DISTRO}-irobot-create-msgs \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-kobuki-ros-interfaces \
    ros-${ROS_DISTRO}-kobuki-velocity-smoother \
    ros-${ROS_DISTRO}-laser-filters \
    ros-${ROS_DISTRO}-magic-enum \
    ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-nav2-msgs \
    ros-${ROS_DISTRO}-navigation2 \
    ros-${ROS_DISTRO}-nao-lola-command-msgs \
    ros-${ROS_DISTRO}-nao-lola-sensor-msgs \
    ros-${ROS_DISTRO}-py-trees \
    ros-${ROS_DISTRO}-py-trees-ros \
    ros-${ROS_DISTRO}-slam-toolbox \
    ros-${ROS_DISTRO}-sophus \
    ros-${ROS_DISTRO}-tf-transformations && \
    rosdep init && \
    rosdep update

# 10. Audio through the host sound server (PipeWire or PulseAudio), when its socket is
#     mounted (see README-docker-install.md): ALSA clients (aplay, PortAudio) use it by default
RUN echo -e 'pcm.!default pulse\nctl.!default pulse' > /etc/asound.conf

# 11. D-Bus security setup and Ubuntu temporary directories
RUN dbus-uuidgen --ensure && \
    ln -sf /var/lib/dbus/machine-id /etc/machine-id && \
    mkdir -p /tmp/runtime-root && \
    chmod 700 /tmp/runtime-root

# 12. Student user with administrator permissions through sudo
RUN usermod --append --groups sudo ubuntu && \
    echo 'ubuntu:ubuntu' | chpasswd && \
    mkdir -p /tmp/runtime-ubuntu && \
    chown -R ubuntu:ubuntu /tmp/runtime-ubuntu && \
    chmod 700 /tmp/runtime-ubuntu

# 13. Clone rsocial with the same third-party packages and Kobuki as the native
#     installation (README.md) and build it in the student's home
RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    git clone --depth 1 https://github.com/rodperex/rsocial.git /home/ubuntu/rsocial && \
    cd /home/ubuntu/rsocial/src && \
    vcs import < thirdparty-native.repos && \
    vcs import < kobuki-native.repos && \
    cd /home/ubuntu/rsocial && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y \
        --skip-keys="gazebo gazebo_ros gazebo_plugins python3-torchvision-pip python3-ultralytics-pip" && \
    chown -R ubuntu:ubuntu /home/ubuntu/rsocial

# 14. Python environment shared by simple_hri and yolo_ros, with CPU-only PyTorch (the
#     container has no GPU). uv is not installed on purpose: without it, yolo_ros uses this
#     environment instead of creating its own one with CUDA PyTorch on every build
USER ubuntu
RUN cd /home/ubuntu/rsocial && \
    python3 -m venv --system-site-packages .venv && \
    source .venv/bin/activate && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    python3 -c "import tomllib; print('\n'.join(tomllib.load(open('src/thirdparty/yolo_ros/yolo_ros/pyproject.toml', 'rb'))['project']['dependencies']))" > /tmp/yolo_requirements.txt && \
    pip install --no-cache-dir colcon-common-extensions \
        -r src/thirdparty/simple_hri/simple_hri/requirements.txt \
        -r /tmp/yolo_requirements.txt && \
    rm /tmp/yolo_requirements.txt

# 15. Build the workspace with the Python of the environment
RUN cd /home/ubuntu/rsocial && \
    source /opt/ros/${ROS_DISTRO}/setup.bash && \
    source .venv/bin/activate && \
    python3 -m colcon build --symlink-install
USER root

# 16. Classroom convenience: open a terminal automatically when the desktop starts
RUN mkdir -p /etc/xdg/autostart && \
    echo -e '[Desktop Entry]\nType=Application\nExec=terminator\nHidden=false\nNoDisplay=false\nX-GNOME-Autostart-enabled=true\nName=TerminalInicio' > /etc/xdg/autostart/terminal.desktop

# 17. Supervisor configuration for XFCE4 (Full HD resolution)
RUN mkdir -p /etc/supervisor/conf.d
RUN echo -e '[supervisord]\nnodaemon=true\n\n[program:xvfb]\ncommand=Xvfb :1 -screen 0 1920x1080x24\nautorestart=true\n\n[program:x11vnc]\ncommand=x11vnc -forever -shared -nopw -display :1 -rfbport 5900 -listen 127.0.0.1\nautorestart=true\n\n[program:xfce]\nenvironment=DISPLAY=":1",HOME="/home/ubuntu",USER="ubuntu",XDG_RUNTIME_DIR="/tmp/runtime-ubuntu"\ncommand=dbus-launch --exit-with-session startxfce4\nautorestart=true\n\n[program:web]\ncommand=websockify --web=/usr/lib/novnc 0.0.0.0:6080 127.0.0.1:5900\nautorestart=true' > /etc/supervisor/conf.d/desktop.conf

RUN echo "source /opt/ros/jazzy/setup.bash" >> /etc/bash.bashrc
RUN echo "source /home/ubuntu/rsocial/.venv/bin/activate" >> /etc/bash.bashrc
RUN echo "if [ -f /home/ubuntu/rsocial/install/setup.bash ]; then source /home/ubuntu/rsocial/install/setup.bash; fi" >> /etc/bash.bashrc
RUN echo -e '[supervisord]\nnodaemon=true\nlogfile=/home/ubuntu/supervisord.log\npidfile=/home/ubuntu/supervisord.pid\nchildlogdir=/home/ubuntu\n\n[include]\nfiles=/etc/supervisor/conf.d/*.conf' > /home/ubuntu/supervisord.conf && \
    chown ubuntu:ubuntu /home/ubuntu/supervisord.conf

WORKDIR /home/ubuntu/rsocial
EXPOSE 6080

USER ubuntu

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/bin/supervisord", "-c", "/home/ubuntu/supervisord.conf"]