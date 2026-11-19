import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import sys
import time
import paramiko

sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')

HOST = os.environ.get('PROXMOX_HOST', '192.168.1.100')
PORT = 22
USER = "root"
PASS = os.environ.get('PROXMOX_PASSWORD', '')

FINISH_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail

CT_IP=$(pct exec 100 -- ip -4 addr show eth0 2>/dev/null | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}' || true)
echo "LXC 100 IP: $CT_IP"

echo "=========================================================="
echo " [3/5] INSTALLATION DE ZSTD ET D OLLAMA"
echo "=========================================================="
pct exec 100 -- bash -c '
set -euo pipefail

apt update
apt install -y zstd curl pciutils ca-certificates gnupg git python3

# Installation officielle d Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configuration d Ollama pour AMD Radeon RX 5600 XT (Navi 10 -> HSA_OVERRIDE_GFX_VERSION=10.3.0)
mkdir -p /etc/systemd/system/ollama.service.d
cat << "OLLAMA_ENV" > /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=10.3.0"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
OLLAMA_ENV

systemctl daemon-reload
systemctl restart ollama
sleep 3
systemctl status ollama --no-pager
'

echo "=========================================================="
echo " [4/5] INSTALLATION DE DOCKER ET OPEN WEBUI"
echo "=========================================================="
pct exec 100 -- bash -c '
set -euo pipefail

# Installer Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# S assurer que docker tourne
systemctl enable --now docker

# Supprimer conteneur si existant
docker rm -f open-webui 2>/dev/null || true

# Démarrer Open WebUI avec le réseau host (port 8080)
docker run -d \\
  --name open-webui \\
  --restart always \\
  --network host \\
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \\
  -v /app/backend/data:/app/backend/data \\
  ghcr.io/open-webui/open-webui:main

# Attendre quelques secondes et vérifier
sleep 5
docker ps
'

echo "=========================================================="
echo " [5/5] TELECHARGEMENT DES MODELES (UNCENSORED + RAPIDE)"
echo "=========================================================="
pct exec 100 -- bash -c '
# Modèle rapide pour tester immédiatement
echo "Pull de llama3.2:3b..."
ollama pull llama3.2:3b

# Modèle non censuré (Dolphin Llama 3 8B)
echo "Pull du modèle non censuré dolphin-llama3:8b..."
ollama pull dolphin-llama3:8b

echo "Modèles installés :"
ollama list
'

echo "=========================================================="
echo "DEPLOYMENT COMPLETE!"
echo "Open WebUI URL : http://${CT_IP}:8080"
echo "Ollama API URL : http://${CT_IP}:11434"
echo "=========================================================="
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/finish_ollama.sh", "w") as f:
        f.write(FINISH_SCRIPT)
    sftp.close()

    print("Lancement de la finalisation...")
    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/finish_ollama.sh && /tmp/finish_ollama.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(main())
