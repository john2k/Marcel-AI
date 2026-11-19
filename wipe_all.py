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

print("Stopping and destroying LXC 100...")
stdin, stdout, stderr = ssh.exec_command("pct stop 100; pct destroy 100 --purge 1")
print(stdout.read().decode())
print(stderr.read().decode())

print("Cleaning up old directories on /datastore...")
stdin, stdout, stderr = ssh.exec_command("rm -rf /datastore/ollama-models /datastore/open-webui-data /tmp/*")
print(stdout.read().decode())
print(stderr.read().decode())

print("Current LXC and VM list:")
stdin, stdout, stderr = ssh.exec_command("pct list; qm list")
print(stdout.read().decode())
print(stderr.read().decode())
