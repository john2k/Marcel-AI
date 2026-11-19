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

cmd = """pct exec 100 -- bash -c 'curl -s -X POST http://127.0.0.1:8880/v1/audio/speech -H "Content-Type: application/json" -d "{\\"model\\": \\"kokoro\\", \\"input\\": \\"Bonjour, le studio créatif est en ligne.\\", \\"voice\\": \\"ff_siwis\\"}" -o /tmp/test_speech.mp3 && ls -lh /tmp/test_speech.mp3'"""
stdin, stdout, stderr = ssh.exec_command(cmd)
print("TTS TEST RESULT:")
print(stdout.read().decode())
print(stderr.read().decode())
