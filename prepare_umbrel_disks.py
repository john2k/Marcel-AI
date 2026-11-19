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
DISK_12TB_1="/dev/disk/by-id/ata-ST12000VN0007-2GS116_ZJV5FBBW"
DISK_12TB_2="/dev/disk/by-id/ata-ST12000VN0008-2PH103_ZLW2KWN5"

echo "=== [1/5] ARRET DE LA VM 100 ==="
qm stop 100 || true
while qm status 100 | grep -q "running"; do
    echo "Attente de l arret complet..."
    sleep 2
done

echo "=== [2/5] CREATION DES PARTITIONS GPT SUR L HOTE ==="
sgdisk -Z "$DISK_8TB"
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"HDD_8TB" "$DISK_8TB"

sgdisk -Z "$DISK_12TB_1"
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"HDD_12TB_1" "$DISK_12TB_1"

sgdisk -Z "$DISK_12TB_2"
sgdisk -o -n 1:0:0 -t 1:8300 -c 1:"HDD_12TB_2" "$DISK_12TB_2"

partprobe
sleep 2

echo "=== [3/5] FORMATAGE EN EXT4 (RAPIDE) AVEC LABELS ==="
# -T largefile4 pour optimiser l allocation des inodes sur les disques de 8-12 To
mkfs.ext4 -F -T largefile4 -L "HDD_8TB" "${DISK_8TB}-part1"
mkfs.ext4 -F -T largefile4 -L "HDD_12TB_1" "${DISK_12TB_1}-part1"
mkfs.ext4 -F -T largefile4 -L "HDD_12TB_2" "${DISK_12TB_2}-part1"

echo "=== [4/5] CONFIGURATION EN SATA SUR LA VM 100 (RECONNAISSANCE NATIVE) ==="
# Suppression des anciens slots scsi1/scsi2/scsi3
qm set 100 -delete scsi1,scsi2,scsi3 || true

# Attachement en SATA (émulation AHCI native, vue comme disque physique standard par udisks2)
qm set 100 -sata1 "$DISK_8TB"
qm set 100 -sata2 "$DISK_12TB_1"
qm set 100 -sata3 "$DISK_12TB_2"

echo "Verification de la configuration de la VM 100 :"
qm config 100 | grep -E "sata|scsi|boot"

echo "=== [5/5] REDEMARRAGE DE LA VM 100 ==="
qm start 100
echo "Statut VM 100 : $(qm status 100)"
"""

def execute_remote():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/prepare_umbrel_disks.sh", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/prepare_umbrel_disks.sh && /tmp/prepare_umbrel_disks.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(execute_remote())
