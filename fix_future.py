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

fix_future_script = r'''
import os

base = '/datastore/ComfyUI/venv/lib/python3.12/site-packages/comfy_kitchen'

for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r') as fp:
                lines = fp.readlines()
            
            future_lines = [l for l in lines if 'from __future__' in l]
            other_lines = [l for l in lines if 'from __future__' not in l]
            if future_lines:
                lines = future_lines + other_lines
                with open(p, 'w') as fp:
                    fp.writelines(lines)

print("Fixed __future__ order!")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/fix_future.py', 'w') as f:
    f.write(fix_future_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/fix_future.py /tmp/fix_future.py && pct exec 100 -- python3 /tmp/fix_future.py && pct exec 100 -- systemctl restart comfyui")
print(stdout.read().decode())
print(stderr.read().decode())
