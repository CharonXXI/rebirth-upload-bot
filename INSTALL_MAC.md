# 🍎 Installation macOS — REBiRTH AIO v2.9.4

> **Ce guide s'adresse aux débutants.** Chaque étape est détaillée. Lis attentivement avant de cliquer.

---

## 📋 Logiciels à installer avant de commencer

Tu as besoin de **3 logiciels** avant de démarrer. Installe-les dans cet ordre.

---

### 1️⃣ Homebrew (gestionnaire de paquets macOS)

**Homebrew** permet d'installer des outils en ligne de commande facilement.

Ouvre le **Terminal** (Cmd+Espace → tape "Terminal" → Entrée) et colle cette commande :

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Suis les instructions à l'écran. L'installation prend quelques minutes.

> Si tu as déjà Homebrew, passe à l'étape suivante.

---

### 2️⃣ Python 3.12

macOS inclut une version de Python trop ancienne. Il faut installer Python 3.12 via Homebrew :

```bash
brew install python@3.12
```

**Vérification :** dans le Terminal, tape :
```bash
python3 --version
```
Tu dois voir `Python 3.12.x`.

---

### 3️⃣ MediaInfo CLI

Le bot utilise MediaInfo pour lire les métadonnées des fichiers `.mkv` :

```bash
brew install mediainfo
```

**Vérification :**
```bash
mediainfo --version
```
Tu dois voir `MediaInfo Command line, ...`.

---

### 4️⃣ Git (optionnel, pour cloner le projet)

```bash
brew install git
```

> Si tu ne veux pas utiliser Git, tu peux télécharger le ZIP directement depuis GitHub.

---

## 🚀 Installation du bot

### Étape 1 — Récupérer le projet

**Option A — Avec Git (recommandé) :**

Dans le Terminal, navigue vers le dossier où tu veux installer le bot, puis :

```bash
git clone https://github.com/CharonXXI/rebirth-upload-bot.git
cd rebirth-upload-bot
```

