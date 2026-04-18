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
| 🧲 **Torrent SB** | Création côté seedbox via plugin ruTorrent (hash SB), .torrent sauvegardé dans `TORRENTS/` |
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
                           │
                           ▼
              Aller sur page Torrent SB
                           │
        └─ [TORRENT SB]  Creation torrents via plugin ruTorrent
                          Seeding démarre immédiatement
                          .torrent sauvegardé dans TORRENTS/

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

### 🧲 Torrent SB
- Page dédiée à la création de torrents, indépendante du workflow Upload
- Sélectionne un dossier déjà présent sur la seedbox dans la liste FTP, ou saisie manuelle
- Les cases trackers se **synchronisent automatiquement** depuis la page Upload à l'ouverture
- Création côté seedbox via le plugin `create` de ruTorrent (hash serveur, aucun fichier local requis)
- Piece size **4 MiB**, flag **Privé** coché par défaut (modifiable)
- Seeding démarre immédiatement sur ruTorrent
- Le fichier `.torrent` binaire retourné par le plugin est sauvegardé dans `TORRENTS/`

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
- Feat : **onglet BD Info complet** — scan COMPLETE BLURAY, rapport BDInfoCLI filtré (DISC INFO/VIDEO/AUDIO/SUBTITLES), upload ZIP vers Gofile/BuzzHeavier
- Feat : **identification MPLS intelligente** — `makemkvcon --robot info` détecte le titre principal (TINFO code 3), fallback sur `BDInfoCLI --list` si MakeMKV absent
- Feat : **upload ZIP BD Info** — compresse dossier film + NFO en `ZIP_STORED` (rapide, M2TS déjà compressé) et upload en un seul fichier ; ZIP supprimé après upload
- Feat : **UI BD Info** — deux colonnes (gauche : scan + statut ; droite : NFO preview), toggle BuzzHeavier/Gofile + bouton ENVOYER, URL copiée dans le presse-papier
- Fix : **détection rapport sur rescan** — timestamp avant scan pour trouver les fichiers modifiés (fix set-diff vide sur rescan même film)
- Fix : **output path BDInfoCLI** — passe le dossier `BDINFO/` (pas un chemin `.nfo`) comme 2e argument positionnel
- Fix : **OOM BDInfoCLI** — pipe `yes` vers stdin pour répondre automatiquement aux prompts "Continue scanning ?"
- Feat : **Méthode F Torrent SB** — création locale `.torrent` via streaming FTP (calcul SHA1 pièce par pièce sans chargement en mémoire)

### v2.3.0
- Nouveau : **méthode XML-RPC execute + FTP** (Method B) — utilise `execute.nothrow.bg` via l'interface XML-RPC de rtorrent pour copier le `.torrent` depuis le dossier session (inaccessible via FTP) vers `rtorrent/` (accessible via FTP), puis le télécharge en FTP TLS. Aucune dépendance externe supplémentaire.
- Cascade mise à jour : A) HTTP plugin (bail rapide) → **B) XML-RPC exec + FTP** → C) Filebrowser API → D) SFTP paramiko → E) FTP tasks (si `RUTORRENT_TASKS_PATH` configuré)
- La méthode B trouve le hash rtorrent par nom (`download_list` + `system.multicall(d.name)`), dérive le home depuis `session.path`, exécute un `cp` via rtorrent, et nettoie le fichier temporaire après récupération

### v2.2.9
- Fix : **découverte automatique du chemin tasks/ dans Filebrowser** — liste la racine FB et teste plusieurs chemins candidats (skip de 0 à N préfixes) pour trouver `config/rutorrent/share/users/{user}/settings/tasks/` quelle que soit la racine chroot du Filebrowser

