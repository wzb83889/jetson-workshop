#!/usr/bin/env bash
# 只读检查，不提权、不改源、不升级、不输出IP或序列号。
set -u
run() {
  if command -v "$1" >/dev/null 2>&1; then
    "$@" || true
  else
    printf '未找到命令：%s\n' "$1"
  fi
}
printf 'UTC时间：'; date -u '+%Y-%m-%dT%H:%M:%SZ'
printf '架构：'; uname -m
printf '内核：'; uname -r
if [ -r /etc/os-release ]; then
  sed -n '/^PRETTY_NAME=/p' /etc/os-release
fi
if [ -r /etc/nv_tegra_release ]; then
  sed -n '1s/, GCID:.*//p' /etc/nv_tegra_release
fi
run dpkg-query -W -f='${Package}: ${Version}\n' nvidia-jetpack nvidia-l4t-core cuda-toolkit-13-2 tensorrt
run df -h /
run free -h
run systemctl --failed --no-pager
