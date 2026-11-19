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

override_content = """[Service]
Environment="OLLAMA_MODELS=/datastore/ollama-models"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/ollama_override.conf', 'w') as f:
    f.write(override_content)
sftp.close()

cmds = [
    "pct exec 100 -- mkdir -p /datastore/ollama-models",
    "pct exec 100 -- chown -R ollama:ollama /datastore/ollama-models",
    "pct exec 100 -- mkdir -p /etc/systemd/system/ollama.service.d",
    "pct push 100 /tmp/ollama_override.conf /etc/systemd/system/ollama.service.d/override.conf",
    "pct exec 100 -- systemctl daemon-reload",
    "pct exec 100 -- systemctl restart ollama",
    "pct exec 100 -- systemctl status ollama --no-pager"
]

for cmd in cmds:
    print(f"Exec: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

ssh.close()
