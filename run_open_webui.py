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

cmds = [
    "pct exec 100 -- bash -c 'echo nameserver 8.8.8.8 >> /etc/resolv.conf'",
    "pct exec 100 -- docker rm -f open-webui || true",
    "pct exec 100 -- docker run -d -p 3000:8080 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 -e WEBUI_AUTH=False --add-host=host.docker.internal:host-gateway -v /datastore/open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main"
]

for cmd in cmds:
    print(f"Exec: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print("ERR:", err)

ssh.close()
