import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

cmd = """pct exec 100 -- curl -s http://127.0.0.1:5050/v1/audio/voices"""
stdin, stdout, stderr = client.exec_command(cmd)
res = stdout.read().decode()
try:
    voices = json.loads(res)
    fr_voices = [v for v in voices.get("voices", []) if "fr-" in v.get("id", "").lower() or "fr-" in v.get("name", "").lower()]
    print("French voices available:")
    for v in fr_voices:
        print(f" - {v.get('id')}: {v.get('name')} ({v.get('gender', '')})")
except Exception as e:
    print("Raw output:", res[:300])
client.close()
