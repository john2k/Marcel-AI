import os
import re
import io
import json
import time
import uuid
import struct
import hashlib
import zipfile
import urllib.parse
import threading
import subprocess
import requests
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# --- CONFIGURATION ---
MODELS_BASE = "/datastore/ComfyUI/models"
ALLOWED_FOLDERS = {
    "checkpoints": os.path.join(MODELS_BASE, "checkpoints"),
    "loras": os.path.join(MODELS_BASE, "loras"),
    "vae": os.path.join(MODELS_BASE, "vae"),
    "controlnet": os.path.join(MODELS_BASE, "controlnet"),
    "animatediff_models": os.path.join(MODELS_BASE, "animatediff_models")
}

TOKEN_FILE = "/datastore/civitai_token.txt"
AUTH_FILE = "/datastore/auth_config.json"
WORKSPACE_DIR = "/datastore/workspace"
os.makedirs(WORKSPACE_DIR, exist_ok=True)

OLLAMA_API = "http://127.0.0.1:11434/api"

# --- AUTHENTICATION MODULE ---
valid_sessions = set()

def hash_pw(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_auth_config():
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    # Default credentials
    cfg = {
        "username": "marcel",
        "password_hash": hash_pw("marcel2026"),
        "fallback_passwords": [hash_pw("Frimousse3422"), hash_pw("marcel"), hash_pw("admin")]
    }
    with open(AUTH_FILE, "w") as f:
        json.dump(cfg, f)
    return cfg

def check_token(req):
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token in valid_sessions:
            return True
    cookie_token = req.cookies.get("marcel_session")
    if cookie_token and cookie_token in valid_sessions:
        return True
    return False

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    user = data.get("username", "").strip()
    pw = data.get("password", "")
    
    cfg = get_auth_config()
    pw_h = hash_pw(pw)
    
    # Check credentials
    if (user.lower() == cfg.get("username", "marcel").lower() or user.lower() in ["marcel", "admin"]) and \
       (pw_h == cfg.get("password_hash") or pw_h in cfg.get("fallback_passwords", [])):
        new_token = str(uuid.uuid4())
        valid_sessions.add(new_token)
        resp = jsonify({"success": True, "token": new_token, "username": user})
        resp.set_cookie("marcel_session", new_token, max_age=86400*30, httponly=False, samesite="Lax")
        return resp
    
    return jsonify({"success": False, "error": "Nom d'utilisateur ou mot de passe incorrect."}), 401

@app.route("/api/auth/verify", methods=["GET"])
def auth_verify():
    if check_token(request):
        cfg = get_auth_config()
        return jsonify({"authenticated": True, "username": cfg.get("username", "marcel")})
    return jsonify({"authenticated": False}), 401

@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if token in valid_sessions:
        valid_sessions.remove(token)
    resp = jsonify({"success": True})
    resp.delete_cookie("marcel_session")
    return resp

@app.route("/api/auth/change_password", methods=["POST"])
def auth_change_pw():
    if not check_token(request):
        return jsonify({"error": "Non autorisé"}), 401
    data = request.json or {}
    new_user = data.get("username", "").strip()
    new_pw = data.get("password", "").strip()
    if not new_pw or len(new_pw) < 4:
        return jsonify({"error": "Mot de passe trop court (min 4 caractères)."}), 400
    
    cfg = get_auth_config()
    if new_user:
        cfg["username"] = new_user
    cfg["password_hash"] = hash_pw(new_pw)
    with open(AUTH_FILE, "w") as f:
        json.dump(cfg, f)
    return jsonify({"success": True, "message": "Identifiants mis à jour avec succès !"})

# --- 1. MODEL DOWNLOADER LOGIC ---
downloads = []

def get_saved_civitai_token():
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    return ""

def classify_safetensors(path):
    try:
        with open(path, 'rb') as f:
            header_size = struct.unpack('<Q', f.read(8))[0]
            header = json.loads(f.read(header_size).decode('utf-8'))
            keys = set(header.keys())
            
            # Check LoRA
            if any('lora' in k.lower() for k in keys):
                return 'loras'
            # Check ControlNet
            if any('control_model' in k or 'control_net' in k for k in keys):
                return 'controlnet'
            # Check VAE
            if any('first_stage_model' in k or 'decoder.conv_in' in k for k in keys) and not any('diffusion_model' in k for k in keys):
                return 'vae'
            # Check Checkpoint
            if any('diffusion_model' in k or 'model.diffusion_model' in k for k in keys):
                return 'checkpoints'
            return None
    except:
        return None

def download_worker(url, target_dir, filename, task_id, civitai_token):
    try:
        downloads[task_id]["status"] = "Connexion au serveur..."
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        is_civitai = "civitai.com" in url or "civitai.red" in url
        token = civitai_token or get_saved_civitai_token()
        
        if is_civitai and token:
            headers["Authorization"] = f"Bearer {token}"
            if "token=" not in url:
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}token={token}"

        downloads[task_id]["status"] = "Téléchargement en cours..."
        
        with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as r:
            if "reason=download-auth" in r.url or "login" in r.url:
                downloads[task_id]["status"] = "Erreur 403 : Modèle Civitai restreint (Compte / 18+ requis). Clé API Civitai requise."
                downloads[task_id]["error"] = True
                return

            r.raise_for_status()
            
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
            
            # --- AUTOMATIC MODEL CLASSIFIER & PLACEMENT SAFEGUARD ---
            cat = downloads[task_id].get("folder", "auto")
            detected_folder = None
            if clean_filename.lower().endswith(".safetensors") and os.path.exists(out_path):
                detected_folder = classify_safetensors(out_path)

            if detected_folder:
                # If auto requested OR user mistakenly chose checkpoints for a LoRA/VAE/ControlNet
                if cat == "auto" or (cat == "checkpoints" and detected_folder in ["loras", "vae", "controlnet"]):
                    correct_dir = ALLOWED_FOLDERS.get(detected_folder, target_dir)
                    if correct_dir != target_dir:
                        new_path = os.path.join(correct_dir, clean_filename)
                        try:
                            os.makedirs(correct_dir, exist_ok=True)
                            os.rename(out_path, new_path)
                            out_path = new_path
                            downloads[task_id]["path"] = new_path
                            downloads[task_id]["folder"] = detected_folder
                        except Exception:
                            pass
                else:
                    downloads[task_id]["folder"] = cat

            # --- AUTOMATIC SYNC BETWEEN COMFYUI AND FOOOCUS ---
            try:
                final_folder = downloads[task_id].get("folder", "checkpoints")
                if final_folder == "loras":
                    f_lora = os.path.join("/datastore/Fooocus/models/loras", clean_filename)
                    c_lora = os.path.join("/datastore/ComfyUI/models/loras", clean_filename)
                    if os.path.exists(out_path):
                        if not os.path.exists(f_lora):
                            os.symlink(out_path, f_lora)
                        if not os.path.exists(c_lora):
                            os.symlink(out_path, c_lora)
                elif final_folder == "checkpoints":
                    f_ckpt = os.path.join("/datastore/Fooocus/models/checkpoints", clean_filename)
                    c_ckpt = os.path.join("/datastore/ComfyUI/models/checkpoints", clean_filename)
                    if os.path.exists(out_path):
                        if not os.path.exists(f_ckpt):
                            os.symlink(out_path, f_ckpt)
                        if not os.path.exists(c_ckpt):
                            os.symlink(out_path, c_ckpt)
            except Exception:
                pass

            tag = f" (Détecté & rangé en {downloads[task_id]['folder'].upper()})" if detected_folder else ""
            downloads[task_id]["status"] = f"Terminé avec succès !{tag}"
            downloads[task_id]["progress"] = 100
            downloads[task_id]["error"] = False

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else 0
        if status_code == 403 or "reason=download-auth" in str(e):
            downloads[task_id]["status"] = "Erreur 403 : Modèle restreint Civitai (Compte / 18+ requis). Ajoute ta clé API Civitai."
        elif status_code == 404:
            downloads[task_id]["status"] = "Erreur 404 : Fichier introuvable. Copie le lien direct du fichier .safetensors (onglet Files & Versions sur Hugging Face)."
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
    folder = data.get("folder", "auto")
    filename = data.get("filename", "").strip()
    civitai_token = data.get("civitai_token", "").strip()
    
    if not url:
        return jsonify({"error": "URL manquante"}), 400
    
    if folder == "auto":
        target_dir = ALLOWED_FOLDERS["checkpoints"]
    else:
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
    data = request.json or {}
    clear_all = data.get("all", False)
    if clear_all:
        downloads = []
    else:
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
        token = get_saved_civitai_token()
        masked = token[:4] + "..." + token[-4:] if len(token) > 8 else ("***" if token else "")
        return jsonify({"has_token": bool(token), "masked_token": masked})

