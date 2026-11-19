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

cmd = "pct exec 100 -- journalctl -u ollama -n 30 --no-pager"
stdin, stdout, stderr = client.exec_command(cmd)
print("=== Ollama Logs ===")
print(stdout.read().decode())

cmd2 = "pct exec 100 -- ps aux | grep -E 'ollama|python|docker'"
stdin, stdout, stderr = client.exec_command(cmd2)
print("=== Processes ===")
print(stdout.read().decode())

client.close()
