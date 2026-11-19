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

setup_script = """
set -e

# Create directories on datastore
mkdir -p /datastore/ComfyUI
mkdir -p /datastore/ai-models/checkpoints
mkdir -p /datastore/ai-models/animatediff_models
mkdir -p /datastore/ai-models/loras
mkdir -p /datastore/ai-models/vae
mkdir -p /datastore/ai-outputs

# Clone ComfyUI if not cloned
if [ ! -d "/datastore/ComfyUI/.git" ]; then
    git clone https://github.com/comfyanonymous/ComfyUI.git /datastore/ComfyUI
fi

# Clone ComfyUI-Manager
if [ ! -d "/datastore/ComfyUI/custom_nodes/ComfyUI-Manager" ]; then
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git /datastore/ComfyUI/custom_nodes/ComfyUI-Manager
fi

# Clone AnimateDiff for Video generation
if [ ! -d "/datastore/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved" ]; then
    git clone https://github.com/Kosinkadink/ComfyUI-AnimateDiff-Evolved.git /datastore/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved
fi

# Create virtualenv
if [ ! -d "/datastore/ComfyUI/venv" ]; then
    python3 -m venv /datastore/ComfyUI/venv
fi

# Install PyTorch with ROCm
/datastore/ComfyUI/venv/bin/pip install --upgrade pip wheel setuptools
/datastore/ComfyUI/venv/bin/pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.1
/datastore/ComfyUI/venv/bin/pip install -r /datastore/ComfyUI/requirements.txt
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/setup_comfy.sh', 'w') as f:
    f.write(setup_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/setup_comfy.sh /tmp/setup_comfy.sh && pct exec 100 -- bash /tmp/setup_comfy.sh")
while True:
    line = stdout.readline()
    if not line:
        break
    print(line, end='')
