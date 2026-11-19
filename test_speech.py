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

cmd = """pct exec 100 -- curl -s -X POST http://127.0.0.1:5050/v1/audio/speech \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-tts" \
  -d '{"model": "tts-1", "input": "Salut mon cher! C est Marcel qui te parle en direct du Quebec!", "voice": "fr-CA-AntoineNeural"}' \
  --output /tmp/test_antoine.mp3

pct exec 100 -- ls -lh /tmp/test_antoine.mp3
"""
stdin, stdout, stderr = client.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
client.close()
