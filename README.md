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
[![Version](https://img.shields.io/badge/Version-2.7.1-FFA500?style=for-the-badge)](.)
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
| 🧲 **Torrent SB** | Création torrent via SSH+mktorrent côté seedbox, chargement automatique dans ruTorrent |
| 💿 **BD Info** | Rapport exact via **BDInfo v0.7.5.6** (Wine/Whisky) — DISC INFO/VIDEO/AUDIO/SUBTITLES, upload ZIP vers Gofile ou BuzzHeavier |
| 🎛️ **Trackers** | Page dédiée pour gérer les announces URL |
| ☕ **Anti-veille** | caffeinate (macOS) / SetThreadExecutionState (Windows) |
| 🌙 **Interface** | PyWebView moderne avec mode jour/nuit, animations, toasts |

---

## 🚀 Installation

### macOS

```bash
brew install mediainfo

git clone https://github.com/CharonXXI/rebirth-upload-bot.git
cd rebirth-upload-bot

python3 -m venv venv
source venv/bin/activate

pip install pywebview python-dotenv pymediainfo parse-torrent-name
pip install -r NFO_CUSTOM/requirements.txt
```

#### BD Info (via BDInfo v0.7.5.6 + Whisky)

Le bot utilise **BDInfo v0.7.5.6** (version Windows GUI) via Wine/Whisky pour obtenir des bitrates exacts (comptage paquets TS).

1. Installer **[Whisky](https://github.com/Whisky-App/Whisky/releases)** (wrapper Wine pour macOS)
2. Placer `BDInfo.exe` et ses DLLs dans un dossier (ex: `~/Desktop/BDInfo_v0/`)
3. Configurer la variable d'environnement :

```bash
export BDINFO_WIN_EXE="$HOME/Desktop/BDInfo_v0/BDInfo.exe"
```

> 💡 Ajouter cette ligne dans `~/.zshrc` pour la rendre permanente, ou lancer le bot depuis un terminal avec la variable définie.

### Windows

Voir **[INSTALL_WINDOWS.md](./INSTALL_WINDOWS.md)** pour le guide complet.

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

# ── BD Info ───────────────────────────
BDINFO_WIN_EXE=/chemin/vers/BDInfo.exe   # requis pour l'onglet BD Info
# BDINFO_WINE_TIMEOUT=1800               # timeout max en secondes (défaut 30 min)
```

> ⚠️ Ne jamais commiter le fichier `V1.env` — il contient tous tes tokens et mots de passe.

---

## ▶️ Lancement

**macOS** → Double-cliquer sur `REBiRTH.command`

**Terminal :**
```bash
source venv/bin/activate && python3 app.py
```

---

## 🔄 Workflow complet

```
─────────────────────────────────────────────
Workflow principal (MKV / REMUX)
─────────────────────────────────────────────
Sélectionner le .mkv
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
Onglet BD INFO
        │
        ▼
  SCANNER (optionnel — ouvre BDInfo v0.7.5.6 via Wine/Whisky)
  ou directement depuis un rapport existant :
        │
        ▼
  Dans BDInfo v0.7.5.6 :
    1. Scan Bitrates
    2. View Report → sauvegarder dans BDINFO/
        │
        ▼
  📂 CHARGER RAPPORT BDINFO
        │
        ├─ Conversion RTF → texte brut (si TextEdit)
        ├─ Extraction DISC INFO / PLAYLIST REPORT / VIDEO / AUDIO / SUBTITLES
        ├─ Renommage automatique avec le Disc Label (ex: DISC_LABEL.nfo)
        ├─ Sauvegarde .txt + .nfo dans BDINFO/
        ├─ Affichage dans la preview
        └─ BDInfo/Wine fermé automatiquement
                   │
                   ▼
        Choisir BuzzHeavier / Gofile → ENVOYER
        └─ ZIP (dossier COMPLETE BLURAY + NFO) uploadé en un seul fichier
```

---

## ✨ Fonctionnalités

### 💿 BD Info
- Onglet dédié pour les releases COMPLETE BLURAY
- Lance **BDInfo v0.7.5.6** (Windows GUI) via Wine/Whisky — bitrates exacts par comptage paquets TS (ex: 24 980 kbps précis)
- Workflow manuel : Scan Bitrates → View Report → sauvegarder dans `BDINFO/`
- Bouton **📂 CHARGER RAPPORT BDINFO** : traite le fichier le plus récent du dossier (`.rtf`, `.txt` ou `.nfo`)
  - Conversion automatique RTF → texte brut (TextEdit sauvegarde en RTF par défaut)
  - Extraction de la playlist principale (00001.MPLS ou la plus longue)
  - Contenu filtré : **DISC INFO + PLAYLIST REPORT + VIDEO + AUDIO + SUBTITLES** uniquement
  - Renommage automatique avec le `Disc Label` (ex: `THE_STRANGERS_CHAPTER_3_BD.nfo`)
  - Sauvegarde double : `.txt` + `.nfo`
  - Ferme BDInfo/Wine automatiquement
- **Upload ZIP** : compresse le dossier COMPLETE BLURAY + NFO → BuzzHeavier ou Gofile

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
- Embed avec poster TMDB, liens TMDB/IMDb, source, trackers, note

### 🧲 Torrent SB
- Création du torrent via **SSH + mktorrent** directement sur la seedbox (piece size 4 MiB, privé)
- Chargement automatique dans ruTorrent pour seeding immédiat
- Un `.torrent` par tracker coché — sauvegardé dans `TORRENTS/`
- Requiert un accès SSH sur port 22 (configurer `SFTP_HOST_FTP`, `SFTP_USER`, `SFTP_PASS`, `SFTP_PORT=22`)

---

## 📁 Structure

```
rebirth-upload-bot/
├── app.py                  ← Backend Python (PyWebView)
├── gui_index.html          ← Frontend HTML/CSS/JS
├── gofile.py               ← Module upload Gofile
├── auto-up-discord.py      ← Script CLI autonome
├── V1.env                  ← Configuration (ne pas commiter)
├── REBiRTH.command         ← Lanceur macOS
├── REBiRTH.bat             ← Lanceur Windows
├── NFO_CUSTOM/             ← Générateur NFO
├── FILMS/                  ← Déposer les .mkv ici
├── FINAL/                  ← Sortie (MKV + NFO)
├── TORRENTS/               ← Fichiers .torrent
└── BDINFO/                 ← Rapports BD Info (.nfo + .txt)
```

---

## 📝 Changelog

### v2.7.1
- Feat : **espace disque seedbox** affiché en bas du sidebar (`SB : X.XX Tio / Y.YY Tio`)
- Feat : rafraîchissement automatique toutes les 60 secondes
- Fix : calcul `used = total - available` pour matcher l'affichage ruTorrent (blocs réservés inclus)
- Fix : `df -P` pour éviter le wrap des noms de filesystem longs

### v2.7.0
- **Torrent SB opérationnel** — création via SSH + mktorrent côté seedbox, chargement automatique dans ruTorrent pour seeding immédiat
- Feat : méthode SSH prioritaire dans la cascade de création torrent (port 22 détecté automatiquement)
- Feat : un `.torrent` par tracker coché, sauvegardé dans `TORRENTS/`
- Feat : **source tag par tracker** — info hash unique par tracker via `-s` mktorrent (`TOS=TheOldSchool`, `ABN`, `C411`, `Torr9`, `LaCale`) — cross-seeding immédiat sur TOS sans re-télécharger
- Feat : migration seedbox complète en **SFTP/SSH paramiko** (port 22) — `list_seedbox_files` et `_ftp_upload` réécrits
- Fix : `tsbSelect()` — suppression du `.replace(/\.[^.]+$/, '')` qui tronquait le nom du dossier (ex: `.AVC-REBiRTH` retiré à tort)
- Fix : `Path.stem` → `Path.name` côté Python pour `remote_path` — même troncature corrigée
- Fix : mise à jour credentials seedbox (nouveau VPS avec accès SSH complet)

### v2.6.0
- **Refactor BD Info complet** — abandon de BDInfoCLI (.NET) au profit de **BDInfo v0.7.5.6** (Windows GUI via Wine/Whisky)
- Feat : **bitrates exacts** — BDInfo v0.7.5.6 utilise le comptage paquets TS (ex: 24 980 kbps au lieu de ~9 918 kbps avec BDInfoCLI)
- Feat : **bouton 📂 CHARGER RAPPORT BDINFO** — traite le rapport le plus récent du dossier `BDINFO/` sans dépendre du timing du scan
- Feat : **conversion RTF automatique** — TextEdit sauvegarde en `.rtf` ; le bot le convertit en texte brut propre (nettoyage font-table, commandes RTF)
- Feat : **extraction ciblée** — seules les sections DISC INFO / PLAYLIST REPORT / VIDEO / AUDIO / SUBTITLES sont conservées (FILES, CHAPTERS, STREAM DIAGNOSTICS supprimés)
- Feat : **renommage par Disc Label** — le fichier brut est remplacé par `DISC_LABEL.txt` + `DISC_LABEL.nfo` (priorité à `Disc Label:` sur `Disc Title:`)
- Feat : **kill Wine automatique** au clic "Charger rapport" — BDInfo est fermé proprement
- Feat : **polling .rtf** ajouté en plus de `.txt` / `.nfo`
- Feat : **mini-tuto intégré** dans l'onglet BD Info (3 étapes)
- Feat : **lancement direct BDInfo.exe sur Windows** depuis `BDInfo_v0\` sans Wine ni .NET
- Feat : **section THX dans le NFO** — ManixQC & MenFox centrés entre LiNKS et NO RULES
- Feat : **LANGUAGE_MAP étendu** — ajout `fr-FR`, `fr-CA`, `no` (Norvégien), `es-419` (Spanish Latin America)
- Fix : **post-traitement unifié** — même logique extraction/renommage pour le polling Wine et le chargement manuel
- Fix : **upload BD Info** — `_bdi_last_nfo` correctement exposé après chargement manuel du rapport
- Fix : **upload BD Info** — détection automatique du dossier COMPLETE.BLURAY dans `FILMS/` pour les deux workflows (scan ou chargement manuel)

### v2.5.9
- Feat : onglet BD Info complet — scan COMPLETE BLURAY, rapport BDInfoCLI filtré, upload ZIP
- Feat : identification MPLS intelligente via makemkvcon / BDInfoCLI --list
- Feat : upload ZIP BD Info (ZIP_STORED, dossier + NFO)
- Fix : reset section upload au démarrage d'un nouveau scan
- Fix : détection rapport sur rescan (mtime)
- Fix : upload 400 BuzzHeavier (exclusion .DS_Store, BACKUP/)

### v2.5.8
- Fix : upload 400 — filtrage `.DS_Store` / `._*` / `BACKUP/`
- Feat : UI upload BD Info — toggle BuzzHeavier/Gofile + bouton ENVOYER

### v2.5.7
- Fix : détection rapport sur rescan — timestamp `scan_start`

### v2.5.6
- Fix : section upload non réinitialisée entre deux scans

### v2.5.5
- Feat : upload BD Info inclut le dossier film complet + NFO

### v2.5.4
- Feat : upload BD Info — envoi `.nfo` vers Gofile ou BuzzHeavier

### v2.5.3
- Revert : retour v2.5.0 — suppression patches bitrates non concluants

### v2.5.0
- Fix : filtrage rapport — `.txt` source filtré aussi

### v2.4.9
- Feat : filtrage rapport BDInfoCLI — DISC INFO → SUBTITLES uniquement

### v2.4.7
- Feat : flow makemkvcon → BDInfoCLI — identification MPLS principal

### v2.4.0
- Feat : séparation canaux `bdinfo_status` / `bdinfo_output`

### v2.3.7
- Feat : onglet BD Info — intégration BDInfoCLI, scan COMPLETE BLURAY

### v2.0.0
- Release initiale PyWebView, failover Gofile 7 serveurs

---

## 💡 Notes

- Pour les fichiers > 10 GB, BuzzHeavier est plus stable que Gofile
- Le bot empêche automatiquement la mise en veille pendant l'upload
- `V1.env` n'est jamais publié sur GitHub
- BD Info nécessite BDInfo v0.7.5.6 + Whisky (voir section Installation)
- Torrent SB nécessite un accès SSH sur port 22 et `mktorrent` installé sur la seedbox

---

<div align="center">

**REBiRTH Upload Bot v2.7.1** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
