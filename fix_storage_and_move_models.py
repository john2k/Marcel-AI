import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), port=22, username="root", password=os.environ.get('PROXMOX_PASSWORD', ''))

script = """
pct exec 100 -- bash -c '
set -euo pipefail
echo "=== 1. Stopping Ollama ==="
systemctl stop ollama

echo "=== 2. Moving models to 29TB datastore ==="
mkdir -p /root/.ollama/models
if [ -d /usr/share/ollama/.ollama/models ]; then
    cp -rn /usr/share/ollama/.ollama/models/* /root/.ollama/models/ 2>/dev/null || true
    rm -rf /usr/share/ollama/.ollama
fi

mkdir -p /usr/share/ollama
ln -sfn /root/.ollama /usr/share/ollama/.ollama
chown -R ollama:ollama /root/.ollama
chown -h ollama:ollama /usr/share/ollama/.ollama

# Nettoyer les fichiers partiels temporaires
rm -f /root/.ollama/models/blobs/*-partial 2>/dev/null || true

echo "=== 3. Updating systemd environment ==="
cat << "EOF" > /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_MODELS=/root/.ollama/models"
Environment="OLLAMA_VULKAN=1"
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
EOF

systemctl daemon-reload
systemctl start ollama
sleep 3

echo "=== 4. Check Disk Space ==="
df -h / /root/.ollama
ollama list
'
"""

stdin, stdout, stderr = client.exec_command(script, get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")
client.close()
