import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import sys
import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

script = """
pct exec 100 -- bash -c '
# Tuer ancien llama-server
systemctl stop ollama
pkill -9 llama-server 2>/dev/null || true

# Installer drivers Vulkan RADV
apt update
apt install -y mesa-vulkan-drivers vulkan-tools libvulkan1

# Tester vulkaninfo
vulkaninfo --summary || true

# Configurer Ollama pour Vulkan
mkdir -p /etc/systemd/system/ollama.service.d
cat << "OLLAMA_ENV" > /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_VULKAN=1"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
OLLAMA_ENV

systemctl daemon-reload
systemctl start ollama
sleep 3
systemctl status ollama --no-pager
journalctl -u ollama -n 25 --no-pager
'
"""
stdin, stdout, stderr = client.exec_command(script, get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")
client.close()
