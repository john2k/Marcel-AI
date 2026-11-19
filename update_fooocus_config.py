import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username='root', password=os.environ.get('PROXMOX_PASSWORD', ''))

config_data = {
    "path_checkpoints": [
        "/datastore/Fooocus/models/checkpoints",
        "/datastore/ComfyUI/models/checkpoints"
    ],
    "path_loras": [
        "/datastore/Fooocus/models/loras",
        "/datastore/ComfyUI/models/loras"
    ],
    "path_embeddings": "/datastore/Fooocus/models/embeddings",
    "path_vae_approx": "/datastore/Fooocus/models/vae_approx",
    "path_vae": [
        "/datastore/Fooocus/models/vae",
        "/datastore/ComfyUI/models/vae"
    ],
    "path_upscale_models": "/datastore/Fooocus/models/upscale_models",
    "path_inpaint": "/datastore/Fooocus/models/inpaint",
    "path_controlnet": [
        "/datastore/Fooocus/models/controlnet",
        "/datastore/ComfyUI/models/controlnet"
    ],
    "path_clip_vision": "/datastore/Fooocus/models/clip_vision",
    "path_fooocus_expansion": "/datastore/Fooocus/models/prompt_expansion/fooocus_expansion",
    "path_wildcards": "/datastore/Fooocus/wildcards",
    "path_safety_checker": "/datastore/Fooocus/models/safety_checker",
    "path_sam": "/datastore/Fooocus/models/sam",
    "path_outputs": "/datastore/Fooocus/outputs"
}

sftp = ssh.open_sftp()
with sftp.file('/tmp/fooocus_config.txt', 'w') as f:
    json.dump(config_data, f, indent=4)
sftp.close()

commands = [
    "pct push 100 /tmp/fooocus_config.txt /datastore/Fooocus/config.txt",
    "pct exec 100 -- systemctl restart fooocus.service"
]

for cmd in commands:
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

ssh.close()
