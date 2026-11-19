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

nginx_conf = """server {
    listen 80 default_server;
    listen 8080 default_server;
    server_name _;

    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api/download {
        proxy_pass http://127.0.0.1:8085/api/download;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/downloads {
        proxy_pass http://127.0.0.1:8085/api/downloads;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/nginx_site', 'w') as f:
    f.write(nginx_conf)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('pct push 100 /tmp/nginx_site /etc/nginx/sites-available/default && pct exec 100 -- systemctl restart nginx')
print(stdout.read().decode())
print(stderr.read().decode())
