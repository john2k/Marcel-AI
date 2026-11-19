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

REMOTE_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo " [1/5] CREATION DU DATASTORE ZFS STRIPE RAPIDE (32 To)"
echo "=========================================================="
DISK_8TB="/dev/disk/by-id/ata-ST8000VN004-3CP101_WWZ2MCD8"
DISK_12TB_1="/dev/disk/by-id/ata-ST12000VN0007-2GS116_ZJV5FBBW"
DISK_12TB_2="/dev/disk/by-id/ata-ST12000VN0008-2PH103_ZLW2KWN5"

# Détruire ancien pool s'il existe
zpool destroy datastore 2>/dev/null || true
pvesm remove datastore 2>/dev/null || true
pvesm remove datastore-dir 2>/dev/null || true

# Création du pool Stripe sans parité (rapide, espace maximal)
zpool create -f -o ashift=12 datastore "$DISK_8TB" "$DISK_12TB_1" "$DISK_12TB_2"
zfs set compression=lz4 datastore

# Enregistrement dans Proxmox
pvesm add zfspool datastore --pool datastore --content rootdir,images
mkdir -p /datastore/ollama-models /datastore/open-webui-data
pvesm add dir datastore-dir --path /datastore --content rootdir,images,backup,iso,vztmpl

zpool status datastore
df -h /datastore

echo "=========================================================="
echo " [2/5] CREATION DU CONTENEUR LXC 100 (UBUNTU 24.04)"
echo "=========================================================="
# Arrêt et destruction si existant
pct stop 100 2>/dev/null || true
pct destroy 100 2>/dev/null || true

# Création du conteneur avec GPU passthrough
pct create 100 local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \\
  --hostname ollama-ai \\
  --ostype ubuntu \\
  --cores 8 \\
  --memory 16384 \\
  --swap 2048 \\
  --rootfs local-lvm:32 \\
  --net0 name=eth0,bridge=vmbr0,ip=dhcp,firewall=0 \\
  --unprivileged 0 \\
  --features nesting=1 \\
  --onboot 1

# Montage du dossier des modèles sur le datastore ZFS (pour avoir des To de modèles)
pct set 100 -mp0 /datastore/ollama-models,mp=/root/.ollama
pct set 100 -mp1 /datastore/open-webui-data,mp=/app/backend/data

# Configuration du GPU Passthrough AMD (Radeon RX 5600 XT)
KFD_MAJOR=$(ls -l /dev/kfd | awk '{print $5}' | tr -d ',')
cat << EOF >> /etc/pve/lxc/100.conf

# --- Passthrough GPU AMD (Radeon RX 5600 XT) ---
lxc.cgroup2.devices.allow: c 226:* rwm
lxc.cgroup2.devices.allow: c ${KFD_MAJOR}:* rwm
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
lxc.mount.entry: /dev/kfd dev/kfd none bind,optional,create=file
EOF

echo "Démarrage du conteneur LXC 100..."
pct start 100

# Attente d'obtention de l'IP DHCP
echo "Attente du réseau dans le conteneur..."
CT_IP=""
for i in {1..20}; do
    CT_IP=$(pct exec 100 -- ip -4 addr show eth0 2>/dev/null | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}' || true)
    if [ -n "$CT_IP" ]; then
        echo "Conteneur en ligne avec IP : $CT_IP"
        break
    fi
    sleep 1
done

if [ -z "$CT_IP" ]; then
    echo "Impossible d'obtenir une IP DHCP, attribution d'une IP statique de secours..."
    pct set 100 -net0 name=eth0,bridge=vmbr0,ip=192.168.1.150/24,gw=192.168.1.1
    pct restart 100
    sleep 3
    CT_IP="192.168.1.10000"
fi

echo "=========================================================="
echo " [3/5] CONFIGURATION DU GPU AMD ET INSTALLATION D OLLAMA"
echo "=========================================================="
pct exec 100 -- bash -c '
set -euo pipefail

# Mettre à jour et installer les outils nécessaires
apt update
apt install -y curl pciutils ca-certificates gnupg git python3 python3-pip

# Vérification de l accès au GPU
ls -la /dev/kfd /dev/dri

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

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Démarrer le conteneur Open WebUI
docker run -d \\
  --name open-webui \\
  --restart always \\
  --network host \\
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \\
  -v /app/backend/data:/app/backend/data \\
  ghcr.io/open-webui/open-webui:main
'

echo "=========================================================="
echo " [5/5] TELECHARGEMENT DE MODELES INITIAUX DONT NON CENSURE"
echo "=========================================================="
pct exec 100 -- bash -c '
# Modèle non censuré populaire et conversationnel (Llama 3 8B Uncensored/Dolphin)
echo "Téléchargement du modèle non censuré : dolphin-llama3:8b..."
ollama pull dolphin-llama3:8b &

# Modèle léger ultra rapide pour démarrer immédiatement
echo "Téléchargement du modèle compact ultra-rapide : llama3.2:3b..."
ollama pull llama3.2:3b

wait
ollama list
'

echo "=========================================================="
echo "INSTALLATION TERMINEE AVEC SUCCES !"
echo "Accès à Open WebUI : http://${CT_IP}:8080 ou http://${CT_IP}:3000"
echo "=========================================================="
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/setup_ollama.sh", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    print("Lancement du déploiement complet...")
    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/setup_ollama.sh && /tmp/setup_ollama.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(main())
