FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
RUN sed -i \
      -e 's|http://archive.ubuntu.com/ubuntu|http://mirrors.aliyun.com/ubuntu|g' \
      -e 's|http://security.ubuntu.com/ubuntu|http://mirrors.aliyun.com/ubuntu|g' \
      /etc/apt/sources.list.d/ubuntu.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      qemu-system-arm \
      qemu-utils \
      libepoxy0 \
      libgtk-3-0t64 \
      libcairo2 \
      libgdk-pixbuf-2.0-0 \
      libx11-6 \
      libasound2t64 \
      alsa-utils \
      python3 \
      python3-aiohttp \
      gdb-multiarch \
      binutils-arm-none-eabi \
      ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/im6
EXPOSE 8765
CMD ["python3", "web/server.py"]

