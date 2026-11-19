#!/usr/bin/env bash
# ==============================================================================
# Script 04 : Installation et configuration de SnapRAID et snapraid-runner
# ==============================================================================
set -euo pipefail

echo "Installation de snapraid, git, python3..."
apt update
apt install -y snapraid git python3

# Déploiement du fichier de configuration snapraid.conf
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "${SCRIPT_DIR}/../configs/snapraid.conf" /etc/snapraid.conf

echo "Installation de snapraid-runner (script d'automatisation avec seuil de sécurité)..."
if [ ! -d "/opt/snapraid-runner" ]; then
    git clone https://github.com/Chronial/snapraid-runner.git /opt/snapraid-runner
fi

cp "${SCRIPT_DIR}/../configs/snapraid-runner.conf" /opt/snapraid-runner/snapraid-runner.conf

# Configuration du service et timer systemd pour exécution quotidienne
cat << 'EOF' > /etc/systemd/system/snapraid-runner.service
[Unit]
Description=SnapRAID Runner Backup and Scrub Job
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/snapraid-runner/snapraid-runner.py -c /opt/snapraid-runner/snapraid-runner.conf
User=root
EOF

cat << 'EOF' > /etc/systemd/system/snapraid-runner.timer
[Unit]
Description=Daily SnapRAID Sync and Scrub Timer

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable snapraid-runner.timer
systemctl start snapraid-runner.timer

echo "Statut du timer SnapRAID :"
systemctl list-timers snapraid-runner.timer

echo "Vérification de la configuration SnapRAID :"
snapraid check --audit-only 2>&1 || true
echo "Pour initialiser la parité pour la première fois, lancez :"
echo "  snapraid sync"
