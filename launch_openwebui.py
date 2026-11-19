import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import sys
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')

HOST = os.environ.get('PROXMOX_HOST', '192.168.1.100')
PORT = 22
USER = "root"
PASS = os.environ.get('PROXMOX_PASSWORD', '')

CMD = """#!/usr/bin/env bash
set -euo pipefail

# 1. Configurer AppArmor unconfined pour LXC 100
if ! grep -q "lxc.apparmor.profile" /etc/pve/lxc/100.conf; then
    echo "lxc.apparmor.profile: unconfined" >> /etc/pve/lxc/100.conf
fi
sed -i 's/features: nesting=1/features: nesting=1,keyctl=1/' /etc/pve/lxc/100.conf || true

# 2. Configurer Docker dans le conteneur pour désactiver AppArmor
pct exec 100 -- bash -c '
mkdir -p /etc/docker
cat << "EOF" > /etc/docker/daemon.json
{
  "default-security-opt": ["apparmor=unconfined"]
}
EOF
systemctl restart docker
sleep 2

# Lancer Open WebUI
docker rm -f open-webui 2>/dev/null || true
docker run -d \\
  --name open-webui \\
  --restart always \\
  --network host \\
  --security-opt apparmor=unconfined \\
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \\
  -e WEBUI_AUTH=True \\
  -v /app/backend/data:/app/backend/data \\
  ghcr.io/open-webui/open-webui:main

sleep 5
docker ps
'

echo "Open WebUI lancé avec succès !"
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/launch_openwebui.sh", "w") as f:
        f.write(CMD)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/launch_openwebui.sh && /tmp/launch_openwebui.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(main())
