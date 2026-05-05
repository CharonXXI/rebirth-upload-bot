# 🪟 Installation Windows — REBiRTH Upload Bot v2.8.3

> **Ce guide s'adresse aux débutants.** Chaque étape est détaillée. Lis attentivement avant de cliquer.

---

## 📋 Logiciels à installer avant de commencer

Tu as besoin de **3 logiciels** avant de démarrer. Installe-les dans cet ordre.

---

### 1️⃣ Python 3.12

**Télécharger :** [https://www.python.org/downloads/](https://www.python.org/downloads/)

1. Clique sur le gros bouton jaune **"Download Python 3.12.x"**
2. Lance le fichier `.exe` téléchargé
3. **⚠️ IMPORTANT :** Avant de cliquer sur "Install Now", coche la case **"Add Python to PATH"** en bas de la fenêtre
   ```
   ☑ Add Python 3.12 to PATH   ← cocher cette case !
   ```
4. Clique **"Install Now"**
5. Attends la fin, puis clique **"Close"**

**Vérification :** Ouvre PowerShell (voir étape suivante) et tape :
```
python --version
```
Tu dois voir `Python 3.12.x`. Si tu vois une erreur, Python n'est pas dans le PATH — désinstalle et réinstalle en cochant bien la case.

---

### 2️⃣ Git (optionnel mais recommandé)

**Télécharger :** [https://git-scm.com/download/win](https://git-scm.com/download/win)

1. Le téléchargement démarre automatiquement
2. Lance l'installeur et clique **"Next"** à chaque étape (les options par défaut sont correctes)
3. Clique **"Install"** puis **"Finish"**

> Si tu ne veux pas utiliser Git, tu peux télécharger le projet en ZIP (voir étape 2 de l'installation).

---

### 3️⃣ Comment ouvrir PowerShell dans un dossier

> **PowerShell** est le terminal Windows que tu vas utiliser pour taper les commandes. C'est **différent de CMD** — ne pas confondre.

**Méthode rapide :**
1. Navigue dans l'explorateur Windows jusqu'au dossier du projet
2. Clique dans la **barre d'adresse** du dossier (en haut, là où il y a le chemin du dossier)
3. Tape `powershell` et appuie sur **Entrée**
4. Une fenêtre bleue/noire s'ouvre — c'est PowerShell ✓

---

## 🚀 Installation du bot

### Étape 1 — Récupérer le projet

**Option A — Avec Git (recommandé) :**

Ouvre PowerShell dans le dossier où tu veux installer le bot, puis tape :
```powershell
git clone https://github.com/CharonXXI/rebirth-upload-bot.git
cd rebirth-upload-bot
```

**Option B — Sans Git (ZIP) :**
1. Va sur [https://github.com/CharonXXI/rebirth-upload-bot](https://github.com/CharonXXI/rebirth-upload-bot)
2. Clique sur le bouton vert **"Code"** → **"Download ZIP"**
3. Extrait le ZIP dans un dossier (ex: `C:\REBiRTH\`)
4. Ouvre PowerShell dans ce dossier extrait

---

### Étape 2 — Créer l'environnement virtuel

> L'environnement virtuel isole les dépendances du bot — il ne touche pas à ton Python système.

Dans PowerShell, tape :
```powershell
python -m venv venv
```

Tu dois voir quelque chose comme :
```
(aucune sortie ou "created virtual environment...")
```

Ensuite, active l'environnement :
```powershell
venv\Scripts\activate
```

Tu dois voir `(venv)` apparaître devant ton invite de commande :
```
(venv) PS C:\REBiRTH\rebirth-upload-bot>
```

> ⚠️ Si tu obtiens `Permission denied` sur `venv\Scripts\python.exe`, un venv existait déjà. Supprime-le et recommence :
> ```powershell
> Remove-Item -Recurse -Force venv
> python -m venv venv
> venv\Scripts\activate
> ```

---

### Étape 3 — Installer les dépendances

> ⚠️ Ces commandes doivent être tapées dans **PowerShell** avec `(venv)` actif (voir étape précédente).

Tape ces deux commandes **une par une** (attends que chaque commande se termine avant de passer à la suivante) :

```powershell
$env:PYTHONUTF8="1"
```
*(pas de sortie visible — c'est normal)*

```powershell
pip install pywebview python-dotenv requests requests_toolbelt tqdm rich pymediainfo parse-torrent-name numpy
```
*(téléchargement de plusieurs packages — peut prendre 1 à 2 minutes)*

```powershell
pip install -r NFO_CUSTOM\requirements.txt
```

À la fin, tu dois voir `Successfully installed ...` sans ligne rouge `ERROR`.

> 💡 **Pourquoi `$env:PYTHONUTF8="1"` ?** C'est nécessaire pour que `parse-torrent-name` s'installe correctement sur Python 3.12. Sans ça, le build du package plante avec une erreur d'encodage.

---

### Étape 4 — Installer BDInfo (pour l'onglet BD Info)

> Cette étape est uniquement nécessaire si tu utilises l'onglet **BD Info** du bot.

1. Télécharge **BDInfo v0.7.5.6** depuis [VideoHelp](https://www.videohelp.com/software/BDInfo)
2. Dans le dossier du projet, crée un dossier nommé exactement **`BDInfo_v0`**
3. Place `BDInfo.exe` et toutes ses DLLs dans ce dossier :

```
rebirth-upload-bot\
└── BDInfo_v0\
    ├── BDInfo.exe       ← obligatoire
    ├── BDInfoLib.dll
    └── ...
```

Le bot détecte `BDInfo_v0\BDInfo.exe` automatiquement — rien d'autre à configurer.

**Utilisation :**
1. Onglet **BD Info** → clique **SCANNER** → BDInfo s'ouvre
2. Dans BDInfo : Scan Bitrates → View Report → sauvegarde dans le dossier `BDINFO\`
3. Retourne dans le bot → clique **📂 CHARGER RAPPORT BDINFO**

---

### Étape 5 — Configurer le fichier V1.env

> C'est ici que tu renseignes tes clés d'API, tokens et accès seedbox.

1. Dans le dossier du projet, tu vois un fichier **`V1.env`**
2. Fais un clic droit dessus → **"Ouvrir avec"** → **Notepad** (Bloc-notes)
3. Remplis les valeurs une par une :

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
TRACKER_LACALE=https://lacale.com/announce/PASSKEY
TRACKER_HDT=https://hdts-announce.ru/announce.php?passkey=PASSKEY
TRACKER_NEXUM=https://nexum-core.com/announce/PASSKEY
```

4. Sauvegarde : **Ctrl+S**, puis ferme le Bloc-notes

---

### Étape 6 — Lancer le bot

**Double-clique sur `REBiRTH.bat`** dans le dossier du projet.

Une fenêtre noire s'ouvre brièvement (c'est normal), puis l'interface graphique du bot apparaît en 2 à 6 secondes.

> Alternatively, via PowerShell avec `(venv)` actif :
> ```powershell
> python app.py
> ```

---

## 📦 Créer un `.exe` autonome (optionnel)

Si tu veux partager le bot ou l'utiliser sans avoir Python d'installé :

1. **Double-clique sur `build_win.bat`**
2. Attends la fin du build (1 à 3 minutes)
3. Le résultat se trouve dans :

```
dist\
└── REBiRTH\
    ├── REBiRTH.exe     ← double-cliquer pour lancer
    ├── V1.env          ← ta config (à remplir si vide)
    ├── FILMS\          ← déposer les .mkv ici
    ├── FINAL\          ← généré automatiquement
    ├── TORRENTS\       ← généré automatiquement
    └── BDINFO\         ← rapports BD Info
```

> ⚠️ **Ne déplace pas `REBiRTH.exe`** hors du dossier `dist\REBiRTH\`. Le `.exe` a besoin de tous les fichiers autour de lui.
>
> Pour partager : zippe le dossier `dist\REBiRTH\` entier **sans le `V1.env`** (qui contient tes tokens personnels).

---

## 🔧 Dépannage

| Problème | Cause | Solution |
|---|---|---|
| `'python' n'est pas reconnu` | Python pas dans le PATH | Désinstaller Python et réinstaller en cochant **"Add Python to PATH"** |
| `No module named 'webview'` | pywebview manquant | `pip install pywebview` |
| `No module named 'PTN'` | parse-torrent-name non installé | Dans PowerShell : `$env:PYTHONUTF8="1"` puis `pip install parse-torrent-name` |
| `Failed to build parse-torrent-name` | Encodage Python | Même solution : PowerShell + `$env:PYTHONUTF8="1"` avant le pip |
| Fenêtre blanche au lancement | WebView2 manquant | Installer [Microsoft Edge WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) |
| `Permission denied` sur venv | Venv déjà existant | `Remove-Item -Recurse -Force venv` puis relancer `python -m venv venv` |
| `Fatal error in launcher` | Venv corrompu | Même solution que ci-dessus |
| `Invalid requirement 'requests\_toolbelt'` | Backslash au lieu d'underscore | Utiliser `requests_toolbelt` (underscore `_`, pas `\`) |
| `Could not open requirements file` | Chemin avec backslash | Utiliser `NFO_CUSTOM\requirements.txt` tel quel dans PowerShell |
| `(venv)` ne s'affiche pas | Venv pas activé | Relancer `venv\Scripts\activate` |
| FTP timeout | Mauvais identifiants | Vérifier `SFTP_HOST`, `SFTP_PORT`, `SFTP_USER`, `SFTP_PASS` dans `V1.env` |
| Erreur NFO vide | Fichier .mkv inaccessible | Vérifier que le fichier est dans le dossier `FILMS\` et accessible |
| Torrent SB : mauvais répertoire | Mauvais chemin seedbox | Vérifier que `SFTP_PATH` dans `V1.env` correspond au chemin réel sur la seedbox |
| BD Info : `BDInfo.exe introuvable` | Mauvais emplacement | Vérifier que `BDInfo.exe` est dans `BDInfo_v0\` à la racine du projet |
| BD Info : `not a directory` | Mauvais dossier sélectionné | Le dossier doit contenir un sous-dossier `BDMV\` |
| Le bot démarre mais reste blanc | WebView2 pas à jour | Mettre à jour Microsoft Edge ou installer WebView2 Runtime |

---

## ❓ Résumé des logiciels utilisés

| Logiciel | Rôle | Lien |
|---|---|---|
| **Python 3.12** | Fait tourner le bot | [python.org](https://www.python.org/downloads/) |
| **Git** | Télécharge et met à jour le projet | [git-scm.com](https://git-scm.com/) |
| **PowerShell** | Terminal pour les commandes (déjà installé sur Windows) | — |
| **BDInfo v0.7.5.6** | Analyse les Blu-rays (onglet BD Info) | [VideoHelp](https://www.videohelp.com/software/BDInfo) |
| **Microsoft Edge WebView2** | Affiche l'interface graphique (déjà installé sur W10/11) | [microsoft.com](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) |
