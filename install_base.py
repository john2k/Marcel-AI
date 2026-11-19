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

setup_base = """
pct exec 100 -- bash -c '
export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y python3-full python3-pip python3-venv git curl wget ffmpeg mesa-vulkan-drivers vulkan-tools radeontop zstd build-essential ca-certificates
'
"""

stdin, stdout, stderr = ssh.exec_command(setup_base)
while True:
    line = stdout.readline()
    if not line:
        break
    print(line, end='')
