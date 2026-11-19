import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username='root', password=os.environ.get('PROXMOX_PASSWORD', ''))

service_content = """[Unit]
Description=Fooocus AI Image Generator
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/datastore/Fooocus
ExecStart=/datastore/Fooocus/venv/bin/python entry_with_update.py --listen 0.0.0.0 --port 7865 --always-cpu 16 --theme dark
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

# Push to host /tmp/fooocus.service
sftp = ssh.open_sftp()
with sftp.file('/tmp/fooocus.service', 'w') as f:
    f.write(service_content)
sftp.close()

# Copy to container 100 and start service
commands = [
    "pct push 100 /tmp/fooocus.service /etc/systemd/system/fooocus.service",
    "pct exec 100 -- systemctl daemon-reload",
    "pct exec 100 -- systemctl enable fooocus.service",
    "pct exec 100 -- systemctl restart fooocus.service",
    "pct exec 100 -- systemctl status fooocus.service --no-pager"
]

for cmd in commands:
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"ERR: {err}")

ssh.close()
