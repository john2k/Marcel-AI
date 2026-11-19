#!/usr/bin/env bash
# ==============================================================================
# Script 05 : Installation de Cockpit et plugins 45Drives (File Sharing)
# ==============================================================================
set -euo pipefail

echo "Installation de Cockpit et stockage..."
apt update
apt install -y cockpit cockpit-storaged samba

echo "Configuration du dépôt officiel 45Drives pour Debian Bookworm..."
curl -sSL https://repo.45drives.com/setup | bash

echo "Installation des modules 45Drives..."
apt update
apt install -y cockpit-file-sharing cockpit-identities

echo "Activation du service Cockpit..."
systemctl enable --now cockpit.socket

echo "Configuration initiale d'un partage Samba test sur /mnt/storage..."
SAMBA_CONF="/etc/samba/smb.conf"
if ! grep -q "\[StoragePool\]" "$SAMBA_CONF"; then
    cat << 'EOF' >> /etc/samba/smb.conf

[StoragePool]
   comment = Pool Unifié MergerFS
   path = /mnt/storage
   browseable = yes
   read only = no
   guest ok = no
   create mask = 0775
   directory mask = 0775
   valid users = @users root
EOF
    systemctl restart smbd
fi

echo "=========================================================="
echo "Installation terminée avec succès !"
echo "Accès Web Cockpit : https://<IP-DE-VOTRE-PROXMOX>:9090"
echo "Plugins disponibles dans le menu de gauche :"
echo "  - File Sharing (45Drives)"
echo "  - Identities (Gestion des utilisateurs / groupes)"
echo "=========================================================="
