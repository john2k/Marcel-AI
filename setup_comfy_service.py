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

service_unit = """[Unit]
Description=ComfyUI AI Generation Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/datastore/ComfyUI
ExecStart=/datastore/ComfyUI/venv/bin/python main.py --listen 0.0.0.0 --port 8188 --cpu --high-ram --enable-cors-header
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/comfyui.service', 'w') as f:
    f.write(service_unit)
sftp.close()

setup_cmd = """
pct push 100 /tmp/comfyui.service /etc/systemd/system/comfyui.service
pct exec 100 -- systemctl daemon-reload
pct exec 100 -- systemctl enable --now comfyui
sleep 3
pct exec 100 -- systemctl status comfyui
"""

stdin, stdout, stderr = ssh.exec_command(setup_cmd)
print("STDOUT:\n", stdout.read().decode())
print("STDERR:\n", stderr.read().decode())
