import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko
import time

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

cmd = """pct exec 100 -- curl -s -X POST http://127.0.0.1:8880/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model": "kokoro", "input": "Bonjour mon ami! C est une vraie voix naturelle sans robotique.", "voice": "ff_siwis", "response_format": "mp3"}' \
  --output /tmp/test_kokoro.mp3

pct exec 100 -- ls -lh /tmp/test_kokoro.mp3
"""
t0 = time.time()
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())
print("Temps de generation:", round(time.time() - t0, 2), "s")
client.close()
