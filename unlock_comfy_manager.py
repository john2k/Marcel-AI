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

update_config = """
[default]
preview_method = none
git_exe = 
use_uv = True
channel_url = https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main
share_option = all
bypass_ssl = False
file_logging = True
component_policy = workflow
update_policy = stable-comfyui
windows_selector_event_loop_policy = False
model_download_by_agent = False
downgrade_blacklist = 
security_level = weak
always_lazy_install = False
network_mode = private
db_mode = cache
allow_git_url_install = True
allow_pip_install = True
allow_flagged_nodepack_install = True
"""

sftp = ssh.open_sftp()
with sftp.file('/datastore/ComfyUI/user/__manager/config.ini', 'w') as f:
    f.write(update_config.strip() + "\n")
sftp.close()

stdin, stdout, stderr = ssh.exec_command('pct exec 100 -- systemctl restart comfyui')
print("Restarting comfyui:", stdout.read().decode())
print(stderr.read().decode())
