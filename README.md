# REBiRTH Upload Bot

<div align="center">

```
██████╗ ███████╗██████╗ ██╗██████╗ ████████╗██╗  ██╗
██╔══██╗██╔════╝██╔══██╗██║██╔══██╗╚══██╔══╝██║  ██║
██████╔╝█████╗  ██████╔╝██║██████╔╝   ██║   ███████║
██╔══██╗██╔══╝  ██╔══██╗██║██╔══██╗   ██║   ██╔══██║
██║  ██║███████╗██████╔╝██║██║  ██║   ██║   ██║  ██║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
```

**NO RULES ! JUST FILES !**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Windows-lightgrey?style=flat-square)
![Version](https://img.shields.io/badge/Version-2.0.6-orange?style=flat-square)

</div>

---

## Presentation

**REBiRTH Upload Bot** est une application desktop qui automatise le workflow complet de release :

- Generation automatique de fichiers **NFO** (UTF-8 + CP437)
- Recherche **TMDB** avec confirmation interactive et possibilite de changer l'ID
- Upload sur **Gofile** (failover automatique 7 serveurs) ou **BuzzHeavier**
- Upload des 3 fichiers dans le meme dossier (MKV + NFO CP437 + NFO UTF-8)
- Notification automatique sur **Discord** avec embed complet
- Interface graphique moderne (PyWebView) avec mode jour/nuit
- Affichage de la taille du fichier avant upload
- Temps ecoule en temps reel pendant l'upload
- Creation automatique du dossier **FINAL/** avec le bon NFO selon le tracker
- Upload automatique du dossier complet sur la **seedbox via FTP TLS**
- Creation automatique des **.torrent** (un par tracker) et envoi a **ruTorrent** via XML-RPC
- Page **Trackers** pour gerer les announces URL de chaque tracker
- Option pour ignorer Gofile/BuzzHeavier et aller directement sur la seedbox
- Anti-veille integre (caffeinate macOS / SetThreadExecutionState Windows)

---

## Installation

### Prerequis

- Python 3.10+
- MediaInfo CLI
- Git

### macOS

```bash
brew install mediainfo

git clone https://github.com/CharonXXI/rebirth-upload-bot.git
cd rebirth-upload-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pywebview python-dotenv parse-torrent-name paramiko torf
```

### Windows

```bash
# Installer MediaInfo CLI depuis https://mediaarea.net/en/MediaInfo/Download/Windows

git clone https://github.com/CharonXXI/rebirth-upload-bot.git
cd rebirth-upload-bot

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pywebview python-dotenv parse-torrent-name paramiko torf
```

---

## Configuration

Cree un fichier `.env` a la racine du projet :

```env
GOFILE_TOKEN=ton_token_gofile
WEBHOOK_URL=ton_webhook_discord
API_KEY=ta_cle_tmdb
LANGUAGE=fr-FR
BUZZHEAVIER_ACC_ID=ton_account_id_buzzheavier

SFTP_HOST=https://ton-filebrowser.seedbox.link
SFTP_HOST_FTP=ton-host-ftp.seedbox.link
SFTP_PORT=23421
SFTP_USER=ton_user
SFTP_PASS=ton_password
SFTP_PATH=/rtorrent/REBiRTH

RUTORRENT_URL=https://ton-rutorrent.seedbox.link
RUTORRENT_USER=ton_user
RUTORRENT_PASS=ton_password

TRACKER_ABN=https://abn.com/announce/PASSKEY
TRACKER_TOS=https://tos.com/announce/PASSKEY
TRACKER_C411=https://c411.com/announce/PASSKEY
TRACKER_TORR9=https://torr9.com/announce/PASSKEY
TRACKER_LACALE=https://lacale.com/announce/PASSKEY
```

| Variable | Description |
|---|---|
| `GOFILE_TOKEN` | gofile.io -> My Profile -> API Token |
| `WEBHOOK_URL` | Discord -> Parametres serveur -> Integrations -> Webhooks |
| `API_KEY` | themoviedb.org -> Parametres -> API -> Cle v3 |
| `LANGUAGE` | Code langue TMDB (ex: fr-FR) |
| `BUZZHEAVIER_ACC_ID` | buzzheavier.com -> Parametres compte |
| `SFTP_HOST` | URL Filebrowser de ta seedbox |
| `SFTP_HOST_FTP` | Host FTP de ta seedbox |
| `SFTP_PORT` | Port FTP (ex: 23421) |
| `SFTP_USER` | Login seedbox |
| `SFTP_PASS` | Mot de passe seedbox |
| `SFTP_PATH` | Chemin distant (ex: /rtorrent/REBiRTH) |
| `RUTORRENT_URL` | URL ruTorrent |
| `RUTORRENT_USER` | Login ruTorrent |
| `RUTORRENT_PASS` | Mot de passe ruTorrent |
| `TRACKER_XXX` | Announce URL du tracker (avec passkey) |

> Ne jamais commiter le fichier `.env` — il contient tes tokens prives.

Tous ces champs sont aussi configurables directement depuis l'interface graphique via les pages **Config** et **Trackers**.

---

## Lancement

### macOS

Double-cliquer sur `REBiRTH.command`. macOS demandera une validation la premiere fois uniquement.

### Windows

Double-cliquer sur `REBiRTH.bat`.

### Via le terminal

```bash
# macOS
source venv/bin/activate && python3 app.py

# Windows
venv\Scripts\activate && python app.py
```

---

## Structure

```
rebirth-upload-bot/
├── app.py                  <- Interface graphique (PyWebView)
├── auto-up-discord.py      <- Script principal CLI
├── gofile.py               <- Module upload Gofile (failover 7 serveurs)
├── gui_index.html          <- Frontend HTML/CSS/JS
├── requirements.txt
├── REBiRTH.command         <- Lanceur macOS
├── REBiRTH.bat             <- Lanceur Windows
├── FILMS/                  <- Dossier pour tes fichiers .mkv
├── FINAL/                  <- Dossier de sortie (MKV + bon NFO par tracker)
├── TORRENT/                <- Dossier des fichiers .torrent generes
└── NFO_CUSTOM/
    ├── NFO_v1_7.py
    ├── source_detector.py
    └── tmdb_helper.py
```

---

## Workflow complet

1. Selectionner le fichier `.mkv` via la dropzone
2. Remplir Source, Note, Trackers, Autre info
3. Choisir le type NFO : **UTF-8** (LaCale, C411, Torr9) ou **CP437** (TOS, ABN)
4. Choisir la plateforme (Gofile / BuzzHeavier) ou cocher "Ignorer"
5. Cliquer **LANCER** — tout est automatique :
   - TMDB recherche, affiche et confirme (possibilite de changer l'ID)
   - NFO genere avec le bon lien TMDB
   - Upload Gofile ou BuzzHeavier avec les 3 fichiers (si non ignore)
   - Notification Discord avec embed
   - Dossier `FINAL/nom_film/` cree avec MKV + bon NFO
   - Upload du dossier complet sur la seedbox via FTP TLS
   - Creation d'un `.torrent` par tracker configure dans la page Trackers
   - Envoi automatique de chaque `.torrent` a ruTorrent via XML-RPC
   - ruTorrent demarre le seeding automatiquement

---

## Fonctionnalites

### Upload Gofile
- Upload anonyme (guest) pour compatibilite maximale
- Failover automatique sur 7 serveurs
- MKV + NFO CP437 + NFO UTF-8 dans le meme dossier

### Upload BuzzHeavier
- Recommande pour les fichiers > 10 GB
- Temps ecoule affiche en temps reel

### Seedbox FTP
- Upload automatique du dossier FINAL via FTP TLS
- Cree le sous-dossier `nom_film` automatiquement
- Progression affichee en temps reel

### Torrent & ruTorrent
- Creation d'un `.torrent` par tracker (avec announce URL depuis la page Trackers)
- Piece size : 4 MiB, flag prive active
- Envoi direct a ruTorrent via XML-RPC (`load.raw_start`)
- ruTorrent demarre le seeding immediatement sur le dossier seedbox

### Page Trackers
- Saisie et sauvegarde des announces URL pour ABN, TOS, C411, Torr9, LaCale
- Les announces sont chargees au demarrage depuis le `.env`

---

## Changelog

### v2.0.6
- Creation automatique des `.torrent` (un par tracker) apres upload seedbox
- Envoi automatique a ruTorrent via XML-RPC
- Page Trackers avec announces URL sauvegardees dans le `.env`
- Scroll sur la colonne gauche pour voir la carte TMDB
- Barre de progression complete jusqu'a 100% en fin de workflow

### v2.0.5
- Upload automatique sur seedbox via FTP TLS
- Creation dossier FINAL/ avec MKV + bon NFO selon tracker
- Selecteur type NFO (UTF-8 / CP437) dans le GUI
- Option pour ignorer Gofile/BuzzHeavier
- Banner de fin adapte selon le mode

### v2.0.4
- TMDB confirme avant la generation du NFO
- Fix lien TMDB dans le NFO quand l'ID est change
- Temps ecoule en temps reel pendant l'upload BuzzHeavier
- Mode jour/nuit

### v2.0.3
- Confirmation TMDB interactive dans le GUI

### v2.0.2
- Upload NFO UTF-8 sur Gofile/BuzzHeavier

### v2.0.1
- Affichage de la taille du fichier

### v2.0.0
- Release initiale avec interface graphique PyWebView
- Failover automatique Gofile sur 7 serveurs

---

## Notes

- Pour les fichiers > 10 GB, BuzzHeavier est plus stable que Gofile
- Le bot empeche automatiquement la mise en veille pendant l'upload
- L'upload Gofile est anonyme (guest) — les fichiers expirent apres inactivite
- Sur macOS, le `.command` doit etre valide une seule fois

---

<div align="center">

**REBiRTH Upload Bot v2.0.6** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
