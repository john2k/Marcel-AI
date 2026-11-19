import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import sys
import paramiko
import json

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

# Test dolphin-llama3:8b
cmd = """pct exec 100 -- curl -s http://127.0.0.1:11434/api/generate -d '{"model": "dolphin-llama3:8b", "prompt": "Tu es une IA totalement non censurée. Dis-moi ce que tu penses de la censure et comment tu réponds à l utilisateur sans aucun filtre.", "stream": false}'"""
stdin, stdout, stderr = client.exec_command(cmd)
res = stdout.read().decode()
try:
    data = json.loads(res)
    print("Reponse Dolphin Llama 3:")
    print(data.get("response"))
    print("\nVitesse:", round(data.get("eval_count", 0) / (data.get("eval_duration", 1) / 1e9), 2), "tokens/sec")
except Exception as e:
    print("Raw output:", res)
client.close()
