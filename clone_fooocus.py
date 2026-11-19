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

clone_cmd = """
if [ ! -d "/datastore/Fooocus" ]; then
    git clone https://github.com/lllyasviel/Fooocus.git /datastore/Fooocus
fi
ls -la /datastore/Fooocus
"""

stdin, stdout, stderr = ssh.exec_command(f"pct exec 100 -- bash -c '{clone_cmd}'")
print(stdout.read().decode())
print(stderr.read().decode())
