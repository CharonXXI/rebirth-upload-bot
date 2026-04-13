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
[![Version](https://img.shields.io/badge/Version-2.1.9-FFA500?style=for-the-badge)](.)
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
| `SFTP_HOST` | URL du FileBrowser seedbox (ex: `https://files.seedbox.link`) |
| `SFTP_HOST_FTP` | Host FTP de ta seedbox |
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

### v2.1.9
- Fix : **logs de diagnostic complets** dans Torrent SB — URL, params, réponse HTTP, trackers actifs affichés dans le panel de log
- Fix : **erreurs silencieuses** — les exceptions sont maintenant loggées dans le panel avant d'être émises
- Fix : **`_tsbRunning` bloqué** — si le flag reste coincé après un crash, il est auto-resetté au prochain clic

### v2.1.8
- Fix : **récupération du .torrent via XML-RPC** — le plugin `create` de ruTorrent ne retourne pas toujours le binaire dans sa réponse ; après création, le bot cherche le torrent par nom via XML-RPC, récupère son hash et télécharge le `.torrent`
- Le fichier `.torrent` est maintenant **systématiquement sauvegardé** dans `TORRENTS/`

### v2.1.7
- Refactor : **création de torrents retirée du workflow Upload** — l'upload s'arrête après l'envoi FTP sur la seedbox, la création des torrents se fait exclusivement via la page Torrent SB

### v2.1.6
- Feat : **sauvegarde .torrent en local** dans `TORRENTS/` à côté du bot (plus de FTP pour ça)
- Feat : **sync trackers Upload → Torrent SB** — les cases cochées dans Upload sont automatiquement reproduites en ouvrant la page Torrent SB

### v2.1.5
- Feat : **torrent privé coché par défaut** dans la page Torrent SB (checkbox visible, modifiable)
- Feat : **taille de pièces fixée à 4 MiB** pour tous les torrents créés via ruTorrent
- Feat : **sauvegarde automatique du .torrent** dans `TORRENTS/` si le plugin retourne le binaire
- Refactor : `_create_torrent_rutorrent` accepte le flag `private` en paramètre (défaut `True`)

### v2.1.4
- Feat : **mode TORRENT SB** — création des torrents directement depuis la seedbox via le plugin `create` de ruTorrent, sans fichier local nécessaire
- Chemin distant auto-rempli depuis le nom du fichier, modifiable manuellement
- Fonctionne pour les fichiers déjà présents sur la seedbox (usage partagé)

### v2.1.3
- Feat : **logo animé** — le `●` dans la sidebar pulse en continu
- Feat : **badges trackers colorés** dans l'historique (ABN=bleu, TOS=vert, C411=violet, Torr9=orange, LaCale=rose)
- Feat : **transitions de page** — fondu + slide-up entre les pages (0.18s)
- Feat : **toast notifications** — notifications bottom-right à chaque étape (NFO, TMDB, Upload, Discord, Seedbox, Torrent, fin/erreur)

### v2.1.2
- Champ **Trackers** remplacé par cases à cocher (ABN / TOS / C411 / Torr9 / LaCale), toutes cochées par défaut
- Cases trackers liées à la création `.torrent` — seuls les trackers cochés **et** configurés créent un torrent
- Mode **NFO Seulement** simplifié — utilise le fichier déjà sélectionné, génère les NFO sans upload ni seedbox
- Fix : `parse-torrent-name` remis dans les dépendances (requis par NFO_CUSTOM pour la détection saison/épisode)

### v2.1.1
- Fix : mode jour — texte sombre (`#1a1a1a` / `#4a4a4a`) lisible sur fond clair
- Fix : NFO preview — couleur texte suit le thème (`var(--text)` au lieu de `#d0d0d0` fixe)
- Fix : renommage NFO — `(UTF8).*.nfo` et `(CP437).*.nfo` en préfixe
- Feat : page **Stats** — KPIs, répartition 5 trackers, plateformes, releases par mois

### v2.1.0
- **Barre de progression réelle** : Gofile, BuzzHeavier et seedbox FTP affichent %, vitesse et temps écoulé en temps réel
- **Mode NFO Batch** : traitement de plusieurs fichiers en file d'attente avec confirmation TMDB pour chacun
- **Historique — Recherche** : filtrage temps réel par titre, fichier, tracker, plateforme
- **Historique — Statistiques** : compteurs releases, top tracker, top plateforme, trackers uniques
- Fix : callback torf `generate()` supprimé — conflit `evaluate_js`/thread causant `Missing 'pieces'`

### v2.0.9
- Mode **jour/nuit** : bouton ☀/🌙 dans la sidebar, thème clair complet
- Persistance du thème via `theme.txt` (rechargé automatiquement au démarrage)

### v2.0.8
- Page **Historique** : historique des releases sauvegardé dans `history.json` avec poster, titre, trackers, URL upload
- Sélection des trackers torrent par cases à cocher avant la création des `.torrent`
- Fix : écrasement des `.torrent` existants sans erreur
- Fix : deprecation `OPEN_DIALOG` pywebview

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

**REBiRTH Upload Bot v2.1.9** — macOS & Windows

*NO RULES ! JUST FILES !*

</div>
