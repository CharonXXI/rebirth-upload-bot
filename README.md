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
![Version](https://img.shields.io/badge/Version-2.0.7-orange?style=flat-square)

</div>

---

## Presentation

**REBiRTH Upload Bot** est une application desktop qui automatise le workflow complet de release :

- Generation automatique de fichiers **NFO** (UTF-8 + CP437)
- Recherche **TMDB** avec confirmation interactive et possibilite de changer l'ID
- Upload sur **Gofile** (failover automatique 7 serveurs) ou **BuzzHeavier**
- Notification automatique sur **Discord** avec les `.torrent` en pieces jointes
- Creation automatique du dossier **FINAL/** avec le bon NFO selon le tracker
- Upload automatique du dossier complet sur la **seedbox via FTP TLS**
- Creation automatique des **.torrent** (un par tracker) et envoi a **ruTorrent** via XML-RPC
- Page **Trackers** pour gerer les announces URL de chaque tracker
- **Systeme de login** multi-utilisateurs securise
- Interface graphique moderne (PyWebView) avec mode jour/nuit
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

Voir le fichier `INSTALL_WINDOWS.md` pour le guide detaille.

---

## Configuration

Cree un fichier `.env` a la racine du projet :

```env
# Acces
REBIRTH_USER_REBiRTH01=ton_password_user1
REBIRTH_USER_REBiRTH02=ton_password_user2

# TMDB
API_KEY=ta_cle_tmdb
LANGUAGE=fr-FR

# Gofile
GOFILE_TOKEN=ton_token_gofile

# BuzzHeavier
BUZZHEAVIER_ACC_ID=ton_account_id

# Discord
WEBHOOK_URL=ton_webhook_discord

# Seedbox FTP
SFTP_HOST=https://ton-filebrowser.seedbox.link
SFTP_HOST_FTP=ton-host-ftp.seedbox.link
SFTP_PORT=23421
SFTP_USER=ton_user
SFTP_PASS=ton_password
SFTP_PATH=/rtorrent/REBiRTH

# ruTorrent
RUTORRENT_URL=https://ton-rutorrent.seedbox.link
RUTORRENT_USER=ton_user
RUTORRENT_PASS=ton_password

# Announces trackers
TRACKER_ABN=https://abn.com/announce/PASSKEY
TRACKER_TOS=https://tos.com/announce/PASSKEY
TRACKER_C411=https://c411.com/announce/PASSKEY
TRACKER_TORR9=https://torr9.com/announce/PASSKEY
TRACKER_LACALE=https://lacale.com/announce/PASSKEY
```

### Gestion des utilisateurs

Chaque utilisateur a sa propre ligne dans le `.env` :

```env
REBIRTH_USER_NOM=motdepasse
```

Pour ajouter un user : ajouter une ligne. Pour le desactiver : supprimer ou commenter la ligne. Le `.env` n'est jamais commite sur GitHub — les utilisateurs qui telechargent le repo ne peuvent pas se connecter sans leur `.env` personnel.

> Ne jamais commiter le fichier `.env` — il contient tous tes tokens et mots de passe.

---

## Lancement

### macOS

Double-cliquer sur `REBiRTH.command`.

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
├── INSTALL_WINDOWS.md      <- Guide installation Windows
├── FILMS/                  <- Dossier pour tes fichiers .mkv
├── FINAL/                  <- Dossier de sortie (MKV + bon NFO par tracker)
├── TORRENT/                <- Dossier fichiers .torrent generes
└── NFO_CUSTOM/
    ├── NFO_v1_7.py
    ├── source_detector.py
    └── tmdb_helper.py
```

---

## Workflow complet

1. Se connecter avec son login/password
2. Selectionner le fichier `.mkv`
3. Remplir Source, Note, Trackers, Autre info
4. Choisir le type NFO : **UTF-8** (LaCale, C411, Torr9) ou **CP437** (TOS, ABN)
5. Choisir la plateforme (Gofile / BuzzHeavier) ou cocher "Ignorer"
6. Cliquer **LANCER** — tout est automatique :
   - TMDB recherche et confirme
   - NFO genere avec le bon lien TMDB
   - Upload Gofile ou BuzzHeavier (si non ignore)
   - Creation .torrent par tracker + envoi ruTorrent
   - Notification Discord avec les .torrent en pieces jointes
   - Dossier FINAL/ cree avec MKV + bon NFO
   - Upload du dossier complet sur la seedbox via FTP TLS

---

## Changelog

### v2.0.7
- Systeme de login multi-utilisateurs (REBIRTH_USER_XXX dans le .env)
- Page de connexion au demarrage du bot
- Impossible d'acceder au bot sans credentials valides

### v2.0.6
- Creation automatique des `.torrent` (un par tracker) apres upload seedbox
- Envoi automatique a ruTorrent via XML-RPC
- Notification Discord avec les `.torrent` en pieces jointes
- Page Trackers avec announces URL sauvegardees
- Scroll sur la colonne gauche pour voir la carte TMDB
- Barre de progression complete jusqu'a 100%

### v2.0.5
- Upload automatique sur seedbox via FTP TLS
- Creation dossier FINAL/ avec MKV + bon NFO
- Selecteur type NFO (UTF-8 / CP437)
- Option pour ignorer Gofile/BuzzHeavier

### v2.0.4
- TMDB confirme avant la generation du NFO
- Temps ecoule en temps reel pendant l'upload BuzzHeavier
- Mode jour/nuit

### v2.0.0
- Release initiale avec interface graphique PyWebView
- Failover automatique Gofile sur 7 serveurs

---

## Notes

- Pour les fichiers > 10 GB, BuzzHeavier est plus stable que Gofile
- Le bot empeche automatiquement la mise en veille pendant l'upload
- Le `.env` n'est jamais publie — chaque installation a ses propres credentials

---

<div align="center">

**REBiRTH Upload Bot v2.0.7** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
