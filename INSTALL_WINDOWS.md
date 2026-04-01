# Installation Windows — REBiRTH Upload Bot

## Prérequis

- Windows 10 / 11 (64-bit)
- Python 3.10+ ([python.org](https://www.python.org/downloads/))
  - Cocher **"Add Python to PATH"** pendant l'installation
- Git ([git-scm.com](https://git-scm.com/)) *(optionnel, pour cloner)*
- .NET Framework 4.5+ *(déjà présent sur Windows 10/11)*

> **Note :** MediaInfo CLI n'est **pas** nécessaire sur Windows.
> Le bot utilise directement la librairie Python `pymediainfo` qui embarque MediaInfo.dll.

---

## Installation

### 1. Récupérer le projet

```cmd
git clone https://github.com/CharonXXI/rebirth-upload-bot.git
cd rebirth-upload-bot
```

Ou télécharger le ZIP depuis GitHub et extraire dans un dossier.

### 2. Créer l'environnement virtuel

```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Installer les dépendances

```cmd
pip install pywebview python-dotenv torf requests requests_toolbelt tqdm rich pymediainfo parse-torrent-name
pip install -r NFO_CUSTOM\requirements.txt
```

### 4. Configurer le fichier `.env`

Copier `V1.env` et remplir les variables :

```cmd
copy V1.env V1.env.bak
notepad V1.env
```

Variables à renseigner :

```env
API_KEY=ta_cle_tmdb
LANGUAGE=fr-FR
GOFILE_TOKEN=ton_token_gofile
BUZZHEAVIER_ACC_ID=ton_account_id
WEBHOOK_URL=ton_webhook_discord
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

---

## Lancement

Double-cliquer sur **`REBiRTH.bat`**, ou via le terminal :

```cmd
venv\Scripts\activate
python app.py
```

---

## Build — Créer un `.exe` autonome

Le `.exe` généré en mode **onedir** (dossier autonome) conserve la configuration entre les lancements.

### 1. Lancer le build

Double-cliquer sur **`build_win.bat`**.

### 2. Résultat

```
dist\
└── REBiRTH\
    ├── REBiRTH.exe     ← lancer ce fichier
    ├── V1.env          ← config persistante
    ├── FILMS\          ← déposer les .mkv ici
    ├── FINAL\          ← généré automatiquement
    └── TORRENTS\       ← généré automatiquement
```

> **Important :** Ne pas déplacer `REBiRTH.exe` hors du dossier `dist\REBiRTH\`.
> Toute la config et les dossiers de travail doivent rester au même niveau que l'exe.

### 3. Distribution

Pour partager le bot, zipper l'intégralité de `dist\REBiRTH\` (sans le `.env` qui contient tes tokens).

---

## Dépannage

| Problème | Solution |
|---|---|
| `No module named 'webview'` | `pip install pywebview` |
| Fenêtre blanche au lancement | Installer/réparer .NET Framework |
| `No module named 'torf'` | `pip install torf` |
| Erreur NFO vide | Vérifier que le fichier `.mkv` est accessible |
| FTP timeout | Vérifier host, port et identifiants seedbox |
| ruTorrent : erreur XML-RPC | Vérifier URL et credentials ruTorrent |
