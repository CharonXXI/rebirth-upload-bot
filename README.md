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
[![Version](https://img.shields.io/badge/Version-2.5.9-FFA500?style=for-the-badge)](.)
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
| 🧲 **Torrent SB** | ⚠️ *En attente — non fonctionnel actuellement* — création côté seedbox via plugin ruTorrent |
| 💿 **BD Info** | Scan COMPLETE BLURAY via BDInfoCLI — rapport DISC INFO/VIDEO/AUDIO/SUBTITLES, upload ZIP vers Gofile ou BuzzHeavier |
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

#### BDInfoCLI (optionnel — pour l'onglet BD Info)

```bash
# Prérequis : .NET 8
brew install dotnet@8

# Cloner et compiler BDInfoCLI (fork tetrahydroc)
git clone https://github.com/zoffline/BDInfoCLI-ng.git ~/BDInfoCLI
cd ~/BDInfoCLI/BDInfo
dotnet build -c Release -r osx-arm64
```

> 💡 **MakeMKV** (facultatif mais recommandé) : si installé, le bot l'utilise pour identifier automatiquement le MPLS principal avant de lancer BDInfoCLI.

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

# ── BD Info (optionnel) ───────────────
# Chemin vers BDInfo.dll si non détecté automatiquement
# BDINFO_CLI_PATH=/chemin/vers/BDInfo.dll
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
| `SFTP_HOST` | URL du FileBrowser seedbox (ex: `https://files.seedbox.link`) |
| `RUTORRENT_URL` | URL complète de ruTorrent |
| `TRACKER_XXX` | Announce URL du tracker (avec passkey) |
| `BDINFO_CLI_PATH` | Chemin vers `BDInfo.dll` (détection auto si absent) |

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
Remplir Source / Note / Autre info
Cocher les trackers : ABN / TOS / C411 / Torr9 / LaCale
        │
        ▼
Choisir type NFO : UTF-8 → `(UTF8).nom.nfo` ou CP437 → `(CP437).nom.nfo`
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
        └─ [FTP]      Upload seedbox via FTP TLS

─────────────────────────────────────────────
Workflow BD Info (indépendant)
─────────────────────────────────────────────
Onglet BD INFO → Sélectionner dossier COMPLETE BLURAY
        │
        ▼
      SCANNER
        │
        ├─ [makemkvcon]   Identification MPLS principal (si installé)
        ├─ [BDInfoCLI]    Scan -m XXXXX.MPLS → rapport DISC INFO/VIDEO/AUDIO/SUBTITLES
        └─ Rapport filtré sauvegardé dans BDINFO/*.nfo
                           │
                           ▼
        Choisir BuzzHeavier / Gofile → ENVOYER
        └─ ZIP (dossier + NFO) uploadé en un seul fichier
```

> ⚠️ **Torrent SB** : la page est présente dans l'interface mais la fonctionnalité est actuellement **en attente / non fonctionnelle**. Les différentes méthodes de récupération du `.torrent` depuis ruTorrent n'ont pas abouti à une solution stable. À reprendre ultérieurement.

---

## ✨ Fonctionnalités

### 📄 Type NFO
- **UTF-8** → `(UTF8).nom.nfo` pour LaCale, C411, Torr9
- **CP437** → `(CP437).nom.nfo` pour TOS, ABN

### ☁️ Gofile
- Upload anonyme pour compatibilité maximale
- Failover automatique sur 7 serveurs
- MKV + NFO CP437 + NFO UTF-8 dans le même dossier

### ☁️ BuzzHeavier
- Recommandé pour les fichiers > 10 GB
- Progression réelle : %, vitesse MB/s et temps écoulé en temps réel

### 🌱 Seedbox FTP
- Upload automatique du dossier FINAL via FTP TLS
- Création automatique du sous-dossier `nom_film`

### 🧲 Torrent SB *(en attente — non fonctionnel)*
- Page dédiée à la création de torrents, indépendante du workflow Upload
- Sélectionne un dossier déjà présent sur la seedbox dans la liste FTP, ou saisie manuelle
- Les cases trackers se **synchronisent automatiquement** depuis la page Upload à l'ouverture
- Création côté seedbox via le plugin `create` de ruTorrent (hash serveur, aucun fichier local requis)
- Piece size **4 MiB**, flag **Privé** coché par défaut (modifiable)
- **⚠️ Actuellement non fonctionnel** — la récupération du fichier `.torrent` généré par ruTorrent n'est pas stable. Plusieurs méthodes testées (XML-RPC, FTP session, Filebrowser API, SFTP, streaming FTP local) sans résultat concluant. À reprendre ultérieurement.

### 💿 BD Info
- Onglet dédié pour les releases COMPLETE BLURAY
- Sélection du dossier source via Finder (détection automatique de `BDMV/`)
- **Identification MPLS** : `makemkvcon --robot info` (si MakeMKV installé) ou `BDInfoCLI --list` en fallback
- **Scan BDInfoCLI** : `-m XXXXX.MPLS` sur la playlist principale — rapport complet avec codecs, résolutions, langues, bitrates
- **Filtrage automatique** : seules les sections DISC INFO / PLAYLIST REPORT / VIDEO / AUDIO / SUBTITLES sont conservées
- **Rapport sauvegardé** dans `BDINFO/<nom>.nfo` (réécriture propre sur rescan)
- **Upload ZIP** : compresse le dossier COMPLETE BLURAY + NFO en un seul `.zip` (ZIP_STORED, rapide) et l'envoie vers BuzzHeavier ou Gofile

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
├── build_mac.spec          ← Spec PyInstaller macOS
├── INSTALL_WINDOWS.md      ← Guide installation Windows
├── NFO_CUSTOM/
│   ├── NFO_v1_7.py
│   ├── source_detector.py
│   └── tmdb_helper.py
├── FILMS/                  ← Déposer les .mkv ici
├── FINAL/                  ← Sortie (MKV + NFO par tracker)
├── TORRENTS/               ← Fichiers .torrent générés
└── BDINFO/                 ← Rapports BD Info (.nfo)
```

---

## 📝 Changelog

### v2.5.9
- Bump version 2.3.6 → 2.5.9 dans `build_mac.spec`, `version_win.txt`, `gui_index.html`
- Feat : **onglet BD Info complet** — scan COMPLETE BLURAY, rapport BDInfoCLI filtré (DISC INFO/VIDEO/AUDIO/SUBTITLES), upload ZIP vers Gofile/BuzzHeavier
- Feat : **identification MPLS intelligente** — `makemkvcon --robot info` détecte le titre principal (TINFO code 3, plus grand fichier), fallback sur `BDInfoCLI --list` si MakeMKV absent
- Feat : **upload ZIP BD Info** — compresse dossier film + NFO en `ZIP_STORED` (rapide, M2TS déjà compressé) ; upload en un seul fichier ; ZIP supprimé après upload
- Feat : **UI BD Info** — deux colonnes (gauche : scan + statut ; droite : NFO preview), toggle BuzzHeavier/Gofile + bouton ENVOYER, URL copiée dans le presse-papier
- Fix : **reset section upload au démarrage d'un nouveau scan** — les boutons et statut sont réinitialisés à chaque SCANNER
- Fix : **détection rapport sur rescan** — timestamp avant scan, détection par `mtime` (fix set-diff vide sur rescan du même film)
- Fix : **upload 400 BuzzHeavier** — exclusion des fichiers `.DS_Store`, `._*` et du dossier `BACKUP/` lors du rglob
- Fix : **output path BDInfoCLI** — passage du dossier `BDINFO/` (pas d'un chemin `.nfo`) comme 2e argument positionnel
- Fix : **OOM BDInfoCLI** — pipe `yes` vers stdin pour répondre automatiquement aux prompts "Continue scanning ?"
- Feat : **Méthode F Torrent SB** — création locale `.torrent` via streaming FTP SHA1 pièce par pièce (non concluant, en attente)

### v2.5.8
- Fix : **upload 400** — filtrage `.DS_Store` / `._*` / `BACKUP/` dans le ZIP
- Feat : **UI upload BD Info** — toggle BuzzHeavier/Gofile et bouton ENVOYER dédié (au lieu de cliquer sur le logo de la plateforme)

### v2.5.7
- Fix : **détection rapport sur rescan** — timestamp `scan_start` avant le scan, comparaison `mtime >= scan_start - 2` au lieu du set-diff

### v2.5.6
- Fix : **section upload non réinitialisée** entre deux scans — `bdiScan()` remet à zéro le bouton ENVOYER et le statut upload

### v2.5.5
- Feat : **upload BD Info inclut le dossier film complet** (`rglob` du dossier COMPLETE BLURAY) + NFO dans le ZIP

### v2.5.4
- Feat : **upload BD Info** — envoi du `.nfo` seul vers Gofile ou BuzzHeavier avec affichage URL

### v2.5.3
- Revert : **retour à la version v2.5.0** — suppression des patches bitrates (ffprobe + filesystem) qui ne corrigeaient pas le problème OOM

### v2.5.2
- Tentative fix bitrates à 0 : patch taille/bitrate depuis filesystem + ffprobe (revert en v2.5.3)

### v2.5.1
- Tentative fix bitrates à 0 : suppression des limites GC .NET (revert en v2.5.3)

### v2.5.0
- Fix : **filtrage rapport** — `.txt` source filtré également (pas seulement le `.nfo`) + fix tracking `src_file`

### v2.4.9
- Feat : **filtrage rapport BDInfoCLI** — extraction des sections DISC INFO → SUBTITLES uniquement (stop avant FILES:, CHAPTERS:, STREAM DIAGNOSTICS:)

### v2.4.8
- Fix : **output path BDInfoCLI** — passage du dossier (pas du chemin `.nfo`) comme 2e argument

### v2.4.7
- Feat : **flow makemkvcon → BDInfoCLI** — `makemkvcon --robot info` identifie le MPLS principal (TINFO code 3, titre avec la plus grande taille code 10), puis `BDInfoCLI -m XXXXX.MPLS` scanne uniquement cette playlist

### v2.4.6
- Feat : **makemkvcon comme méthode principale** d'identification du MPLS (avant BDInfoCLI --list)

### v2.4.5
- Fix : **lecture du fichier rapport** généré par BDInfoCLI au lieu de lire stdout (qui est vide en mode fichier)

### v2.4.4
- Fix : **format argument `-m`** — `00003.MPLS` au lieu de `00003` (BDInfoCLI attend le nom de fichier avec extension)

### v2.4.3
- Feat : **auto-sélection playlist principale** via `BDInfoCLI --list` puis scan avec `-m`

### v2.4.2
- Fix : **réponse automatique aux prompts OOM** de BDInfoCLI — pipe `yes` vers stdin

### v2.4.1
- Fix : **éviter l'OOM sur `-w`** (scan complet) — utilisation de `--list` puis `-m` sur la playlist principale uniquement

### v2.4.0
- Feat : **séparation des canaux** — `bdinfo_status` (debug, colonne gauche) vs `bdinfo_output` (contenu NFO, colonne droite)
- Fix : **erreur exit code -9** (SIGKILL OOM) interceptée proprement

### v2.3.9
- Fix : **layout BD Info** — correction des colonnes left/right
- Fix : **OutOfMemoryException** BDInfoCLI interceptée

### v2.3.8
- Feat : **layout BD Info en deux colonnes** — gauche statut debug, droite preview NFO

### v2.3.7
- Feat : **onglet BD Info** — intégration BDInfoCLI, scan COMPLETE BLURAY, sauvegarde `.nfo`

### v2.3.6
- Feat : **Méthode F Torrent SB** — tentative création locale `.torrent` via streaming FTP (calcul SHA1 pièce par pièce sans chargement en mémoire) — non concluant

### v2.3.5
- Fix Torrent SB : XML escape + mktorrent direct + répertoire `tmp/`

### v2.3.4
- Fix Torrent SB : `directory.default` + `d.tied_to_file` + `/bin/sh -c` dans execute

### v2.3.3
- Fix Torrent SB : NLST debug + fallback Filebrowser API pour download `.torrent`

### v2.3.2
- Fix Torrent SB : `chmod 644` après `cp` pour corriger les permissions FTP

### v2.3.1
- Fix Torrent SB : format `execute.nothrow.bg` + fallback FTP session

### v2.3.0
- Feat Torrent SB : **méthode XML-RPC execute + FTP** (Method B) — `execute.nothrow.bg` pour copier le `.torrent` depuis le dossier session vers un chemin FTP accessible
- Cascade mise à jour : A) HTTP plugin → B) XML-RPC exec + FTP → C) Filebrowser API → D) SFTP paramiko → E) FTP tasks

### v2.2.9
- Fix Torrent SB : **découverte automatique du chemin `tasks/`** dans Filebrowser — test de plusieurs chemins candidats quelle que soit la racine chroot

### v2.2.8
- Fix Torrent SB : **méthode Filebrowser API** — `POST /api/login` + `GET /api/raw/...` depuis `SFTP_HOST`
- Cascade : A) HTTP plugin → B) Filebrowser API → C) SFTP paramiko → D) FTP tasks

### v2.2.7
- Fix Torrent SB : **HTTP bail rapide** — abandon après 3 réponses `[]` vides
- Fix Torrent SB : **auto-install `paramiko`** via pip si absent

### v2.2.6
- Fix Torrent SB : **cascade HTTP/SFTP/FTP** — le répertoire `config/` étant inaccessible via FTP, ajout SFTP (paramiko) et FTP tasks (`RUTORRENT_TASKS_PATH`)
- Ajout variables opt. `SFTP_SSH_PORT` et `RUTORRENT_TASKS_PATH`

### v2.2.5
- Fix Torrent SB : **stratégie récupération `.torrent` entièrement repensée** — snapshot `tasks/` + poll FTP toutes les 5 s jusqu'à `temp.torrent` valide (timeout 10 min)

### v2.2.4
- Fix Torrent SB : **navigation FTP itérative** — skip des N premiers composants du chemin absolu pour trouver le chemin relatif depuis la racine chroot

### v2.2.3
- Fix Torrent SB : **FTP chroot** — navigation dossier par dossier au lieu du chemin absolu
- Fix : log des réponses HTTP + endpoint `/export/HASH.torrent`

### v2.2.2
- Fix Torrent SB : **`-506 Method not defined`** — abandon `d.multicall2` ; stratégie `download_list` → `system.multicall(d.name)` → match nom → `session.path` + FTP

### v2.2.1
- Fix Torrent SB : **XML-RPC `-503 Wrong object type`** — méthodes `d.multicall` avec `<param>` séparés

### v2.2.0
- Fix Torrent SB : **parsing XML-RPC** corrigé via `xmlrpc.client.loads()` (stdlib Python)
- Fix : recherche torrent par nom dans ruTorrent (match exact puis partiel)

### v2.1.9
- Fix Torrent SB : **logs de diagnostic complets**
- Fix : `_tsbRunning` bloqué → auto-reset au prochain clic

### v2.1.8
- Fix Torrent SB : **récupération du `.torrent` via XML-RPC** après création
- Le `.torrent` est **systématiquement sauvegardé** dans `TORRENTS/`

### v2.1.7
- Refactor : **création de torrents retirée du workflow Upload** — exclusivement via la page Torrent SB

### v2.1.6
- Feat : **sauvegarde `.torrent` en local** dans `TORRENTS/`
- Feat : **sync trackers Upload → Torrent SB** à l'ouverture de la page

### v2.1.5
- Feat : **torrent privé coché par défaut**, piece size 4 MiB
- Feat : **sauvegarde automatique du `.torrent`** dans `TORRENTS/`

### v2.1.4
- Feat : **mode TORRENT SB** — création des torrents directement depuis la seedbox via le plugin `create` de ruTorrent

### v2.1.3
- Feat : **logo animé**, **badges trackers colorés**, **transitions de page**, **toast notifications**

### v2.1.2
- Champ **Trackers** remplacé par cases à cocher (ABN / TOS / C411 / Torr9 / LaCale)
- Mode **NFO Seulement** simplifié

### v2.1.1
- Fix : mode jour lisible
- Fix : NFO preview couleur thème
- Feat : page **Stats**

### v2.1.0
- **Barre de progression réelle** : Gofile, BuzzHeavier et seedbox FTP
- **Mode NFO Batch** : traitement de plusieurs fichiers en file d'attente
- **Historique — Recherche** et **Statistiques**

### v2.0.9
- Mode **jour/nuit** avec persistance via `theme.txt`

### v2.0.8
- Page **Historique** avec `history.json`

### v2.0.7
- Compatibilité Windows complète

### v2.0.6
- Création automatique des `.torrent` + envoi ruTorrent via XML-RPC
- Page Trackers

### v2.0.5
- Upload seedbox FTP TLS + dossier FINAL/

### v2.0.4
- TMDB confirmé avant NFO, temps écoulé BuzzHeavier

### v2.0.0
- Release initiale PyWebView, failover Gofile 7 serveurs

---

## 💡 Notes

- Pour les fichiers > 10 GB, BuzzHeavier est plus stable que Gofile
- Le bot empêche automatiquement la mise en veille pendant l'upload
- Le `V1.env` n'est jamais publié sur GitHub
- BD Info nécessite BDInfoCLI compilé en local (voir section Installation)
- Torrent SB est présent dans l'interface mais **non fonctionnel** — à reprendre ultérieurement

---

<div align="center">

**REBiRTH Upload Bot v2.5.9** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
