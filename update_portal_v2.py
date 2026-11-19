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

html_content = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Studio - Fenrir Creative</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #08090d;
            --card-bg: rgba(20, 24, 38, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.4);
            --accent-pink: #ec4899;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            position: relative;
        }
        .glow-1 {
            position: absolute;
            top: -150px;
            left: -100px;
            width: 550px;
            height: 550px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.28) 0%, transparent 70%);
            filter: blur(80px);
            z-index: 0;
            pointer-events: none;
        }
        .glow-2 {
            position: absolute;
            bottom: -100px;
            right: -100px;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(236, 72, 153, 0.22) 0%, transparent 70%);
            filter: blur(100px);
            z-index: 0;
            pointer-events: none;
        }
        .container {
            max-width: 1240px;
            width: 100%;
            margin: 0 auto;
            padding: 40px 24px;
            position: relative;
            z-index: 1;
            flex: 1;
        }
        header {
            text-align: center;
            margin-bottom: 45px;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 18px;
            border-radius: 999px;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.35);
            color: #818cf8;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 12px var(--accent-green);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }
        h1 {
            font-size: 3.2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 12px;
        }
        p.subtitle {
            font-size: 1.15rem;
            color: var(--text-sub);
            max-width: 700px;
            margin: 0 auto;
            line-height: 1.6;
        }

        /* HERO CARD (FOOOCUS) */
        .hero-card {
            background: linear-gradient(135deg, rgba(30, 27, 75, 0.8) 0%, rgba(20, 24, 38, 0.9) 100%);
            border: 1px solid rgba(99, 102, 241, 0.4);
            border-radius: 24px;
            padding: 36px;
            backdrop-filter: blur(20px);
            margin-bottom: 36px;
            box-shadow: 0 20px 50px -15px rgba(99, 102, 241, 0.3);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .hero-badge {
            align-self: flex-start;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, #f59e0b, #ec4899);
            color: #fff;
            padding: 5px 14px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .hero-content {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 28px;
            align-items: center;
        }
        @media (max-width: 820px) {
            .hero-content { grid-template-columns: 1fr; }
        }
        .hero-title {
            font-size: 2.1rem;
            font-weight: 800;
            color: #fff;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .hero-desc {
            color: #cbd5e1;
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 16px;
        }
        .hero-tags {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        /* REGULAR GRID */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 24px;
            margin-bottom: 36px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 28px;
            backdrop-filter: blur(16px);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }
        .card:hover {
            transform: translateY(-5px);
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6);
        }
        .card-icon {
            font-size: 2.2rem;
            margin-bottom: 16px;
        }
        .card h2 {
            font-size: 1.45rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .card p {
            color: var(--text-sub);
            font-size: 0.95rem;
            line-height: 1.55;
            margin-bottom: 20px;
            flex-grow: 1;
        }
        .card-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 24px;
        }
        .tag {
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            padding: 4px 10px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #cbd5e1;
        }

        /* BUTTONS */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 14px 24px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 1rem;
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
            border: none;
            text-align: center;
        }
        .btn-hero {
            background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
            color: #fff;
            box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.5);
            padding: 18px 32px;
            font-size: 1.15rem;
            white-space: nowrap;
        }
        .btn-hero:hover {
            transform: scale(1.03);
            box-shadow: 0 15px 35px -5px rgba(236, 72, 153, 0.6);
        }
        .btn-primary {
            background: var(--primary);
            color: #fff;
            box-shadow: 0 8px 20px -6px var(--primary-glow);
        }
        .btn-primary:hover {
            background: #4f46e5;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.07);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.12);
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.12);
            transform: translateY(-2px);
        }

        /* DOWNLOADER SECTION */
        .downloader-box {
            background: rgba(15, 18, 30, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 32px;
            margin-bottom: 36px;
        }
        .downloader-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        .downloader-title {
            font-size: 1.35rem;
            font-weight: 700;
        }
        .downloader-desc {
            color: var(--text-sub);
            font-size: 0.95rem;
            margin-bottom: 24px;
        }
        .form-row {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .input-url {
            flex: 1;
            min-width: 280px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 14px 16px;
            color: #fff;
            font-family: inherit;
            font-size: 0.95rem;
        }
        .input-url:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        .select-folder {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 14px 16px;
            color: #fff;
            font-family: inherit;
            font-size: 0.95rem;
            cursor: pointer;
        }
        .tasks-container {
            margin-top: 24px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .task-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 10px;
            padding: 14px 18px;
        }
        .task-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            margin-bottom: 8px;
            font-family: 'JetBrains Mono', monospace;
        }
        .progress-bar-bg {
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--accent-pink));
            width: 0%;
            transition: width 0.3s ease;
        }

        /* SPECS */
        .specs-panel {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            background: rgba(15, 18, 30, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
        }
        .spec-item {
            text-align: center;
        }
        .spec-label {
            font-size: 0.8rem;
            color: var(--text-sub);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }
        .spec-value {
            font-size: 1.15rem;
            font-weight: 700;
            color: #fff;
        }
        footer {
            text-align: center;
            padding: 30px;
            color: rgba(255, 255, 255, 0.3);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="glow-1"></div>
    <div class="glow-2"></div>

    <div class="container">
        <header>
            <div class="badge">
                <span class="pulse-dot"></span>
                Serveur IA Opérationnel
            </div>
            <h1>Studio Créatif IA Dédié</h1>
            <p class="subtitle">Génération d'images haute fidélité, vidéos cinématiques et synthèse vocale réaliste. Tout s'exécute localement avec 31 To de stockage.</p>
        </header>

        <!-- HERO FOOOCUS : L'INTERFACE SIMPLE MIDJOURNEY -->
        <div class="hero-card">
            <span class="hero-badge">⭐ Recommandé • Le Plus Simple (Façon Midjourney)</span>
            <div class="hero-content">
                <div>
                    <h2 class="hero-title">🎨 Fooocus (Générateur d'Images Simple)</h2>
                    <p class="hero-desc">
                        <strong>Oublie la complexité des nœuds !</strong> Fooocus est pensé comme Midjourney : tu écris simplement ce que tu veux, tu coches les styles de ton choix (Photo Réaliste, Cinématique, Anime...), et tu cliques sur <strong>Generate</strong>.<br>
                        Modèle <strong>Juggernaut XL v8</strong> et <strong>DreamShaper 8</strong> pré-chargés pour des résultats photoréalistes époustouflants sans aucun casse-tête.
                    </p>
                    <div class="hero-tags">
                        <span class="tag">Zéro Nœud</span>
                        <span class="tag">Juggernaut XL</span>
                        <span class="tag">Prompt & Clic</span>
                        <span class="tag">Styles 1-Clic</span>
                        <span class="tag">Inpainting Simple</span>
                    </div>
                </div>
                <div>
                    <a href=":7865" class="btn btn-hero" onclick="this.href='http://' + window.location.hostname + ':7865'">
                        Ouvrir Fooocus ➔
                    </a>
                </div>
            </div>
        </div>

        <div class="grid">
            <!-- KOKORO TTS AUDIO -->
            <div class="card">
                <div class="card-icon">🎙️</div>
                <h2>Synthèse Vocale HD (Kokoro)</h2>
                <p>72 voix neurales ultra-réalistes en français et en anglais (voix de fille et de gars comme Nicole, Siwis, Fenrir, Heart). Lecteur Web intégré et génération instantanée.</p>
                <div class="card-tags">
                    <span class="tag">Kokoro HD</span>
                    <span class="tag">Voix Fille & Gars</span>
                    <span class="tag">Web Player</span>
                </div>
                <a href=":8880/web/" class="btn btn-primary" style="background:#06b6d4; box-shadow:0 8px 20px -6px rgba(6,182,212,0.35);" onclick="this.href='http://' + window.location.hostname + ':8880/web/'">Ouvrir Studio Vocal ➔</a>
            </div>

            <!-- ANIMATEDIFF VIDEOS -->
            <div class="card">
                <div class="card-icon">🎬</div>
                <h2>Génération de Vidéos IA</h2>
                <p>AnimateDiff v3 préconfiguré dans ComfyUI. Donne vie à tes images fixes avec des mouvements de caméra cinématiques et des animations en boucle sans saccade.</p>
                <div class="card-tags">
                    <span class="tag">AnimateDiff v3</span>
                    <span class="tag">Motion Modules</span>
                    <span class="tag">Video Loop</span>
                </div>
                <a href=":8188" class="btn btn-secondary" onclick="this.href='http://' + window.location.hostname + ':8188'">Créer une Vidéo ➔</a>
            </div>

            <!-- COMFYUI EXPERT -->
            <div class="card">
                <div class="card-icon">⚙️</div>
                <h2>ComfyUI (Mode Avancé / Nœuds)</h2>
                <p>Pour les utilisateurs experts : architecture nodale complète avec ComfyUI-Manager débloqué pour configurer des pipelines complexes et du contrôle précis par masque.</p>
                <div class="card-tags">
                    <span class="tag">Mode Expert</span>
                    <span class="tag">Nœuds avancés</span>
                    <span class="tag">ComfyUI-Manager</span>
                </div>
                <a href=":8188" class="btn btn-secondary" onclick="this.href='http://' + window.location.hostname + ':8188'">ComfyUI Studio ➔</a>
            </div>
        </div>

        <!-- DOWNLOADER DIRECT -->
        <div class="downloader-box">
            <div class="downloader-header">
                <span style="font-size:1.6rem">⚡</span>
                <div class="downloader-title">Téléchargeur Direct sur le Serveur (Sans passer par ton PC)</div>
            </div>
            <p class="downloader-desc">
                Colle un lien direct (Civitai, Hugging Face, etc.). Le serveur télécharge le modèle à <strong>80-120 Mo/s</strong> directement dans tes <strong>31 To de stockage</strong>. Les modèles sont partagés automatiquement entre <strong>Fooocus</strong> et <strong>ComfyUI</strong> !
            </p>
            <form onsubmit="handleDownload(event)">
                <div class="form-row">
                    <input type="url" id="modelUrl" class="input-url" placeholder="https://civitai.com/api/download/models/... ou HuggingFace" required>
                    <select id="modelFolder" class="select-folder">
                        <option value="checkpoints">Modèle Principal (Checkpoints)</option>
                        <option value="loras">LoRA (Style / Personnage)</option>
                        <option value="vae">VAE (Couleurs)</option>
                        <option value="controlnet">ControlNet (Poses / Traits)</option>
                    </select>
                    <button type="submit" class="btn btn-primary">Télécharger sur le Serveur</button>
                </div>
            </form>
            <div class="tasks-container" id="tasksList"></div>
        </div>

        <div class="specs-panel">
            <div class="spec-item">
                <div class="spec-label">Processeur</div>
                <div class="spec-value">Ryzen 7 2700X (8C/16T)</div>
            </div>
            <div class="spec-item">
                <div class="spec-label">Mémoire RAM Dédiée</div>
                <div class="spec-value">56 GB DDR4</div>
            </div>
            <div class="spec-item">
                <div class="spec-label">Carte Graphique</div>
                <div class="spec-value">Radeon RX 5600 XT</div>
            </div>
            <div class="spec-item">
                <div class="spec-label">Stockage Datastore</div>
                <div class="spec-value">31 To ZFS Stripe</div>
            </div>
        </div>
    </div>
    <footer>
        AI Creative Studio • Hébergé localement sur Proxmox VE
    </footer>

    <script>
        async function handleDownload(e) {
            e.preventDefault();
            const urlInput = document.getElementById('modelUrl');
            const folderInput = document.getElementById('modelFolder');
            const url = urlInput.value.trim();
            const folder = folderInput.value;

            if (!url) return;

            try {
                const res = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, folder })
                });
                const data = await res.json();
                if (data.success) {
                    urlInput.value = '';
                    fetchTasks();
                } else {
                    alert('Erreur: ' + (data.error || 'Impossible de lancer le téléchargement'));
                }
            } catch(err) {
                alert('Erreur réseau : ' + err.message);
            }
        }

        async function fetchTasks() {
            try {
                const res = await fetch('/api/downloads');
                const tasks = await res.json();
                const container = document.getElementById('tasksList');
                if (!tasks.length) return;

                container.innerHTML = tasks.map(t => `
                    <div class="task-item">
                        <div class="task-header">
                            <span class="task-name">📁 [${t.folder}] ${t.filename}</span>
                            <span class="task-status">${t.status} (${t.progress}%)</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: ${t.progress}%"></div>
                        </div>
                    </div>
                `).join('');
            } catch(err) {}
        }

        setInterval(fetchTasks, 2000);
        fetchTasks();
    </script>
</body>
</html>
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/portal_index.html', 'w') as f:
    f.write(html_content)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/portal_index.html /var/www/html/index.html")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)

ssh.close()
print("Portal HTML updated successfully!")
