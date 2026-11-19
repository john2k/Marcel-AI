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

code = """
import os
import torch

print("PyTorch version:", torch.__version__)
print("ROCm available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device name:", torch.cuda.get_device_name(0))
    print("VRAM (GB):", torch.cuda.get_device_properties(0).total_memory / (1024**3))
    x = torch.randn(500, 500, device="cuda")
    y = x @ x
    print("GPU matrix multiplication test passed! Result sum:", y.sum().item())
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_gpu.py', 'w') as f:
    f.write(code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/test_gpu.py /tmp/test_gpu.py && pct exec 100 -- bash -c 'export HSA_OVERRIDE_GFX_VERSION=10.3.0 export ROC_ENABLE_PRE_VEGA=1 export HIP_VISIBLE_DEVICES=0; /datastore/ComfyUI/venv/bin/python3 /tmp/test_gpu.py'")
print("TEST STDOUT:\n", stdout.read().decode())
print("TEST STDERR:\n", stderr.read().decode())
