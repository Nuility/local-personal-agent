"""Stop only verified processes belonging to this project."""
import os
from pathlib import Path
import signal

root = Path(__file__).resolve().parent
runtime = (root / '.runtime').resolve()
for pidfile, expected in [(root / 'data/worker.pid', 'worker'),
                          (root / 'data/model.pid', 'model'),
                          (runtime / 'model.pid', 'model')]:
    if not pidfile.exists(): continue
    pid = int(pidfile.read_text().strip())
    proc = Path('/proc') / str(pid)
    if not proc.exists(): continue
    args = (proc / 'cmdline').read_bytes().split(b'\0')
    matches = False
    if expected == 'worker':
        matches = (proc / 'cwd').resolve() == root and b'agent.py' in args and b'worker' in args
    else:
        matches = str(runtime / 'ollama/bin/ollama').encode() in args and b'serve' in args
    if matches:
        try:
            os.kill(pid, signal.SIGTERM)
            print('已发送停止请求:', expected, pid)
        except ProcessLookupError:
            pass
    else:
        print('进程身份不匹配，未停止:', pid)
