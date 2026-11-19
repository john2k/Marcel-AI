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

# Pull huihui_ai/llama3.1-abliterated:8b and huihui_ai/qwen2.5-abliterated:7b
cmd = """pct exec 100 -- bash -c '
echo "Pulling huihui_ai/llama3.1-abliterated:8b..."
ollama pull huihui_ai/llama3.1-abliterated:8b
'"""
stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")
client.close()
