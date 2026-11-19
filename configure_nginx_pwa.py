import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username='root', password=os.environ.get('PROXMOX_PASSWORD', ''))

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

    # Model Downloader API
    location /api/ {
        proxy_pass http://127.0.0.1:8085/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # PWA App Shell
    location / {
        try_files $uri $uri/ /index.html;
    }
}
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/nginx_default.conf', 'w') as f:
    f.write(nginx_conf)
sftp.close()

commands = [
    "pct push 100 /tmp/nginx_default.conf /etc/nginx/sites-available/default",
    "pct exec 100 -- nginx -t",
    "pct exec 100 -- systemctl reload nginx"
]

for cmd in commands:
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print("ERR:", err)

ssh.close()
