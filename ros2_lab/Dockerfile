# Image ROS2 Humble pour le TP "Sniffing and Analysing a ROS2 Robot Network"
FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-humble-demo-nodes-py \
        python3-pip python3-numpy python3-matplotlib \
        tcpdump iproute2 iputils-ping nano \
    && pip3 install --no-cache-dir scapy \
    && rm -rf /var/lib/apt/lists/*

# ROS2 disponible dans tout shell interactif (docker exec -it ... bash)
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

WORKDIR /lab
COPY lab_nodes/ /lab/lab_nodes/
