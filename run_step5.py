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

echo "=== [1/4] VÉRIFICATION DES MODULES COCKPIT INSTALLES ==="
ls -l /usr/share/cockpit/

echo "=== [2/4] CONFIGURATION DU PARTAGE SAMBA SUR /mnt/storage ==="
chmod 777 /mnt/storage
chmod 777 /mnt/disk1 /mnt/disk2

SAMBA_CONF="/etc/samba/smb.conf"
if ! grep -q "\[StoragePool\]" "$SAMBA_CONF"; then
    cat << 'EOF' >> /etc/samba/smb.conf

[StoragePool]
   comment = Pool Unifie MergerFS
   path = /mnt/storage
   browseable = yes
   read only = no
   guest ok = yes
   create mask = 0777
   directory mask = 0777
EOF
fi

systemctl restart smbd nmbd

echo "=== [3/4] STATUT DES SERVICES COCKPIT ET SAMBA ==="
systemctl is-active cockpit.socket smbd nmbd

echo "=== [4/4] TEST D ECRITURE DANS LE POOL MERGERFS ==="
echo "Test ecriture MergerFS $(date)" > /mnt/storage/test_pool.txt
ls -la /mnt/storage/test_pool.txt
cat /mnt/storage/test_pool.txt

echo "Verification sur quel disque physique le fichier a ete cree :"
ls -la /mnt/disk*/test_pool.txt || true
rm -f /mnt/storage/test_pool.txt

echo "TOUT EST FONCTIONNEL !"
"""

def execute_remote():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/deploy_step5.sh", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/deploy_step5.sh && /tmp/deploy_step5.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(execute_remote())
