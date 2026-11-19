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

stdin, stdout, stderr = ssh.exec_command('cat /etc/pve/lxc/100.conf')
current_conf = stdout.read().decode()
print("CURRENT CONF:\n", current_conf)

extra_config = """mp0: /datastore,mp=/datastore
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: c 226:* rwm
lxc.cgroup2.devices.allow: c 511:* rwm
lxc.mount.entry: /dev/kfd dev/kfd none bind,optional,create=file 0 0
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir 0 0
lxc.mount.entry: /dev/dri/card1 dev/dri/card1 none bind,optional,create=file 0 0
lxc.mount.entry: /dev/dri/renderD128 dev/dri/renderD128 none bind,optional,create=file 0 0
"""

new_conf = current_conf.strip() + "\n" + extra_config
sftp = ssh.open_sftp()
with sftp.file('/etc/pve/lxc/100.conf', 'w') as f:
    f.write(new_conf)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('pct start 100')
print("START STDOUT:\n", stdout.read().decode())
print("START STDERR:\n", stderr.read().decode())
