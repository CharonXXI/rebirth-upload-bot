# Installation Windows — REBiRTH Upload Bot

## Prérequis

- Windows 10 / 11 (64-bit)
- Python 3.10+ ([python.org](https://www.python.org/downloads/))
  - Cocher **"Add Python to PATH"** pendant l'installation
- Git ([git-scm.com](https://git-scm.com/)) *(optionnel, pour cloner)*

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

> ⚠️ Si tu obtiens `Permission denied` sur `venv\Scripts\python.exe`, un venv existe déjà — supprimer le dossier `venv\` avant de recommencer :
> ```powershell
> Remove-Item -Recurse -Force venv
> python -m venv venv
> ```

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Installer les dépendances

> ⚠️ **Utiliser PowerShell** (pas CMD). Ouvrir PowerShell dans le dossier du projet.
>
> ⚠️ **Attention aux underscores** : le nom du package est `requests_toolbelt` avec un **underscore `_`**, pas un backslash `\`. Ne pas copier-coller depuis un terminal macOS.

```powershell
$env:PYTHONUTF8="1"
pip install pywebview python-dotenv requests requests_toolbelt tqdm rich pymediainfo parse-torrent-name
pip install -r NFO_CUSTOM\requirements.txt
```

> 💡 `$env:PYTHONUTF8="1"` est nécessaire pour que `parse-torrent-name` compile correctement sur Python 3.12. Sans cette ligne, le build du package échoue avec une erreur d'encodage.

### 4. BDInfo v0.7.5.6 (pour l'onglet BD Info)

L'onglet **BD Info** utilise **BDInfo v0.7.5.6** (GUI Windows) lancé directement — aucun .NET ni Wine requis.

1. Télécharger BDInfo v0.7.5.6 (ex: depuis [VideoHelp](https://www.videohelp.com/software/BDInfo))
2. Placer `BDInfo.exe` et ses DLLs dans le dossier **`BDInfo_v0\`** à la racine du projet :

```
rebirth-upload-bot\
└── BDInfo_v0\
    ├── BDInfo.exe       ← requis
    ├── BDInfoLib.dll
    └── ...
```

Le bot détecte et lance `BDInfo_v0\BDInfo.exe` automatiquement. Aucune variable d'environnement à configurer.

**Workflow :**
1. Cliquer **SCANNER** dans l'onglet BD Info → BDInfo s'ouvre
2. Dans BDInfo : Scan Bitrates → View Report → sauvegarder dans le dossier `BDINFO\`
3. Cliquer **📂 CHARGER RAPPORT BDINFO** → le bot traite et affiche le rapport

### 5. Configurer le fichier `.env`

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
TRACKER_HDT=https://hdts-announce.ru/announce.php?passkey=PASSKEY
SFTP_PATH_HDT=/home/rtorrent/rtorrent/download/FULL BD

# BD Info (optionnel — chemin auto-détecté si absent)
# BDINFO_CLI_PATH=C:\Users\TonUser\BDInfoCLI\BDInfo\bin\Release\net8.0\win-x64\BDInfo.exe
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
    ├── TORRENTS\       ← généré automatiquement
    └── BDINFO\         ← rapports BD Info (.nfo)
```

> **Important :** Ne pas déplacer `REBiRTH.exe` hors du dossier `dist\REBiRTH\`.
> Toute la config et les dossiers de travail doivent rester au même niveau que l'exe.

### 3. Mettre à jour la version du .exe

La version affichée dans **Propriétés → Détails** du `.exe` est définie dans `version_win.txt`.
À chaque nouvelle version, modifier les lignes `filevers`, `prodvers`, `FileVersion` et `ProductVersion` dans ce fichier.

### 4. Distribution

Pour partager le bot, zipper l'intégralité de `dist\REBiRTH\` (sans le `.env` qui contient tes tokens).

---

## Dépannage

| Problème | Solution |
|---|---|
| `No module named 'webview'` | `pip install pywebview` |
| `No module named 'PTN'` | PowerShell : `$env:PYTHONUTF8="1"` puis `pip install parse-torrent-name` |
| `Failed to build parse-torrent-name` | Même solution : utiliser PowerShell + `$env:PYTHONUTF8="1"` avant le pip |
| Fenêtre blanche au lancement | Installer/réparer .NET Framework |
| `Permission denied` sur venv | Supprimer le dossier `venv\` puis relancer `python -m venv venv` |
| `Fatal error in launcher` | Le venv est corrompu — le recréer : `Remove-Item -Recurse -Force venv` puis `python -m venv venv` |
| `Invalid requirement 'requests\_toolbelt'` | Utiliser `requests_toolbelt` (underscore, pas backslash) |
| `Could not open requirements file: NFO\_CUSTOM` | Utiliser `NFO_CUSTOM\requirements.txt` sans backslash supplémentaire |
| Erreur NFO vide | Vérifier que le fichier `.mkv` est accessible |
| FTP timeout | Vérifier host, port et identifiants seedbox dans `V1.env` |
| Torrent SB : répertoire ruTorrent incorrect | Vérifier que `SFTP_PATH` dans `V1.env` correspond au chemin réel des films sur la seedbox |
| BD Info : `BDInfo.exe introuvable` | Vérifier que `BDInfo.exe` est bien dans le dossier `BDInfo_v0\` à la racine du projet |
| BD Info : `does not exist or is not a directory` | Vérifier que le dossier sélectionné contient bien un sous-dossier `BDMV\` |
