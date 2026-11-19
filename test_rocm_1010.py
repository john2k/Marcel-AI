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

test_sh = """
export HSA_OVERRIDE_GFX_VERSION=10.1.0
export TORCH_BLAS_PREFER_HIPBLASLT=0
export HIP_VISIBLE_DEVICES=0
/datastore/ComfyUI/venv/bin/python3 -c '
import torch
print("Device count:", torch.cuda.device_count())
if torch.cuda.is_available():
    print("Device name:", torch.cuda.get_device_name(0))
    x = torch.ones(10, 10, device="cuda")
    print("Tensor on GPU:", x.device, x.sum().item())
'
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_1010.sh', 'w') as f:
    f.write(test_sh)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/test_1010.sh /tmp/test_1010.sh && pct exec 100 -- bash /tmp/test_1010.sh")
print("STDOUT:\n", stdout.read().decode())
print("STDERR:\n", stderr.read().decode())
