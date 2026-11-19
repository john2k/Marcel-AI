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

code = '''import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()

updates = {
    'audio.tts.engine': json.dumps('openai'),
    'audio.tts.openai.api_base_url': json.dumps('http://127.0.0.1:8880/v1'),
    'audio.tts.openai.api_key': json.dumps('kokoro'),
    'audio.tts.voice': json.dumps('am_fenrir'),
    'audio.tts.model': json.dumps('kokoro'),
}

for k, v in updates.items():
    c.execute("UPDATE config SET value = ? WHERE key = ?", (v, k))

conn.commit()
print("Updated config successfully:")
for row in c.execute("SELECT key, value FROM config WHERE key LIKE 'audio.tts%'"):
    print(row)
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/update_tts.py', 'w') as f:
    f.write(code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('pct push 100 /tmp/update_tts.py /tmp/update_tts.py && pct exec 100 -- python3 /tmp/update_tts.py && pct exec 100 -- docker restart open-webui')
print(stdout.read().decode())
print(stderr.read().decode())
