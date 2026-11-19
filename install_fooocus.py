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

setup_fooocus = """
set -e

# Create virtualenv
if [ ! -d "/datastore/Fooocus/venv" ]; then
    python3 -m venv /datastore/Fooocus/venv
fi

/datastore/Fooocus/venv/bin/pip install --upgrade pip wheel setuptools
/datastore/Fooocus/venv/bin/pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm6.1
/datastore/Fooocus/venv/bin/pip install -r /datastore/Fooocus/requirements_versions.txt

# Link model folders from ComfyUI to Fooocus so models are shared
mkdir -p /datastore/Fooocus/models/checkpoints
mkdir -p /datastore/Fooocus/models/loras
mkdir -p /datastore/Fooocus/models/vae_approx

# Link checkpoints
ln -sf /datastore/ComfyUI/models/checkpoints/* /datastore/Fooocus/models/checkpoints/ 2>/dev/null || true
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/setup_fooocus.sh', 'w') as f:
    f.write(setup_fooocus)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/setup_fooocus.sh /tmp/setup_fooocus.sh && pct exec 100 -- bash /tmp/setup_fooocus.sh")
while True:
    line = stdout.readline()
    if not line:
        break
    print(line, end='')
print(stderr.read().decode())
