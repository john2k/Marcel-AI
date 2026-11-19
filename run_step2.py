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

REMOTE_SCRIPT = """#!/usr/bin/env bash
set -euo pipefail

DISK_8TB="/dev/disk/by-id/ata-ST8000VN004-3CP101_WWZ2MCD8"
DISK_12TB_DATA="/dev/disk/by-id/ata-ST12000VN0007-2GS116_ZJV5FBBW"
DISK_12TB_PARITY="/dev/disk/by-id/ata-ST12000VN0008-2PH103_ZLW2KWN5"

echo "=== [1/6] NETTOYAGE DES ANCIENNES SIGNATURES ZFS ET PARTITIONS ==="
wipefs -a ${DISK_8TB}* || true
wipefs -a ${DISK_12TB_DATA}* || true
wipefs -a ${DISK_12TB_PARITY}* || true

sgdisk -Z "$DISK_8TB"
sgdisk -Z "$DISK_12TB_DATA"
sgdisk -Z "$DISK_12TB_PARITY"

echo "=== [2/6] CRÉATION DES PARTITIONS GPT ==="
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"data1_8tb" "$DISK_8TB"
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"data2_12tb" "$DISK_12TB_DATA"
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"parity1_12tb" "$DISK_12TB_PARITY"

partprobe
sleep 3

echo "=== [3/6] FORMATAGE EN XFS ==="
PART_8TB="${DISK_8TB}-part1"
PART_12TB_DATA="${DISK_12TB_DATA}-part1"
PART_12TB_PARITY="${DISK_12TB_PARITY}-part1"

mkfs.xfs -f -L data1 "$PART_8TB"
mkfs.xfs -f -L data2 "$PART_12TB_DATA"
mkfs.xfs -f -L parity1 "$PART_12TB_PARITY"

echo "=== [4/6] CRÉATION DES POINTS DE MONTAGE ==="
mkdir -p /mnt/disk1 /mnt/disk2 /mnt/parity1 /mnt/storage

UUID_DATA1=$(blkid -s UUID -o value "$PART_8TB")
UUID_DATA2=$(blkid -s UUID -o value "$PART_12TB_DATA")
UUID_PARITY1=$(blkid -s UUID -o value "$PART_12TB_PARITY")

echo "UUID Data 1 (8TB): $UUID_DATA1"
echo "UUID Data 2 (12TB): $UUID_DATA2"
echo "UUID Parity 1 (12TB): $UUID_PARITY1"

echo "=== [5/6] CONFIGURATION DANS /etc/fstab ==="
cp /etc/fstab /etc/fstab.bak.$(date +%F_%T)

# Supprimer anciennes lignes éventuelles
sed -i '/\/mnt\/disk1/d' /etc/fstab
sed -i '/\/mnt\/disk2/d' /etc/fstab
sed -i '/\/mnt\/parity1/d' /etc/fstab

cat << EOF >> /etc/fstab

# --- Stockage SnapRAID / MergerFS (HDD) ---
UUID=${UUID_DATA1}   /mnt/disk1    xfs   defaults,noatime,nofail   0 2
UUID=${UUID_DATA2}   /mnt/disk2    xfs   defaults,noatime,nofail   0 2
UUID=${UUID_PARITY1} /mnt/parity1  xfs   defaults,noatime,nofail   0 2
EOF

systemctl daemon-reload
mount -a

echo "=== [6/6] VÉRIFICATION DES MONTAGES PHYSIQUES ==="
df -hT /mnt/disk1 /mnt/disk2 /mnt/parity1
"""

def execute_remote():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/deploy_step2.sh", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/deploy_step2.sh && /tmp/deploy_step2.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(execute_remote())
