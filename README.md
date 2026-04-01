<div align="center">

<pre>
██████╗ ███████╗██████╗ ██╗██████╗ ████████╗██╗  ██╗
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗╚══██╔══╝██║  ██║
██████╔╝█████╗  ██████╔╝██║██████╔╝   ██║   ███████║
██╔══██╗██╔══╝  ██╔══██╗██║██╔══██╗   ██║   ██╔══██║
██║  ██║███████╗██████╔╝██║██║  ██║   ██║   ██║  ██║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
</pre>

### **NO RULES ! JUST FILES !**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey?style=for-the-badge&logo=apple&logoColor=white)](.)
[![Version](https://img.shields.io/badge/Version-2.0.7-FFA500?style=for-the-badge)](.)
[![License](https://img.shields.io/badge/License-Private-red?style=for-the-badge)](.)

</div>

---

## 📋 Table des matières

- [Présentation](#-présentation)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Lancement](#-lancement)
- [Workflow](#-workflow-complet)
- [Fonctionnalités](#-fonctionnalités)
- [Structure](#-structure)
- [Changelog](#-changelog)

---

## 🎯 Présentation

**REBiRTH Upload Bot** est une application desktop qui automatise le workflow complet de release :

| Fonctionnalité | Description |
|---|---|
| 📄 **NFO** | Génération automatique UTF-8 + CP437 |
| 🎬 **TMDB** | Recherche avec confirmation et changement d'ID |
| ☁️ **Upload** | Gofile (failover 7 serveurs) ou BuzzHeavier |
| 💬 **Discord** | Notification automatique avec embed TMDB |
| 📁 **FINAL/** | Création automatique avec le bon NFO par tracker |
| 🌱 **Seedbox** | Upload complet via FTP TLS |
| 🧲 **Torrent** | Création par tracker + envoi ruTorrent via XML-RPC |
| 🎛️ **Trackers** | Page dédiée pour gérer les announces URL |
| ☕ **Anti-veille** | caffeinate (macOS) / SetThreadExecutionState (Windows) |
| 🌙 **Interface** | PyWebView moderne avec mode jour/nuit |

---

## 🚀 Installation

### macOS

```bash
brew install mediainfo

git clone https://github.com/CharonXXI/rebirth-upload-bot.git
cd rebirth-upload-bot

python3 -m venv venv
source venv/bin/activate

pip install pywebview python-dotenv parse-torrent-name torf pymediainfo
pip install -r NFO_CUSTOM/requirements.txt
```

### Windows

Voir **[INSTALL_WINDOWS.md](./INSTALL_WINDOWS.md)** pour le guide complet.

> 💡 **Note :** MediaInfo CLI n'est **pas** nécessaire sur Windows — `pymediainfo` embarque MediaInfo.dll automatiquement.

---

## ⚙️ Configuration

Renseigner les variables dans le fichier `V1.env` à la racine du projet :

```env
# ── TMDB ──────────────────────────────
API_KEY=ta_cle_tmdb
LANGUAGE=fr-FR

# ── Upload ────────────────────────────
GOFILE_TOKEN=ton_token_gofile
BUZZHEAVIER_ACC_ID=ton_account_id

# ── Discord ───────────────────────────
WEBHOOK_URL=ton_webhook_discord

# ── Seedbox FTP ───────────────────────
SFTP_HOST=https://ton-filebrowser.seedbox.link
SFTP_HOST_FTP=ton-host-ftp.seedbox.link
SFTP_PORT=23421
SFTP_USER=ton_user
SFTP_PASS=ton_password
SFTP_PATH=/rtorrent/REBiRTH

# ── ruTorrent ─────────────────────────
RUTORRENT_URL=https://ton-rutorrent.seedbox.link
RUTORRENT_USER=ton_user
RUTORRENT_PASS=ton_password

# ── Trackers ──────────────────────────
TRACKER_ABN=https://abn.com/announce/PASSKEY
TRACKER_TOS=https://tos.com/announce/PASSKEY
TRACKER_C411=https://c411.com/announce/PASSKEY
TRACKER_TORR9=https://torr9.com/announce/PASSKEY
TRACKER_LACALE=https://lacale.com/announce/PASSKEY
```

<details>
<summary>📖 Description des variables</summary>

| Variable | Description |
|---|---|
| `API_KEY` | themoviedb.org → Paramètres → API → Clé v3 |
| `LANGUAGE` | Code langue TMDB (ex: `fr-FR`) |
| `GOFILE_TOKEN` | gofile.io → My Profile → API Token |
| `BUZZHEAVIER_ACC_ID` | buzzheavier.com → Paramètres compte |
| `WEBHOOK_URL` | Discord → Paramètres serveur → Intégrations → Webhooks |
| `SFTP_HOST_FTP` | Host FTP de ta seedbox |
| `SFTP_PORT` | Port FTP (ex: `23421`) |
| `SFTP_USER / SFTP_PASS` | Login et mot de passe seedbox |
| `SFTP_PATH` | Chemin distant (ex: `/rtorrent/REBiRTH`) |
| `RUTORRENT_URL` | URL complète de ruTorrent |
| `TRACKER_XXX` | Announce URL du tracker (avec passkey) |

</details>

> ⚠️ Ne jamais commiter le fichier `V1.env` — il contient tous tes tokens et mots de passe.

---

## ▶️ Lancement

**macOS** → Double-cliquer sur `REBiRTH.command`

**Windows** → Double-cliquer sur `REBiRTH.bat`

**Terminal :**
```bash
# macOS
source venv/bin/activate && python3 app.py

# Windows
venv\Scripts\activate && python app.py
```

---

## 🔄 Workflow complet

```
Selectionner le .mkv
        │
        ▼
Remplir Source / Note / Trackers / Autre info
        │
        ▼
Choisir type NFO : UTF-8 (LaCale, C411, Torr9) ou CP437 (TOS, ABN)
        │
        ▼
Choisir plateforme : Gofile / BuzzHeavier / Ignorer
        │
        ▼
      LANCER
        │
        ├─ [TMDB]     Recherche + confirmation
        ├─ [NFO]      Generation UTF-8 + CP437
        ├─ [UPLOAD]   Gofile ou BuzzHeavier (si actif)
        ├─ [DISCORD]  Notification embed (si actif)
        ├─ [FINAL]    Creation FINAL/nom_film/ (MKV + NFO)
        ├─ [FTP]      Upload seedbox via FTP TLS
        └─ [TORRENT]  Creation + envoi ruTorrent
```

---

## ✨ Fonctionnalités

### 📄 Type NFO
- **UTF-8** → `(LaCale)-nom.nfo` pour LaCale, C411, Torr9
- **CP437** → `nom.nfo` pour TOS, ABN

### ☁️ Gofile
- Upload anonyme pour compatibilité maximale
- Failover automatique sur 7 serveurs
- MKV + NFO CP437 + NFO UTF-8 dans le même dossier

### ☁️ BuzzHeavier
- Recommandé pour les fichiers > 10 GB
- Temps écoulé affiché en temps réel

### 🌱 Seedbox FTP
- Upload automatique du dossier FINAL via FTP TLS
- Création automatique du sous-dossier `nom_film`

### 🧲 Torrent & ruTorrent
- Création d'un `.torrent` par tracker configuré
- Piece size 4 MiB, flag privé activé
- Envoi direct à ruTorrent via XML-RPC
- ruTorrent démarre le seeding immédiatement

### 💬 Discord
- Embed avec poster TMDB, liens TMDB/IMDb, source, trackers, note
- Ignoré automatiquement si l'upload est désactivé

---

## 📁 Structure

```
rebirth-upload-bot/
├── app.py                  ← Interface graphique (PyWebView)
├── auto-up-discord.py      ← Script principal CLI
├── gofile.py               ← Module upload Gofile
├── gui_index.html          ← Frontend HTML/CSS/JS
├── V1.env                  ← Configuration (ne pas commiter)
├── REBiRTH.command         ← Lanceur macOS
├── REBiRTH.bat             ← Lanceur Windows
├── build_win.bat           ← Build .exe Windows
├── build_win.spec          ← Spec PyInstaller Windows
├── INSTALL_WINDOWS.md      ← Guide installation Windows
├── NFO_CUSTOM/
│   ├── NFO_v1_7.py
│   ├── source_detector.py
│   └── tmdb_helper.py
├── FILMS/                  ← Déposer les .mkv ici
├── FINAL/                  ← Sortie (MKV + NFO par tracker)
└── TORRENTS/               ← Fichiers .torrent générés
```

---

## 📝 Changelog

### v2.0.7
- Compatibilité Windows complète : mediainfo via `pymediainfo` (plus besoin du CLI)
- Build `.exe` corrigé : mode onedir, hiddenimports complets, `V1.env` persistant
- Discord ignoré automatiquement quand l'upload est désactivé
- `INSTALL_WINDOWS.md` : guide d'installation Windows détaillé

### v2.0.6
- Création automatique des `.torrent` (un par tracker) après upload seedbox
- Envoi automatique à ruTorrent via XML-RPC
- Page Trackers avec announces URL sauvegardées dans le `.env`
- Scroll sur la colonne gauche pour voir la carte TMDB
- Barre de progression complète jusqu'à 100%

### v2.0.5
- Upload automatique sur seedbox via FTP TLS
- Création dossier FINAL/ avec MKV + bon NFO selon tracker
- Sélecteur type NFO (UTF-8 / CP437)
- Option pour ignorer Gofile/BuzzHeavier

### v2.0.4
- TMDB confirmé avant la génération du NFO
- Temps écoulé en temps réel pendant l'upload BuzzHeavier
- Mode jour/nuit

### v2.0.0
- Release initiale avec interface graphique PyWebView
- Failover automatique Gofile sur 7 serveurs

---

## 💡 Notes

- Pour les fichiers > 10 GB, BuzzHeavier est plus stable que Gofile
- Le bot empêche automatiquement la mise en veille pendant l'upload
- Le `V1.env` n'est jamais publié sur GitHub

---

<div align="center">

**REBiRTH Upload Bot v2.0.7** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
