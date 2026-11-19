import os
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

TOKEN_FILE = "/datastore/civitai_token.txt"
downloads = []

def get_saved_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    return ""

def download_worker(url, target_dir, filename, task_id, civitai_token):
    try:
        downloads[task_id]["status"] = "Connexion au serveur..."
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        # Check if Civitai URL
        is_civitai = "civitai.com" in url or "civitai.red" in url
        token = civitai_token or get_saved_token()
        
        if is_civitai and token:
            headers["Authorization"] = f"Bearer {token}"
            if "token=" not in url:
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}token={token}"

        downloads[task_id]["status"] = "Téléchargement en cours..."
        
        with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as r:
            # Check for Civitai login redirect
            if "reason=download-auth" in r.url or "login" in r.url:
                downloads[task_id]["status"] = "Erreur: Ce modèle Civitai nécessite une clé API (Compte / 18+ requis). Renseigne ta clé API Civitai ci-dessous."
                downloads[task_id]["error"] = True
                return

            r.raise_for_status()
            
            # Detect filename
            if not filename:
                cd = r.headers.get("content-disposition", "")
                if "filename=" in cd:
                    matches = re.findall(r'filename\*?=(?:UTF-8\'\')?["\']?([^"\';\r\n]+)', cd)
                    if matches:
                        filename = matches[0].strip().strip('"').strip("'")
                
                if not filename:
                    parsed_path = urllib.parse.urlparse(r.url).path
                    base = os.path.basename(parsed_path)
                    if base and base != "download":
                        filename = base
                
                if not filename or filename == "download":
                    filename = f"model_{task_id}.safetensors"
            
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
            downloads[task_id]["error"] = False

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else 0
        if status_code == 403 or "reason=download-auth" in str(e):
            downloads[task_id]["status"] = "Erreur 403 : Modèle restreint Civitai (Compte / 18+ requis). Ajoute ta clé API Civitai."
        elif status_code == 404:
            downloads[task_id]["status"] = "Erreur 404 : Lien introuvable. Assure-toi de copier le lien direct du fichier .safetensors."
        else:
            downloads[task_id]["status"] = f"Erreur HTTP {status_code}: {str(e)}"
        downloads[task_id]["error"] = True
    except Exception as e:
        downloads[task_id]["status"] = f"Erreur: {str(e)}"
        downloads[task_id]["error"] = True

@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json or {}
    url = data.get("url", "").strip()
    folder = data.get("folder", "checkpoints")
    filename = data.get("filename", "").strip()
    civitai_token = data.get("civitai_token", "").strip()
    
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
        "downloaded_bytes": 0,
        "error": False
    }
    downloads.append(task_info)
    
    t = threading.Thread(target=download_worker, args=(url, target_dir, filename, task_id, civitai_token))
    t.daemon = True
    t.start()
    
    return jsonify({"success": True, "task": task_info})

@app.route("/api/downloads", methods=["GET"])
def list_downloads():
    return jsonify(downloads)

@app.route("/api/downloads/clear", methods=["POST"])
def clear_downloads():
    global downloads
    # Keep only running downloads
    downloads = [d for d in downloads if "en cours" in d.get("status", "").lower() or "démarrage" in d.get("status", "").lower()]
    return jsonify({"success": True, "remaining": len(downloads)})

@app.route("/api/civitai_token", methods=["GET", "POST"])
def manage_token():
    if request.method == "POST":
        token = (request.json or {}).get("token", "").strip()
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        return jsonify({"success": True, "has_token": bool(token)})
    else:
        token = get_saved_token()
        masked = token[:4] + "..." + token[-4:] if len(token) > 8 else ("***" if token else "")
        return jsonify({"has_token": bool(token), "masked_token": masked})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8085)