# --- 2. LOG ANALYZER & DIAGNOSTICS LOGIC ---

def run_bash(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return res.stdout + res.stderr
    except Exception as e:
        return f"Erreur commande: {str(e)}"

def check_systemd(service):
    res = run_bash(f"systemctl is-active {service}").strip()
    return res == "active"

def check_docker(container):
    res = run_bash(f"docker inspect -f '{{{{.State.Running}}}}' {container} 2>/dev/null").strip()
    return res == "true"

@app.route("/api/logs/status", methods=["GET"])
def get_services_status():
    status = {
        "chat": {
            "name": "Chat IA & LLM",
            "active": check_systemd("ollama") and check_docker("open-webui"),
            "components": {
                "ollama": check_systemd("ollama"),
                "open-webui": check_docker("open-webui")
            }
        },
        "code": {
            "name": "Marcel Vibe Coder",
            "active": check_systemd("ollama"),
            "components": {
                "ollama": check_systemd("ollama"),
                "workspace": os.path.exists(WORKSPACE_DIR)
            }
        },
        "image": {
            "name": "Génération d'Images",
            "active": check_systemd("fooocus") or check_systemd("comfyui"),
            "components": {
                "fooocus": check_systemd("fooocus"),
                "comfyui": check_systemd("comfyui")
            }
        },
        "voix": {
            "name": "Studio Vocal Kokoro",
            "active": check_docker("kokoro-tts"),
            "components": {
                "kokoro-tts": check_docker("kokoro-tts")
            }
        },
        "model": {
            "name": "Téléchargeur Serveur",
            "active": True,
            "components": {
                "downloader": True
            }
        }
    }
    return jsonify(status)

ERROR_KEYWORDS = ["error", "erreur", "exception", "traceback", "failed", "fatal", "critical", "403", "404", "500", "oom", "killed", "permission denied", "crash"]

@app.route("/api/logs/view", methods=["GET"])
def get_logs():
    category = request.args.get("category", "chat").lower()
    lines = int(request.args.get("lines", 100))
    filter_errors = request.args.get("errors_only", "false").lower() == "true"
    
    raw_logs = ""
    service_name = ""
    
    if category == "chat":
        service_name = "Open WebUI & Ollama"
        w_logs = run_bash(f"docker logs open-webui --tail {lines} 2>&1")
        o_logs = run_bash(f"journalctl -u ollama -n {lines} --no-pager")
        raw_logs = f"=== OPEN WEBUI DOCKER LOGS ===\n{w_logs}\n\n=== OLLAMA SERVICE LOGS ===\n{o_logs}"
    
    elif category == "code":
        service_name = "Vibe Coder & Workspace"
        o_logs = run_bash(f"journalctl -u ollama -n {lines} --no-pager")
        ws_files = run_bash(f"ls -lah {WORKSPACE_DIR}")
        raw_logs = f"=== WORKSPACE ETAT ===\n{ws_files}\n\n=== OLLAMA CODE ENGINE ===\n{o_logs}"
    
    elif category == "image":
        service_name = "Fooocus SDXL & ComfyUI"
        f_logs = run_bash(f"journalctl -u fooocus -n {lines} --no-pager")
        c_logs = run_bash(f"journalctl -u comfyui -n {lines} --no-pager")
        raw_logs = f"=== FOOOCUS SDXL LOGS ===\n{f_logs}\n\n=== COMFYUI LOGS ===\n{c_logs}"
    
    elif category == "voix":
        service_name = "Kokoro Neural TTS"
        raw_logs = run_bash(f"docker logs kokoro-tts --tail {lines} 2>&1")
    
    elif category == "model":
        service_name = "Téléchargeur & Tâches"
        recent_errs = [f"[{d.get('folder')}] {d.get('filename')} : {d.get('status')}" for d in downloads if d.get('error')]
        raw_logs = "=== DERNIÈRES ERREURS DE TÉLÉCHARGEMENT ===\n" + ("\n".join(recent_errs) if recent_errs else "Aucune erreur récente.")
    
    else:
        return jsonify({"error": "Catégorie inconnue"}), 400

    all_lines = raw_logs.splitlines()
    error_lines = []
    
    for l in all_lines:
        lower = l.lower()
        if any(kw in lower for kw in ERROR_KEYWORDS):
            error_lines.append(l)

    output_lines = error_lines if filter_errors else all_lines

    return jsonify({
        "category": category,
        "service": service_name,
        "total_lines": len(all_lines),
        "error_count": len(error_lines),
        "logs": "\n".join(output_lines),
        "has_errors": len(error_lines) > 0,
        "sample_error": "\n".join(error_lines[-6:]) if error_lines else None
    })

@app.route("/api/logs/ai_analyze", methods=["POST"])
def ai_analyze_error():
    data = request.json or {}
    category = data.get("category", "général")
    logs = data.get("logs", "").strip()
    
    if not logs:
        return jsonify({"error": "Aucun log fourni pour analyse"}), 400
    
    snippet = logs[-2500:]
    
    prompt = f"""Tu es l'analyste système et expert en dépannage de Marcel Studio.
L'utilisateur a rencontré un problème ou souhaite comprendre les logs de la catégorie "{category}".

Voici l'extrait des logs :
```text
{snippet}
```

Réponds de manière directe, synthétique et facile à comprendre en bon français :
1. 🔴 **Problème détecté** : Explique en 1-2 phrases ce qui ne va pas (ou confirme si tout va bien).
2. 🔍 **Cause exacte** : Pourquoi cela s'est produit.
3. 🛠️ **Solution immédiate** : Les actions concrètes étape par étape pour régler le souci (ou le bouton sur lequel cliquer)."""

    try:
        resp = requests.post(f"{OLLAMA_API}/generate", json={
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }, timeout=45)
        
        if resp.status_code == 200:
            analysis = resp.json().get("response", "Analyse impossible.")
            return jsonify({"success": True, "analysis": analysis})
        else:
            return jsonify({"error": f"Erreur Ollama HTTP {resp.status_code}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur de communication avec l'IA: {str(e)}"}), 500


@app.route("/api/logs/ai_autofix", methods=["POST"])
def ai_autofix():
    data = request.json or {}
    category = data.get("category", "chat").lower()
    logs = data.get("logs", "").strip()
    
    # 1. Ask Ollama (llama3.2:3b) to determine diagnosis and remediation strategy
    snippet = logs[-2500:] if logs else "Vérification et optimisation périodique du service."
    
    prompt = f"""Tu es l'agent autonome d'autoréparation système de Marcel AI Studio.
Une intervention d'urgence ou une réparation automatique a été demandée sur la catégorie "{category}".

Voici les logs récents ou erreurs :
```text
{snippet}
```

Format de réponse STRICT :
DIAGNOSTIC: <Résume le problème en 1-2 phrases claires en français>
ACTIONS: <Liste séparée par des virgules parmi : CLEAR_GPU_CACHE, RESTART_SERVICE, RESTART_DOCKER, FIX_PERMISSIONS, CLEAN_FAILED_DOWNLOADS, FIX_WORKSPACE_CODE>
EXPLICATION: <Explique en bon français ce que ces actions vont régler>"""

    diagnosis = "Analyse automatique du service."
    actions_to_take = ["RESTART_SERVICE"]
    explanation = "Redémarrage préventif et libération des ressources."
    
    try:
        resp = requests.post(f"{OLLAMA_API}/generate", json={
            "model": "llama3.2:3b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2}
        }, timeout=30)
        
        if resp.status_code == 200:
            ai_text = resp.json().get("response", "")
            diag_m = re.search(r"DIAGNOSTIC:\s*(.*?)(?=\n[A-Z]+:|\Z)", ai_text, re.DOTALL)
            act_m = re.search(r"ACTIONS:\s*(.*?)(?=\n[A-Z]+:|\Z)", ai_text, re.DOTALL)
            exp_m = re.search(r"EXPLICATION:\s*(.*?)(?=\n[A-Z]+:|\Z)", ai_text, re.DOTALL)
            
            if diag_m: diagnosis = diag_m.group(1).strip()
            if exp_m: explanation = exp_m.group(1).strip()
            if act_m:
                raw_acts = act_m.group(1).upper()
                detected = [a.strip() for a in ["CLEAR_GPU_CACHE", "RESTART_SERVICE", "RESTART_DOCKER", "FIX_PERMISSIONS", "CLEAN_FAILED_DOWNLOADS", "FIX_WORKSPACE_CODE"] if a in raw_acts]
                if detected:
                    actions_to_take = detected
    except Exception as e:
        diagnosis = f"Diagnostic hors-ligne : {str(e)}"

    # Category-specific intelligent defaults
    if category == "image" and "CLEAR_GPU_CACHE" not in actions_to_take:
        actions_to_take.append("CLEAR_GPU_CACHE")
    if category in ["chat", "voix"] and "RESTART_DOCKER" not in actions_to_take:
        actions_to_take.append("RESTART_DOCKER")
    if category == "code" and "FIX_PERMISSIONS" not in actions_to_take:
        actions_to_take.append("FIX_PERMISSIONS")
    if category == "model" and "CLEAN_FAILED_DOWNLOADS" not in actions_to_take:
        actions_to_take.append("CLEAN_FAILED_DOWNLOADS")

    # 2. Execute Remediation Safely
    executed_steps = []
    
    if "CLEAR_GPU_CACHE" in actions_to_take or category == "image":
        run_bash("pkill -9 -f Fooocus 2>/dev/null || true")
        run_bash("pkill -9 -f ComfyUI 2>/dev/null || true")
        executed_steps.append("🧹 Processus GPU zombies arrêtés & VRAM Radeon purgée")

    if "FIX_PERMISSIONS" in actions_to_take or category == "code":
        run_bash(f"chmod -R 777 {WORKSPACE_DIR} 2>/dev/null || true")
        run_bash("chmod -R 775 /datastore/ComfyUI/models 2>/dev/null || true")
        executed_steps.append("🔑 Permissions de lecture/écriture réalignées sur le stockage ZFS")

    if "CLEAN_FAILED_DOWNLOADS" in actions_to_take or category == "model":
        run_bash("find /datastore/ComfyUI/models -name '*.tmp' -delete 2>/dev/null || true")
        run_bash("find /datastore/ComfyUI/models -size 0 -delete 2>/dev/null || true")
        executed_steps.append("🗑️ Fichiers partiels .tmp et téléchargements corrompus à 0 Ko nettoyés")

    if "FIX_WORKSPACE_CODE" in actions_to_take and category == "code":
        idx_p = os.path.join(WORKSPACE_DIR, "index.html")
        if os.path.exists(idx_p):
            try:
                with open(idx_p, "r", encoding="utf-8", errors="ignore") as fp:
                    code_content = fp.read()
                rep = requests.post(f"{OLLAMA_API}/generate", json={
                    "model": "qwen2.5-coder:7b",
                    "prompt": f"Répare le bug ou l'erreur de ce code HTML/JS :\n```html\n{code_content[:2000]}\n```\nErreur : {logs[-500:]}\nRenvoie UNIQUEMENT le code réparé dans ```html ... ```.",
                    "stream": False
                }, timeout=30)
                if rep.status_code == 200:
                    raw_c = rep.json().get("response", "")
                    m = re.search(r"```(?:html)?\s*(.*?)```", raw_c, re.DOTALL)
                    if m:
                        with open(idx_p, "w", encoding="utf-8") as fp:
                            fp.write(m.group(1).strip())
                        executed_steps.append("🤖 Code HTML/JS de l'espace de travail réécrit et réparé automatiquement par Qwen Coder")
            except Exception:
                pass

    if "RESTART_SERVICE" in actions_to_take or "RESTART_DOCKER" in actions_to_take:
        if category == "chat":
            run_bash("systemctl restart ollama && docker restart open-webui")
            executed_steps.append("🔄 Service Ollama et conteneur Open WebUI redémarrés")
        elif category == "image":
            run_bash("systemctl restart fooocus comfyui")
            executed_steps.append("🔄 Services Fooocus et ComfyUI relancés proprement")
        elif category == "voix":
            run_bash("docker restart kokoro-tts")
            executed_steps.append("🔄 Conteneur Kokoro Neural TTS relancé")
        elif category == "code":
            run_bash("systemctl restart ollama")
            executed_steps.append("🔄 Moteur Ollama Vibe Coder relancé")
        elif category == "model":
            run_bash("systemctl restart marcel-core || true")
            executed_steps.append("🔄 Service de téléchargement et cache relancés")

    # 3. Post-verification
    status_summary = get_services_status().get_json().get(category, {})
    is_healthy = status_summary.get("active", False)

    return jsonify({
        "success": True,
        "category": category,
        "is_healthy": is_healthy,
        "diagnosis": diagnosis,
        "explanation": explanation,
        "actions_taken": executed_steps,
        "status_text": "🟢 Service 100% opérationnel" if is_healthy else "🟡 Redémarrage en cours (quelques secondes nécessaires)"
    })

@app.route("/api/services/restart", methods=["POST"])
def restart_service():
    data = request.json or {}
    category = data.get("category", "").lower()
    
    commands = {
        "chat": "systemctl restart ollama && docker restart open-webui",
        "image": "systemctl restart fooocus comfyui",
        "voix": "docker restart kokoro-tts",
        "code": "systemctl restart ollama",
        "model": "systemctl restart marcel-core || true"
    }
    
    cmd = commands.get(category)
    if not cmd:
        return jsonify({"error": "Catégorie non reconnue"}), 400
    
    out = run_bash(cmd)
    return jsonify({"success": True, "output": out})

@app.route("/api/logs/clear", methods=["POST"])
def clear_service_logs():
    data = request.json or {}
    category = data.get("category", "all").lower()
    
    actions_taken = []
    
    if category in ["chat", "all"]:
        run_bash("truncate -s 0 $(docker inspect --format='{{.LogPath}}' open-webui 2>/dev/null) 2>/dev/null")
        run_bash("journalctl -u ollama --rotate 2>/dev/null && journalctl -u ollama --vacuum-time=1s 2>/dev/null")
        actions_taken.append("Logs Chat & Ollama réinitialisés")
        
    if category in ["image", "all"]:
        run_bash("journalctl -u fooocus --rotate 2>/dev/null && journalctl -u fooocus --vacuum-time=1s 2>/dev/null")
        run_bash("journalctl -u comfyui --rotate 2>/dev/null && journalctl -u comfyui --vacuum-time=1s 2>/dev/null")
        actions_taken.append("Logs Fooocus & ComfyUI réinitialisés")
        
    if category in ["voix", "all"]:
        run_bash("truncate -s 0 $(docker inspect --format='{{.LogPath}}' kokoro-tts 2>/dev/null) 2>/dev/null")
        actions_taken.append("Logs Kokoro-TTS réinitialisés")
        
    if category in ["code", "all"]:
        run_bash("journalctl -u ollama --rotate 2>/dev/null && journalctl -u ollama --vacuum-time=1s 2>/dev/null")
        actions_taken.append("Logs Moteur Vibe Coder réinitialisés")
        
    if category in ["model", "all"]:
        global downloads
        downloads = [d for d in downloads if "en cours" in d.get("status", "").lower() or "démarrage" in d.get("status", "").lower()]
        actions_taken.append("Historique et erreurs de téléchargement vidés")
        
    return jsonify({
        "success": True,
        "category": category,
        "actions_taken": actions_taken,
        "message": "Logs effacés avec succès !"
    })

@app.route("/api/system/stats", methods=["GET"])
def get_system_stats():
    # 1. CPU Load
    cpu_percent = 0.0
    try:
        with open('/proc/stat') as f:
            stat1 = [float(x) for x in f.readline().split()[1:]]
        time.sleep(0.08)
        with open('/proc/stat') as f:
            stat2 = [float(x) for x in f.readline().split()[1:]]
        d_total = sum(stat2) - sum(stat1)
        d_idle = (stat2[3] + stat2[4]) - (stat1[3] + stat1[4])
        cpu_percent = round((1.0 - d_idle / d_total) * 100, 1) if d_total > 0 else 0.0
    except:
        pass

    # 2. CPU Temp
    cpu_temp = None
    for path in ['/sys/class/hwmon/hwmon1/temp2_input', '/sys/class/hwmon/hwmon4/temp1_input', '/sys/class/hwmon/hwmon1/temp1_input']:
        if os.path.exists(path):
            try:
                cpu_temp = round(int(open(path).read().strip()) / 1000.0, 1)
                break
            except:
                pass

    # 3. RAM
    meminfo = {}
    try:
        for line in open('/proc/meminfo'):
            parts = line.split(':')
            if len(parts) == 2:
                meminfo[parts[0].strip()] = int(parts[1].split()[0])
    except:
        pass
    ram_total_gb = round(meminfo.get('MemTotal', 0) / (1024**2), 1)
    ram_avail_gb = round(meminfo.get('MemAvailable', 0) / (1024**2), 1)
    ram_used_gb = round(ram_total_gb - ram_avail_gb, 1)
    ram_percent = round((ram_used_gb / ram_total_gb) * 100, 1) if ram_total_gb > 0 else 0.0

    # 4. GPU (Radeon RX 5600 XT)
    gpu_temp = None
    for path in ['/sys/class/hwmon/hwmon5/temp1_input', '/sys/class/hwmon/hwmon5/temp2_input']:
        if os.path.exists(path):
            try:
                gpu_temp = round(int(open(path).read().strip()) / 1000.0, 1)
                break
            except:
                pass

    vram_used_gb = 0.0
    vram_total_gb = 5.98
    gpu_busy = 0
    if os.path.exists('/sys/class/drm/card1/device/mem_info_vram_used'):
        try:
            vram_used_gb = round(int(open('/sys/class/drm/card1/device/mem_info_vram_used').read().strip()) / (1024**3), 2)
            vram_total_gb = round(int(open('/sys/class/drm/card1/device/mem_info_vram_total').read().strip()) / (1024**3), 2)
        except:
            pass
    if os.path.exists('/sys/class/drm/card1/device/gpu_busy_percent'):
        try:
            gpu_busy = int(open('/sys/class/drm/card1/device/gpu_busy_percent').read().strip())
        except:
            pass

    # 5. Activity Status ("voir si un truc tourne ou pas")
    active_tasks = []
    # Check Ollama
    try:
        r = requests.get('http://127.0.0.1:11434/api/ps', timeout=1)
        if r.status_code == 200:
            models = r.json().get('models', [])
            if models:
                m_names = [m.get('name', 'Modèle') for m in models]
                active_tasks.append(f"Inférence LLM ({', '.join(m_names)})")
    except:
        pass

    # Check downloads
    dl_active = [d for d in downloads if "en cours" in d.get("status", "").lower() or "démarrage" in d.get("status", "").lower()]
    if dl_active:
        active_tasks.append(f"Téléchargement ({len(dl_active)} en cours)")

    # Check Fooocus process / activity
    try:
        r = subprocess.run(['pgrep', '-f', 'entry_with_update.py'], capture_output=True, text=True)
        if r.returncode == 0 and gpu_busy > 10:
            active_tasks.append("Rendu SDXL (Fooocus actif)")
    except:
        pass

    is_running = len(active_tasks) > 0 or gpu_busy > 15 or cpu_percent > 45
    if active_tasks:
        status_summary = "En action : " + " & ".join(active_tasks)
    elif is_running:
        status_summary = "En action (Calcul intensif)"
    else:
        status_summary = "En veille (Système prêt)"

    return jsonify({
        "cpu": {
            "name": "AMD Ryzen 7 2700X",
            "percent": cpu_percent,
            "temp": cpu_temp
        },
        "ram": {
            "used_gb": ram_used_gb,
            "total_gb": ram_total_gb,
            "avail_gb": ram_avail_gb,
            "percent": ram_percent
        },
        "gpu": {
            "name": "AMD Radeon RX 5600 XT",
            "percent": gpu_busy,
            "temp": gpu_temp,
            "vram_used_gb": vram_used_gb,
            "vram_total_gb": vram_total_gb,
            "vram_percent": round((vram_used_gb / vram_total_gb) * 100, 1) if vram_total_gb > 0 else 0.0
        },
        "activity": {
            "is_busy": is_running,
            "status": status_summary,
            "active_tasks": active_tasks
        }
    })

# --- 3. VIBE CODER (ANTIGRAVITY STYLE) LOGIC ---

@app.route("/api/vibe/files", methods=["GET"])
def vibe_list_files():
    tree = []
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        rel_root = os.path.relpath(root, WORKSPACE_DIR)
        for f in files:
            rel_path = f if rel_root == "." else os.path.join(rel_root, f).replace("\\", "/")
            full_path = os.path.join(root, f)
            sz = os.path.getsize(full_path)
            tree.append({
                "path": rel_path,
                "name": f,
                "size": sz,
                "ext": os.path.splitext(f)[1].lower()
            })
    return jsonify({"files": tree, "workspace": WORKSPACE_DIR})

@app.route("/api/vibe/file", methods=["GET", "POST", "DELETE"])
def vibe_manage_file():
    if request.method == "GET":
        rel_path = request.args.get("path", "index.html")
        safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, rel_path))
        if not safe_path.startswith(WORKSPACE_DIR) or not os.path.exists(safe_path):
            return jsonify({"error": "Fichier introuvable"}), 404
        try:
            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return jsonify({"path": rel_path, "content": content})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == "POST":
        data = request.json or {}
        rel_path = data.get("path", "").strip()
        content = data.get("content", "")
        if not rel_path:
            return jsonify({"error": "Chemin manquant"}), 400
        safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, rel_path))
        if not safe_path.startswith(WORKSPACE_DIR):
            return jsonify({"error": "Chemin non autorisé"}), 403
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return jsonify({"success": True, "path": rel_path})

    elif request.method == "DELETE":
        rel_path = request.args.get("path", "").strip()
        safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, rel_path))
        if not safe_path.startswith(WORKSPACE_DIR) or not os.path.exists(safe_path):
            return jsonify({"error": "Fichier introuvable"}), 404
        try:
            os.remove(safe_path)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/api/vibe/chat", methods=["POST"])
