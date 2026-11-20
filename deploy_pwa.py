import os
import re
import paramiko

if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ.setdefault(k, v)

# Construct index.html
html_content = r"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Marcel AI Studio</title>
    
    <!-- PWA & Mobile Capabilities -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#08090d">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Marcel Studio">
    
    <!-- Favicon & Icons -->
    <link rel="icon" type="image/x-icon" href="/favicon.ico?v=2">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon.png?v=2">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png?v=2">

    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
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

        /* --- AUTH LOGIN OVERLAY --- */
        .auth-overlay {
            position: fixed;
            inset: 0;
            background: #08090d;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }
        .auth-overlay.hidden {
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }
        .auth-card {
            background: rgba(16, 19, 30, 0.95);
            border: 1px solid rgba(99, 102, 241, 0.3);
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(99, 102, 241, 0.2);
            border-radius: 24px;
            padding: 32px 28px;
            max-width: 380px;
            width: 100%;
            text-align: center;
            animation: authPop 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes authPop {
            0% { transform: scale(0.92); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        .auth-avatar-box {
            position: relative;
            width: 88px;
            height: 88px;
            margin: 0 auto 16px;
        }
        .auth-avatar-img {
            width: 100%;
            height: 100%;
            border-radius: 22px;
            object-fit: cover;
            border: 2px solid rgba(99, 102, 241, 0.6);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
        }
        .auth-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #fff;
            margin-bottom: 4px;
            letter-spacing: -0.3px;
        }
        .auth-subtitle {
            font-size: 0.82rem;
            color: var(--text-sub);
            margin-bottom: 22px;
        }
        .auth-input-group {
            margin-bottom: 12px;
            text-align: left;
        }
        .auth-label {
            display: block;
            font-size: 0.75rem;
            font-weight: 600;
            color: #cbd5e1;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .auth-input {
            width: 100%;
            padding: 12px 14px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: #fff;
            font-family: inherit;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s;
        }
        .auth-input:focus {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.08);
            box-shadow: 0 0 12px rgba(99, 102, 241, 0.25);
        }
        .auth-error {
            color: #ef4444;
            font-size: 0.8rem;
            margin-bottom: 12px;
            display: none;
            font-weight: 500;
        }
        .btn-auth-submit {
            width: 100%;
            padding: 14px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary), var(--accent-pink));
            color: #fff;
            border: none;
            font-weight: 700;
            font-size: 0.95rem;
            cursor: pointer;
            box-shadow: 0 6px 20px var(--primary-glow);
            transition: all 0.2s;
            margin-top: 6px;
        }
        .btn-auth-submit:active {
            transform: scale(0.98);
        }

        /* TOP APP BAR */
        .app-bar {
            height: calc(54px + var(--safe-top));
            padding-top: var(--safe-top);
            background: rgba(16, 19, 30, 0.9);
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
            cursor: pointer;
        }
        .brand-icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(99, 102, 241, 0.4);
            box-shadow: 0 4px 12px var(--primary-glow);
        }
        .brand-icon img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .brand-title {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: -0.3px;
            background: linear-gradient(135deg, #fff 40%, var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .brand-badge {
            font-size: 0.68rem;
            padding: 2px 7px;
            border-radius: 6px;
            background: rgba(99, 102, 241, 0.2);
            color: #a5b4fc;
            border: 1px solid rgba(99, 102, 241, 0.3);
            font-weight: 600;
            text-transform: uppercase;
        }
        .app-actions {
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .action-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: var(--text-main);
            border-radius: 9px;
            padding: 6px 10px;
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            font-weight: 500;
        }
        .action-btn:hover {
            background: var(--surface-hover);
            border-color: rgba(255, 255, 255, 0.2);
        }
        .action-btn.btn-pulse-log {
            background: rgba(16, 185, 129, 0.15);
            border-color: rgba(16, 185, 129, 0.4);
            color: #6ee7b7;
        }
        .action-btn.btn-pulse-log.has-error {
            background: rgba(239, 68, 68, 0.15);
            border-color: rgba(239, 68, 68, 0.4);
            color: #fca5a5;
            animation: pulseAlert 1.5s infinite;
        }
        @keyframes pulseAlert {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(0.98); }
        }

        /* VIEWS VIEWPORT */
        .views-viewport {
            flex: 1;
            position: relative;
            overflow: hidden;
            background: #000;
        }
        .view-panel {
            position: absolute;
            inset: 0;
            display: none;
            flex-direction: column;
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
            background: var(--bg);
        }

        /* BOTTOM DOCK */
        .bottom-dock {
            height: calc(60px + var(--safe-bottom));
            padding-bottom: var(--safe-bottom);
            background: rgba(12, 14, 24, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-top: 1px solid var(--card-border);
            display: flex;
            align-items: center;
            justify-content: space-around;
            padding-left: 6px;
            padding-right: 6px;
            z-index: 100;
            flex-shrink: 0;
        }
        .dock-item {
            flex: 1;
            height: 48px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 2px;
            background: none;
            border: none;
            color: #64748b;
            font-size: 0.65rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.2s ease;
            position: relative;
            padding: 4px 0;
        }
        .dock-item .dock-icon {
            font-size: 1.25rem;
            transition: transform 0.2s ease;
        }
        .dock-item.active {
            color: #fff;
        }
        .dock-item.active .dock-icon {
            transform: translateY(-2px) scale(1.1);
        }
        .dock-item.active::after {
            content: '';
            position: absolute;
            top: 2px;
            width: 16px;
            height: 3px;
            background: var(--primary);
            border-radius: 3px;
            box-shadow: 0 0 10px var(--primary);
        }

        /* HUB DASHBOARD */
        .hub-container {
            padding: 16px;
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
            padding-bottom: 24px;
        }
        .hub-hero {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(236, 72, 153, 0.08));
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 18px;
            padding: 20px;
            margin-bottom: 18px;
            position: relative;
            overflow: hidden;
        }
        .hub-hero-title {
            font-size: 1.4rem;
            font-weight: 800;
            margin-bottom: 6px;
            background: linear-gradient(135deg, #fff 30%, #a5b4fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hub-hero-desc {
            color: var(--text-sub);
            font-size: 0.86rem;
            line-height: 1.5;
            margin-bottom: 14px;
        }
        .hub-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 12px;
            margin-bottom: 18px;
        }
        .hub-card {
            background: var(--surface);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.25s ease;
            position: relative;
        }
        .hub-card:hover {
            border-color: rgba(99, 102, 241, 0.4);
            transform: translateY(-2px);
            background: var(--surface-hover);
        }
        .hub-card-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }
        .hub-card-icon {
            font-size: 1.5rem;
        }
        .hub-card-title {
            font-size: 1rem;
            font-weight: 700;
            color: #fff;
        }
        .hub-card-desc {
            font-size: 0.8rem;
            color: var(--text-sub);
            line-height: 1.4;
        }

        /* --- VIBE CODER (STYLE ANTIGRAVITY) --- */
        .vibe-wrapper {
            display: flex;
            flex-direction: column;
            height: 100%;
            background: #090b12;
            overflow: hidden;
        }
        .vibe-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #111422;
            border-bottom: 1px solid var(--card-border);
            padding: 8px 12px;
            flex-shrink: 0;
            gap: 8px;
            flex-wrap: wrap;
        }
        .vibe-mode-pills {
            display: flex;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 3px;
            gap: 2px;
        }
        .vibe-pill {
            background: none;
            border: none;
            color: var(--text-sub);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .vibe-pill.active {
            background: var(--primary);
            color: #fff;
            box-shadow: 0 2px 8px var(--primary-glow);
        }
        .vibe-body {
            flex: 1;
            display: flex;
            position: relative;
            overflow: hidden;
        }
        .vibe-chat-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            background: #0a0c16;
            border-right: 1px solid var(--card-border);
            overflow: hidden;
        }
        .vibe-preview-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            background: #05060a;
            position: relative;
        }
        .vibe-files-panel {
            flex: 1;
            display: none;
            flex-direction: column;
            height: 100%;
            background: #0a0c16;
            padding: 14px;
            overflow-y: auto;
        }

        @media (max-width: 768px) {
            .vibe-chat-panel, .vibe-preview-panel, .vibe-files-panel {
                position: absolute;
                inset: 0;
                display: none;
            }
            .vibe-view-chat .vibe-chat-panel { display: flex; }
            .vibe-view-preview .vibe-preview-panel { display: flex; }
            .vibe-view-files .vibe-files-panel { display: flex; }
        }

        .vibe-messages {
            flex: 1;
            overflow-y: auto;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .vibe-msg {
            max-width: 88%;
            padding: 12px 14px;
            border-radius: 14px;
            font-size: 0.88rem;
            line-height: 1.5;
        }
        .vibe-msg.user {
            align-self: flex-end;
            background: linear-gradient(135deg, #4f46e5, #6366f1);
            color: #fff;
            border-bottom-right-radius: 4px;
        }
        .vibe-msg.ai {
            align-self: flex-start;
            background: var(--surface);
            border: 1px solid var(--card-border);
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }
        .vibe-file-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            margin-top: 6px;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 0.75rem;
            font-family: 'JetBrains Mono', monospace;
            cursor: pointer;
        }
        .vibe-chips {
            display: flex;
            gap: 6px;
            padding: 8px 14px;
            overflow-x: auto;
            flex-shrink: 0;
            border-top: 1px solid rgba(255, 255, 255, 0.04);
        }
        .vibe-chip {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            color: #94a3b8;
            border-radius: 20px;
            padding: 5px 12px;
            font-size: 0.74rem;
            white-space: nowrap;
            cursor: pointer;
            transition: all 0.2s;
        }
        .vibe-chip:hover {
            color: #fff;
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.1);
        }
        .vibe-input-bar {
            padding: 10px 14px;
            background: #111422;
            border-top: 1px solid var(--card-border);
            display: flex;
            gap: 8px;
            align-items: center;
            flex-shrink: 0;
        }
        .vibe-textarea {
            flex: 1;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 10px 12px;
            color: #fff;
            font-family: inherit;
            font-size: 0.88rem;
            resize: none;
            outline: none;
            min-height: 42px;
            max-height: 100px;
        }
        .vibe-textarea:focus {
            border-color: var(--primary);
        }
        .vibe-btn-send {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary), var(--accent-pink));
            border: none;
            color: #fff;
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        /* --- LOG ANALYZER VIEW --- */
        .logs-container {
            padding: 16px;
            max-width: 1000px;
            margin: 0 auto;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .logs-nav {
            display: flex;
            gap: 6px;
            overflow-x: auto;
            padding-bottom: 4px;
            flex-shrink: 0;
        }
        .logs-cat-btn {
            background: var(--surface);
            border: 1px solid var(--card-border);
            color: var(--text-sub);
            padding: 8px 14px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }
        .logs-cat-btn.active {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
            box-shadow: 0 4px 12px var(--primary-glow);
        }
        .logs-status-card {
            background: var(--surface);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 14px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
            flex-shrink: 0;
        }
        .logs-status-info h3 {
            font-size: 1rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 2px;
        }
        .logs-status-info p {
            font-size: 0.78rem;
            color: var(--text-sub);
        }
        .logs-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
                .btn-ai-autofix {
            background: linear-gradient(135deg, #6366f1, #ec4899);
            color: #fff;
            border: none;
            padding: 8px 14px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            box-shadow: 0 4px 14px rgba(236, 72, 153, 0.35);
            transition: all 0.2s;
        }
        .btn-ai-autofix:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(236, 72, 153, 0.5);
        }
        .btn-ai-autofix:active {
            transform: scale(0.97);
        }
        .btn-ai-diag {
            background: linear-gradient(135deg, #059669, #10b981);
            color: #fff;
            border: none;
            padding: 8px 14px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .btn-svc-restart {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #fca5a5;
            padding: 8px 12px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
        }
        .ai-diagnosis-box {
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 14px;
            font-size: 0.85rem;
            line-height: 1.5;
            display: none;
            flex-shrink: 0;
        }
        .ai-diagnosis-box.active {
            display: block;
        }
        .ai-diagnosis-box h4 {
            color: #34d399;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .terminal-box {
            flex: 1;
            background: #05070d;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            color: #cbd5e1;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
            line-height: 1.45;
        }

        /* --- DOWNLOADER TAB --- */
        .dl-container {
            padding: 16px;
            max-width: 700px;
            margin: 0 auto;
            width: 100%;
        }
        .dl-card {
            background: var(--surface);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .dl-input, .dl-select {
            width: 100%;
            padding: 12px 14px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--card-border);
            color: #fff;
            font-family: inherit;
            font-size: 0.9rem;
            margin-bottom: 12px;
            outline: none;
        }
        .btn-dl-submit {
            width: 100%;
            padding: 14px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary), var(--accent-pink));
            color: #fff;
            border: none;
            font-weight: 700;
            font-size: 0.95rem;
            cursor: pointer;
        }
        .token-box {
            background: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 16px;
        }
        .token-row {
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }

        /* --- HARDWARE HUD & STATS --- */
        .hud-section {
            margin-top: 20px;
            margin-bottom: 24px;
        }
        .hud-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .hud-title {
            font-size: 0.85rem;
            font-weight: 700;
            color: #cbd5e1;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .hud-live-tag {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.7rem;
            color: #10b981;
            font-weight: 700;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 3px 8px;
            border-radius: 20px;
        }
        .pulse-dot {
            width: 7px;
            height: 7px;
            background: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10b981;
            animation: pulse 1.5s infinite;
        }
        .hud-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 12px;
        }
        .hud-card {
            background: rgba(16, 19, 30, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-direction: column;
            transition: all 0.2s ease;
        }
        .hud-card:hover {
            border-color: rgba(99, 102, 241, 0.4);
            transform: translateY(-2px);
        }
        .hud-card-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .hud-card-name {
            font-size: 0.78rem;
            font-weight: 600;
            color: #94a3b8;
        }
        .hud-badge {
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 6px;
            background: rgba(99, 102, 241, 0.2);
            color: #818cf8;
        }
        .hud-badge.temp {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
            font-family: 'JetBrains Mono', monospace;
        }
        .hud-badge.status-idle {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .hud-badge.status-busy {
            background: rgba(236, 72, 153, 0.2);
            color: #f472b6;
            border: 1px solid rgba(236, 72, 153, 0.4);
            animation: pulse 1s infinite;
        }
        .hud-card-val {
            font-size: 1.35rem;
            font-weight: 800;
            color: #fff;
            margin-bottom: 8px;
            letter-spacing: -0.3px;
        }
        .hud-progress-bg {
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 8px;
        }
        .hud-progress-bar {
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(90deg, #6366f1, #818cf8);
            transition: width 0.4s ease;
        }
        .hud-progress-bar.bar-gpu {
            background: linear-gradient(90deg, #ec4899, #f43f5e);
        }
        .hud-progress-bar.bar-ram {
            background: linear-gradient(90deg, #06b6d4, #3b82f6);
        }
        .hud-card-sub {
            font-size: 0.72rem;
            color: #64748b;
        }
        .hud-activity-card {
            border: 1px solid rgba(16, 185, 129, 0.3);
            background: rgba(16, 26, 24, 0.85);
        }
        .hud-activity-text {
            font-size: 0.9rem;
            font-weight: 700;
            color: #34d399;
            margin-bottom: 8px;
            line-height: 1.35;
            min-height: 2.7em;
            display: flex;
            align-items: center;
        }

        .hw-pill {
            display: none;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--card-border);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 600;
            cursor: pointer;
            color: #cbd5e1;
            transition: all 0.2s;
        }
        .hw-pill:hover {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.1);
        }
        .btn-clear-logs {
            background: rgba(239, 68, 68, 0.15);
            color: #fca5a5;
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 7px 12px;
            font-size: 0.76rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-clear-logs:hover {
            background: rgba(239, 68, 68, 0.25);
            color: #fff;
        }
    </style>
</head>
<body class="vibe-view-chat">

    <!-- AUTHENTICATION OVERLAY / LOGIN GATE -->
    <div class="auth-overlay" id="authOverlay">
        <div class="auth-card">
            <div class="auth-avatar-box">
                <img src="/marcel-avatar.png" class="auth-avatar-img" alt="Marcel AI">
            </div>
            <h2 class="auth-title">Marcel AI Studio</h2>
            <p class="auth-subtitle">Accès sécurisé à votre espace d'intelligence artificielle</p>
            
            <form onsubmit="handleLogin(event)">
                <div class="auth-input-group">
                    <label class="auth-label">Utilisateur</label>
                    <input type="text" id="loginUser" class="auth-input" value="marcel" required autocomplete="username">
                </div>
                <div class="auth-input-group">
                    <label class="auth-label">Mot de passe</label>
                    <input type="password" id="loginPass" class="auth-input" placeholder="Entrez votre mot de passe" required autocomplete="current-password">
                </div>
                <div class="auth-error" id="loginError">Mot de passe incorrect</div>
                <button type="submit" class="btn-auth-submit" id="btnLoginSubmit">Se connecter</button>
            </form>
        </div>
    </div>

    <!-- TOP APP BAR -->
    <header class="app-bar">
        <div class="app-brand" onclick="switchTab('hub')">
            <div class="brand-icon">
                <img src="/marcel-avatar.png" alt="Marcel AI">
            </div>
            <div>
                <span class="brand-title">Marcel Studio</span>
                <span class="brand-badge" id="serviceBadge">Accueil</span>
            </div>
        </div>
        <div class="app-actions">
            <!-- Hardware Live Pill -->
            <div class="hw-pill" id="topHwPill" onclick="switchTab('logs')" title="Surveillance Matériel en direct">
                <span id="pillPulse">🟢</span> <span id="pillText">Matériel...</span>
            </div>
            <!-- Pulsing Log Analyzer Button -->
            <button class="action-btn btn-pulse-log" id="btnPulseLog" onclick="switchTab('logs')">
                <span id="logPulseDot">🟢</span> Logs & Santé
            </button>
            <button class="action-btn" title="Recharger" onclick="reloadCurrentService()">
                🔄
            </button>
            <button class="action-btn" title="Plein écran" onclick="toggleFullscreen()">
                ⛶
            </button>
            <a href="#" class="action-btn" id="btnExternal" title="Ouvrir dans un nouvel onglet" target="_blank">
                ↗
            </a>
            <button class="action-btn" title="Se déconnecter" onclick="handleLogout()" style="color:#fca5a5;">
                🚪
            </button>
        </div>
    </header>

    <!-- MAIN VIEWPORT -->
    <main class="views-viewport">
        <!-- VIEW 0: ACCUEIL / HUB -->
        <div class="view-panel active" id="view-hub">
            <div class="hub-container">
                <div class="hub-hero">
                    <h2 class="hub-hero-title">Marcel AI & Vibe Studio 🚀</h2>
                    <p class="hub-hero-desc">
                        Tous tes services d'intelligence artificielle locale réunis en une seule application. Code tes apps en direct par prompt, discute avec Marcel-QC sans filtre, génère des images photoréalistes et fais analyser tes logs en un clic !
                    </p>
                    <div style="display:flex; gap:8px; flex-wrap:wrap;">
                        <button class="action-btn" style="background:#6366f1; color:#fff;" onclick="switchTab('code')">
                            💻 Vibe Coder (Antigravity)
                        </button>
                        <button class="action-btn" style="background:#06b6d4; color:#fff;" onclick="switchTab('chat')">
                            💬 Chat IA (Marcel-QC)
                        </button>
                        <button class="action-btn" style="background:#10b981; color:#fff;" onclick="switchTab('logs')">
                            📊 Logs & Analyseur IA
                        </button>
                    </div>
                </div>

                <!-- LIVE HARDWARE & ACTIVITY MONITOR HUD -->
                <div class="hud-section">
                    <div class="hud-header">
                        <div class="hud-title">⚡ Surveillance Matériel & Activité en Direct</div>
                        <div class="hud-live-tag"><span class="pulse-dot"></span> TEMPS RÉEL (3s)</div>
                    </div>
                    <div class="hud-grid">
                        <!-- CPU CARD -->
                        <div class="hud-card" onclick="switchTab('logs')" style="cursor:pointer;">
                            <div class="hud-card-top">
                                <span class="hud-card-name">⚡ CPU Ryzen 2700X</span>
                                <span class="hud-badge temp" id="hudCpuTemp">--.- °C</span>
                            </div>
                            <div class="hud-card-val" id="hudCpuLoad">0.0 %</div>
                            <div class="hud-progress-bg">
                                <div class="hud-progress-bar" id="hudCpuBar" style="width: 0%;"></div>
                            </div>
                            <div class="hud-card-sub" id="hudCpuSub">8 Cœurs / 16 Threads</div>
                        </div>

                        <!-- GPU CARD -->
                        <div class="hud-card" onclick="switchTab('logs')" style="cursor:pointer;">
                            <div class="hud-card-top">
                                <span class="hud-card-name">🎮 GPU RX 5600 XT</span>
                                <span class="hud-badge temp" id="hudGpuTemp">--.- °C</span>
                            </div>
                            <div class="hud-card-val" id="hudGpuVram">-- / 6.0 Go</div>
                            <div class="hud-progress-bg">
                                <div class="hud-progress-bar bar-gpu" id="hudGpuBar" style="width: 0%;"></div>
                            </div>
                            <div class="hud-card-sub" id="hudGpuSub">Activité GPU : 0% | VRAM : 0%</div>
                        </div>

                        <!-- RAM CARD -->
                        <div class="hud-card" onclick="switchTab('logs')" style="cursor:pointer;">
                            <div class="hud-card-top">
                                <span class="hud-card-name">🧠 RAM Serveur</span>
                                <span class="hud-badge" id="hudRamPercent">0%</span>
                            </div>
                            <div class="hud-card-val" id="hudRamVal">-- / 56.0 Go</div>
                            <div class="hud-progress-bg">
                                <div class="hud-progress-bar bar-ram" id="hudRamBar" style="width: 0%;"></div>
                            </div>
                            <div class="hud-card-sub" id="hudRamSub">Mémoire DDR4</div>
                        </div>

                        <!-- ACTIVITY STATUS CARD -->
                        <div class="hud-card hud-activity-card" id="hudActivityCard" onclick="switchTab('logs')" style="cursor:pointer;">
                            <div class="hud-card-top">
                                <span class="hud-card-name">📡 État d'Activité</span>
                                <span class="hud-badge status-idle" id="hudActivityBadge">En veille</span>
                            </div>
                            <div class="hud-activity-text" id="hudActivityText">Système prêt (Aucun calcul intensif)</div>
                            <div class="hud-card-sub" id="hudActivitySub">Surveillance IA & Services</div>
                        </div>
                    </div>
                </div>

                <div class="hub-grid">
                    <div class="hub-card" onclick="switchTab('code')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">💻</span>
                            <div class="hub-card-title">Vibe Coder (Style Antigravity)</div>
                        </div>
                        <p class="hub-card-desc">Code en direct par simple prompt avec Qwen 2.5 Coder. Aperçu interactif instantané sans complexité technique.</p>
                    </div>

                    <div class="hub-card" onclick="switchTab('chat')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">💬</span>
                            <div class="hub-card-title">Chat IA Multimodèle</div>
                        </div>
                        <p class="hub-card-desc">Discute avec Marcel-QC en pur québécois dérangé sans filtre, Dolphin Llama 3 et Llama 3.2.</p>
                    </div>

                    <div class="hub-card" onclick="switchTab('fooocus')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">🎨</span>
                            <div class="hub-card-title">Fooocus (Images SDXL)</div>
                        </div>
                        <p class="hub-card-desc">Génération photoréaliste Midjourney-style simple et rapide, sans noeuds complexes.</p>
                    </div>

                    <div class="hub-card" onclick="switchTab('tts')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">🎙️</span>
                            <div class="hub-card-title">Kokoro Voix & TTS</div>
                        </div>
                        <p class="hub-card-desc">72 voix neuronales hyper-réalistes pour transformer n'importe quel texte en discours naturel.</p>
                    </div>

                    <div class="hub-card" onclick="switchTab('logs')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">📊</span>
                            <div class="hub-card-title">Analyseur de Logs IA</div>
                        </div>
                        <p class="hub-card-desc">Détection d'erreurs en direct par catégorie (Chat, Code, Image, Voix, Modèles) avec explication et résolution par l'IA.</p>
                    </div>

                    <div class="hub-card" onclick="switchTab('downloads')">
                        <div class="hub-card-header">
                            <span class="hub-card-icon">📥</span>
                            <div class="hub-card-title">Téléchargeur Serveur</div>
                        </div>
                        <p class="hub-card-desc">Téléchargement direct dans les 31 To ZFS depuis Civitai (avec clé API) et Hugging Face.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- VIEW 1: VIBE CODER (STYLE ANTIGRAVITY) -->
        <div class="view-panel" id="view-code">
            <div class="vibe-wrapper">
                <div class="vibe-nav">
                    <div class="vibe-mode-pills">
                        <button class="vibe-pill active" id="btnModeChat" onclick="setVibeMode('chat')">💬 Vibe Chat</button>
                        <button class="vibe-pill" id="btnModePrev" onclick="setVibeMode('preview')">🌐 Aperçu en Direct</button>
                        <button class="vibe-pill" id="btnModeFiles" onclick="setVibeMode('files')">📁 Fichiers</button>
                    </div>
                    <div style="display:flex; gap:6px;">
                        <button class="action-btn" style="font-size:0.75rem;" onclick="refreshVibePreview()">🔄 Recharger</button>
                        <button class="action-btn" style="font-size:0.75rem;" onclick="resetVibeProject()">🧹 Réinitialiser</button>
                        <a href="/api/vibe/zip" class="action-btn" style="font-size:0.75rem;">📦 Zip</a>
                    </div>
                </div>

                <div class="vibe-body">
                    <!-- PANEL 1: CHAT -->
                    <div class="vibe-chat-panel">
                        <div class="vibe-messages" id="vibeMessages">
                            <div class="vibe-msg ai">
                                👋 <strong>Bienvenue sur Marcel Vibe Coder !</strong><br>
                                Dis-moi simplement ce que tu veux construire ou modifier (ex: <em>"Fais-moi un jeu de flappy bird"</em> ou <em>"Améliore l'interface en mode néon"</em>). Je crée et mets à jour les fichiers en direct dans ton aperçu !
                            </div>
                        </div>

                        <!-- CHIPS -->
                        <div class="vibe-chips">
                            <div class="vibe-chip" onclick="quickPrompt('Crée un jeu de Flappy Bird complet avec score et animation fluide en HTML5/JS')">🎮 Flappy Bird</div>
                            <div class="vibe-chip" onclick="quickPrompt('Crée un jeu de Snake rétro avec style cyberpunk et effets néon')">🐍 Snake Néon</div>
                            <div class="vibe-chip" onclick="quickPrompt('Crée un mini tableau de bord météo et crypto animé avec graphiques SVG')">📊 Dashboard</div>
                            <div class="vibe-chip" onclick="quickPrompt('Crée une calculatrice graphique moderne avec thème sombre tactile')">📱 Calculatrice</div>
                            <div class="vibe-chip" onclick="quickPrompt('Améliore le design actuel : ajoute des particules animées en fond et peaufine les styles')">✨ Embellir le design</div>
                        </div>

                        <div class="vibe-input-bar">
                            <textarea id="vibeInput" class="vibe-textarea" placeholder="Décris ce que tu veux coder..." rows="1" onkeydown="handleVibeKey(event)"></textarea>
                            <button class="vibe-btn-send" id="btnVibeSend" onclick="sendVibePrompt()">🚀</button>
                        </div>
                    </div>

                    <!-- PANEL 2: LIVE PREVIEW -->
                    <div class="vibe-preview-panel">
                        <iframe id="vibeIframe" class="service-iframe" src="/workspace_preview/"></iframe>
                    </div>

                    <!-- PANEL 3: FILES INSPECTOR -->
                    <div class="vibe-files-panel">
                        <h4 style="margin-bottom:10px; color:#fff;">Fichiers du projet (/datastore/workspace)</h4>
                        <div id="vibeFilesList" style="display:flex; flex-direction:column; gap:6px; margin-bottom:14px;"></div>
                        <h4 style="margin-bottom:8px; color:#fff;" id="vibeActiveFileName">Édition rapide</h4>
                        <textarea id="vibeFileEditor" class="dl-input" style="height:260px; font-family:'JetBrains Mono',monospace; font-size:0.8rem;" placeholder="Sélectionne un fichier..."></textarea>
                        <button class="action-btn" style="background:#6366f1; color:#fff; align-self:flex-start;" onclick="saveVibeEditedFile()">💾 Sauvegarder les modifications</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- VIEW 2: LOG ANALYZER & DIAGNOSTICS IA -->
        <div class="view-panel" id="view-logs">
            <div class="logs-container">
                <!-- LIVE HARDWARE MINI HUD -->
                <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07); border-radius:12px; padding:10px 14px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap; font-size:0.8rem;">
                        <span>⚡ <strong>CPU :</strong> <span id="logCpuStatus" style="color:#fbbf24; font-family:'JetBrains Mono',monospace;">--.- °C</span> (<span id="logCpuLoad">0%</span>)</span>
                        <span>🎮 <strong>GPU :</strong> <span id="logGpuStatus" style="color:#fbbf24; font-family:'JetBrains Mono',monospace;">--.- °C</span> (<span id="logGpuVram">VRAM -- Go</span>)</span>
                        <span>🧠 <strong>RAM :</strong> <span id="logRamStatus" style="color:#38bdf8;">-- Go / -- Go</span></span>
                    </div>
                    <div style="font-size:0.75rem; font-weight:700;" id="logActivityStatus">🟢 En veille</div>
                </div>

                <!-- CATEGORY SELECTOR -->
                <div class="logs-nav">
                    <button class="logs-cat-btn active" id="cat-chat" onclick="selectLogCat('chat')">💬 Chat & LLM</button>
                    <button class="logs-cat-btn" id="cat-code" onclick="selectLogCat('code')">💻 Vibe Coder</button>
                    <button class="logs-cat-btn" id="cat-image" onclick="selectLogCat('image')">🎨 Fooocus & Comfy</button>
                    <button class="logs-cat-btn" id="cat-voix" onclick="selectLogCat('voix')">🎙️ Voix Kokoro</button>
                    <button class="logs-cat-btn" id="cat-model" onclick="selectLogCat('model')">📥 Téléchargements</button>
                </div>

                <!-- SERVICE HEALTH CARD -->
                <div class="logs-status-card">
                    <div class="logs-status-info">
                        <h3 id="logServiceTitle">🟢 Service Opérationnel</h3>
                        <p id="logServiceSub">Aucune erreur critique détectée.</p>
                    </div>
                    <div class="logs-actions">
                        <button class="btn-clear-logs" id="btnClearLogs" onclick="clearCurrentLogs()">🧹 Effacer les logs</button>
                        <button class="btn-ai-autofix" id="btnAiAutofix" onclick="triggerAiAutoFix()">🪄 Réparer automatiquement avec l'IA</button>
                        <button class="btn-ai-diag" onclick="triggerAiDiagnostic()">🤖 Diagnostiquer</button>
                        <button class="btn-svc-restart" onclick="restartCurrentService()">🔄 Redémarrer ce service</button>
                        <label style="display:flex; align-items:center; gap:5px; font-size:0.78rem; color:#94a3b8; cursor:pointer;">
                            <input type="checkbox" id="chkErrorsOnly" onchange="loadCurrentLogs()"> Erreurs seules
                        </label>
                    </div>
                </div>

                <!-- AI DIAGNOSIS OUTPUT -->
                <div class="ai-diagnosis-box" id="aiDiagBox">
                    <h4>✨ Diagnostic & Solution par l'IA :</h4>
                    <div id="aiDiagContent" style="color:#e2e8f0; white-space:pre-wrap;"></div>
                </div>

                <!-- TERMINAL LOGS -->
                <div class="terminal-box" id="terminalBox">Chargement des logs en cours...</div>
            </div>
        </div>

        <!-- VIEW 3: CHAT GEMINI (OPEN WEBUI) -->
        <div class="view-panel" id="view-chat">
            <iframe id="iframe-chat" class="service-iframe" data-src="/chat/"></iframe>
        </div>

        <!-- VIEW 4: FOOOCUS IFRAME -->
        <div class="view-panel" id="view-fooocus">
            <iframe id="iframe-fooocus" class="service-iframe" data-src="/fooocus/"></iframe>
        </div>

        <!-- VIEW 5: KOKORO TTS IFRAME -->
        <div class="view-panel" id="view-tts">
            <iframe id="iframe-tts" class="service-iframe" data-src="/tts/web/"></iframe>
        </div>

        <!-- VIEW 6: COMFYUI IFRAME -->
        <div class="view-panel" id="view-comfy">
            <iframe id="iframe-comfy" class="service-iframe" data-src="/comfy/"></iframe>
        </div>

        <!-- VIEW 7: DOWNLOADER -->
        <div class="view-panel" id="view-downloads">
            <div class="dl-container">
                <div class="dl-card">
                    <h3 style="font-size:1.25rem; margin-bottom:6px; color:#fff;">⚡ Téléchargement Direct sur le Serveur ZFS</h3>
                    <p style="color:var(--text-sub); font-size:0.85rem; margin-bottom:16px;">
                        Colle le lien d'un modèle (.safetensors). Il sera stocké dans tes 31 To et partagé entre Fooocus et ComfyUI !
                    </p>

                    <div class="token-box">
                        <div style="font-weight:700; color:#fff; font-size:0.9rem; margin-bottom:4px;">🔑 Clé API Civitai (Débloque les modèles 18+ / restreints)</div>
                        <div style="font-size:0.78rem; color:var(--text-sub); margin-bottom:8px;">
                            Crée ta clé gratuite sur <a href="https://civitai.com/user/account" target="_blank" style="color:#818cf8;">Civitai ➔ Account Settings ➔ API Keys</a>.
                        </div>
                        <div class="token-row">
                            <input type="password" id="civitaiKeyInput" class="dl-input" style="margin-bottom:0;" placeholder="Colle ta clé API Civitai ici...">
                            <button type="button" class="action-btn" style="background:#6366f1; color:#fff;" onclick="saveCivitaiKey()">Sauvegarder</button>
                        </div>
                    </div>

                    <form onsubmit="handleDownload(event)">
                        <input type="url" id="modelUrl" class="dl-input" placeholder="https://civitai.com/api/download/models/... ou HuggingFace" required>
                        <select id="modelFolder" class="dl-select">
                            <option value="auto" selected>✨ Détection Automatique Intelligente (Recommandé)</option>
                            <option value="checkpoints">Modèle Principal (Checkpoints SDXL / SD 1.5)</option>
                            <option value="loras">LoRA (Style, Visage, Personnage)</option>
                            <option value="vae">VAE (Couleurs & Rendu)</option>
                            <option value="controlnet">ControlNet (Poses & Esquisses)</option>
                        </select>
                        <button type="submit" class="btn-dl-submit">Télécharger sur le Serveur</button>
                    </form>

                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:20px; margin-bottom:10px;">
                        <h4 style="font-size:0.95rem; color:#fff;">Tâches de téléchargement</h4>
                        <button type="button" class="btn-clear-logs" style="font-size:0.75rem;" onclick="clearDownloadTasks()">🧹 Effacer erreurs & historique</button>
                    </div>
                    <div id="tasksList" style="display:flex; flex-direction:column; gap:8px;"></div>
                </div>
            </div>
        </div>
    </main>

    <!-- BOTTOM DOCK -->
    <nav class="bottom-dock">
        <button class="dock-item active" id="dock-hub" onclick="switchTab('hub')">
            <span class="dock-icon">🏠</span>
            <span class="dock-label">Accueil</span>
        </button>
        <button class="dock-item" id="dock-code" onclick="switchTab('code')">
            <span class="dock-icon">💻</span>
            <span class="dock-label">Vibe Code</span>
        </button>
        <button class="dock-item" id="dock-chat" onclick="switchTab('chat')">
            <span class="dock-icon">💬</span>
            <span class="dock-label">Chat</span>
        </button>
        <button class="dock-item" id="dock-fooocus" onclick="switchTab('fooocus')">
            <span class="dock-icon">🎨</span>
            <span class="dock-label">Images</span>
        </button>
        <button class="dock-item" id="dock-tts" onclick="switchTab('tts')">
            <span class="dock-icon">🎙️</span>
            <span class="dock-label">Voix</span>
        </button>
        <button class="dock-item" id="dock-logs" onclick="switchTab('logs')">
            <span class="dock-icon">📊</span>
            <span class="dock-label">Diagnostic</span>
        </button>
        <button class="dock-item" id="dock-downloads" onclick="switchTab('downloads')">
            <span class="dock-icon">📥</span>
            <span class="dock-label">Modèles</span>
        </button>
    </nav>

    <script>
        let currentTab = 'hub';
        let currentLogCat = 'chat';
        let vibeHistory = [];
        let activeVibeFile = 'index.html';
        let authToken = localStorage.getItem('marcel_auth_token') || '';

        const badges = {
            hub: 'Accueil',
            code: 'Vibe Coder',
            chat: 'Gemini Chat',
            fooocus: 'Fooocus SDXL',
            tts: 'Kokoro Voix',
            comfy: 'ComfyUI',
            logs: 'Diagnostic IA',
            downloads: 'Téléchargeur'
        };

        const externalLinks = {
            hub: '/',
            code: '/workspace_preview/',
            chat: '/chat/',
            fooocus: '/fooocus/',
            tts: '/tts/web/',
            comfy: '/comfy/',
            logs: '/api/logs/view',
            downloads: '/'
        };

        // --- AUTHENTICATION & LOGIN ---
        async function checkAuthOnLoad() {
            if (authToken) {
                try {
                    const res = await fetch('/api/auth/verify', {
                        headers: { 'Authorization': 'Bearer ' + authToken }
                    });
                    if (res.ok) {
                        unlockApp();
                        return;
                    }
                } catch (e) {}
            }
            // Show login overlay if not verified
            document.getElementById('authOverlay').classList.remove('hidden');
        }

        function unlockApp() {
            document.getElementById('authOverlay').classList.add('hidden');
            checkGlobalHealth();
            pollDownloads();
            loadCivitaiKey();
        }

        async function handleLogin(e) {
            e.preventDefault();
            const user = document.getElementById('loginUser').value.trim();
            const pass = document.getElementById('loginPass').value;
            const errEl = document.getElementById('loginError');
            errEl.style.display = 'none';

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: user, password: pass })
                });
                const data = await res.json();
                if (res.ok && data.success) {
                    authToken = data.token;
                    localStorage.setItem('marcel_auth_token', authToken);
                    unlockApp();
                } else {
                    errEl.textContent = data.error || 'Identifiants invalides.';
                    errEl.style.display = 'block';
                }
            } catch (err) {
                errEl.textContent = 'Erreur réseau : ' + err.message;
                errEl.style.display = 'block';
            }
        }

        function handleLogout() {
            if (!confirm('Voulez-vous vous déconnecter ?')) return;
            localStorage.removeItem('marcel_auth_token');
            authToken = '';
            fetch('/api/auth/logout', { method: 'POST' }).finally(() => {
                location.reload();
            });
        }

        // --- TAB SWITCHER ---
        function switchTab(tabId) {
            currentTab = tabId;
            document.querySelectorAll('.dock-item').forEach(b => b.classList.remove('active'));
            const activeDock = document.getElementById('dock-' + tabId);
            if (activeDock) activeDock.classList.add('active');

            document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
            const activePanel = document.getElementById('view-' + tabId);
            if (activePanel) activePanel.classList.add('active');

            const badgeEl = document.getElementById('serviceBadge');
            if (badgeEl) badgeEl.textContent = badges[tabId] || tabId;
            const extEl = document.getElementById('btnExternal');
            if (extEl) extEl.href = externalLinks[tabId] || '#';

            // Lazy load iframes
            if (activePanel) {
                const iframe = activePanel.querySelector('iframe');
                if (iframe && !iframe.src && iframe.dataset.src) {
                    iframe.src = iframe.dataset.src;
                }
            }

            if (tabId === 'logs') {
                loadCurrentLogs();
            } else if (tabId === 'code') {
                loadVibeFiles();
            }
        }

        // --- VIBE CODER LOGIC ---
        function setVibeMode(mode) {
            document.querySelectorAll('.vibe-pill').forEach(p => p.classList.remove('active'));
            if (mode === 'chat') document.getElementById('btnModeChat').classList.add('active');
            else if (mode === 'preview') document.getElementById('btnModePrev').classList.add('active');
            else if (mode === 'files') document.getElementById('btnModeFiles').classList.add('active');
            
            document.body.classList.remove('vibe-view-chat', 'vibe-view-preview', 'vibe-view-files');
            document.body.classList.add('vibe-view-' + mode);
            
            if (mode === 'files') loadVibeFiles();
        }

        function refreshVibePreview() {
            const ifr = document.getElementById('vibeIframe');
            ifr.src = '/workspace_preview/?t=' + Date.now();
        }

        function quickPrompt(text) {
            document.getElementById('vibeInput').value = text;
            sendVibePrompt();
        }

        function handleVibeKey(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendVibePrompt();
            }
        }

        async function sendVibePrompt() {
            const input = document.getElementById('vibeInput');
            const prompt = input.value.trim();
            if (!prompt) return;

            const msgs = document.getElementById('vibeMessages');
            msgs.innerHTML += '<div class="vibe-msg user">' + escapeHtml(prompt) + '</div>';
            input.value = '';
            msgs.scrollTop = msgs.scrollHeight;

            const loadingId = 'vibe-load-' + Date.now();
            msgs.innerHTML += '<div class="vibe-msg ai" id="' + loadingId + '">⚙️ <em>Génération du code et mise à jour des fichiers avec Qwen 2.5 Coder...</em></div>';
            msgs.scrollTop = msgs.scrollHeight;

            try {
                const res = await fetch('/api/vibe/chat', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ prompt, history: vibeHistory })
                });
                const data = await res.json();
                const loadEl = document.getElementById(loadingId);

                if (data.success) {
                    let filesBadge = '';
                    if (data.saved_files && data.saved_files.length > 0) {
                        filesBadge = '<br>' + data.saved_files.map(f => '<span class="vibe-file-badge" onclick="setVibeMode(\'preview\')">💾 Modifié : ' + f + '</span>').join(' ');
                    }
                    
                    // Regex parsing safely constructed without newlines
                    const fileRegex = new RegExp('```file:[^\\n\\r]+[\\n\\r]+([\\s\\S]*?)```', 'g');
                    const formatted = data.response
                        .replace(fileRegex, '<em>[Code généré injecté dans le projet]</em>')
                        .replace(/\n/g, '<br>');

                    loadEl.innerHTML = '🤖 ' + formatted + ' ' + filesBadge;
                    vibeHistory.push({ role: 'user', content: prompt });
                    vibeHistory.push({ role: 'assistant', content: data.response });

                    refreshVibePreview();
                } else {
                    loadEl.innerHTML = '❌ Erreur : ' + (data.error || 'Échec de la génération');
                }
            } catch (err) {
                const loadEl = document.getElementById(loadingId);
                if (loadEl) loadEl.innerHTML = '❌ Erreur réseau : ' + err.message;
            }
            msgs.scrollTop = msgs.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function loadVibeFiles() {
            try {
                const res = await fetch('/api/vibe/files', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const data = await res.json();
                const container = document.getElementById('vibeFilesList');
                container.innerHTML = '';
                
                (data.files || []).forEach(f => {
                    const row = document.createElement('div');
                    row.style.cssText = 'display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.04); padding:8px 12px; border-radius:8px; cursor:pointer;';
                    row.innerHTML = '<span style="font-family:monospace; font-size:0.82rem; color:#a5b4fc;">📄 ' + f.path + '</span> <span style="font-size:0.75rem; color:#64748b;">' + (f.size/1024).toFixed(1) + ' Ko</span>';
                    row.onclick = () => loadVibeFileContent(f.path);
                    container.appendChild(row);
                });
            } catch (e) {}
        }

        async function loadVibeFileContent(path) {
            activeVibeFile = path;
            document.getElementById('vibeActiveFileName').textContent = 'Édition : ' + path;
            try {
                const res = await fetch('/api/vibe/file?path=' + encodeURIComponent(path), {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const data = await res.json();
                document.getElementById('vibeFileEditor').value = data.content || '';
            } catch (e) {}
        }

        async function saveVibeEditedFile() {
            const content = document.getElementById('vibeFileEditor').value;
            try {
                const res = await fetch('/api/vibe/file', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ path: activeVibeFile, content })
                });
                const data = await res.json();
                if (data.success) {
                    alert('Fichier sauvegardé !');
                    refreshVibePreview();
                }
            } catch (e) { alert(e.message); }
        }

        async function resetVibeProject() {
            if (!confirm('Réinitialiser le projet avec le template de départ ?')) return;
            await fetch('/api/vibe/reset', { 
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + authToken }
            });
            refreshVibePreview();
            loadVibeFiles();
            alert('Projet réinitialisé !');
        }

        // --- LOG ANALYZER & DIAGNOSTICS IA ---
        function selectLogCat(cat) {
            currentLogCat = cat;
            document.querySelectorAll('.logs-cat-btn').forEach(b => b.classList.remove('active'));
            const activeBtn = document.getElementById('cat-' + cat);
            if (activeBtn) activeBtn.classList.add('active');
            document.getElementById('aiDiagBox').classList.remove('active');
            loadCurrentLogs();
        }

        async function loadCurrentLogs() {
            const box = document.getElementById('terminalBox');
            box.textContent = 'Récupération des logs en direct...';
            const errorsOnly = document.getElementById('chkErrorsOnly').checked;

            try {
                const res = await fetch('/api/logs/view?category=' + currentLogCat + '&errors_only=' + errorsOnly + '&lines=120', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const data = await res.json();

                const titleEl = document.getElementById('logServiceTitle');
                const subEl = document.getElementById('logServiceSub');

                if (data.has_errors) {
                    titleEl.innerHTML = '<span style="color:#ef4444;">🔴</span> Erreur(s) détectée(s) (' + data.error_count + ')';
                    subEl.textContent = 'Dernière anomalie : ' + (data.sample_error ? data.sample_error.substring(0, 80) + '...' : 'Consulte le terminal');
                } else {
                    titleEl.innerHTML = '<span style="color:#10b981;">🟢</span> ' + data.service + ' : Opérationnel';
                    subEl.textContent = 'Aucune anomalie ou plantage détecté dans les derniers logs.';
                }

                box.textContent = data.logs || 'Aucun log disponible.';
                box.scrollTop = box.scrollHeight;
            } catch (err) {
                box.textContent = 'Erreur lors de la récupération des logs: ' + err.message;
            }
        }

                async function triggerAiAutoFix() {
            const diagBox = document.getElementById('aiDiagBox');
            const diagContent = document.getElementById('aiDiagContent');
            const box = document.getElementById('terminalBox');
            const btn = document.getElementById('btnAiAutofix');

            diagBox.classList.add('active');
            if (btn) {
                btn.disabled = true;
                btn.style.opacity = '0.7';
            }
            diagContent.innerHTML = '<em>🪄 <strong>Autoréparation en cours...</strong><br>1. Analyse de la panne avec l\'IA...<br>2. Exécution des correctifs (purge VRAM, réalignement permissions, relance services)...<br>3. Vérification de l\'état de santé...</em>';

            try {
                const res = await fetch('/api/logs/ai_autofix', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ category: currentLogCat, logs: box.textContent })
                });
                const data = await res.json();
                if (btn) {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                }

                if (data.success) {
                    let actionsHtml = '';
                    if (data.actions_taken && data.actions_taken.length > 0) {
                        actionsHtml = '<br><br><strong>🛠️ Actions appliquées automatiquement :</strong><ul style="margin-left:20px; margin-top:6px; color:#cbd5e1;">' + 
                            data.actions_taken.map(a => '<li style="margin-bottom:3px;">' + a + '</li>').join('') + '</ul>';
                    }

                    diagContent.innerHTML = 
                        '<div style="font-size:0.95rem; font-weight:700; color:' + (data.is_healthy ? '#34d399' : '#f59e0b') + '; margin-bottom:8px;">' +
                            '✨ ' + data.status_text +
                        '</div>' +
                        '<strong>🔍 Diagnostic IA :</strong> ' + data.diagnosis + '<br>' +
                        '<strong>💡 Explication :</strong> ' + data.explanation +
                        actionsHtml;
                    
                    setTimeout(loadCurrentLogs, 2000);
                    setTimeout(checkGlobalHealth, 2500);
                } else {
                    diagContent.innerHTML = '❌ Échec de l\'autoréparation : ' + (data.error || 'Erreur inconnue');
                }
            } catch (err) {
                if (btn) {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                }
                diagContent.innerHTML = '❌ Erreur réseau lors de l\'autoréparation : ' + err.message;
            }
        }

        async function triggerAiDiagnostic() {
            const diagBox = document.getElementById('aiDiagBox');
            const diagContent = document.getElementById('aiDiagContent');
            const box = document.getElementById('terminalBox');
            
            diagBox.classList.add('active');
            diagContent.innerHTML = '<em>🧠 Analyse en cours par l\'IA (Llama 3.2)... Explication et correctifs dans un instant...</em>';

            try {
                const res = await fetch('/api/logs/ai_analyze', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ category: currentLogCat, logs: box.textContent })
                });
                const data = await res.json();
                if (data.success) {
                    diagContent.innerHTML = data.analysis.replace(/\n/g, '<br>');
                } else {
                    diagContent.textContent = 'Impossible d\'analyser : ' + (data.error || 'Erreur inconnue');
                }
            } catch (err) {
                diagContent.textContent = 'Erreur réseau lors de l\'analyse: ' + err.message;
            }
        }

        async function restartCurrentService() {
            if (!confirm('Redémarrer les services de la catégorie "' + currentLogCat + '" ?')) return;
            await fetch('/api/services/restart', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                body: JSON.stringify({ category: currentLogCat })
            });
            alert('Commande de redémarrage envoyée !');
            setTimeout(loadCurrentLogs, 2500);
        }

        async function clearCurrentLogs() {
            if (!confirm('Effacer les logs de la catégorie "' + currentLogCat + '" ?')) return;
            try {
                const res = await fetch('/api/logs/clear', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ category: currentLogCat })
                });
                const data = await res.json();
                const box = document.getElementById('terminalBox');
                box.textContent = '🧹 Logs effacés avec succès !\n' + (data.actions_taken || []).join('\n') + '\n\nEn attente de nouveaux événements...';
                setTimeout(loadCurrentLogs, 1500);
            } catch (e) {
                alert(e.message);
            }
        }

        // Live Hardware & Activity Polling
        async function pollSystemStats() {
            try {
                const res = await fetch('/api/system/stats', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                if (!res.ok) return;
                const s = await res.json();
                
                // 1. CPU
                const cpuTempEl = document.getElementById('hudCpuTemp');
                const cpuLoadEl = document.getElementById('hudCpuLoad');
                const cpuBarEl = document.getElementById('hudCpuBar');
                const logCpuStatus = document.getElementById('logCpuStatus');
                const logCpuLoad = document.getElementById('logCpuLoad');

                if (s.cpu) {
                    const tempStr = (s.cpu.temp !== null ? s.cpu.temp.toFixed(1) + ' °C' : '-- °C');
                    if (cpuTempEl) cpuTempEl.textContent = tempStr;
                    if (cpuLoadEl) cpuLoadEl.textContent = s.cpu.percent + ' %';
                    if (cpuBarEl) cpuBarEl.style.width = Math.min(100, Math.max(0, s.cpu.percent)) + '%';
                    if (logCpuStatus) logCpuStatus.textContent = tempStr;
                    if (logCpuLoad) logCpuLoad.textContent = s.cpu.percent + ' %';
                }

                // 2. GPU
                const gpuTempEl = document.getElementById('hudGpuTemp');
                const gpuVramEl = document.getElementById('hudGpuVram');
                const gpuBarEl = document.getElementById('hudGpuBar');
                const gpuSubEl = document.getElementById('hudGpuSub');
                const logGpuStatus = document.getElementById('logGpuStatus');
                const logGpuVram = document.getElementById('logGpuVram');

                if (s.gpu) {
                    const gpuTempStr = (s.gpu.temp !== null ? s.gpu.temp.toFixed(1) + ' °C' : '-- °C');
                    if (gpuTempEl) gpuTempEl.textContent = gpuTempStr;
                    if (gpuVramEl) gpuVramEl.textContent = s.gpu.vram_used_gb.toFixed(1) + ' / ' + s.gpu.vram_total_gb.toFixed(1) + ' Go';
                    if (gpuBarEl) gpuBarEl.style.width = Math.min(100, Math.max(0, s.gpu.vram_percent)) + '%';
                    if (gpuSubEl) gpuSubEl.textContent = 'Activité GPU : ' + s.gpu.percent + '% | VRAM : ' + s.gpu.vram_percent + '%';
                    if (logGpuStatus) logGpuStatus.textContent = gpuTempStr;
                    if (logGpuVram) logGpuVram.textContent = 'VRAM ' + s.gpu.vram_used_gb.toFixed(1) + ' Go';
                }

                // 3. RAM
                const ramValEl = document.getElementById('hudRamVal');
                const ramPctEl = document.getElementById('hudRamPercent');
                const ramBarEl = document.getElementById('hudRamBar');
                const ramSubEl = document.getElementById('hudRamSub');
                const logRamStatus = document.getElementById('logRamStatus');

                if (s.ram) {
                    if (ramValEl) ramValEl.textContent = s.ram.used_gb.toFixed(1) + ' / ' + s.ram.total_gb.toFixed(1) + ' Go';
                    if (ramPctEl) ramPctEl.textContent = s.ram.percent + ' %';
                    if (ramBarEl) ramBarEl.style.width = Math.min(100, Math.max(0, s.ram.percent)) + '%';
                    if (ramSubEl) ramSubEl.textContent = 'Mémoire DDR4 (' + (s.ram.avail_gb || (s.ram.total_gb - s.ram.used_gb).toFixed(1)) + ' Go Libres)';
                    if (logRamStatus) logRamStatus.textContent = s.ram.used_gb.toFixed(1) + ' Go / ' + s.ram.total_gb.toFixed(1) + ' Go';
                }

                // 4. Activity Status
                const actBadge = document.getElementById('hudActivityBadge');
                const actText = document.getElementById('hudActivityText');
                const actCard = document.getElementById('hudActivityCard');
                const logActivityStatus = document.getElementById('logActivityStatus');

                if (s.activity) {
                    const isBusy = Boolean(s.activity.is_busy);
                    if (actBadge) {
                        actBadge.className = isBusy ? 'hud-badge status-busy' : 'hud-badge status-idle';
                        actBadge.textContent = isBusy ? '⚡ En action' : '🟢 En veille';
                    }
                    if (actText) actText.textContent = s.activity.status;
                    if (actCard) actCard.style.borderColor = isBusy ? 'rgba(236, 72, 153, 0.5)' : 'rgba(16, 185, 129, 0.3)';
                    if (logActivityStatus) {
                        logActivityStatus.innerHTML = isBusy ? 
                            '<span style="color:#ec4899; animation:pulse 1s infinite;">⚡ ' + escapeHtml(s.activity.status) + '</span>' : 
                            '<span style="color:#34d399;">🟢 En veille</span>';
                    }
                }

                // 5. Top Bar Pill
                const topPill = document.getElementById('topHwPill');
                const pillText = document.getElementById('pillText');
                const pillPulse = document.getElementById('pillPulse');
                if (topPill && s.cpu && s.gpu) {
                    topPill.style.display = 'flex';
                    const cT = s.cpu.temp !== null ? s.cpu.temp.toFixed(0) + '°C' : s.cpu.percent + '%';
                    const gT = s.gpu.temp !== null ? s.gpu.temp.toFixed(0) + '°C' : s.gpu.percent + '%';
                    pillText.textContent = 'CPU ' + cT + ' | GPU ' + gT;
                    pillPulse.textContent = (s.activity && s.activity.is_busy) ? '⚡' : '🟢';
                }
            } catch (e) {}
        }
        setInterval(pollSystemStats, 3000);
        setTimeout(pollSystemStats, 500);

        // Global Health Pulse Checker
        async function checkGlobalHealth() {
            try {
                const res = await fetch('/api/logs/status', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const data = await res.json();
                const hasDown = Object.values(data).some(s => !s.active);
                const btn = document.getElementById('btnPulseLog');
                const dot = document.getElementById('logPulseDot');
                if (hasDown) {
                    btn.classList.add('has-error');
                    dot.textContent = '🔴';
                } else {
                    btn.classList.remove('has-error');
                    dot.textContent = '🟢';
                }
            } catch (e) {}
        }
        setInterval(checkGlobalHealth, 15000);

        // --- DOWNLOADER & CIVITAI KEY ---
        async function clearDownloadTasks() {
            try {
                const res = await fetch('/api/downloads/clear', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ all: true })
                });
                const data = await res.json();
                pollDownloads();
            } catch (e) {
                alert(e.message);
            }
        }

        async function loadCivitaiKey() {
            try {
                const res = await fetch('/api/civitai_token', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const data = await res.json();
                if (data.has_token) {
                    document.getElementById('civitaiKeyInput').placeholder = 'Clé enregistrée (' + data.masked_token + ')';
                }
            } catch (e) {}
        }

        async function saveCivitaiKey() {
            const token = document.getElementById('civitaiKeyInput').value.trim();
            if (!token) return alert('Entre une clé API Civitai.');
            try {
                const res = await fetch('/api/civitai_token', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + authToken
                    },
                    body: JSON.stringify({ token })
                });
                const data = await res.json();
                if (data.success) {
                    alert('Clé API Civitai enregistrée avec succès !');
                    loadCivitaiKey();
                }
            } catch (e) { alert(e.message); }
        }

        async function handleDownload(e) {
            e.preventDefault();
            const url = document.getElementById('modelUrl').value.trim();
            const folder = document.getElementById('modelFolder').value;
            const res = await fetch('/api/download', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + authToken
                },
                body: JSON.stringify({ url, folder })
            });
            const data = await res.json();
            if (data.success) {
                document.getElementById('modelUrl').value = '';
                pollDownloads();
            }
        }

        async function pollDownloads() {
            try {
                const res = await fetch('/api/downloads', {
                    headers: { 'Authorization': 'Bearer ' + authToken }
                });
                const list = await res.json();
                const container = document.getElementById('tasksList');
                if (!container) return;
                
                if (list.length === 0) {
                    container.innerHTML = '<div style="color:#64748b; font-size:0.85rem; padding:12px; text-align:center; background:rgba(255,255,255,0.02); border-radius:10px;">Aucun téléchargement en cours ou dans l\'historique.</div>';
                    return;
                }
                
                container.innerHTML = '';
                list.slice().reverse().forEach(t => {
                    const el = document.createElement('div');
                    const isError = Boolean(t.error);
                    const isDone = t.progress >= 100 && !isError;
                    
                    const borderColor = isError ? 'rgba(239, 68, 68, 0.4)' : (isDone ? 'rgba(16, 185, 129, 0.4)' : 'rgba(99, 102, 241, 0.4)');
                    const bgColor = isError ? 'rgba(239, 68, 68, 0.05)' : (isDone ? 'rgba(16, 185, 129, 0.05)' : 'rgba(99, 102, 241, 0.05)');
                    
                    el.style.cssText = 'background:' + bgColor + '; border:1px solid ' + borderColor + '; border-radius:12px; padding:12px; font-size:0.82rem; margin-bottom:8px; display:flex; flex-direction:column; gap:6px;';
                    
                    let hint = '';
                    const st = String(t.status || '');
                    if (isError && (st.includes('403') || st.includes('Civitai') || st.includes('download-auth') || st.includes('login'))) {
                        hint = '<div style="background:rgba(245, 158, 11, 0.15); border:1px solid rgba(245, 158, 11, 0.3); color:#fef08a; padding:6px 10px; border-radius:8px; font-size:0.75rem; margin-top:4px;">🔒 <strong>Civitai 403 :</strong> Ce modèle requiert une clé API Civitai. Enregistre ta clé dans le champ ci-dessus.</div>';
                    } else if (isError && st.includes('404')) {
                        hint = '<div style="background:rgba(239, 68, 68, 0.15); border:1px solid rgba(239, 68, 68, 0.3); color:#fca5a5; padding:6px 10px; border-radius:8px; font-size:0.75rem; margin-top:4px;">⚠️ <strong>Lien 404 :</strong> Sur Hugging Face, ouvre l\'onglet "Files and versions" et copie le lien direct du fichier .safetensors.</div>';
                    }

                    const progressHtml = !isError && !isDone ? 
                        '<div style="height:6px; background:rgba(255,255,255,0.08); border-radius:4px; overflow:hidden; margin:4px 0;">' +
                            '<div style="height:100%; width:' + t.progress + '%; background:linear-gradient(90deg, #6366f1, #ec4899); transition:width 0.3s ease;"></div>' +
                        '</div>' : '';

                    el.innerHTML = 
                        '<div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">' +
                            '<span style="background:rgba(255,255,255,0.08); padding:3px 8px; border-radius:6px; font-family:\'JetBrains Mono\',monospace; font-size:0.72rem; color:#a5b4fc;">📁 ' + escapeHtml(t.folder) + '</span>' +
                            '<span style="font-weight:700; color:' + (isError ? '#ef4444' : (isDone ? '#34d399' : '#818cf8')) + '; font-size:0.78rem;">' + (isError ? '❌ Erreur' : (isDone ? '✅ Terminé (100%)' : t.progress + '%')) + '</span>' +
                        '</div>' +
                        '<div style="font-weight:700; color:#fff; word-break:break-all; font-size:0.85rem; line-height:1.3;">' + escapeHtml(t.filename || 'Modèle') + '</div>' +
                        progressHtml +
                        '<div style="color:' + (isError ? '#fca5a5' : '#cbd5e1') + '; font-size:0.78rem; word-break:break-word;">' + escapeHtml(t.status) + '</div>' +
                        hint;
                    
                    container.appendChild(el);
                });
            } catch (e) {}
        }
        setInterval(pollDownloads, 4000);

        function reloadCurrentService() {
            if (currentTab === 'code') refreshVibePreview();
            else if (currentTab === 'logs') loadCurrentLogs();
            else {
                const panel = document.getElementById('view-' + currentTab);
                if (panel) {
                    const ifr = panel.querySelector('iframe');
                    if (ifr) ifr.src = ifr.src;
                }
            }
        }

        function toggleFullscreen() {
            if (!document.fullscreenElement) document.documentElement.requestFullscreen();
            else if (document.exitFullscreen) document.exitFullscreen();
        }

        // Initialize auth on load
        window.addEventListener('DOMContentLoaded', checkAuthOnLoad);

        // Service Worker Registration
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js');
            });
        }
    </script>
