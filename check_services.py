import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import sys
import time
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

script = """
pct exec 100 -- bash -c '
ip -4 addr show eth0
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080 || true
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:11434 || true
'
"""
stdin, stdout, stderr = client.exec_command(script)
print(stdout.read().decode())
print(stderr.read().decode())
client.close()