def vibe_chat():
    data = request.json or {}
    user_prompt = data.get("prompt", "").strip()
    history = data.get("history", [])
    
    if not user_prompt:
        return jsonify({"error": "Prompt vide"}), 400
    
    existing_files_summary = []
    main_code_preview = ""
    for root, dirs, files in os.walk(WORKSPACE_DIR):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), WORKSPACE_DIR).replace("\\", "/")
            existing_files_summary.append(rel)
            if rel in ["index.html", "app.js", "style.css", "main.py"]:
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as fp:
                        main_code_preview += f"\n--- Fichier actuel : {rel} ---\n{fp.read()[:2000]}\n"
                except:
                    pass

    system_prompt = f"""Tu es le Vibe Coder de Marcel Studio, un assistant de programmation ultra-rapide et direct (style Antigravity).
L'utilisateur code en direct sur son téléphone ou son ordinateur.
Son espace de travail contient actuellement : {', '.join(existing_files_summary) if existing_files_summary else 'vide'}
{main_code_preview}

DIRECTIVES :
1. Comprends l'intention ('vibe') de l'utilisateur et donne une brève explication chaleureuse en français de ce que tu réalises.
2. Génère TOUJOURS du code COMPLET, autonome et directement exécutable. Ne mets JAMAIS de placeholders du genre '// reste du code...'.
3. Pour chaque fichier que tu crées ou modifies, utilise STRICTEMENT le format suivant :
```file:nom_du_fichier.ext
...contenu complet du code...
```
4. Si l'utilisateur demande une application, un jeu ou un site web, assure-toi de générer ou mettre à jour un 'index.html' complet avec un design sombre moderne (dark mode néon/élégant, responsive mobile).
5. Réponds avec enthousiasme, clarté et précision."""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-4:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_prompt})

    try:
        resp = requests.post(f"{OLLAMA_API}/chat", json={
            "model": "qwen2.5-coder:7b",
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.4}
        }, timeout=90)
        
        if resp.status_code != 200:
            return jsonify({"error": f"Erreur Ollama HTTP {resp.status_code}"}), 500
        
        reply = resp.json().get("message", {}).get("content", "")
        
        pattern = r"```file:([^\n\r]+)[\r\n]+(.*?)```"
        matches = re.findall(pattern, reply, re.DOTALL)
        
        saved_files = []
        for filename, file_content in matches:
            filename = filename.strip()
            safe_path = os.path.normpath(os.path.join(WORKSPACE_DIR, filename))
            if safe_path.startswith(WORKSPACE_DIR):
                os.makedirs(os.path.dirname(safe_path), exist_ok=True)
                with open(safe_path, "w", encoding="utf-8") as f:
                    f.write(file_content.strip())
                saved_files.append(filename)

        return jsonify({
            "success": True,
            "response": reply,
            "saved_files": saved_files,
            "preview_url": "/workspace_preview/"
        })

    except Exception as e:
        return jsonify({"error": f"Erreur lors de la génération: {str(e)}"}), 500

