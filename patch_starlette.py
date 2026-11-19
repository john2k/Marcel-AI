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

patch_code = """
import sys

filepath = '/datastore/Fooocus/venv/lib/python3.12/site-packages/starlette/templating.py'
with open(filepath, 'r') as f:
    text = f.read()

target = '        context = context or {}\\n\\n        context.setdefault(\"request\", request)'
replacement = '''        if isinstance(request, str):
            name, context = request, name
            request = context.get(\"request\") if isinstance(context, dict) else None

        context = context or {}
        if request is not None:
            context.setdefault(\"request\", request)'''

if target in text:
    text = text.replace(target, replacement, 1)
    with open(filepath, 'w') as f:
        f.write(text)
    print('PATCHED starlette templating.py successfully!')
else:
    print('Target not found in templating.py, checking if already patched...')
    if 'isinstance(request, str)' in text:
        print('Already patched!')
    else:
        print('Could not find target block.')
"""

# Push script to /tmp/patch_starlette.py on LXC 100
sftp = ssh.open_sftp()
with sftp.file('/tmp/patch_starlette.py', 'w') as f:
    f.write(patch_code)
sftp.close()

commands = [
    "pct push 100 /tmp/patch_starlette.py /tmp/patch_starlette.py",
    "pct exec 100 -- /datastore/Fooocus/venv/bin/python /tmp/patch_starlette.py",
    "pct exec 100 -- systemctl restart fooocus.service"
]

for cmd in commands:
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"ERR: {err}")

ssh.close()
