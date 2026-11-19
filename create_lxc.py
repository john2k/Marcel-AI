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

create_cmd = """
pct create 100 /var/lib/vz/template/cache/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
  --hostname ai-generator \
  --cores 8 \
  --memory 57344 \
  --swap 4096 \
  --rootfs datastore:200 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.150/24,gw=192.168.1.1 \
  --nameserver 1.1.1.1 \
  --features nesting=1,keyctl=1 \
  --ostype ubuntu \
  --unprivileged 0 \
  --password ChangeMe123! \
  --start 0
"""

stdin, stdout, stderr = ssh.exec_command(create_cmd)
print("CREATE STDOUT:\n", stdout.read().decode())
print("CREATE STDERR:\n", stderr.read().decode())
