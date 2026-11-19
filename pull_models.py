import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import sys
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

script = """
pct exec 100 -- bash -c '
echo "=== Pulling llama3.2:3b ==="
ollama pull llama3.2:3b

echo "=== Pulling dolphin-llama3:8b (Uncensored) ==="
ollama pull dolphin-llama3:8b

echo "=== Current Ollama Models ==="
ollama list

echo "=== Docker Containers ==="
docker ps

echo "=== Testing Open WebUI HTTP ==="
curl -I http://127.0.0.1:8080 || true
'
"""
stdin, stdout, stderr = client.exec_command(script, get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")
client.close()