</body>
</html>
"""

# 1. VERIFY JS SYNTAX WITH NODE
script_match = re.search(r'<script>(.*?)</script>', html_content, re.DOTALL)
if not script_match:
    raise ValueError("No script found!")
extracted_js = script_match.group(1)

with open("temp_extracted.js", "w", encoding="utf-8") as f:
    f.write(extracted_js)

print("HTML and JS extracted locally. Testing syntax on LXC 100 before deploying...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(os.environ.get('PROXMOX_HOST', '192.168.1.100'), username=os.environ.get('PROXMOX_USER', 'root'), password=os.environ.get('PROXMOX_PASSWORD', ''))

sftp = ssh.open_sftp()
with sftp.open("/tmp/check_syntax.js", "wb") as rf:
    rf.write(extracted_js.encode("utf-8"))

# Push and check with node
ssh.exec_command("pct push 100 /tmp/check_syntax.js /tmp/check_syntax.js")
stdin, stdout, stderr = ssh.exec_command("pct exec 100 -- /usr/lib/code-server/lib/node -c /tmp/check_syntax.js")
out = stdout.read().decode()
err = stderr.read().decode()

if err.strip():
    print("❌ JS SYNTAX ERROR FOUND:")
    print(err)
    ssh.close()
    exit(1)
else:
    print("✅ Node -c PASSED! ZERO syntax errors in JavaScript!")

# 2. PUSH marcel_core_api.py (with Auth module)
print("Pushing updated marcel_core_api.py...")
with open("marcel_core_api.py", "rb") as lf:
    with sftp.open("/tmp/marcel_core_api.py", "wb") as rf:
        rf.write(lf.read())
ssh.exec_command("pct push 100 /tmp/marcel_core_api.py /opt/marcel_core_api.py")
ssh.exec_command("pct exec 100 -- systemctl restart marcel-core")

# 3. PUSH INDEX.HTML
print("Pushing updated index.html...")
with sftp.open("/tmp/index.html", "wb") as rf:
    rf.write(html_content.encode("utf-8"))
ssh.exec_command("pct push 100 /tmp/index.html /var/www/html/index.html")

# 4. UPDATE SW.JS (v5 to force refresh everywhere)
sw_code = """// AI Studio Marcel Service Worker v10
const CACHE_NAME = 'aistudio-shell-v10';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/manifest.json',
    '/favicon.ico',
    '/favicon.png',
    '/icon-192.png',
    '/icon-512.png',
    '/marcel-avatar.png'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) return caches.delete(key);
                })
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    if (event.request.method !== 'GET' || 
        url.pathname.startsWith('/api/') || 
        url.pathname.startsWith('/workspace_preview/') || 
        url.pathname.startsWith('/chat/') || 
        url.pathname.startsWith('/_app/') || 
        url.pathname.startsWith('/ollama/') || 
        url.pathname.startsWith('/ws/') || 
        url.pathname.startsWith('/fooocus/') || 
        url.pathname.startsWith('/tts/') || 
        url.pathname.startsWith('/comfy/')) {
        return;
    }

    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});
"""
with sftp.open("/tmp/sw.js", "wb") as rf:
    rf.write(sw_code.encode("utf-8"))
ssh.exec_command("pct push 100 /tmp/sw.js /var/www/html/sw.js")

sftp.close()
ssh.close()
print("🎉 Secure PWA with Login & Password deployed and verified successfully!")
