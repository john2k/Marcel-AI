import os
if os.path.exists('.env'):
    with open('.env') as _f:
        for _l in _f:
            if '=' in _l and not _l.startswith('#'):
                _k, _v = _l.strip().split('=', 1)
                os.environ.setdefault(_k, _v)

import sys
import paramiko

HOST = os.environ.get('PROXMOX_HOST', '192.168.1.100')
PORT = 22
USER = "root"
PASS = os.environ.get('PROXMOX_PASSWORD', '')

SCRIPT = """#!/usr/bin/env python3
import socket, json, os

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/var/run/qemu-server/100.qmp")
s.recv(1024)
s.sendall(json.dumps({"execute": "qmp_capabilities"}).encode() + b"\\n")
s.recv(1024)
s.sendall(json.dumps({"execute": "screendump", "arguments": {"filename": "/tmp/hexos_screen.ppm"}}).encode() + b"\\n")
s.recv(1024)
s.close()
print("Screendump taken. Size:", os.path.getsize("/tmp/hexos_screen.ppm"))
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/dump_screen.py", "w") as f:
        f.write(SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/dump_screen.py", get_pty=True)
    print(stdout.read().decode('utf-8', errors='replace'))
    client.close()

if __name__ == "__main__":
    main()
