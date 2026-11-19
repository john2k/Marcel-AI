import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

script = """
pct exec 100 -- bash -c '
docker rm -f kokoro-fastapi openai-edge-tts 2>/dev/null || true

docker run -d \\
  --name kokoro-fastapi \\
  --restart always \\
  --network host \\
  -e PORT=8880 \\
  ghcr.io/remsky/kokoro-fastapi-cpu:latest

sleep 5
docker ps
curl -s http://127.0.0.1:8880/v1/models || true
'
"""
stdin, stdout, stderr = client.exec_command(script, get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")
client.close()
