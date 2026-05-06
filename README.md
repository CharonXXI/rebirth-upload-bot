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
[![Version](https://img.shields.io/badge/Version-2.8.4-FFA500?style=for-the-badge)](.)
[![License](https://img.shields.io/badge/License-Private-red?style=for-the-badge)](.)

</div>

---

## 📋 Table des matières

- [Présentation](#-présentation)
- [Installation](#-installation)
  - [📖 Guide macOS complet](./INSTALL_MAC.md)
  - [📖 Guide Windows complet](./INSTALL_WINDOWS.md)
- [Configuration](#-configuration)
- [Lancement](#-lancement)
- [Workflow](#-workflow-complet)
- [Fonctionnalités](#-fonctionnalités)
- [Structure](#-structure)
- [Changelog](#-changelog)

---

## 🎯 Présentation

**REBiRTH AIO** est une application desktop tout-en-un qui automatise le workflow complet de release : du remux Blu-ray à la notification Discord, en passant par la création de torrents et la gestion seedbox.

| Fonctionnalité | Description |
|---|---|
| 🔄 **Remux** | Extraction ISO/BDMV → MKV via MakeMKV + MKVToolNix, sélection des pistes (vidéo/audio/subs), tag VF automatique, nommage REBiRTH |
| 📄 **NFO** | Génération automatique UTF-8 + CP437 |
| 🎬 **TMDB** | Recherche avec confirmation et changement d'ID |
| ☁️ **Upload** | Gofile (failover 7 serveurs) ou BuzzHeavier |
| 💬 **Discord** | Notification automatique avec embed TMDB |
| 📁 **FINAL/** | Création automatique avec le bon NFO par tracker |
| 🌱 **Seedbox** | Upload complet via FTP TLS |
| 🧲 **Torrent SB** | Création torrent via SSH+mktorrent côté seedbox, chargement automatique dans ruTorrent |
| 💿 **BD Info** | Rapport exact via **BDInfo v0.7.5.6** (Wine/Whisky) — DISC INFO/VIDEO/AUDIO/SUBTITLES, upload ZIP vers Gofile ou BuzzHeavier |
| 🗂️ **Fichiers SB** | Explorateur de fichiers seedbox — navigation dans les sous-dossiers, suppression via SSH sudo |
| 🎛️ **Trackers** | Page dédiée pour gérer les announces URL (ABN · TOS · C411 · Torr9 · LaCale · HDT · Nexum) |
| ☕ **Anti-veille** | caffeinate (macOS) / SetThreadExecutionState (Windows) |
| 🌙 **Interface** | PyWebView moderne avec mode jour/nuit, animations, toasts |

---

## 🚀 Installation

### macOS

Voir **[INSTALL_MAC.md](./INSTALL_MAC.md)** pour le guide complet.

Commandes rapides :

```bash
brew install mediainfo mkvtoolnix ffmpeg
brew install --cask makemkv

git clone https://github.com/CharonXXI/rebirth-upload-bot.git
cd rebirth-upload-bot

python3 -m venv venv
source venv/bin/activate

pip install pywebview python-dotenv requests requests_toolbelt tqdm rich pymediainfo parse-torrent-name numpy paramiko
pip install -r NFO_CUSTOM/requirements.txt
```

Lancement : **double-cliquer sur `REBiRTH.command`**

#### BD Info (via BDInfo v0.7.5.6 + Whisky)

Le bot utilise **BDInfo v0.7.5.6** (version Windows GUI) via Wine/Whisky pour obtenir des bitrates exacts (comptage paquets TS).

1. Installer **[Whisky](https://github.com/Whisky-App/Whisky/releases)** (wrapper Wine pour macOS)
2. Placer `BDInfo.exe` et ses DLLs dans un dossier (ex: `~/Desktop/BDInfo_v0/`)
3. Ajouter dans `~/.zshrc` :

```bash
export BDINFO_WIN_EXE="$HOME/Desktop/BDInfo_v0/BDInfo.exe"
```

### Windows

Voir **[INSTALL_WINDOWS.md](./INSTALL_WINDOWS.md)** pour le guide complet (inclut la section onglet Remux).

#### BD Info (Windows)

Placer `BDInfo.exe` et ses DLLs dans le dossier **`BDInfo_v0\`** à la racine du projet — le bot le détecte et le lance directement, sans Wine ni .NET.

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
WEBHOOK_URL=ton_webhook_discord_rebirth
WEBHOOK_HDT_URL=ton_webhook_discord_fullbd

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
TRACKER_HDT=https://hdts-announce.ru/announce.php?passkey=PASSKEY
TRACKER_NEXUM=https://nexum-core.com/announce/PASSKEY
SFTP_PATH_HDT=/home/rtorrent/rtorrent/download/FULL BD

# ── BD Info ───────────────────────────
BDINFO_WIN_EXE=/chemin/vers/BDInfo.exe   # requis pour l'onglet BD Info
# BDINFO_WINE_TIMEOUT=1800               # timeout max en secondes (défaut 30 min)
```

> ⚠️ Ne jamais commiter le fichier `V1.env` — il contient tous tes tokens et mots de passe.

---

## ▶️ Lancement

**macOS** → Double-cliquer sur `REBiRTH.command`

**Windows** → Double-cliquer sur `REBiRTH.bat`

**Terminal :**
```bash
source venv/bin/activate && python3 app.py
```

---

## 🔄 Workflow complet

```
─────────────────────────────────────────────
Workflow Remux (ISO/BDMV → MKV)
─────────────────────────────────────────────
Onglet 🔄 REMUX
        │
        ▼
Placer l'ISO ou le dossier BDMV dans remux_tool/FULL/
⟳ Refresh → sélectionner la source
        │
        ▼
ANALYSER → MakeMKV scanne le disque (30 s à 2 min)
  └─ Sélection automatique du titre principal
  └─ TMDB récupère le titre FR
        │
        ▼
Sélectionner les pistes (vidéo / audio / subs)
Renseigner titre et année si besoin
        │
        ▼
▶ LANCER LE REMUX
  ├─ [MakeMKV]     Extraction titre principal vers tmp
  ├─ [MediaInfo]   Analyse des pistes du MKV extrait
  ├─ [MKVMerge]    Remux avec sélection précise des pistes
  └─ [FILMS/]      MKV final → Bot Upload peut prendre le relais

─────────────────────────────────────────────
Workflow principal (MKV → Upload)
─────────────────────────────────────────────
Sélectionner le .mkv (onglet Upload)
        │
        ▼
Remplir Source / Note / Autre info
Cocher les trackers : ABN / TOS / C411 / Torr9 / LaCale
        │
        ▼
Choisir type NFO : UTF-8 (LaCale · C411 · Torr9)
                   CP437 (TOS · ABN)
Choisir plateforme : BuzzHeavier / Gofile / Ignorer
        │
        ▼
      LANCER
        │
        ├─ [TMDB]     Recherche automatique + confirmation / changement d'ID
        ├─ [NFO]      Génération UTF-8 + CP437
        ├─ [UPLOAD]   BuzzHeavier (recommandé > 10 GB) ou Gofile (failover 7 serveurs)
        ├─ [DISCORD]  Notification embed (poster TMDB, liens, source, trackers, note)
        ├─ [FINAL]    Création FINAL/nom_film/ avec le bon NFO par tracker
        └─ [SFTP]     Upload complet du dossier FINAL sur la seedbox (SSH port 22)

─────────────────────────────────────────────
Workflow Torrent SB (après upload seedbox)
─────────────────────────────────────────────
Onglet TORRENT SB
        │
        ▼
Recharger la liste seedbox → cliquer sur le film
        │
        ▼
Cocher les trackers → CRÉER TORRENTS SB
        │
        ├─ [SSH]      Connexion paramiko → mktorrent côté seedbox
        │              -p (privé) · -l 22 (4 MiB) · -s source_tag par tracker
        │              → hash unique par tracker (TOS=TheOldSchool, etc.)
        ├─ [SFTP]     Rapatriement du .torrent → sauvegardé dans TORRENTS/
        └─ [ruTorrent] Chargement via addtorrent.php → seeding immédiat

─────────────────────────────────────────────
Workflow BD Info (COMPLETE BLURAY)
─────────────────────────────────────────────
Onglet BD INFO → SCANNER → BDInfo v0.7.5.6 s'ouvre
        │
        ▼
  Dans BDInfo : Scan Bitrates → View Report → sauvegarder dans BDINFO/
        │
        ▼
  📂 CHARGER RAPPORT BDINFO
        │
        ├─ Extraction DISC INFO / PLAYLIST REPORT / VIDEO / AUDIO / SUBTITLES
        ├─ Renommage automatique avec le Disc Label
        ├─ Sauvegarde .txt + .nfo dans BDINFO/
        └─ Upload ZIP → BuzzHeavier ou Gofile
```

---

## ✨ Fonctionnalités

### 🔄 Remux (onglet intégré)
- Interface complète dans REBiRTH AIO — pas besoin de lancer un outil séparé
- Source : ISO ou dossier BDMV dans `remux_tool/FULL/`
- Analyse automatique via **MakeMKV** (scan du disque, sélection titre principal)
- Recherche **TMDB** pour récupérer le titre français
- Sélection manuelle des pistes vidéo / audio / sous-titres avec recommandations auto
- Tag VF automatique : VFF / VFQ / VFi / VF2 (si VFF+VFQ)
- Remux via **MKVToolNix** avec titrage correct (VO, VFF, FR FORCED…)
- Résultat directement dans `FILMS/` — l'onglet Upload peut prendre le relais
- 📸 **4 Screenshots** : extraction automatique depuis le MKV → `PICS/<titre>/`
- Console live, barre de progression, étapes en temps réel

### 💿 BD Info
- Onglet dédié pour les releases COMPLETE BLURAY
- Lance **BDInfo v0.7.5.6** via Wine/Whisky (macOS) ou directement (Windows)
- Workflow : Scan Bitrates → View Report → sauvegarder dans `BDINFO/`
- Bouton **📂 CHARGER RAPPORT BDINFO** : traite le fichier le plus récent
- **Upload ZIP** : compresse le dossier COMPLETE BLURAY + NFO

### 📄 Type NFO
- **UTF-8** → `(UTF8).nom.nfo` pour LaCale, C411, Torr9
- **CP437** → `(CP437).nom.nfo` pour TOS, ABN

### ☁️ Gofile
- Upload anonyme, failover automatique sur 7 serveurs

### ☁️ BuzzHeavier
- Recommandé pour les fichiers > 10 GB
- Progression réelle : %, vitesse MB/s, temps écoulé

### 🌱 Seedbox FTP
- Upload automatique du dossier FINAL via FTP TLS

### 💬 Discord
- **REBiRTH** — 6 trackers (TOS / ABN / C411 / Torr9 / LaCale / Nexum), webhook REBiRTH
- **FULL BD** — tracker HDT uniquement, webhook séparé

### 🗂️ Fichiers SB
- Navigation dans `/home/rtorrent/rtorrent/download` et sous-dossiers
- Suppression via SSH `sudo rm -rf`

### 🧲 Torrent SB
- Création via **SSH + mktorrent** côté seedbox (piece size 4 MiB, privé)
- Hash unique par tracker via source tag
- Chargement automatique dans ruTorrent

---

## 📁 Structure

```
rebirth-upload-bot/
├── app.py                      ← Backend Python principal (PyWebView + toute la logique)
├── gui_index.html              ← Frontend HTML/CSS/JS (interface complète)
├── gofile.py                   ← Module upload Gofile (failover 7 serveurs)
├── V1.env                      ← Configuration (ne pas commiter — gitignored)
├── REBiRTH.command             ← Lanceur macOS (double-clic)
├── REBiRTH.bat                 ← Lanceur Windows (double-clic)
├── NFO_CUSTOM/                 ← Générateur NFO (TMDB, templates, helpers)
├── BDInfo_v0/                  ← BDInfo v0.7.5.6 (BDInfo.exe + DLLs — non commité)
├── remux_tool/                 ← Outil de remux Blu-ray (intégré dans l'onglet Remux)
│   ├── gui.py                  ← Backend remux (API PyWebView)
│   ├── makemkv_extract.py      ← Extraction MakeMKV
│   ├── mediainfo_parse.py      ← Analyse des pistes MediaInfo/ffprobe
│   ├── mkvtoolnix_remux.py     ← Remux MKVMerge
│   ├── config.py               ← Configuration remux (dossiers, options)
│   ├── FULL/                   ← Sources ISO/BDMV (non commité)
│   └── MAKEMKV_KEY.txt         ← Clé beta MakeMKV
├── FILMS/                      ← .mkv finaux (remux → ici, puis upload bot)
├── PICS/                       ← Screenshots extraits par l'onglet Remux
│   └── Nom Du Film/            ← 4 captures par film
├── FINAL/                      ← Sortie upload (MKV + NFO par tracker)
├── TORRENTS/                   ← Fichiers .torrent par tracker
└── BDINFO/                     ← Rapports BD Info (.txt + .nfo)
```

---

## 📝 Changelog

### v2.8.4
- Feat : **onglet Remux intégré** dans REBiRTH AIO — plus besoin de lancer un outil séparé
  - Analyse MakeMKV directement dans l'interface (30 s à 2 min selon le disque)
  - Sélection des pistes vidéo / audio / sous-titres avec recommandations auto
  - Tag VF automatique (VFF / VFQ / VFi / VF2)
  - Barre de progression + étapes en temps réel + console live
  - MKV final déposé directement dans `FILMS/` pour enchaîner avec l'upload
  - 📸 4 Screenshots automatiques → `PICS/<titre du film>/`
  - TMDB intégré pour récupérer le titre français
- Fix : boutons Test MakeMKV / Reset MakeMKV / 4 Screens (`toast` → `showToast`)
- Renommage : **REBiRTH AIO** (titre fenêtre, sidebar, topbar)
- Réorganisation navigation : Upload · Remux · Trackers · BD Info · Torrent SB · Fichiers SB · Discord · Historique · Stats · Config

### v2.8.3
- Feat : **tracker Nexum** (nexum-core.com) — intégration complète
  - Upload : case à cocher Nexum (UTF-8)
  - Torrent SB : création `.torrent` avec source tag `Nexum` → `TORRENTS/NEXUM/`
  - Discord mode REBiRTH : Nexum dans la liste des statuts (6 trackers)
  - Config Trackers : champ `TRACKER_NEXUM`
  - Historique : badge cyan `#00e5cc`
- Feat : **layout trackers Upload** en grille 4 colonnes

### v2.8.2
- Feat : **onglet Fichiers SB** — explorateur de fichiers seedbox intégré
- Fix : page Fichiers SB placée hors du conteneur principal

### v2.8.1
- Feat : **onglet Discord → mode FULL BD** — toggle REBiRTH / FULL BD

### v2.8.0
- Feat : **tracker HD-Torrents (HDT)** — Config, Torrent SB, BD Info

### v2.7.1
- Feat : **espace disque seedbox** affiché en bas du sidebar

### v2.7.0
- Feat : **Torrent SB opérationnel** — SSH + mktorrent, source tag par tracker

### v2.6.0
- Feat : **BD Info** — BDInfo v0.7.5.6 (Windows GUI via Wine/Whisky), bitrates exacts

### v2.0.0
- Release initiale PyWebView, failover Gofile 7 serveurs

---

## 💡 Notes

- Pour les fichiers > 10 GB, BuzzHeavier est plus stable que Gofile
- Le bot empêche automatiquement la mise en veille pendant l'upload
- `V1.env` n'est jamais publié sur GitHub
- L'onglet Remux nécessite : **MakeMKV**, **MKVToolNix**, **MediaInfo**, **ffmpeg** (voir INSTALL_WINDOWS.md)
- BD Info nécessite BDInfo v0.7.5.6 + Whisky (macOS) ou BDInfo_v0\ (Windows)
- Torrent SB nécessite un accès SSH port 22 et `mktorrent` installé sur la seedbox
- Trackers supportés : ABN · TOS · C411 · Torr9 · LaCale · HDT · Nexum

---

<div align="center">

**REBiRTH AIO v2.8.4** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
