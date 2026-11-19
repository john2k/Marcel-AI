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

echo "=== [1/6] ARRET DES SERVICES SNAPRAID ET AUTOMATISATION ==="
systemctl stop snapraid-runner.timer || true
systemctl disable snapraid-runner.timer || true
rm -f /etc/systemd/system/snapraid-runner.service /etc/systemd/system/snapraid-runner.timer
systemctl daemon-reload

echo "=== [2/6] NETTOYAGE DU PARTAGE SAMBA ==="
if [ -f /etc/samba/smb.conf ]; then
    sed -i '/\[StoragePool\]/,+8d' /etc/samba/smb.conf || true
    systemctl restart smbd nmbd || true
fi

echo "=== [3/6] DEMONTAGE DES VOLUMES SUR L HOTE ==="
umount /mnt/storage || true
umount /mnt/parity1 || true
umount /mnt/disk1 || true
umount /mnt/disk2 || true

echo "=== [4/6] NETTOYAGE DE /etc/fstab ==="
sed -i '/\/mnt\/disk/d' /etc/fstab
sed -i '/\/mnt\/parity1/d' /etc/fstab
sed -i '/\/mnt\/storage/d' /etc/fstab
systemctl daemon-reload

rm -f /var/snapraid.content

echo "=== [5/6] REMISE A ZERO DES DISQUES (RAW POUR UMBREL OS) ==="
DISK_8TB="/dev/disk/by-id/ata-ST8000VN004-3CP101_WWZ2MCD8"
DISK_12TB_1="/dev/disk/by-id/ata-ST12000VN0007-2GS116_ZJV5FBBW"
DISK_12TB_2="/dev/disk/by-id/ata-ST12000VN0008-2PH103_ZLW2KWN5"

# Verification stricte NVMe
for d in "$DISK_8TB" "$DISK_12TB_1" "$DISK_12TB_2"; do
    if [[ "$d" =~ nvme ]]; then
        echo "ERREUR CRITIQUE : NVME DETECTE DANS LES CIBLES !"
        exit 1
    fi
done

wipefs -a ${DISK_8TB}* || true
wipefs -a ${DISK_12TB_1}* || true
wipefs -a ${DISK_12TB_2}* || true

sgdisk -Z "$DISK_8TB"
sgdisk -Z "$DISK_12TB_1"
sgdisk -Z "$DISK_12TB_2"
partprobe
sleep 2

echo "=== [6/6] ATTACHEMENT DES HDD A LA VM 100 (PASSTHROUGH) ==="
qm set 100 -scsi1 "$DISK_8TB"
qm set 100 -scsi2 "$DISK_12TB_1"
qm set 100 -scsi3 "$DISK_12TB_2"

echo "Configuration actuelle de la VM 100 :"
qm config 100
"""

def execute_remote():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/revert_and_passthrough.sh", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/revert_and_passthrough.sh && /tmp/revert_and_passthrough.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(execute_remote())
