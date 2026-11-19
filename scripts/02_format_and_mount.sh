#!/usr/bin/env bash
# ==============================================================================
# Script 02 : Partitionnement GPT, formatage XFS et configuration fstab
# ==============================================================================
set -euo pipefail

# SÉCURITÉ : Remplacer impérativement ces variables après confirmation de l'Étape 1
DISK_8TB_ID=""       # Ex: /dev/disk/by-id/ata-WDC_WD80EFZX-...
DISK_12TB_DATA_ID=""  # Ex: /dev/disk/by-id/ata-WDC_WD120EFBX-...
DISK_12TB_PARITY_ID=""# Ex: /dev/disk/by-id/ata-WDC_WD120EFBX-...

if [[ -z "$DISK_8TB_ID" || -z "$DISK_12TB_DATA_ID" || -z "$DISK_12TB_PARITY_ID" ]]; then
    echo "ERREUR DE SÉCURITÉ : Veuillez renseigner les IDs matériels des 3 disques avant exécution."
    exit 1
fi

# Interdiction stricte de toucher au NVMe
for id in "$DISK_8TB_ID" "$DISK_12TB_DATA_ID" "$DISK_12TB_PARITY_ID"; do
    if [[ "$id" =~ nvme ]]; then
        echo "ALERTE CRITIQUE : Un identifiant NVMe a été détecté dans les cibles ! Arrêt immédiat."
        exit 1
    fi
done

echo "Création des points de montage..."
mkdir -p /mnt/disk1 /mnt/disk2 /mnt/parity1 /mnt/storage

echo "Partitionnement GPT (sgdisk) et étiquetage..."
sgdisk -Z "$DISK_8TB_ID"
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"data1_8tb" "$DISK_8TB_ID"

sgdisk -Z "$DISK_12TB_DATA_ID"
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"data2_12tb" "$DISK_12TB_DATA_ID"

sgdisk -Z "$DISK_12TB_PARITY_ID"
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"parity1_12tb" "$DISK_12TB_PARITY_ID"

# Rafraîchir la table des partitions
partprobe

# Récupération des partitions
PART_8TB="${DISK_8TB_ID}-part1"
PART_12TB_DATA="${DISK_12TB_DATA_ID}-part1"
PART_12TB_PARITY="${DISK_12TB_PARITY_ID}-part1"

echo "Formatage en XFS..."
mkfs.xfs -f -L data1 "$PART_8TB"
mkfs.xfs -f -L data2 "$PART_12TB_DATA"
mkfs.xfs -f -L parity1 "$PART_12TB_PARITY"

# Récupération des UUID
UUID_DATA1=$(blkid -s UUID -o value "$PART_8TB")
UUID_DATA2=$(blkid -s UUID -o value "$PART_12TB_DATA")
UUID_PARITY1=$(blkid -s UUID -o value "$PART_12TB_PARITY")

echo "Sauvegarde de /etc/fstab..."
cp /etc/fstab /etc/fstab.bak.$(date +%F_%T)

echo "Ajout des montages persistants dans /etc/fstab..."
cat << EOF >> /etc/fstab

# --- Stockage HDD (Data & Parité) ---
UUID=${UUID_DATA1}   /mnt/disk1    xfs   defaults,noatime,nofail   0 2
UUID=${UUID_DATA2}   /mnt/disk2    xfs   defaults,noatime,nofail   0 2
UUID=${UUID_PARITY1} /mnt/parity1  xfs   defaults,noatime,nofail   0 2
EOF

systemctl daemon-reload
mount -a

echo "Montages effectués :"
df -h /mnt/disk1 /mnt/disk2 /mnt/parity1
