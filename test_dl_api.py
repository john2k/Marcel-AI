import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username='root', password=os.environ.get('PROXMOX_PASSWORD', ''))

cmd = """pct exec 100 -- bash -c 'curl -s -X POST http://127.0.0.1:8080/api/download -H "Content-Type: application/json" -d "{\\"url\\": \\"https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/README.md\\", \\"folder\\": \\"vae\\"}"'"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("POST RESULT:", stdout.read().decode())

time.sleep(2)
cmd2 = """pct exec 100 -- curl -s http://127.0.0.1:8080/api/downloads"""
stdin, stdout, stderr = ssh.exec_command(cmd2)
print("GET TASKS:", stdout.read().decode())
