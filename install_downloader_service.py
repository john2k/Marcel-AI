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

setup_downloader_service = """
pct exec 100 -- apt install -y python3-flask python3-requests

cat << 'EOF' > /tmp/model-downloader.service
[Unit]
Description=Model Downloader Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /opt/model_downloader.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

pct push 100 /tmp/model-downloader.service /etc/systemd/system/model-downloader.service
pct exec 100 -- systemctl daemon-reload
pct exec 100 -- systemctl enable --now model-downloader
pct exec 100 -- systemctl status model-downloader
"""

stdin, stdout, stderr = ssh.exec_command(setup_downloader_service)
print("STDOUT:\n", stdout.read().decode())
print("STDERR:\n", stderr.read().decode())
