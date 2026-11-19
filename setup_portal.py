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

portal_html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Creative Studio - Fenrir</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #090a0f;
            --card-bg: rgba(22, 25, 37, 0.7);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.35);
            --accent-pink: #ec4899;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
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
        /* Glowing background orbs */
        .glow-1 {
            position: absolute;
            top: -150px;
            left: -100px;
            width: 500px;
            height: 500px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%);
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
            background: radial-gradient(circle, rgba(236, 72, 153, 0.2) 0%, transparent 70%);
            filter: blur(100px);
            z-index: 0;
            pointer-events: none;
        }
        .container {
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            padding: 40px 24px;
            position: relative;
            z-index: 1;
            flex: 1;
        }
        header {
            text-align: center;
            margin-bottom: 50px;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 16px;
            border-radius: 999px;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #818cf8;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 18px;
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
            font-size: 3rem;
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
            max-width: 650px;
            margin: 0 auto;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 28px;
            margin-bottom: 40px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 32px;
            backdrop-filter: blur(16px);
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
        }
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, var(--card-glow, var(--primary)), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .card:hover {
            transform: translateY(-6px);
            border-color: rgba(255, 255, 255, 0.18);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
        }
        .card:hover::before {
            opacity: 1;
        }
        .card-icon {
            width: 58px;
            height: 58px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            margin-bottom: 24px;
        }
        .card-comfy .card-icon { background: rgba(99, 102, 241, 0.15); color: #818cf8; --card-glow: #6366f1; }
        .card-video .card-icon { background: rgba(236, 72, 153, 0.15); color: #f472b6; --card-glow: #ec4899; }
        .card-tts .card-icon { background: rgba(6, 182, 212, 0.15); color: #22d3ee; --card-glow: #06b6d4; }
        .card h2 {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .card p {
            color: var(--text-sub);
            font-size: 0.95rem;
            line-height: 1.6;
            margin-bottom: 24px;
            flex: 1;
        }
        .card-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 24px;
        }
        .tag {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            padding: 4px 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            color: #cbd5e1;
        }
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 14px 24px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1rem;
            text-decoration: none;
            transition: all 0.2s ease;
            cursor: pointer;
            border: none;
        }
        .btn-primary {
            background: var(--primary);
            color: white;
            box-shadow: 0 8px 20px -6px var(--primary-glow);
        }
        .btn-primary:hover {
            background: #4f46e5;
            box-shadow: 0 12px 24px -4px var(--primary-glow);
            transform: scale(1.02);
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-main);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.14);
        }
        .specs-panel {
            background: rgba(15, 18, 28, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-around;
            gap: 20px;
            text-align: center;
        }
        .spec-item {
            flex: 1;
            min-width: 140px;
        }
        .spec-label {
            font-size: 0.8rem;
            color: var(--text-sub);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }
        .spec-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.1rem;
            font-weight: 600;
            color: #f1f5f9;
        }
        footer {
            text-align: center;
            padding: 24px;
            color: #64748b;
            font-size: 0.85rem;
            border-top: 1px solid var(--card-border);
        }
    </style>
</head>
<body>
    <div class="glow-1"></div>
    <div class="glow-2"></div>
    <div class="container">
        <header>
            <div class="badge">
                <span class="pulse-dot"></span> Serveur IA Dédié & Opérationnel
            </div>
            <h1>Studio Génératif Local</h1>
            <p class="subtitle">Plateforme IA tout-en-un pour la création de photos, vidéos animées, musiques et voix humaines haute fidélité.</p>
        </header>

        <div class="grid">
            <!-- COMFYUI PHOTOS -->
            <div class="card card-comfy">
                <div class="card-icon">🎨</div>
                <h2>Génération de Photos & Images</h2>
                <p>Moteur ComfyUI avec DreamShaper 8 et VAE haute précision. Crée des images photoréalistes, portraits, paysages et concepts artistiques avec contrôle total du workflow.</p>
                <div class="card-tags">
                    <span class="tag">DreamShaper 8</span>
                    <span class="tag">SD 1.5</span>
                    <span class="tag">ComfyUI-Manager</span>
                </div>
                <a href=":8188" class="btn btn-primary" onclick="this.href='http://' + window.location.hostname + ':8188'">Ouvrir ComfyUI Studio ➔</a>
            </div>

            <!-- ANIMATEDIFF VIDEOS -->
            <div class="card card-video">
                <div class="card-icon">🎬</div>
                <h2>Génération de Vidéos IA</h2>
                <p>Module AnimateDiff v3 préinstallé. Transforme tes images fixes en vidéos fluides et animations cinématographiques avec contrôle des mouvements de caméra.</p>
                <div class="card-tags">
                    <span class="tag">AnimateDiff v3</span>
                    <span class="tag">Motion Modules</span>
                    <span class="tag">Video Loop</span>
                </div>
                <a href=":8188" class="btn btn-secondary" onclick="this.href='http://' + window.location.hostname + ':8188'">Créer une Vidéo ➔</a>
            </div>

            <!-- KOKORO TTS AUDIO -->
            <div class="card card-tts">
                <div class="card-icon">🎙️</div>
                <h2>Synthèse Vocale HD (TTS)</h2>
                <p>Kokoro Neural TTS avec 72 voix ultra-réalistes (voix de fille et de gars en français et anglais). Lecteur Web intégré et génération audio instantanée en moins d'une seconde.</p>
                <div class="card-tags">
                    <span class="tag">Kokoro HD</span>
                    <span class="tag">Voix Fille & Gars</span>
                    <span class="tag">Web Player</span>
                </div>
                <a href=":8880/web/" class="btn btn-primary" style="background:#06b6d4; box-shadow:0 8px 20px -6px rgba(6,182,212,0.35);" onclick="this.href='http://' + window.location.hostname + ':8880/web/'">Ouvrir Studio Vocal ➔</a>
            </div>
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
</body>
</html>
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/index.html', 'w') as f:
    f.write(portal_html)
sftp.close()

install_portal = """
pct exec 100 -- apt install -y nginx
pct push 100 /tmp/index.html /var/www/html/index.html
pct exec 100 -- sed -i 's/listen 80 default_server;/listen 8080 default_server; listen 80 default_server;/g' /etc/nginx/sites-available/default
pct exec 100 -- systemctl restart nginx
"""

stdin, stdout, stderr = ssh.exec_command(install_portal)
print("PORTAL INSTALL STDOUT:\n", stdout.read().decode())
print("PORTAL INSTALL STDERR:\n", stderr.read().decode())
