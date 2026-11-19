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

echo "=== [1/4] ARRET DE LA VM POUR FINALISATION ==="
qm stop 100 || true
while qm status 100 | grep -q "running"; do
    echo "Attente de l arret complet..."
    sleep 2
done

echo "=== [2/4] EJECTION DE L ISO D INSTALLATION ==="
qm set 100 -delete sata0
qm set 100 --boot 'order=scsi0'

echo "=== [3/4] RATTACHEMENT DES 3 DISQUES DURS EN PASSTHROUGH (ZFS) ==="
qm set 100 -scsi1 "$DISK_8TB"
qm set 100 -scsi2 "$DISK_12TB_1"
qm set 100 -scsi3 "$DISK_12TB_2"

echo "Configuration finale de la VM HexOS :"
qm config 100

echo "=== [4/4] DEMARRAGE DE HEXOS SUR SON DISQUE SYSTEME ==="
qm start 100
echo "Statut VM 100 : $(qm status 100)"
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/finalize_hexos.sh", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/finalize_hexos.sh && /tmp/finalize_hexos.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(main())
