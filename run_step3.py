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

echo "=== [1/3] CONFIGURATION DE MERGERFS DANS /etc/fstab ==="
mkdir -p /mnt/storage

# Options optimales MergerFS
MERGERFS_OPTS="cache.files=partial,dropcacheonclose=true,category.create=mfs,minfreespace=50G,fsname=mergerfsPool,x-systemd.requires=/mnt/disk1,x-systemd.requires=/mnt/disk2"

# Nettoyage si déjà présent
sed -i '/\/mnt\/storage/d' /etc/fstab

cat << EOF >> /etc/fstab

# --- Pool Unifié MergerFS ---
/mnt/disk*   /mnt/storage   mergerfs   ${MERGERFS_OPTS}   0 0
EOF

echo "=== [2/3] MONTAGE DU POOL MERGERFS ==="
systemctl daemon-reload
mount /mnt/storage

echo "=== [3/3] VÉRIFICATION DE L ESPACE DU POOL ==="
df -hT /mnt/storage
"""

def execute_remote():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/deploy_step3.sh", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/deploy_step3.sh && /tmp/deploy_step3.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(execute_remote())
