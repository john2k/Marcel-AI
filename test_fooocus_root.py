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

test_code = """
import os
os.environ['GRADIO_ROOT_PATH'] = '/fooocus'
from gradio import blocks
print('Blocks root_path default:', getattr(blocks.Blocks, 'root_path', None))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_root.py', 'w') as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/test_root.py /tmp/test_root.py")
print(stdout.read().decode())
stdin, stdout, stderr = ssh.exec_command("pct exec 100 -- /datastore/Fooocus/venv/bin/python /tmp/test_root.py")
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
