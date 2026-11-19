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
import socket, sys

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(3.0)
try:
    s.connect("/var/run/qemu-server/100.serial0")
    s.sendall(b"\\n")
    data = s.recv(8192)
    print("--- SERIAL DATA RECEIVED ---")
    print(data.decode("utf-8", errors="replace"))
except Exception as e:
    print("Error:", e)
finally:
    s.close()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()
    with sftp.file("/tmp/check_serial.py", "w") as f:
        f.write(SCRIPT)
    sftp.close()

    stdin, stdout, stderr = client.exec_command("python3 /tmp/check_serial.py", get_pty=True)
    print(stdout.read().decode('utf-8', errors='replace'))
    client.close()

if __name__ == "__main__":
    main()
