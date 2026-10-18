#!/usr/bin/env bash
# 按需启动，只监听本机；使用现有llama.cpp，不下载模型。
set -euo pipefail
if [ "${1:-}" = "--help" ] || [ "$#" -lt 1 ]; then
  printf '用法：bash scripts/start_llm.sh MODEL.gguf [llama-server附加参数]\n'
  exit 0
fi
model_path=$1
shift
server_path=${LLAMA_SERVER:-"$HOME/llama.cpp/build/bin/llama-server"}
[ -x "$server_path" ] || { printf '未找到llama-server：%s\n' "$server_path" >&2; exit 1; }
[ -f "$model_path" ] || { printf '模型不存在：%s\n' "$model_path" >&2; exit 1; }
# 附加参数不可更改监听范围或端口。
for arg in "$@"; do
  case "$arg" in
    --host|--host=*|--port|--port=*) printf '此入口固定回环8080，请通过SSH隧道访问。\n' >&2; exit 1;;
  esac
done
exec "$server_path" -m "$model_path" -ngl 99 -c 2048 -np 1 --host 127.0.0.1 --port 8080 --no-ui "$@"
