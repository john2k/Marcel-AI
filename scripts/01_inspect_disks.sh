#!/usr/bin/env bash
# ==============================================================================
# Script 01 : Inspection sécurisée du matériel de stockage
# Proxmox VE 8 / Debian 12 (Bookworm)
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo " [1/3] VÉRIFICATION DU DISQUE SYSTÈME (NVMe - PROTECTION)"
echo "=========================================================="
lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS,MODEL | grep -E "nvme|pve" || true
echo ""

echo "=========================================================="
echo " [2/3] TOPOLOGIE COMPLÈTE DES DISQUES ET SERIALS"
echo "=========================================================="
lsblk -o NAME,SIZE,FSTYPE,LABEL,MODEL,SERIAL,TRAN,MOUNTPOINTS
echo ""

echo "=========================================================="
echo " [3/3] IDENTIFIANTS PERSISTANTS MATÉRIELS (/dev/disk/by-id)"
echo "=========================================================="
ls -l /dev/disk/by-id/ | grep -v "part" | grep -E "ata-|scsi-|nvme-" || true

echo ""
echo "----------------------------------------------------------"
echo "CONSIGNE DE SÉCURITÉ :"
echo "Relevez les identifiants uniques (/dev/disk/by-id/ata-...) pour :"
echo "  1) Le HDD 8 To  (Data 1)"
echo "  2) Le HDD 12 To (Data 2)"
echo "  3) Le HDD 12 To (Parity 1 - STRICTEMENT IDENTIQUE OU PLUS GRAND)"
echo "Ne procédez à AUCUN formatage avant validation."
echo "----------------------------------------------------------"
