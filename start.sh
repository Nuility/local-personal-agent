#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
root="$PWD"
mkdir -p .runtime
runtime="$(cd .runtime && pwd)"
export OLLAMA_HOST=127.0.0.1:11435
export OLLAMA_MODELS="$runtime/models"
export OLLAMA_NO_CLOUD=1
export OLLAMA_NUM_PARALLEL=1
export LD_LIBRARY_PATH="/usr/lib/wsl/lib:${LD_LIBRARY_PATH:-}"
mkdir -p data "$OLLAMA_MODELS"
if ! curl -fsS --max-time 2 http://127.0.0.1:11435/api/version >/dev/null 2>&1; then
    if [ ! -x "$runtime/ollama/bin/ollama" ]; then
        echo '运行时尚未安装。请先执行 bash setup.sh。'
        exit 1
    fi
    nohup "$runtime/ollama/bin/ollama" serve >data/model.log 2>&1 &
    echo $! >data/model.pid
    for i in $(seq 1 30); do
        if curl -fsS --max-time 2 http://127.0.0.1:11435/api/version >/dev/null 2>&1; then break; fi
        sleep 1
    done
fi
python3 agent.py init
python3 agent.py status
nohup python3 agent.py worker >>data/worker.log 2>&1 &
python3 agent.py chat
