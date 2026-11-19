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

code = '''import os
import re
import urllib.parse
import threading
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

MODELS_BASE = "/datastore/ComfyUI/models"
ALLOWED_FOLDERS = {
    "checkpoints": os.path.join(MODELS_BASE, "checkpoints"),
    "loras": os.path.join(MODELS_BASE, "loras"),
    "vae": os.path.join(MODELS_BASE, "vae"),
    "controlnet": os.path.join(MODELS_BASE, "controlnet"),
    "animatediff_models": os.path.join(MODELS_BASE, "animatediff_models")
}

downloads = []

def download_worker(url, target_dir, filename, task_id):
    try:
        downloads[task_id]["status"] = "Téléchargement en cours..."
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            
            if not filename:
                cd = r.headers.get("content-disposition", "")
                if "filename=" in cd:
                    filename = re.findall(r'filename\*?=(?:UTF-8\\'\\')?["\\']?([^"\\';\\r\\n]+)', cd)[0]
                else:
                    filename = os.path.basename(urllib.parse.urlparse(r.url).path)
                
                if not filename or filename == "download":
                    filename = "model_" + str(task_id) + ".safetensors"
            
            clean_filename = urllib.parse.unquote(filename).strip()
            downloads[task_id]["filename"] = clean_filename
            out_path = os.path.join(target_dir, clean_filename)
            downloads[task_id]["path"] = out_path
            
            total_size = int(r.headers.get("content-length", 0))
            downloads[task_id]["total_bytes"] = total_size
            
            downloaded = 0
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024*4):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        downloads[task_id]["downloaded_bytes"] = downloaded
                        if total_size > 0:
                            downloads[task_id]["progress"] = round((downloaded / total_size) * 100, 1)
            
            downloads[task_id]["status"] = "Terminé avec succès!"
            downloads[task_id]["progress"] = 100
    except Exception as e:
        downloads[task_id]["status"] = f"Erreur: {str(e)}"

@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json or {}
    url = data.get("url", "").strip()
    folder = data.get("folder", "checkpoints")
    filename = data.get("filename", "").strip()
    
    if not url:
        return jsonify({"error": "URL manquante"}), 400
    
    target_dir = ALLOWED_FOLDERS.get(folder, ALLOWED_FOLDERS["checkpoints"])
    os.makedirs(target_dir, exist_ok=True)
    
    task_id = len(downloads)
    task_info = {
        "id": task_id,
        "url": url,
        "folder": folder,
        "filename": filename or "Recherche du nom...",
        "progress": 0,
        "status": "Démarrage...",
        "total_bytes": 0,
        "downloaded_bytes": 0
    }
    downloads.append(task_info)
    
    t = threading.Thread(target=download_worker, args=(url, target_dir, filename, task_id))
    t.daemon = True
    t.start()
    
    return jsonify({"success": True, "task": task_info})

@app.route("/api/downloads", methods=["GET"])
def list_downloads():
    return jsonify(downloads)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8085)
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/model_downloader.py', 'w') as f:
    f.write(code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('pct push 100 /tmp/model_downloader.py /opt/model_downloader.py && pct exec 100 -- systemctl restart model-downloader')
print(stdout.read().decode())
print(stderr.read().decode())