**Option B — Sans Git (ZIP) :**
1. Va sur [https://github.com/CharonXXI/rebirth-upload-bot](https://github.com/CharonXXI/rebirth-upload-bot)
2. Clique sur le bouton vert **"Code"** → **"Download ZIP"**
3. Décompresse le ZIP sur ton Bureau ou dans un dossier de ton choix
4. Dans le Terminal, accède au dossier :
   ```bash
   cd ~/Desktop/rebirth-upload-bot
   ```

---

### Étape 2 — Créer l'environnement virtuel

> L'environnement virtuel isole les dépendances du bot de ton Python système.

```bash
python3 -m venv venv
```

Ensuite, active l'environnement :

```bash
source venv/bin/activate
```

Tu dois voir `(venv)` apparaître devant ton invite de commande :
```
(venv) user@Mac rebirth-upload-bot %
```

> Si tu obtiens une erreur, supprime le dossier `venv/` et recommence :
> ```bash
> rm -rf venv
> python3 -m venv venv
> source venv/bin/activate
> ```

---

### Étape 3 — Installer les dépendances

Avec `(venv)` actif, installe les packages (attends la fin de chaque commande) :

```bash
pip install pywebview python-dotenv requests requests_toolbelt tqdm rich pymediainfo parse-torrent-name numpy paramiko
pip install -r NFO_CUSTOM/requirements.txt
```

À la fin, tu dois voir `Successfully installed ...` sans ligne rouge `ERROR`.

---

### Étape 4 — BDInfo via Whisky (pour l'onglet BD Info)

> Cette étape est uniquement nécessaire si tu utilises l'onglet **BD Info** du bot.

Le bot utilise **BDInfo v0.7.5.6** (application Windows) via **Whisky** (Wine pour macOS) pour obtenir des bitrates exacts.

**A. Installer Whisky :**
1. Télécharge Whisky sur [https://github.com/Whisky-App/Whisky/releases](https://github.com/Whisky-App/Whisky/releases)
2. Ouvre le `.dmg` et glisse **Whisky.app** dans Applications
3. Lance Whisky au moins une fois pour qu'il initialise son environnement Wine

**B. Préparer BDInfo.exe :**
1. Télécharge **BDInfo v0.7.5.6** depuis [VideoHelp](https://www.videohelp.com/software/BDInfo)
2. Crée un dossier sur ton Bureau ou dans ton dossier Home, ex: `~/Desktop/BDInfo_v0/`
3. Place `BDInfo.exe` et toutes ses DLLs dans ce dossier :
   ```
   ~/Desktop/BDInfo_v0/
   ├── BDInfo.exe       ← obligatoire
   ├── BDInfoLib.dll
   └── ...
   ```

**C. Configurer la variable d'environnement :**

Ajoute cette ligne dans ton fichier `~/.zshrc` (ou `~/.bashrc`) :
```bash
export BDINFO_WIN_EXE="$HOME/Desktop/BDInfo_v0/BDInfo.exe"
```

Puis recharge :
```bash
source ~/.zshrc
```

> 💡 Si tu lances le bot depuis le Terminal (via `REBiRTH.command` ou `python3 app.py`), la variable sera lue automatiquement. Si tu utilises un `.app` PyInstaller, définis la dans `~/.zshrc`.

**Workflow :**
1. Onglet **BD Info** → clique **SCANNER** → BDInfo s'ouvre via Whisky
2. Dans BDInfo : Scan Bitrates → View Report → sauvegarde dans le dossier `BDINFO/`
3. Retourne dans le bot → clique **📂 CHARGER RAPPORT BDINFO**

---

### Étape 5 — Configurer le fichier V1.env

1. Dans le dossier du projet, ouvre le fichier **`V1.env`** avec un éditeur texte (TextEdit en mode texte brut, VS Code, nano, etc.)
2. Remplis les valeurs une par une :

```env
# ── TMDB ──────────────────────────────────────────────
API_KEY=ta_cle_tmdb                     # Clé API sur https://www.themoviedb.org/settings/api
LANGUAGE=fr-FR

# ── Hébergeurs ────────────────────────────────────────
GOFILE_TOKEN=ton_token_gofile           # https://gofile.io/myProfile
BUZZHEAVIER_ACC_ID=ton_account_id       # Ton ID BuzzHeavier

# ── Discord ───────────────────────────────────────────
WEBHOOK_URL=ton_webhook_discord_rebirth         # Webhook du salon REBiRTH
WEBHOOK_HDT_URL=ton_webhook_discord_fullbd      # Webhook du salon FULL BD

# ── Seedbox SFTP / FileBrowser ────────────────────────
SFTP_HOST=https://ton-filebrowser.seedbox.link  # URL FileBrowser
SFTP_HOST_FTP=ton-host-ftp.seedbox.link         # Host FTP/SFTP
SFTP_PORT=23421                                  # Port SFTP
SFTP_USER=ton_user
SFTP_PASS=ton_password
SFTP_PATH=/rtorrent/REBiRTH                     # Chemin dépôt torrents REBiRTH
SFTP_PATH_HDT=/home/rtorrent/rtorrent/download/FULL BD   # Chemin FULL BD

# ── ruTorrent ─────────────────────────────────────────
RUTORRENT_URL=https://ton-rutorrent.seedbox.link
RUTORRENT_USER=ton_user
RUTORRENT_PASS=ton_password

# ── Trackers (remplace PASSKEY par ta clé) ────────────
TRACKER_ABN=https://abn.com/announce/PASSKEY
TRACKER_TOS=https://tos.com/announce/PASSKEY
TRACKER_C411=https://c411.com/announce/PASSKEY
TRACKER_TORR9=https://torr9.com/announce/PASSKEY

TRACKER_HDT=https://hdts-announce.ru/announce.php?passkey=PASSKEY
TRACKER_NEXUM=https://nexum-core.com/announce/PASSKEY
TRACKER_HDF=https://tracker.hdf.world:2443/PASSKEY/announce
```

---

### Étape 6 — Lancer le bot

**Double-clique sur `REBiRTH.command`** dans le dossier du projet.

> Si macOS refuse de l'ouvrir ("impossible d'ouvrir un développeur non identifié") :
> - Clic droit sur `REBiRTH.command` → **"Ouvrir"** → **"Ouvrir"** dans la boîte de dialogue

Une fenêtre Terminal s'ouvre brièvement, puis l'interface graphique du bot apparaît en 2 à 6 secondes.

Alternatively, depuis le Terminal avec `(venv)` actif :
```bash
python3 app.py
```

---

## 📦 Créer un `.app` autonome (optionnel)

Si tu veux une application macOS cliquable sans avoir à ouvrir le Terminal :

```bash
source venv/bin/activate
bash build_mac.sh
```

Le résultat se trouve dans :
```
dist/
└── REBiRTH.app     ← glisser dans Applications
```

> ⚠️ Pour partager le `.app`, compresse le dossier `dist/REBiRTH/` entier (pas juste le `.app`) **sans le `V1.env`** qui contient tes tokens.

---

## 🔧 Dépannage

| Problème | Cause | Solution |
|---|---|---|
| `python3: command not found` | Python pas installé | `brew install python@3.12` |
| `mediainfo: command not found` | MediaInfo pas installé | `brew install mediainfo` |
| `No module named 'webview'` | pywebview manquant | `pip install pywebview` |
| `No module named 'PTN'` | parse-torrent-name manquant | `pip install parse-torrent-name` |
| `No module named 'paramiko'` | paramiko manquant | `pip install paramiko` |
| `(venv)` ne s'affiche pas | venv pas activé | `source venv/bin/activate` |
| Fenêtre blanche au lancement | WebKit / pywebview | Mettre à jour macOS ou réinstaller pywebview |
| `REBiRTH.command` refusé | Gatekeeper | Clic droit → Ouvrir → Ouvrir |
| BD Info : `BDInfo.exe introuvable` | Variable non définie | Vérifier `BDINFO_WIN_EXE` dans `~/.zshrc` |
| BD Info : Whisky ne s'ouvre pas | Whisky non initialisé | Lancer Whisky manuellement au moins une fois |
| FTP timeout | Mauvais identifiants | Vérifier `SFTP_HOST`, `SFTP_PORT`, `SFTP_USER`, `SFTP_PASS` dans `V1.env` |
| Torrent SB : mauvais répertoire | Mauvais chemin seedbox | Vérifier `SFTP_PATH` dans `V1.env` |
| NFO vide / erreur MediaInfo | mediainfo CLI absent | `brew install mediainfo` |

---

## ❓ Résumé des logiciels utilisés

| Logiciel | Rôle | Lien |
|---|---|---|
| **Homebrew** | Gestionnaire de paquets macOS | [brew.sh](https://brew.sh) |
| **Python 3.12** | Fait tourner le bot | [python.org](https://www.python.org/) ou `brew install python@3.12` |
| **MediaInfo CLI** | Lit les métadonnées `.mkv` | `brew install mediainfo` |
| **Git** | Télécharge et met à jour le projet | `brew install git` |
| **Whisky** | Lance BDInfo.exe via Wine (onglet BD Info) | [GitHub Whisky](https://github.com/Whisky-App/Whisky/releases) |
| **BDInfo v0.7.5.6** | Analyse les Blu-rays (onglet BD Info) | [VideoHelp](https://www.videohelp.com/software/BDInfo) |
