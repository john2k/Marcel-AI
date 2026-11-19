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
stdin, stdout, stderr = ssh.exec_command('pct exec 100 -- python3 -c "import sqlite3; conn = sqlite3.connect(\'/app/backend/data/webui.db\'); c = conn.cursor(); print([row for row in c.execute(\'SELECT key, value FROM config\') if \'audio\' in row[0] or \'tts\' in row[0] or \'stt\' in row[0] or \'voice\' in row[0]])"')
print("AUDIO CONFIG:")
print(stdout.read().decode())