### v2.2.8
- Fix : **méthode Filebrowser API** — `SFTP_HOST` (URL du Filebrowser seedbox) est utilisé pour lister les tâches et télécharger `temp.torrent` via `POST /api/login` + `GET /api/raw/...`. Aucune dépendance supplémentaire.
- Fix : cascade mise à jour : A) HTTP plugin (bail rapide) → B) Filebrowser API → C) SFTP paramiko → D) FTP tasks (si `RUTORRENT_TASKS_PATH` configuré)
- SSH host = même que FTP host (`SFTP_HOST_FTP`), port configurable via `SFTP_SSH_PORT` (défaut 22)

### v2.2.7
- Fix : **HTTP API bail rapide** — si le plugin create retourne `[]` vide 3 fois de suite, abandon immédiat (le plugin ne supporte pas le GET) pour passer directement à SFTP
- Fix : **auto-install paramiko** — si `paramiko` n'est pas installé, le bot l'installe automatiquement via `pip` avant la tentative SFTP

### v2.2.6
- Fix : **`config/` inaccessible via FTP** — le répertoire tasks/ de ruTorrent est chroot-bloqué pour le FTP. Nouvelle cascade de récupération :
  - **A) HTTP GET** sur `plugins/create/action.php` — poll le statut des tâches et télécharge quand terminé (aucun FTP requis)
  - **B) SFTP (SSH)** via `paramiko` — accès direct au filesystem sans restriction chroot
  - **C) FTP tasks/** — fallback si `RUTORRENT_TASKS_PATH` est configuré manuellement dans le .env
- Ajout variable d'env optionnelle `SFTP_SSH_PORT` (défaut 22) pour le port SSH
- Ajout variable d'env optionnelle `RUTORRENT_TASKS_PATH` pour chemin FTP custom

### v2.2.5
- Fix : **stratégie de récupération du .torrent entièrement repensée** — snapshot tasks/ avant création, poll FTP toutes les 5 s jusqu'à `temp.torrent` valide (timeout 10 min)
- Suppression de toute la logique XML-RPC devenue inutile

### v2.2.4
- Fix : **FTP session path** — navigation itérative avec reconnexion FTP ; skip des N premiers composants du chemin absolu jusqu'à trouver le chemin relatif correct depuis la racine chroot

### v2.2.3
- Fix : **FTP chroot** — navigation dossier par dossier au lieu du chemin absolu
- Fix : log du contenu des réponses HTTP pour identifier l'endpoint correct
- Ajout endpoint `/export/HASH.torrent` dans les tentatives HTTP

### v2.2.2
- Fix : **`-506 Method not defined`** — abandon de `d.multicall`/`d.multicall2` ; nouvelle stratégie : `download_list` → `system.multicall(d.name)` → match nom → `session.path` + FTP
- Fallback `d.name` individuel si `system.multicall` échoue

### v2.2.1
- Fix : **XML-RPC `-503 Wrong object type`** — `d.multicall` avec méthodes comme `<param>` séparés

### v2.2.0
- Fix : **parsing XML-RPC corrigé** — utilisation de `xmlrpc.client.loads()` (stdlib Python)
- Fix : **recherche par nom** dans ruTorrent — match exact puis fallback partiel
- Fix : délai augmenté à 5 s pour laisser rtorrent terminer le hashing

### v2.1.9
- Fix : **logs de diagnostic complets** dans Torrent SB
- Fix : **`_tsbRunning` bloqué** — auto-resetté au prochain clic

### v2.1.8
- Fix : **récupération du .torrent via XML-RPC** après création
- Le fichier `.torrent` est maintenant **systématiquement sauvegardé** dans `TORRENTS/`

### v2.1.7
- Refactor : **création de torrents retirée du workflow Upload** — exclusivement via la page Torrent SB

### v2.1.6
- Feat : **sauvegarde .torrent en local** dans `TORRENTS/`
- Feat : **sync trackers Upload → Torrent SB**

### v2.1.5
- Feat : **torrent privé coché par défaut**, piece size 4 MiB
- Feat : **sauvegarde automatique du .torrent** dans `TORRENTS/`

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

---

<div align="center">

**REBiRTH Upload Bot v2.5.9** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
