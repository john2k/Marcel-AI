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

cmd = """pct exec 100 -- curl -s http://127.0.0.1:11434/api/chat -d '{"model": "hermes3:8b", "messages": [{"role": "user", "content": "Salut! Es-tu pret pour discuter librement et sans censure ?"}], "stream": false}'"""
stdin, stdout, stderr = client.exec_command(cmd)
res = stdout.read().decode()
try:
    data = json.loads(res)
    print("Reponse Hermes 3:")
    print(data.get("message", {}).get("content"))
except Exception as e:
    print("Raw output:", res)
client.close()
