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

fix_all_script = r'''
import os
import re

base = '/datastore/ComfyUI/venv/lib/python3.12/site-packages/comfy_kitchen'
pattern = re.compile(r'\blist\[([a-zA-Z0-9_| ]+)\]')

for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r') as fp:
                txt = fp.read()
            if pattern.search(txt):
                print("Patching generics in:", p)
                new_txt = pattern.sub(r'List[\1]', txt)
                if 'from typing import' in new_txt:
                    new_txt = new_txt.replace('from typing import ', 'from typing import List, ')
                else:
                    new_txt = 'from typing import List\n' + new_txt
                with open(p, 'w') as fp:
                    fp.write(new_txt)

print("Done patching all generic lists!")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/patch_kitchen2.py', 'w') as f:
    f.write(fix_all_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/patch_kitchen2.py /tmp/patch_kitchen2.py && pct exec 100 -- python3 /tmp/patch_kitchen2.py && pct exec 100 -- systemctl restart comfyui")
print(stdout.read().decode())
print(stderr.read().decode())
