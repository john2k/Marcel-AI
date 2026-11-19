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
docker rm -f open-webui 2>/dev/null || true

docker run -d \\
  --name open-webui \\
  --restart always \\
  --network host \\
  --security-opt apparmor=unconfined \\
  -e OLLAMA_BASE_URL=http://127.0.0.1:11434 \\
  -e AUDIO_TTS_ENGINE=openai \\
  -e AUDIO_TTS_OPENAI_API_BASE_URL=http://127.0.0.1:8880/v1 \\
  -e AUDIO_TTS_OPENAI_API_KEY=kokoro \\
  -e AUDIO_TTS_VOICE=am_fenrir \\
  -v /app/backend/data:/app/backend/data \\
  ghcr.io/open-webui/open-webui:main

sleep 4
docker ps
'
"""
stdin, stdout, stderr = client.exec_command(script, get_pty=True)
for line in iter(stdout.readline, ""):
    print(line, end="")
client.close()
