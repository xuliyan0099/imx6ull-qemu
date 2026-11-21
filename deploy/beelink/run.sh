#!/usr/bin/env bash
set -euo pipefail

project="${IM6_PROJECT_DIR:-/vol1/im6-qemu}"
image="${IM6_DOCKER_IMAGE:-im6-qemu-runtime:latest}"
container="${IM6_CONTAINER_NAME:-im6-qemu}"
port="${IM6_WEB_PORT:-8765}"

if [ ! -x "$project/bin/qemu-system-arm-official-linux" ]; then
  echo "缺少 $project/bin/qemu-system-arm-official-linux" >&2
  exit 1
fi
if [ ! -f "$project/web/server.py" ]; then
  echo "缺少 $project/web/server.py" >&2
  exit 1
fi

hosts="${IM6_ALLOWED_HOSTS:-}"
if [ -z "$hosts" ]; then
  hosts="localhost:${port},127.0.0.1:${port},beelink:${port}"
  for ip in $(hostname -I); do
    hosts="${hosts},${ip}:${port}"
  done
fi

if [ "$(id -u)" -eq 0 ]; then
  docker_cmd=(docker)
else
  docker_cmd=(sudo docker)
fi

audio_backend="${IM6_AUDIO_BACKEND:-auto}"
audio_device="${IM6_AUDIO_DEVICE:-default}"
audio_run=()
if [ "$audio_backend" = "auto" ]; then
  if [ -e /dev/snd ]; then audio_backend=alsa; else audio_backend=none; fi
fi
if [ -e /dev/snd ]; then
  audio_run+=(--device /dev/snd)
elif [ "$audio_backend" = "alsa" ]; then
  echo "未找到 /dev/snd，音频后端退化为 none" >&2
  audio_backend=none
fi

if [ "${IM6_REBUILD:-0}" = "1" ] || ! "${docker_cmd[@]}" image inspect "$image" >/dev/null 2>&1; then
  echo "构建容器镜像 $image"
  "${docker_cmd[@]}" build --network=host -t "$image" "$project/deploy/beelink"
else
  echo "复用已有镜像 $image（IM6_REBUILD=1 可强制重建）"
fi

echo "重建容器 $container"
"${docker_cmd[@]}" rm -f "$container" >/dev/null 2>&1 || true
"${docker_cmd[@]}" run -d \
  --name "$container" \
  --restart unless-stopped \
  -p "0.0.0.0:${port}:${port}" \
  -v "$project:/opt/im6" \
  "${audio_run[@]}" \
  -e "IM6_BIND_HOST=0.0.0.0" \
  -e "IM6_ALLOWED_HOSTS=$hosts" \
  -e "IM6_WEB_PORT=$port" \
  -e "IM6_VNC_DISPLAY=77" \
  -e "IM6_AUDIO_BACKEND=$audio_backend" \
  -e "IM6_AUDIO_DEVICE=$audio_device" \
  -e "IM6_AUDIO_FILE=/opt/im6/runs/audio.wav" \
  -e "IM6_IMAGE_DIR=/opt/im6/images" \
  -e "IM6_FREERTOS_DIR=/opt/im6/freertos" \
  -e "PYTHONPATH=/opt/im6/web/deps" \
  "$image"

echo "等待服务"
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${port}/version" >/tmp/im6-version.json 2>/dev/null; then
    cat /tmp/im6-version.json
    echo
    echo "打开 http://<beelink-ip>:${port}/"
    exit 0
  fi
  sleep 1
done

echo "服务没有在 60 秒内就绪，查看日志：" >&2
"${docker_cmd[@]}" logs --tail 60 "$container" >&2
exit 1

