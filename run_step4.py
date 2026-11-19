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

echo "=== [1/5] CONFIGURATION DE /etc/snapraid.conf ==="
cat << 'EOF' > /etc/snapraid.conf
# ==============================================================================
# SnapRAID Configuration for Proxmox VE 8/9
# ==============================================================================

# Disque de parité (12 To)
parity /mnt/parity1/snapraid.parity

# Fichiers de métadonnées (1 sur root NVMe + 1 par disque de données)
content /var/snapraid.content
content /mnt/disk1/.snapraid.content
content /mnt/disk2/.snapraid.content

# Disques de données
data d1 /mnt/disk1/
data d2 /mnt/disk2/

# Exclusions
exclude *.unrecoverable
exclude /tmp/
exclude /lost+found/
exclude .snapshots/
exclude *.bak
exclude *.tmp
exclude .DS_Store
exclude Thumbs.db
exclude .Trash-*/
EOF

echo "=== [2/5] INSTALLATION DE SNAPRAID-RUNNER ==="
mkdir -p /opt/snapraid-runner
if [ ! -d "/opt/snapraid-runner/.git" ]; then
    rm -rf /opt/snapraid-runner
    git clone https://github.com/Chronial/snapraid-runner.git /opt/snapraid-runner
fi

cat << 'EOF' > /opt/snapraid-runner/snapraid-runner.conf
[snapraid]
executable = /usr/bin/snapraid
config = /etc/snapraid.conf
deletethreshold = 100
touch = true

[logging]
file = /var/log/snapraid-runner.log
maxsize = 5000

[email]
enabled = false

[scrub]
enabled = true
percentage = 5
older-than = 10
EOF

echo "=== [3/5] CONFIGURATION SYSTEMD DU TIMER SNAPRAID ==="
cat << 'EOF' > /etc/systemd/system/snapraid-runner.service
[Unit]
Description=SnapRAID Runner Backup and Scrub Job
After=network.target local-fs.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/snapraid-runner/snapraid-runner.py -c /opt/snapraid-runner/snapraid-runner.conf
User=root
EOF

cat << 'EOF' > /etc/systemd/system/snapraid-runner.timer
[Unit]
Description=Daily SnapRAID Sync and Scrub Timer

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now snapraid-runner.timer

echo "=== [4/5] INITIALISATION SNAPRAID TOUCH ==="
snapraid touch

echo "=== [5/5] INITIALISATION PREMIER SNAPRAID SYNC ==="
snapraid sync

echo "Vérification du statut SnapRAID :"
snapraid status
"""

def execute_remote():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/deploy_step4.sh", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("chmod +x /tmp/deploy_step4.sh && /tmp/deploy_step4.sh", get_pty=True)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    code = stdout.channel.recv_exit_status()
    client.close()
    return code

if __name__ == "__main__":
    sys.exit(execute_remote())
