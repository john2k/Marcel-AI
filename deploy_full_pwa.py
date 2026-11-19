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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>AI Studio Marcel</title>
    
    <!-- PWA & Mobile Capabilities -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#08090d">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="AI Studio">
    <link rel="apple-touch-icon" href="/icon-192.png">
    <link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">

    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #08090d;
            --surface: #10131e;
            --surface-hover: #181d2e;
            --card-border: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.4);
            --accent-pink: #ec4899;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-amber: #f59e0b;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
            --safe-bottom: env(safe-area-inset-bottom, 0px);
            --safe-top: env(safe-area-inset-top, 0px);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: var(--text-main);
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
        }

        /* TOP APP BAR */
        .app-bar {
            height: calc(56px + var(--safe-top));
            padding-top: var(--safe-top);
            background: rgba(16, 19, 30, 0.85);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--card-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-left: 14px;
            padding-right: 14px;
            z-index: 100;
            flex-shrink: 0;
        }
        .app-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: #fff;
        }
        .brand-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: linear-gradient(135deg, #6366f1, #ec4899);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }
        .brand-title {
            font-weight: 800;
            font-size: 1.05rem;
            letter-spacing: -0.01em;
            background: linear-gradient(135deg, #ffffff 40%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-badge {
            font-size: 0.65rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 999px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #10b981;
            text-transform: uppercase;
        }

        .app-actions {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .action-btn {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--card-border);
            color: #cbd5e1;
            padding: 6px 10px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
        }
        .action-btn:hover {
            background: rgba(255, 255, 255, 0.12);
            color: #fff;
        }
        .btn-install-pwa {
            background: linear-gradient(135deg, #6366f1, #ec4899);
            color: #fff;
            border: none;
            display: none;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
        }

        /* VIEWPORT / TABS CONTAINER */
        .views-viewport {
            flex: 1;
            position: relative;
            overflow: hidden;
            width: 100%;
        }
        .view-panel {
            position: absolute;
            inset: 0;
            display: none;
            flex-direction: column;
            width: 100%;
            height: 100%;
            overflow-y: auto;
            -webkit-overflow-scrolling: touch;
        }
        .view-panel.active {
            display: flex;
        }
        .service-iframe {
            width: 100%;
            height: 100%;
            border: none;
            flex: 1;
            background: #08090d;
        }

        /* BOTTOM DOCK NAVIGATION */
        .bottom-dock {
            height: calc(60px + var(--safe-bottom));
            padding-bottom: var(--safe-bottom);
            background: rgba(14, 17, 27, 0.94);
            backdrop-filter: blur(24px);
            -webkit-backdrop-filter: blur(24px);
            border-top: 1px solid var(--card-border);
            display: flex;
            align-items: center;
            justify-content: space-around;
            padding-left: 4px;
            padding-right: 4px;
            z-index: 100;
            flex-shrink: 0;
        }
        .dock-item {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            color: #64748b;
            text-decoration: none;
            font-size: 0.68rem;
            font-weight: 600;
            padding: 4px 0;
            border-radius: 10px;
            transition: all 0.2s ease;
            cursor: pointer;
            border: none;
            background: transparent;
        }
        .dock-item .dock-icon {
            font-size: 1.25rem;
            transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .dock-item.active {
            color: #fff;
        }
        .dock-item.active .dock-icon {
            transform: scale(1.15) translateY(-2px);
            filter: drop-shadow(0 2px 8px var(--primary-glow));
        }
        .dock-item.active .dock-label {
            font-weight: 700;
            background: linear-gradient(135deg, #a5b4fc, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* HUB / DASHBOARD VIEW */
        .hub-container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 20px 16px 36px;
            width: 100%;
        }
        .hub-hero {
            background: linear-gradient(135deg, rgba(30, 27, 75, 0.7) 0%, rgba(16, 19, 30, 0.85) 100%);
            border: 1px solid rgba(99, 102, 241, 0.35);
            border-radius: 20px;
            padding: 22px;
            margin-bottom: 20px;
            box-shadow: 0 16px 40px -15px rgba(99, 102, 241, 0.25);
        }
        .hub-hero-title {
            font-size: 1.5rem;
            font-weight: 800;
            margin-bottom: 6px;
            color: #fff;
        }
        .hub-hero-desc {
            color: #cbd5e1;
            font-size: 0.92rem;
            line-height: 1.5;
            margin-bottom: 16px;
        }
        .hub-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }
        .hub-card {
            background: var(--surface);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 18px;
            cursor: pointer;
            transition: all 0.25s ease;
            display: flex;
            flex-direction: column;
        }
        .hub-card:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 255, 255, 0.18);
            background: var(--surface-hover);
        }
        .hub-card-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }
        .hub-card-icon {
            font-size: 1.6rem;
        }
        .hub-card-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #fff;
        }
        .hub-card-desc {
            color: var(--text-sub);
            font-size: 0.85rem;
            line-height: 1.45;
            margin-bottom: 14px;
            flex-grow: 1;
        }
        .btn-launch {
            align-self: flex-start;
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 700;
            color: #fff;
            background: rgba(99, 102, 241, 0.2);
            border: 1px solid rgba(99, 102, 241, 0.4);
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        /* SPECS BAR */
        .specs-strip {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 10px;
            background: rgba(16, 19, 30, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 14px;
            text-align: center;
        }
        .spec-label {
            font-size: 0.7rem;
            color: var(--text-sub);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 2px;
        }
        .spec-val {
            font-size: 1rem;
            font-weight: 700;
            color: #fff;
        }

        /* DOWNLOADER VIEW */
        .dl-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px 16px 40px;
            width: 100%;
        }
        .dl-card {
            background: var(--surface);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
        }
        .dl-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 12px 14px;
            color: #fff;
            font-family: inherit;
            font-size: 0.95rem;
            margin-bottom: 12px;
        }
        .dl-input:focus {
            outline: none;
            border-color: var(--primary);
        }
        .dl-select {
            width: 100%;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 12px 14px;
            color: #fff;
            font-family: inherit;
            font-size: 0.95rem;
            margin-bottom: 16px;
            cursor: pointer;
        }
        .btn-dl-submit {
            width: 100%;
            padding: 14px;
            border-radius: 12px;
            background: linear-gradient(135deg, #6366f1, #ec4899);
            color: #fff;
            font-weight: 700;
            font-size: 1rem;
            border: none;
            cursor: pointer;
            box-shadow: 0 8px 20px -6px rgba(99, 102, 241, 0.4);
            transition: transform 0.2s ease;
        }
        .btn-dl-submit:active {
            transform: scale(0.98);
        }

        /* CIVITAI TOKEN PANEL */
        .token-box {
            background: rgba(0, 0, 0, 0.25);
            border: 1px dashed rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 18px;
        }
        .token-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: #cbd5e1;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .token-desc {
            font-size: 0.78rem;
            color: var(--text-sub);
            margin-bottom: 10px;
            line-height: 1.4;
        }
        .token-row {
            display: flex;
            gap: 8px;
        }

        /* TASK LIST & CARDS */
        .task-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 16px;
        }
        .task-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .task-card.is-error {
            border-color: rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.05);
        }
        .task-card.is-success {
            border-color: rgba(16, 185, 129, 0.35);
            background: rgba(16, 185, 129, 0.04);
        }
        .task-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }
        .task-folder-tag {
            font-size: 0.7rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            text-transform: uppercase;
            padding: 2px 8px;
            border-radius: 6px;
            background: rgba(99, 102, 241, 0.2);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }
        .task-filename {
            font-size: 0.9rem;
            font-weight: 700;
            color: #fff;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex: 1;
        }
        .task-status-text {
            font-size: 0.8rem;
            line-height: 1.4;
            color: #cbd5e1;
            word-break: break-word;
        }
        .task-status-text.err {
            color: #fca5a5;
        }
        .task-status-text.ok {
            color: #86efac;
            font-weight: 600;
        }
        .task-bar-bg {
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            overflow: hidden;
        }
        .task-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #ec4899);
            width: 0%;
            transition: width 0.3s ease;
        }
        .task-bar-fill.err {
            background: #ef4444;
        }

        .guide-box {
            background: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 12px;
            padding: 14px;
            margin-top: 16px;
            font-size: 0.82rem;
            color: #cbd5e1;
            line-height: 1.5;
        }
        .guide-box strong { color: #fff; }
        .guide-box a { color: #818cf8; text-decoration: none; }

        /* PWA BANNER POPUP */
        .pwa-banner {
            position: fixed;
            bottom: calc(68px + var(--safe-bottom));
            left: 14px;
            right: 14px;
            max-width: 500px;
            margin: 0 auto;
            background: rgba(20, 24, 38, 0.95);
            border: 1px solid rgba(99, 102, 241, 0.4);
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            display: none;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            z-index: 200;
            animation: slideUp 0.3s ease-out;
        }
        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .pwa-banner-text h4 {
            font-size: 0.92rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 2px;
        }
        .pwa-banner-text p {
            font-size: 0.78rem;
            color: var(--text-sub);
        }
    </style>
</head>
<body>
    <!-- TOP APP BAR -->
    <header class="app-bar">
        <div class="app-brand">
            <div class="brand-icon">✨</div>
            <div>
                <span class="brand-title">Marcel Studio</span>
                <span class="brand-badge" id="serviceBadge">Accueil</span>
            </div>
        </div>
        <div class="app-actions">
            <button class="action-btn btn-install-pwa" id="btnInstallPwa" onclick="promptPwaInstall()">
                📲 Installer
            </button>
            <button class="action-btn" title="Recharger le service actuel" onclick="reloadCurrentService()">
                🔄
            </button>
            <button class="action-btn" title="Plein écran" onclick="toggleFullscreen()">
                ⛶
            </button>
            <a href="#" class="action-btn" id="btnExternal" title="Ouvrir dans un nouvel onglet" target="_blank">
                ↗
            </a>
        </div>
    </header>

    <!-- VIEWS VIEWPORT -->
    <main class="views-viewport">
        <!-- VIEW 0: ACCUEIL / HUB -->
        <div class="view-panel active" id="view-hub">
            <div class="hub-container">
                <div class="hub-hero">
                    <h2 class="hub-hero-title">Studio IA & Code Tout-en-Un</h2>
                    <p class="hub-hero-desc">
                        Tous tes services d'intelligence artificielle hébergés localement sur ton serveur Proxmox. Discute comme sur Gemini, code avec ton assistant IA façon Cursor, génère des images photoréalistes et fais parler des voix hyper-naturelles.
                    </p>
                    <div style="display:flex; gap:10px; flex-wrap:wrap;">
                        <button class="action-btn" style="background:#6366f1; color:#fff;" onclick="switchTab('chat')">
                            💬 Chat IA (Style Gemini)
                        </button>
                        <button class="action-btn" style="background:#10b981; color:#fff;" onclick="switchTab('code')">
                            💻 Coder (Style Cursor / VS Code)
                        </button>
                        <button class="action-btn" onclick="switchTab('fooocus')">
                            🎨 Images (Fooocus)
                        </button>
                    </div>
                </div>

                <div class="hub-grid">
                    <!-- CHAT GEMINI CARD -->
                    <div class="hub-card" onclick="switchTab('chat')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">💬</span>
                            <div class="hub-card-title">Chat IA (Style Gemini)</div>
                        </div>
                        <p class="hub-card-desc">
                            Interface de conversation complète : sélectionne ton modèle (Llama 3.2, Dolphin-Llama3 dérangé, Qwen Coder), pose tes questions, génère des idées et fais analyser des documents.
                        </p>
                        <span class="btn-launch">Ouvrir le Chat ➔</span>
                    </div>

                    <!-- CODE CURSOR CARD -->
                    <div class="hub-card" onclick="switchTab('code')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">💻</span>
                            <div class="hub-card-title">Studio de Code (Style Cursor)</div>
                        </div>
                        <p class="hub-card-desc">
                            VS Code Web avec assistant IA Continue.dev connecté à Qwen 2.5 Coder 7B local. Autocomplétion, chat de code, édition en ligne avec <code>Ctrl+I</code> et terminal intégré.
                        </p>
                        <span class="btn-launch">Ouvrir l'IDE ➔</span>
                    </div>

                    <!-- FOOOCUS CARD -->
                    <div class="hub-card" onclick="switchTab('fooocus')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">🎨</span>
                            <div class="hub-card-title">Fooocus (Style Midjourney)</div>
                        </div>
                        <p class="hub-card-desc">
                            Génération d'images simplifiée : écris ton prompt, choisis tes styles en 1 clic (Cinématique, Réaliste...) et clique sur Generate. Modèle Juggernaut XL pré-chargé.
                        </p>
                        <span class="btn-launch">Générer des Images ➔</span>
                    </div>

                    <!-- KOKORO TTS -->
                    <div class="hub-card" onclick="switchTab('tts')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">🎙️</span>
                            <div class="hub-card-title">Kokoro Neural TTS</div>
                        </div>
                        <p class="hub-card-desc">
                            72 voix ultra-réalistes d'hommes et de femmes en français et en anglais. Lecteur audio instantané avec écoute et export WAV/MP3 en 1 seconde.
                        </p>
                        <span class="btn-launch">Créer des Voix ➔</span>
                    </div>

                    <!-- COMFYUI -->
                    <div class="hub-card" onclick="switchTab('comfy')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">🎬</span>
                            <div class="hub-card-title">ComfyUI & Vidéos</div>
                        </div>
                        <p class="hub-card-desc">
                            Mode expert nodal avec AnimateDiff v3 pour animer tes images en vidéos cinématographiques et flux de travail personnalisés.
                        </p>
                        <span class="btn-launch">Studio Nœuds / Vidéo ➔</span>
                    </div>

                    <!-- DOWNLOADER -->
                    <div class="hub-card" onclick="switchTab('downloads')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">⚡</span>
                            <div class="hub-card-title">Téléchargeur de Modèles</div>
                        </div>
                        <p class="hub-card-desc">
                            Télécharge des modèles Civitai (avec clé API pour les modèles 18+/restreints) ou Hugging Face directement sur tes 31 To sans toucher à ton PC ou téléphone.
                        </p>
                        <span class="btn-launch">Gérer les Modèles ➔</span>
                    </div>
                </div>

                <!-- SPECS -->
                <div class="specs-strip">
                    <div>
                        <div class="spec-label">Processeur</div>
                        <div class="spec-val">Ryzen 2700X (16T)</div>
                    </div>
                    <div>
                        <div class="spec-label">Mémoire Dédiée</div>
                        <div class="spec-val">56 GB RAM</div>
                    </div>
                    <div>
                        <div class="spec-label">GPU Dédié</div>
                        <div class="spec-val">RX 5600 XT (Vulkan)</div>
                    </div>
                    <div>
                        <div class="spec-label">Stockage ZFS</div>
                        <div class="spec-val">31 To Stripe</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- VIEW 1: CHAT GEMINI (OPEN WEBUI) -->
        <div class="view-panel" id="view-chat">
            <iframe id="iframe-chat" class="service-iframe" data-src="/chat/"></iframe>
        </div>

        <!-- VIEW 2: CODE STUDIO (CURSOR / VS CODE WEB) -->
        <div class="view-panel" id="view-code">
            <iframe id="iframe-code" class="service-iframe" data-src="/code/?folder=/datastore/workspace"></iframe>
        </div>

        <!-- VIEW 3: FOOOCUS IFRAME -->
        <div class="view-panel" id="view-fooocus">
            <iframe id="iframe-fooocus" class="service-iframe" data-src="/fooocus/"></iframe>
        </div>

        <!-- VIEW 4: KOKORO TTS IFRAME -->
        <div class="view-panel" id="view-tts">
            <iframe id="iframe-tts" class="service-iframe" data-src="/tts/web/"></iframe>
        </div>

        <!-- VIEW 5: COMFYUI IFRAME -->
        <div class="view-panel" id="view-comfy">
            <iframe id="iframe-comfy" class="service-iframe" data-src="/comfy/"></iframe>
        </div>

        <!-- VIEW 6: DOWNLOADER -->
        <div class="view-panel" id="view-downloads">
            <div class="dl-container">
                <div class="dl-card">
                    <h3 style="font-size:1.25rem; margin-bottom:6px; color:#fff;">⚡ Téléchargement Direct sur le Serveur</h3>
                    <p style="color:var(--text-sub); font-size:0.85rem; margin-bottom:16px;">
                        Colle l'adresse de téléchargement d'un modèle. Il sera stocké dans tes 31 To et partagé entre Fooocus et ComfyUI !
                    </p>

                    <!-- CIVITAI API TOKEN BOX -->
                    <div class="token-box">
                        <div class="token-title">
                            <span>🔑 Clé API Civitai (Débloque les modèles restreints)</span>
                            <span id="tokenBadge" style="font-size:0.75rem; color:#10b981;"></span>
                        </div>
                        <div class="token-desc">
                            Nécessaire pour télécharger les modèles Civitai qui demandent d'être connecté (18+, NSFW ou modèles restreints). Crée ta clé gratuite sur <a href="https://civitai.com/user/account" target="_blank" style="color:#818cf8; text-decoration:underline;">Civitai ➔ Account Settings ➔ API Keys</a>.
                        </div>
                        <div class="token-row">
                            <input type="password" id="civitaiKeyInput" class="dl-input" style="margin-bottom:0;" placeholder="Colle ta clé API Civitai ici...">
                            <button type="button" class="action-btn" style="background:#6366f1; color:#fff;" onclick="saveCivitaiKey()">Sauvegarder</button>
                        </div>
                    </div>

                    <form onsubmit="handleDownload(event)">
                        <input type="url" id="modelUrl" class="dl-input" placeholder="https://civitai.com/api/download/models/... ou HuggingFace" required>
                        <select id="modelFolder" class="dl-select">
                            <option value="checkpoints">Modèle Principal (Checkpoints SDXL / SD 1.5)</option>
                            <option value="loras">LoRA (Style, Visage, Personnage)</option>
                            <option value="vae">VAE (Couleurs & Rendu)</option>
                            <option value="controlnet">ControlNet (Poses & Esquisses)</option>
                        </select>
                        <button type="submit" class="btn-dl-submit">Télécharger sur le Serveur</button>
                    </form>

                    <div class="guide-box">
                        💡 <strong>Conseils utiles :</strong><br>
                        • <strong>Hugging Face :</strong> Clique sur l'onglet <strong>Files and versions</strong> et copie le lien du fichier <strong>.safetensors</strong> (et non pas config.json ou README.md !).<br>
                        • <strong>Civitai :</strong> Fais un clic droit sur le bouton <strong>Download</strong> ➔ <em>Copier l'adresse du lien</em>.
                    </div>

                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px; margin-bottom:10px;">
                        <h4 style="font-size:0.95rem; color:#fff;">Tâches de téléchargement</h4>
                        <button type="button" class="action-btn" style="font-size:0.75rem; padding:4px 10px;" onclick="clearDownloadTasks()">Effacer l'historique</button>
                    </div>

                    <div class="task-list" id="tasksList"></div>
                </div>
            </div>
        </div>
    </main>

    <!-- FLOATING PWA INSTALL BANNER -->
    <div class="pwa-banner" id="pwaBanner">
        <div class="pwa-banner-text">
            <h4>Installer l'application</h4>
            <p>Ajoute Marcel Studio à ton écran d'accueil pour une expérience plein écran rapide.</p>
        </div>
        <button class="action-btn" style="background:#6366f1; color:#fff;" onclick="promptPwaInstall()">
            Installer
        </button>
    </div>

    <!-- BOTTOM DOCK NAVIGATION -->
    <nav class="bottom-dock">
        <button class="dock-item active" id="dock-hub" onclick="switchTab('hub')">
            <span class="dock-icon">🏠</span>
            <span class="dock-label">Accueil</span>
        </button>
        <button class="dock-item" id="dock-chat" onclick="switchTab('chat')">
            <span class="dock-icon">💬</span>
            <span class="dock-label">Chat</span>
        </button>
        <button class="dock-item" id="dock-code" onclick="switchTab('code')">
            <span class="dock-icon">💻</span>
            <span class="dock-label">Code</span>
        </button>
        <button class="dock-item" id="dock-fooocus" onclick="switchTab('fooocus')">
            <span class="dock-icon">🎨</span>
            <span class="dock-label">Images</span>
        </button>
        <button class="dock-item" id="dock-tts" onclick="switchTab('tts')">
            <span class="dock-icon">🎙️</span>
            <span class="dock-label">Voix</span>
        </button>
        <button class="dock-item" id="dock-downloads" onclick="switchTab('downloads')">
            <span class="dock-icon">📥</span>
            <span class="dock-label">Modèles</span>
        </button>
    </nav>

    <script>
        // Tab routing state
        let currentTab = 'hub';
        const externalLinks = {
            hub: '/',
            chat: '/chat/',
            code: '/code/?folder=/datastore/workspace',
            fooocus: '/fooocus/',
            tts: '/tts/web/',
            comfy: '/comfy/',
            downloads: '/'
        };
        const badges = {
            hub: 'Accueil',
            chat: 'Gemini Chat',
            code: 'Cursor IDE',
            fooocus: 'Fooocus SDXL',
            tts: 'Kokoro Voix',
            comfy: 'ComfyUI Vidéo',
            downloads: 'Téléchargeur'
        };

        function switchTab(tabId) {
            currentTab = tabId;
            
            // Update dock styles
            document.querySelectorAll('.dock-item').forEach(el => el.classList.remove('active'));
            const activeDock = document.getElementById('dock-' + tabId);
            if (activeDock) activeDock.classList.add('active');

            // Update panels
            document.querySelectorAll('.view-panel').forEach(el => el.classList.remove('active'));
            const activePanel = document.getElementById('view-' + tabId);
            if (activePanel) activePanel.classList.add('active');

            // Lazy load iframe if needed
            if (['chat', 'code', 'fooocus', 'tts', 'comfy'].includes(tabId)) {
                const iframe = document.getElementById('iframe-' + tabId);
                if (iframe && !iframe.getAttribute('src')) {
                    iframe.setAttribute('src', iframe.getAttribute('data-src'));
                }
            }

            // Update Header External Link & Badge
            const btnExt = document.getElementById('btnExternal');
            btnExt.href = externalLinks[tabId] || '/';
            document.getElementById('serviceBadge').innerText = badges[tabId] || 'Studio';

            // Refresh downloads if tab selected
            if (tabId === 'downloads') {
                fetchTasks();
                checkSavedToken();
            }
        }

        function reloadCurrentService() {
            if (['chat', 'code', 'fooocus', 'tts', 'comfy'].includes(currentTab)) {
                const iframe = document.getElementById('iframe-' + currentTab);
                if (iframe) iframe.src = iframe.src;
            } else {
                window.location.reload();
            }
        }

        function toggleFullscreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(() => {});
            } else {
                document.exitFullscreen().catch(() => {});
            }
        }

        // PWA Installation Handling
        let deferredPrompt = null;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const btn = document.getElementById('btnInstallPwa');
            const banner = document.getElementById('pwaBanner');
            if (btn) btn.style.display = 'inline-flex';
            if (banner) banner.style.display = 'flex';
        });

        function promptPwaInstall() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        document.getElementById('pwaBanner').style.display = 'none';
                        document.getElementById('btnInstallPwa').style.display = 'none';
                    }
                    deferredPrompt = null;
                });
            } else {
                alert("Sur mobile : ouvre le menu de ton navigateur (3 petits points sur Android ou bouton Partager sur iPhone) et choisis 'Ajouter à l\\'écran d\\'accueil' ou 'Installer l\\'application'.");
            }
        }

        window.addEventListener('appinstalled', () => {
            document.getElementById('pwaBanner').style.display = 'none';
            document.getElementById('btnInstallPwa').style.display = 'none';
            deferredPrompt = null;
        });

        // Register Service Worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(reg => console.log('PWA ServiceWorker registered', reg.scope))
                    .catch(err => console.log('PWA ServiceWorker registration failed', err));
            });
        }

        // Civitai API Key management
        async function checkSavedToken() {
            try {
                const res = await fetch('/api/civitai_token');
                const data = await res.json();
                const badge = document.getElementById('tokenBadge');
                if (data.has_token) {
                    badge.innerText = '✓ Clé active (' + data.masked_token + ')';
                    badge.style.color = '#10b981';
                } else {
                    badge.innerText = '⚠️ Aucune clé enregistrée';
                    badge.style.color = '#f59e0b';
                }
            } catch(e) {}
        }

        async function saveCivitaiKey() {
            const input = document.getElementById('civitaiKeyInput');
            const token = input.value.trim();
            if (!token) return;
            try {
                const res = await fetch('/api/civitai_token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token })
                });
                const data = await res.json();
                if (data.success) {
                    input.value = '';
                    alert('Clé API Civitai enregistrée avec succès sur le serveur !');
                    checkSavedToken();
                }
            } catch(e) {
                alert('Erreur: ' + e.message);
            }
        }

        async function clearDownloadTasks() {
            try {
                await fetch('/api/downloads/clear', { method: 'POST' });
                fetchTasks();
            } catch(e) {}
        }

        // Downloader API
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
                if (!tasks.length) {
                    container.innerHTML = '<div style="color:var(--text-sub); font-size:0.85rem; text-align:center; padding:16px;">Aucun téléchargement en cours</div>';
                    return;
                }

                container.innerHTML = tasks.slice().reverse().map(t => {
                    const isErr = t.error || t.status.toLowerCase().includes('erreur') || t.status.toLowerCase().includes('client error');
                    const isOk = t.progress === 100 && !isErr;
                    const statusClass = isErr ? 'err' : (isOk ? 'ok' : '');
                    const cardClass = isErr ? 'is-error' : (isOk ? 'is-success' : '');
                    const barFillClass = isErr ? 'err' : '';

                    return `
                        <div class="task-card ${cardClass}">
                            <div class="task-header">
                                <span class="task-folder-tag">${t.folder}</span>
                                <span class="task-filename" title="${t.filename}">${t.filename}</span>
                                <span style="font-size:0.75rem; font-family:'JetBrains Mono'; color:#cbd5e1;">${t.progress}%</span>
                            </div>
                            <div class="task-status-text ${statusClass}">${t.status}</div>
                            ${!isErr ? `
                                <div class="task-bar-bg">
                                    <div class="task-bar-fill ${barFillClass}" style="width: ${t.progress}%"></div>
                                </div>
                            ` : ''}
                        </div>
                    `;
                }).join('');
            } catch(err) {}
        }

        setInterval(fetchTasks, 3000);
        switchTab('hub');
        checkSavedToken();
    </script>
</body>
</html>
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/pwa_index.html', 'wb') as f:
    f.write(html_content.encode('utf-8'))
sftp.close()

stdin, stdout, stderr = ssh.exec_command("pct push 100 /tmp/pwa_index.html /var/www/html/index.html")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)

ssh.close()
print("PWA index.html with Chat and Code IDE deployed successfully!")
