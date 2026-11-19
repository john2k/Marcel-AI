import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko
import json
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username='root', password=os.environ.get('PROXMOX_PASSWORD', ''))

# 1. code-server systemd service
service_code = """[Unit]
Description=code-server (Web VS Code / Cursor IDE)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/datastore/workspace
ExecStart=/usr/bin/code-server --bind-addr 0.0.0.0:8088 --auth none --disable-telemetry /datastore/workspace
Restart=always
RestartSec=5
Environment=PASSWORD=""

[Install]
WantedBy=multi-user.target
"""

# 2. Continue.dev config (Cursor-like AI Assistant connected to local Ollama)
continue_config = {
    "models": [
        {
            "title": "Qwen 2.5 Coder 7B (Local AI)",
            "provider": "ollama",
            "model": "qwen2.5-coder:7b",
            "apiBase": "http://127.0.0.1:11434"
        },
        {
            "title": "Llama 3.2 3B (Fast Chat)",
            "provider": "ollama",
            "model": "llama3.2:3b",
            "apiBase": "http://127.0.0.1:11434"
        }
    ],
    "tabAutocompleteModel": {
        "title": "Autocomplete (Qwen Coder)",
        "provider": "ollama",
        "model": "qwen2.5-coder:7b",
        "apiBase": "http://127.0.0.1:11434"
    },
    "customCommands": [
        {
            "name": "test",
            "prompt": "Génère des tests unitaires complets pour ce code.",
            "description": "Générer des tests"
        },
        {
            "name": "explain",
            "prompt": "Explique ce code en détail en français.",
            "description": "Expliquer le code"
        },
        {
            "name": "fix",
            "prompt": "Trouve et corrige les bugs potentiels dans ce code.",
            "description": "Corriger les bugs"
        }
    ],
    "allowAnonymousTelemetry": False
}

sftp = ssh.open_sftp()
with sftp.file('/tmp/code-server.service', 'w') as f:
    f.write(service_code)
with sftp.file('/tmp/continue_config.json', 'w') as f:
    json.dump(continue_config, f, indent=2)
sftp.close()

cmds = [
    "pct exec 100 -- mkdir -p /datastore/workspace /root/.continue",
    "pct push 100 /tmp/code-server.service /etc/systemd/system/code-server.service",
    "pct push 100 /tmp/continue_config.json /root/.continue/config.json",
    "pct exec 100 -- systemctl daemon-reload",
    "pct exec 100 -- systemctl enable code-server.service",
    "pct exec 100 -- systemctl restart code-server.service",
    "pct exec 100 -- systemctl status code-server.service --no-pager"
]

for cmd in cmds:
    print(f"Exec: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

ssh.close()
