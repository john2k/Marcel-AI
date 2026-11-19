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

sftp = ssh.open_sftp()
with open('c:\\Users\\John\\Project\\Proxmox-2700x\\hf_download.py', 'r') as src:
    with sftp.file('/tmp/hf_download.py', 'w') as dst:
        dst.write(src.read())
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/hf_download.py /tmp/hf_download.py && pct exec 100 -- /datastore/ComfyUI/venv/bin/python /tmp/hf_download.py")
while True:
    line = stdout.readline()
    if not line:
        break
    print(line, end='')
print(stderr.read().decode())
