import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username='root', password=os.environ.get('PROXMOX_PASSWORD', ''))

test_comfy = """
/datastore/ComfyUI/venv/bin/python /datastore/ComfyUI/main.py --help
"""

stdin, stdout, stderr = ssh.exec_command(f"pct exec 100 -- bash -c '{test_comfy}'")
print(stdout.read().decode())
print(stderr.read().decode())
