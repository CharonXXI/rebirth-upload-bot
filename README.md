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
[![Version](https://img.shields.io/badge/Version-2.9.8-FFA500?style=for-the-badge)](.)
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
  - [📀 Full BD](#-full-bd)
  - [🔄 Remux](#-remux-onglet-intégré)
  - [🎨 PREZ](#-prez-présentation-release)
  - [💿 BD Info](#-bd-info)
- [Structure](#-structure)
- [Changelog](#-changelog)

---

## 🎯 Présentation

**REBiRTH AIO** est une application desktop tout-en-un qui automatise le workflow complet de release : du remux Blu-ray à la notification Discord, en passant par la création de torrents et la gestion seedbox.

| Fonctionnalité | Description |
|---|---|
| 📀 **Full BD** | Sauvegarde FULL BLURAY depuis le lecteur optique via MakeMKV (`backup --decrypt`), sortie dans `remux_tool/FULL/` — recherche TMDB intégrée pour auto-remplir le nom du dossier (format 1080p / 2160p) |
| 🔄 **Remux** | Extraction ISO/BDMV → MKV via MakeMKV + MKVToolNix, sélection des pistes (vidéo/audio/subs), tag VF automatique, nommage REBiRTH |
| 📄 **NFO** | Génération automatique UTF-8 + CP437 |
| 🎬 **TMDB** | Recherche avec confirmation et changement d'ID |
| ☁️ **Upload** | Gofile (failover 7 serveurs) ou BuzzHeavier |
| 💬 **Discord** | Notification automatique avec embed TMDB |
| 📁 **FINAL/** | Création automatique avec le bon NFO par tracker (nom de fichier sans tag encodage) |
| 🌱 **Seedbox** | Upload complet via FTP TLS |
| 🧲 **Torrent SB** | Création torrent via SSH+mktorrent côté seedbox, chargement automatique dans ruTorrent |
| 🎨 **PREZ** | Génération de fiche de présentation HTML pour tracker — specs vidéo/audio/subs auto-remplies, screenshots uploadés sur ImgBB (350×197 px), aperçu en temps réel |
| 💿 **BD Info** | Rapport exact via **BDInfo v0.7.5.6** (Wine/Whisky) — DISC INFO/VIDEO/AUDIO/SUBTITLES, upload ZIP vers Gofile ou BuzzHeavier |
| 🗂️ **Fichiers SB** | Explorateur de fichiers seedbox — navigation dans les sous-dossiers, suppression via SSH sudo |
| 🎛️ **Trackers** | Page dédiée pour gérer les announces URL (ABN · TOS · C411 · Torr9 · HDT · HDF · HDO) |
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

TRACKER_HDT=https://hdts-announce.ru/announce.php?passkey=PASSKEY
TRACKER_HDF=https://tracker.hdf.world:2443/PASSKEY/announce
TRACKER_HDO=http://hd-only.org:2710/PASSKEY/announce
SFTP_PATH_HDT=/home/rtorrent/rtorrent/download/FULL BD

# ── BD Info ───────────────────────────
BDINFO_WIN_EXE=/chemin/vers/BDInfo.exe   # requis pour l'onglet BD Info
# BDINFO_WINE_TIMEOUT=1800               # timeout max en secondes (défaut 30 min)

# ── PREZ ──────────────────────────────
IMGBB_API_KEY=ta_cle_imgbb               # upload screenshots → imgbb.com/api
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
Workflow Full BD (Disque → FULL BLURAY)
─────────────────────────────────────────────
Onglet 📀 FULL BD
        │
        ▼
Insérer le disque Blu-ray dans le lecteur externe
⟳ Détecter le lecteur → lecteur détecté avec titre du disque
        │
        ▼
🔍 Rechercher le film (TMDB) → sélectionner dans le dropdown
  └─ Choisir 1080p ou 2160p → nom du dossier auto-formaté
  (ou renseigner / ajuster le nom manuellement)
        │
        ▼
▶ LANCER LE BACKUP
  └─ [MakeMKV]  makemkvcon backup --decrypt disc:X → remux_tool/FULL/<nom>/
     Barre de progression globale + console live + annulation possible
        │
        ▼
Dossier BDMV complet dans remux_tool/FULL/ → prêt pour l'onglet Remux

─────────────────────────────────────────────
Workflow Remux (ISO/BDMV → MKV)
─────────────────────────────────────────────
Onglet 🔄 REMUX
        │
        ▼
Placer l'ISO ou le dossier BDMV dans remux_tool/FULL/
  (ou utiliser directement la sortie de l'onglet Full BD)
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
Cocher les trackers : ABN / TOS / C411 / Torr9 / HDF / HDO
        │
        ▼
Choisir type NFO : UTF-8 (C411 · Torr9 · HDF · HDO)
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
Workflow PREZ (Fiche de présentation tracker)
─────────────────────────────────────────────
Onglet 🎨 PREZ
        │
        ▼
Charger le .mkv depuis FILMS/ → specs vidéo/audio/subs auto-remplies
        │
        ▼
📸 4 SCREENS (FILMS/) → extraction automatique → aperçu des captures
        │
        ▼
☁ UPLOAD IMGBB → resize 350×197 px + upload → liens insérés dans la fiche
        │
        ▼
Aperçu HTML en temps réel de la présentation complète
  └─ Sections : TMDB · Spécifications techniques · Screenshots · Release

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

### 📀 Full BD
- Sauvegarde FULL BLURAY depuis le lecteur optique, sans passer par MakeMKV manuellement
- Détection automatique des lecteurs avec le titre du disque (`makemkvcon -r info disc:9999`)
- Backup complet avec déchiffrement : `makemkvcon backup --decrypt disc:X`
- Sortie directement dans `remux_tool/FULL/` — enchaînement immédiat avec l'onglet Remux
- Barre de progression globale (basée sur `tot`), console MakeMKV live, annulation en cours de backup
- 🔍 **Recherche TMDB intégrée** : tape le nom du film, sélectionne dans le dropdown (poster + année) → nom du dossier auto-formaté
- 🔘 **Toggle 1080p / 2160p** :
  - `1080p` → `Nom.Année.FRA.COMPLETE.BLURAY-REBiRTH`
  - `2160p` → `Nom.Année.FRA.COMPLETE.UHD.BLURAY-REBiRTH`

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

### 🎨 PREZ (Présentation release)
- Génération d'une fiche de présentation HTML complète (aperçu en temps réel)
- Remplissage automatique : titre TMDB, synopsis, specs vidéo/audio/sous-titres
- Source affichée sans résolution (nom seul)
- 📸 **Screenshots** : bouton "4 SCREENS (FILMS/)" → extraction automatique depuis `FILMS/` → `PICS/`
- ☁️ **Upload ImgBB** : upload des screenshots redimensionnés 350×197 px, clé API persistante
- Sections ordonnées : TMDB · Spécifications techniques · Screenshots · Release

### 📄 Type NFO
- **UTF-8** → `(UTF8).nom.nfo` pour C411, Torr9, HDF, HDO
- **CP437** → `(CP437).nom.nfo` pour TOS, ABN

### ☁️ Gofile
- Upload anonyme, failover automatique sur 7 serveurs

### ☁️ BuzzHeavier
- Recommandé pour les fichiers > 10 GB
- Progression réelle : %, vitesse MB/s, temps écoulé

### 🌱 Seedbox FTP
- Upload automatique du dossier FINAL via FTP TLS

### 💬 Discord
- **REBiRTH** — 7 trackers (TOS / ABN / C411 / Torr9 / HDF / HDO), webhook REBiRTH
- **FULL BD** — HDT + HDF + HDO, webhook séparé

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
│                                  inclut : onglets Upload, BD Info, Full BD, Seedbox…
├── gui_index.html              ← Frontend HTML/CSS/JS (interface complète)
├── gofile.py                   ← Module upload Gofile (failover 7 serveurs)
├── V1.env                      ← Configuration (ne pas commiter — gitignored)
├── REBiRTH.command             ← Lanceur macOS (double-clic)
├── REBiRTH.bat                 ← Lanceur Windows (double-clic)
├── NFO_CUSTOM/                 ← Générateur NFO (TMDB, templates, helpers)
├── BDInfo_v0/                  ← BDInfo v0.7.5.6 (BDInfo.exe + DLLs — non commité)
├── remux_tool/                 ← Outil Remux + Full BD (onglets intégrés)
│   ├── gui.py                  ← Backend remux (API PyWebView)
│   ├── makemkv_extract.py      ← Extraction MakeMKV (utilisé par Remux et Full BD)
│   ├── mediainfo_parse.py      ← Analyse des pistes MediaInfo/ffprobe
│   ├── mkvtoolnix_remux.py     ← Remux MKVMerge
│   ├── config.py               ← Configuration (dossiers, options)
│   ├── FULL/                   ← Sources ISO/BDMV + sorties Full BD (non commité)
│   └── MAKEMKV_KEY.txt         ← Clé beta MakeMKV
├── FILMS/                      ← .mkv finaux (remux → ici, puis upload bot)
├── PICS/                       ← Screenshots extraits par l'onglet Remux
│   └── Nom Du Film/            ← 4 captures par film
├── FINAL/                      ← Sortie upload (MKV + NFO sans tag encodage)
├── TORRENTS/                   ← Fichiers .torrent par tracker
└── BDINFO/                     ← Rapports BD Info (.txt + .nfo)
```

---

## 📝 Changelog

### v2.9.8
- Feat (CUSTOM) : **onglet CUSTOM muxer** — détection automatique des pistes depuis les fichiers MKV/SRT du dossier `CUSTOM/`, configuration par piste (langue, nom, forced, default, inclure/exclure), bitrate audio affiché via pymediainfo (`@ XXXX kbps`), classification automatique des sous-titres (FORCED / SDH / FULL / COMMENTARY) portée depuis le moteur remux, détection VF (VFF / VFQ / VFi / VOF) depuis le nom de la piste source
- Feat (CUSTOM) : **aperçu NFO** (bouton 👁 NFO) — prévisualisation du NFO final dans la section CUSTOM avant muxage, basée sur la config pistes en cours ; séparé du NFO réel généré par `NFO_v1_7.py`
- Fix (CUSTOM) : duplication du tag de langue dans le nom de sortie lors des renommages successifs — `_cstFinalizeOutputName` repart désormais toujours du nom vidéo original stocké dans `window._cstVideoBaseName`
- Fix (CUSTOM) : titres des pistes affichaient les noms de la team source — désormais ignorés, noms générés entièrement côté outil
- Tracker : **TORR9 fusionné avec TR4KER** — toutes les références `TORR9` remplacées par `TR4KER` (`app.py`, `gui_index.html`, `PREDB/`, `DISCORD/`, `notif_upload_discord.py`) ; announce URL à renseigner dans `V1.env`
- Seedbox : configuration vidée (`SFTP_HOST/USER/PASS/PATH`, ruTorrent) — structure conservée pour la prochaine seedbox

### v2.9.7
- Feat (BD Info) : **upload Seedbox découplé de la création des torrents** — un seul bouton « ↑ SB UPLOAD » envoie le dossier FULL BD une seule fois ; les boutons HDT / HDF / HDO ne font plus que créer le `.torrent` depuis ce dossier déjà sur la SB (plus de triple ré-upload du même contenu)
- Feat (Discord) : nouveau salon **« à faire »** dédié — les notifications d'upload Gofile/BuzzHeavier (REMUX et tout nom non reconnu) partent désormais sur ce salon (`WEBHOOK_TODO_URL`) au lieu de `#remux`, qui restait encombré par les releases déjà traitées. WEB et BluRay Rip gardent leur salon dédié, inchangé
- Fix (Discord) : retrait du ping `@everyone` sur les notifications de statut d'upload (mode REBiRTH, statut des 7 trackers) — l'embed part toujours, mais sans notifier tout le serveur
- Chore : synchronisation du numéro de version (`version_win.txt`, `build_mac.spec`) qui était resté bloqué sur 2.8.3 alors que le badge/changelog étaient déjà à 2.9.6

### v2.9.6
- Feat (Discord) : **guide de nommage REBiRTH enrichi** — placement du tag `[CUSTOM]`, règles REPACK / éditions (`THEATRICAL.CUT`, `EXTENDED.CUT`, `DIRECTOR'S.CUT`, `UNRATED`, `UNCENSORED`, `REMASTERED`), titrage des pistes audio MULTi/VO clarifié (langues réelles : Français / Anglais / Japonais…) — guide complet `REBIRTH_NAMING_GUIDE.md` désormais joint en pièce jointe au message Discord
- Feat (Discord/Upload) : **routage automatique des notifications par salon** — détection du type de release depuis le champ Source (REMUX → salon REMUX, WEB → salon WEB, BluRay seul → salon BluRay Rip), avec priorité REMUX pour ne pas confondre un `BluRay REMUX` avec un `BluRay Rip`
- Feat (Config) : ajout des webhooks dédiés `WEBHOOK_WEB_URL` et `WEBHOOK_BLURAYRIP_URL`
- Feat (Discord) : **mode « Saisie manuelle »** sur la page de notification Discord — permet de chercher un film via TMDB et de saisir le nom de la release à la main quand le fichier n'est pas présent dans la seedbox

### v2.9.5
- Fix (Remux) : détection FORCED des sous-titres — le flag `Forced` de MediaInfo n'est plus pris pour argent comptant si l'`ElementCount` dépasse 800 (certains BDs taguent un FULL comme Forced à tort)
- Fix (Remux) : classification FORCED/FULL/SDH (cas 3+ pistes) — comparaison désormais faite par rapport au 2e plus gros élément (au lieu du plus gros), plus robuste quand la piste forcée fait 25-35 % de la suivante
- Fix (Remux) : sélection de la piste audio "de référence" (codec/canaux affichés dans le nom final) — prend désormais la piste avec le plus gros débit/canaux toutes langues confondues, au lieu de la première piste FR (évite une 2.0 alors qu'une 5.1 existe)
- Feat (Full BD/PREZ) : nouvelle méthode `prez_detect_full_source()` — détection automatique du nom du groupe source depuis le dossier dans `FULL/` (tout ce qui suit le dernier `-`)

### v2.9.4
- Feat (Trackers) : **ajout HDF (HDForever) + HDO (HD-Only)** — announces, SFTP seedbox, création torrent via SSH + mktorrent
- Feat (Full BD) : **HDT + HDF + HDO** en mode FULL BD — un seul bouton Discord, même canal, même webhook
- Feat (HDO) : piece size 16 MB (`-l 24`), source `"HD-Only"`, torrent privé — conformément aux règles du tracker
- Fix : **retrait complet du tracker LaCale** (fermeture définitive) — tous les fichiers nettoyés

### v2.9.3
- Feat (Full BD) : **recherche TMDB intégrée** dans l'onglet Full BD — barre de recherche avec debounce, dropdown résultats (poster + titre + année), sélection → nom du dossier auto-formaté
- Feat (Full BD) : **boutons 1080p / 2160p** pour choisir le format du nom de dossier
  - `1080p` → `Nom.Année.FRA.COMPLETE.BLURAY-REBiRTH`
  - `2160p` → `Nom.Année.FRA.COMPLETE.UHD.BLURAY-REBiRTH`
- Fix (Remux) : mapping langues ISO 639-1/639-2 étendu à 20 langues (it, pt, ja, ko, zh, ru, nl, pl, ar, hi, th, sv, no, da, fi, cs, hu, tr, uk, he)

### v2.9.2
- Fix (NFO) : ligne FORMAT recentrée (`center(79)`) — était passée en `ljust` par erreur
- Fix (NFO) : ligne vide bordée `█...█` conservée après TMDB quand il n'y a pas de note (plus de saut de ligne non bordé)
- Fix (PREZ) : suppression du doublon `kb/s` dans l'aperçu HTML (le backend l'incluait déjà)
- Fix (PREZ) : erreurs upload affichées en persistant dans un div dédié (plus seulement en toast)
- Fix (PREZ) : crash silencieux `errBox` avant le bloc try corrigé (null-check déplacé à l'intérieur)
- Fix (PREZ) : SOURCE affiche uniquement le nom de la source, sans la résolution
- Fix (Full BD) : barre de progression globale — utilise `tot` (global) au lieu de `cur` (par fichier, se remettait à 0)
- Feat (PREZ) : remplacement de imgbox par **ImgBB** — API fiable, upload base64, clé API persistante dans `V1.env`
- Feat (PREZ) : upload ImgBB avec **resize automatique 350×197 px** (Pillow LANCZOS) avant envoi
- Feat (PREZ) : clé API ImgBB configurable depuis l'interface (modal dédié, indicateur de statut)
- Feat (PREZ) : auto-login imgbox au chargement si session déjà sauvegardée (maintenu en parallèle)
- Feat (PREZ) : bouton **📸 4 SCREENS (FILMS/)** — extraction automatique depuis `FILMS/` → `PICS/` → chargement auto dans le panneau
- Feat (PREZ) : section Screenshots déplacée après Spécifications techniques dans la fiche

### v2.9.1
- Fix (Seedbox) : `list_seedbox_files` et `list_seedbox_files_hdt` utilisaient `paramiko.Transport` sans timeout → pouvait accrocher indéfiniment. Remplacé par `SSHClient.connect(timeout=8)` — cohérent avec `get_seedbox_space`
- Fix (Remux/MakeMKV) : ajout du flag `-r` (robot mode) pour un parsing fiable de la sortie MakeMKV ; détection de l'erreur espace disque insuffisant (MSG:2018 / "No space left on device") avec message clair
- Fix (Remux/MakeMKV) : recherche récursive du MKV extrait (glob `**/*.mkv`) en cas de sous-dossier inattendu ; sélection du fichier le plus volumineux en cas de multiples résultats

### v2.9.0
- Feat : **onglet Full BD** — générateur de FULL BLURAY via MakeMKV
  - Détection automatique du lecteur optique (`makemkvcon -r info disc:9999`)
  - Backup complet avec déchiffrement (`makemkvcon backup --decrypt`)
  - Sortie directement dans `remux_tool/FULL/` prête pour l'onglet Remux
  - Barre de progression + console live + annulation
- Fix (Remux) : matching des pistes audio/subs par `StreamOrder` MediaInfo = `id` mkvmerge — corrige le décalage quand plusieurs pistes ont la même langue
- Fix (Remux) : piste audio `Default: Yes` correctement assignée (VFF ou EN selon priorité)
- Fix (Remux) : dossier d'entrée BD Info → `remux_tool/FULL/` au lieu de `FILMS/`
- Fix : NFO envoyé sur la seedbox sans tag `(UTF8)`/`(CP437)` dans le nom de fichier

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
- L'onglet **Full BD** nécessite : **MakeMKV** installé et accessible dans le PATH
- L'onglet **Remux** nécessite : **MakeMKV**, **MKVToolNix**, **MediaInfo**, **ffmpeg** (voir INSTALL_WINDOWS.md)
- **BD Info** nécessite BDInfo v0.7.5.6 + Whisky (macOS) ou `BDInfo_v0\` (Windows)
- **Torrent SB** nécessite un accès SSH port 22 et `mktorrent` installé sur la seedbox
- Trackers supportés : ABN · TOS · C411 · Torr9 · HDT · HDF · HDO

---

<div align="center">

**REBiRTH AIO v2.9.8** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