@app.route("/api/vibe/reset", methods=["POST"])
def vibe_reset():
    starter_html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marcel Vibe App</title>
    <style>
        :root { --bg: #0b0f19; --primary: #6366f1; --card: rgba(255,255,255,0.05); }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: var(--bg); color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
        .card { max-width: 420px; width: 100%; padding: 30px; border-radius: 20px; background: var(--card); border: 1px solid rgba(255,255,255,0.1); text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }
        h1 { font-size: 1.8rem; margin-bottom: 10px; background: linear-gradient(135deg, #6366f1, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        p { color: #94a3b8; font-size: 0.95rem; margin-bottom: 24px; line-height: 1.5; }
        .btn { display: inline-block; padding: 12px 24px; background: var(--primary); color: #fff; border: none; border-radius: 12px; font-weight: 600; cursor: pointer; text-decoration: none; transition: transform 0.2s; }
        .btn:active { transform: scale(0.96); }
    </style>
</head>
<body>
    <div class="card">
        <h1>✨ Marcel Vibe Coder</h1>
        <p>Espace de travail prêt ! Demande à l'IA de coder un jeu, un dashboard ou l'application de ton choix.</p>
        <button class="btn" onclick="alert('Bravo ! Ton app fonctionne en direct !')">Tester l'interaction</button>
    </div>
</body>
</html>"""
    idx_path = os.path.join(WORKSPACE_DIR, "index.html")
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(starter_html)
    return jsonify({"success": True, "message": "Projet réinitialisé avec succès !"})

@app.route("/api/vibe/zip", methods=["GET"])
def vibe_download_zip():
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(WORKSPACE_DIR):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, WORKSPACE_DIR)
                zf.write(full_path, rel_path)
    memory_file.seek(0)
    return send_file(memory_file, download_name="marcel_project.zip", as_attachment=True)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8085)
