import os
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ.setdefault(k, v)

import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username=os.environ.get('PROXMOX_USER', 'root'), password=os.environ.get('PROXMOX_PASSWORD', ''))

def run_cmd(cmd):
    stdin, stdout, stderr = ssh.exec_command(f'pct exec 100 -- {cmd}')
    out = stdout.read().decode('utf-8', errors='ignore')
    err = stderr.read().decode('utf-8', errors='ignore')
    return out.strip(), err.strip()

print("1. Pushing marcel_core_api.py to LXC 100...")
sftp = ssh.open_sftp()
with open("marcel_core_api.py", "rb") as lf:
    with sftp.open("/tmp/marcel_core_api.py", "wb") as rf:
        rf.write(lf.read())
sftp.close()

run_cmd("cp /tmp/marcel_core_api.py /opt/marcel_core_api.py")
run_cmd("chmod +x /opt/marcel_core_api.py")

print("2. Configuring systemd service marcel-core.service...")
service_content = """[Unit]
Description=Marcel Studio Core API (Downloader, Log Analyzer, Vibe Coder)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt
ExecStart=/usr/bin/python3 /opt/marcel_core_api.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""

run_cmd(f"bash -c \"cat << 'EOF' > /etc/systemd/system/marcel-core.service\n{service_content}\nEOF\"")
run_cmd("systemctl stop model-downloader || true")
run_cmd("systemctl disable model-downloader || true")
run_cmd("systemctl daemon-reload")
run_cmd("systemctl enable marcel-core")
run_cmd("systemctl restart marcel-core")

print("3. Updating Nginx configuration...")
nginx_conf = """map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80 default_server;
    listen 8080 default_server;
    server_name _;

    root /var/www/html;
    index index.html;

    client_max_body_size 500M;

    # Service Worker & Manifest headers
    location = /sw.js {
        add_header Cache-Control "no-cache";
        add_header Service-Worker-Allowed "/";
    }
    location = /manifest.json {
        add_header Cache-Control "no-cache";
        add_header Access-Control-Allow-Origin "*";
    }

    # Marcel Core API (Downloader, Logs, Vibe Coder)
    location /api/ {
        proxy_pass http://127.0.0.1:8085/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # Workspace Live Preview (Vibe Coder)
    location /workspace_preview/ {
        alias /datastore/workspace/;
        index index.html;
        autoindex on;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Access-Control-Allow-Origin "*";
    }

    # Fooocus (SDXL Midjourney Simple)
    location /fooocus/ {
        proxy_pass http://127.0.0.1:7865/fooocus/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }

    # Kokoro TTS (Voice Studio)
    location /tts/ {
        proxy_pass http://127.0.0.1:8880/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # ComfyUI (Advanced Nodes & Video)
    location /comfy/ {
        proxy_pass http://127.0.0.1:8188/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 86400;
    }

    # Open WebUI (Gemini Chat) static assets & API
    location /_app/ {
        proxy_pass http://127.0.0.1:3000/_app/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
    location /ollama/ {
        proxy_pass http://127.0.0.1:3000/ollama/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
    }
    location /ws/ {
        proxy_pass http://127.0.0.1:3000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
    }
    location /chat/ {
        proxy_pass http://127.0.0.1:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }

    # PWA App Shell
    location / {
        try_files $uri $uri/ /index.html;
    }
}
"""

run_cmd(f"bash -c \"cat << 'EOF' > /etc/nginx/sites-available/default\n{nginx_conf}\nEOF\"")
out, err = run_cmd("nginx -t")
print("Nginx test:", out, err)
run_cmd("systemctl reload nginx")

print("4. Verifying marcel-core service status...")
status, _ = run_cmd("systemctl status marcel-core --no-pager")
print(status[:400])

ssh.close()
