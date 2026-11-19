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

# Let's run a test in LXC 100 to check ROCm pytorch
cmd = """pct exec 100 -- bash -c '
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/rocm6.1 --break-system-packages
python3 -c "
import os
os.environ[\"HSA_OVERRIDE_GFX_VERSION\"] = \"10.3.0\"
import torch
print(\"PyTorch version:\", torch.__version__)
print(\"CUDA/ROCm available:\", torch.cuda.is_available())
if torch.cuda.is_available():
    print(\"Device name:\", torch.cuda.get_device_name(0))
    x = torch.randn(100, 100, device=\"cuda\")
    y = x @ x
    print(\"Matrix mult on GPU successful! Sum:\", y.sum().item())
"
'"""

stdin, stdout, stderr = ssh.exec_command(cmd)
while True:
    line = stdout.readline()
    if not line:
        break
    print(line, end='')
print(stderr.read().decode())
