#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
model="$(python3 -c 'import agent; print(agent.CONFIG["model"])')"
mkdir -p .runtime
runtime="$(cd .runtime && pwd)"
mkdir -p "$runtime/ollama" "$runtime/models"
cd "$runtime"
if [ ! -x ollama/bin/ollama ]; then
    if [ ! -x zstd-local/usr/bin/zstd ]; then
        apt download zstd
        dpkg-deb -x zstd_*.deb zstd-local
    fi
    curl -fL --retry 3 --connect-timeout 20 -C - -o ollama-linux-amd64.tar.zst https://ollama.com/download/ollama-linux-amd64.tar.zst
    tar --use-compress-program="$runtime/zstd-local/usr/bin/zstd" -xf ollama-linux-amd64.tar.zst -C ollama
fi
export OLLAMA_HOST=127.0.0.1:11435
export OLLAMA_MODELS="$runtime/models"
export OLLAMA_NO_CLOUD=1
export OLLAMA_NUM_PARALLEL=1
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
if ! curl -fsS --max-time 2 http://127.0.0.1:11435/api/version >/dev/null 2>&1; then
    nohup "$runtime/ollama/bin/ollama" serve >"$runtime/model.log" 2>&1 &
    echo $! >"$runtime/model.pid"
    for i in $(seq 1 30); do
        if curl -fsS --max-time 2 http://127.0.0.1:11435/api/version >/dev/null 2>&1; then break; fi
        sleep 1
    done
fi
"$runtime/ollama/bin/ollama" pull "$model"
echo '安装完成。执行 bash start.sh 开始使用。'
