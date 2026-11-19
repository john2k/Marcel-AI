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

download_script = """
set -e

mkdir -p /datastore/ComfyUI/models/checkpoints
mkdir -p /datastore/ComfyUI/models/vae
mkdir -p /datastore/ComfyUI/models/animatediff_models
mkdir -p /datastore/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/models

echo "Downloading Photo Model: DreamShaper 8..."
if [ ! -f "/datastore/ComfyUI/models/checkpoints/dreamshaper_8.safetensors" ]; then
    wget -q --show-progress -c "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors" -O "/datastore/ComfyUI/models/checkpoints/dreamshaper_8.safetensors"
fi

echo "Downloading SD 1.5 VAE..."
if [ ! -f "/datastore/ComfyUI/models/vae/vae-ft-mse-840000-ema-pruned.safetensors" ]; then
    wget -q --show-progress -c "https://huggingface.co/stabilityai/sd-vae-ft-mse-original/resolve/main/vae-ft-mse-840000-ema-pruned.safetensors" -O "/datastore/ComfyUI/models/vae/vae-ft-mse-840000-ema-pruned.safetensors"
fi

echo "Downloading Video Model: AnimateDiff v3 Motion Module..."
if [ ! -f "/datastore/ComfyUI/models/animatediff_models/v3_sd15_mm.ckpt" ]; then
    wget -q --show-progress -c "https://huggingface.co/guoyww/animatediff/resolve/main/v3_sd15_mm.ckpt" -O "/datastore/ComfyUI/models/animatediff_models/v3_sd15_mm.ckpt"
    cp "/datastore/ComfyUI/models/animatediff_models/v3_sd15_mm.ckpt" "/datastore/ComfyUI/custom_nodes/ComfyUI-AnimateDiff-Evolved/models/v3_sd15_mm.ckpt"
fi

echo "Models downloaded successfully!"
ls -lh /datastore/ComfyUI/models/checkpoints
ls -lh /datastore/ComfyUI/models/animatediff_models
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/download_models.sh', 'w') as f:
    f.write(download_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/download_models.sh /tmp/download_models.sh && pct exec 100 -- bash /tmp/download_models.sh")
while True:
    line = stdout.readline()
    if not line:
        break
    print(line, end='')
print(stderr.read().decode())
