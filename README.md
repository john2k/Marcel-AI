# Marcel-AI 🤖✨ - The Ultimate Self-Hosted AI Studio

<p align="center">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/Platform-Proxmox%20VE%20%7C%20LXC-orange?style=for-the-badge&logo=proxmox" alt="Proxmox">
  <img src="https://img.shields.io/badge/Inference-Vulkan%20GPU%20%7C%20ROCm-red?style=for-the-badge&logo=amd" alt="AMD">
  <img src="https://img.shields.io/badge/Interface-PWA%20Mobile%20%26%20Desktop-blue?style=for-the-badge&logo=pwa" alt="PWA">
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="License">
</p>

> **Marcel-AI** est une suite complète d'intelligence artificielle locale et auto-hébergée sur **Proxmox VE (LXC)**, optimisée avec accélération GPU AMD (Vulkan & ROCm), stockage ZFS haute performance, et accessible partout de manière sécurisée sous forme de **PWA (Progressive Web App)** via Cloudflare Tunnel.

---

## ⚡ En Bref : Tout Votre Studio IA en Une Seule App

| Composant | Rôle & Expérience | Moteur / Technologie |
| :--- | :--- | :--- |
| 💻 **Marcel Vibe Coder** | IDE interactif simplifié style **Antigravity** : code en direct par prompt avec aperçu temps réel | Qwen 2.5 Coder 7B + Live Preview |
| 📊 **Analyseur de Logs & Auto-Réparation IA** | Détection d'erreurs en direct par catégorie (Chat, Code, Image, Voix, Modèles) avec **résolution et autoréparation automatique par l'IA** (purge VRAM GPU, réalignement permissions, relance ciblée) | Llama 3.2 + Autonomous Agent API |
| 💬 **Chat IA Multimodèle** | Interface conversationnelle style **Gemini** avec le persona déjanté québécois **Marcel-QC** | Open WebUI + Ollama (Vulkan GPU) |
| 🎨 **Génération d'Images** | Rendu photoréaliste SDXL simple façon **Midjourney** | Fooocus (PyTorch ROCm) |
| 🎬 **Workflows Créatifs Avancés** | Génération nodulaire de photos et vidéos IA | ComfyUI |
| 🎙️ **Studio Vocal / TTS** | Synthèse vocale neuronale ultra-réaliste (72 voix HD) | Kokoro Neural TTS Docker |
| 📥 **Gestionnaire de Modèles** | Téléchargement direct sur serveur avec bypass Civitai Auth | Fast REST API + Civitai Token |
| 📱 **PWA Mobile-First** | Application installable sur iOS/Android avec dock unifié | Nginx Reverse Proxy + Service Worker v3 |

---

## 🏗️ Architecture Système

```text
                                [ Mobile / Desktop (iOS, Android, PC) ]
                                                   │
                                                   ▼  (PWA Standalone)
                                   [ Cloudflare Tunnel Ingress ]
                                                   │
                                                   ▼
                                    [ Nginx Reverse Proxy (:8080) ]
        ┌──────────────────┬───────────────────────┼───────────────────┬──────────────────┐
        ▼                  ▼                       ▼                   ▼                  ▼
   [ Open WebUI ]    [ code-server ]          [ Fooocus ]        [ Kokoro TTS ]    [ Downloader ]
   (Chat Gemini)    (Cursor Web IDE)       (Midjourney UI)       (72 Voix IA)      (Civitai & HF)
      :3000               :8088                   :7865               :8880              :8085
        │                  │
        ▼                  ▼
  [ Ollama Engine (:11434) - Accélération Vulkan GPU ]
        │
  ┌─────┴───────────────────────────────────────────────────────┐
  │ Modèles LLM : marcel-qc:latest (Québécois pure laine),     │
  │               dolphin-llama3:8b (Sans filtre),              │
  │               qwen2.5-coder:7b (Spécialiste programmation), │
  │               llama3.2:3b (Ultra-rapide)                    │
  └─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Démarrage Rapide

### 1. Cloner le Dépôt
```bash
git clone https://github.com/john2k/Marcel-AI.git
cd Marcel-AI
```

### 2. Configurer les Variables d'Environnement
Copiez le modèle de configuration et renseignez vos identifiants :
```bash
cp .env.example .env
nano .env
```

```ini
# Proxmox Host Configuration
PROXMOX_HOST=192.168.1.100
PROXMOX_PORT=22
PROXMOX_USER=root
PROXMOX_PASSWORD=votre_mot_de_passe

# Cloudflare Tunnel Configuration
CLOUDFLARE_ZONE=votredomaine.com
CLOUDFLARE_API_TOKEN=votre_token_cloudflare
CLOUDFLARE_ACCOUNT_ID=votre_account_id

# AI Service Keys (Optionnel)
CIVITAI_API_TOKEN=votre_cle_civitai
HUGGING_FACE_TOKEN=votre_token_hf
```

### 3. Déployer la PWA et les Services
```bash
python deploy_full_pwa.py
```

### 4. Configurer le Domaine Public (Cloudflare Tunnel)
```powershell
./cloudflare-add-marcel-tunnel.ps1 -Hostname "marcel.votredomaine.com" -ZoneName "votredomaine.com"
```

---

## 💡 Points Forts & Innovations

* **Zéro Fuite de Données** : Tout s'exécute 100% en local dans un conteneur Proxmox LXC haute performance.
* **GPU Passthrough AMD Radeon** : Accélération d'inférence LLM via Vulkan Compute et rendu SDXL avec PyTorch ROCm.
* **Contournement des restrictions Civitai** : Le téléchargeur serveur injecte automatiquement votre clé API pour récupérer les modèles 18+ / NSFW sans erreur 403.
* **PWA Tactile & Fluide** : Dock de navigation fluide en bas de l'écran, gestion du plein écran, Service Worker v2 et chargement instantané.

---

## 📄 Licence
Distribué sous licence **MIT**. Libre d'utilisation, de modification et de déploiement.
