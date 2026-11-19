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

test_script = """
import os
os.environ['GRADIO_ROOT_PATH'] = '/fooocus'
import gradio as gr

with gr.Blocks() as demo:
    gr.Markdown("# Test Fooocus Subpath")

app, local_url, share_url = demo.launch(server_name='127.0.0.1', server_port=7899, prevent_thread_lock=True)
print("Started on local_url:", local_url)
print("App root_path:", getattr(demo, 'root_path', None))

import urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:7899/fooocus/', timeout=5) as r:
        print('/fooocus/ status:', r.status)
except Exception as e:
    print('/fooocus/ error:', e)

try:
    with urllib.request.urlopen('http://127.0.0.1:7899/', timeout=5) as r:
        print('/ status:', r.status)
except Exception as e:
    print('/ error:', e)

demo.close()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_gradio_subpath.py', 'w') as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/test_gradio_subpath.py /tmp/test_gradio_subpath.py")
stdin, stdout, stderr = ssh.exec_command("pct exec 100 -- /datastore/Fooocus/venv/bin/python /tmp/test_gradio_subpath.py")
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
