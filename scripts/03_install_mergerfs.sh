#!/usr/bin/env bash
# ==============================================================================
# Script 03 : Installation et Configuration de MergerFS
# ==============================================================================
set -euo pipefail

echo "Installation de mergerfs..."
apt update
apt install -y mergerfs

# Vérification du point de montage
mkdir -p /mnt/storage

echo "Configuration du pool MergerFS dans /etc/fstab..."
# Options recommandées :
# cache.files=partial : performances équilibrées
# dropcacheonclose=true : libère le cache fichier à la fermeture
# category.create=mfs (Most Free Space) : répartit les écritures sur le disque ayant le plus de place disponible
# minfreespace=50G : réserve 50 Go avant de passer au disque suivant
# fsname=mergerfsPool : nom visible pour monitoring et SMB
# x-systemd.requires= : garantit que les disques physiques sont montés au préalable
MERGERFS_OPTS="cache.files=partial,dropcacheonclose=true,category.create=mfs,minfreespace=50G,fsname=mergerfsPool,x-systemd.requires=/mnt/disk1,x-systemd.requires=/mnt/disk2"

# Vérifie si le montage existe déjà
if ! grep -q "/mnt/storage" /etc/fstab; then
    cat << EOF >> /etc/fstab

# --- Pool Unifié MergerFS ---
/mnt/disk*   /mnt/storage   mergerfs   ${MERGERFS_OPTS}   0 0
EOF
fi

systemctl daemon-reload
mount /mnt/storage

echo "Vérification du pool unifié :"
df -h /mnt/storage
