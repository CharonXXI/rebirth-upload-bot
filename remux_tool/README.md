# 🔄 Remux Tool — Onglet intégré dans REBiRTH AIO

Le Remux Tool est intégré directement dans **REBiRTH AIO** (onglet 🔄 Remux).  
Il n'est plus nécessaire de le lancer séparément.

**Workflow :** ISO/BDMV → MakeMKV → MediaInfo → MKVToolNix → `FILMS/`

---

## ⚙️ Prérequis (outils externes)

| Outil | Windows | macOS |
|-------|---------|-------|
| **MakeMKV** | [makemkv.com](https://www.makemkv.com/download/) | `brew install --cask makemkv` |
| **MediaInfo** | [mediaarea.net](https://mediaarea.net/en/MediaInfo/Download) | `brew install mediainfo` |
| **MKVToolNix** | [mkvtoolnix.download](https://mkvtoolnix.download/) | `brew install mkvtoolnix` |
| **FFmpeg** | `winget install ffmpeg` | `brew install ffmpeg` |

Voir **[INSTALL_WINDOWS.md](../INSTALL_WINDOWS.md)** pour les instructions détaillées sous Windows.

---

## 📂 Organisation des sources

Place les films dans le dossier `remux_tool/FULL/` :

```
remux_tool/FULL/
├── Cold.Storage.2026.BluRay.1080p.AVC-MTeam/   ← dossier BDMV
│   └── BDMV/
└── MonFilm.iso                                  ← ou ISO directement
```

---

## 🔄 Workflow dans l'interface

1. **⟳ Refresh** — recharge la liste des sources dans `FULL/`
2. **Cliquer sur un film** → **Analyser** — MakeMKV scanne le disque (30 s à 2 min)
   - Sélection automatique du titre principal
   - Recherche TMDB pour le titre français
3. **Sélectionner les pistes** vidéo / audio / sous-titres (recommandations auto)
4. **▶ Lancer le remux** — barre de progression + console live
5. Le MKV final atterrit dans `../FILMS/` — prêt pour l'onglet Upload

---

## 📛 Convention de nommage

```
Movie.Title.Year.MULTi.VF*.Resolution.Source.REMUX.[HDR].Audio.Codec-REBiRTH AIO.mkv
```

**Exemples :**
```
Cold.Storage.2026.MULTi.VFF.1080p.BluRay.REMUX.DTS-HD.MA.5.1.AVC-REBiRTH AIO.mkv
Dune.Part.Two.2024.MULTi.VF2.2160p.UHD.BluRay.REMUX.DV.HDR10.TrueHD.7.1.HEVC-REBiRTH AIO.mkv
```

**Tags VF :**
- `VFF` — Version Française France
- `VFQ` — Version Française Québec
- `VFi` — Version Française internationale
- `VF2` — VFF + VFQ incluses

---

## 📸 Screenshots

Après un remux, le bouton **📸 4 Screens** extrait 4 captures du MKV (10%–90% de la durée)  
et les sauvegarde dans `../PICS/<Titre du Film>/`.

---

## 🔧 Dépannage

| Problème | Solution |
|----------|----------|
| `makemkvcon introuvable` | Installer MakeMKV et/ou ajouter au PATH |
| `MSG:5021` | Licence MakeMKV expirée → **Help → Register** dans MakeMKV |
| `mkvmerge introuvable` | Installer MKVToolNix et ajouter au PATH |
| `mediainfo introuvable` | Installer MediaInfo CLI (fallback ffprobe automatique) |
| `ffmpeg/ffprobe introuvable` | Installer FFmpeg et ajouter au PATH |
| `Aucune piste FR/EN` | Vérifier les métadonnées du disque dans MakeMKV |
| Analyse bloquée | Vérifier que le disque/ISO est accessible et non corrompu |

---

## 📁 Fichiers du module

```
remux_tool/
├── gui.py               ← Backend API (exposé à app.py via importlib)
├── makemkv_extract.py   ← Extraction MakeMKV
├── mediainfo_parse.py   ← Analyse des pistes (MediaInfo/ffprobe)
├── mkvtoolnix_remux.py  ← Remux MKVMerge
├── main.py              ← Orchestrateur CLI (usage standalone)
├── config.py            ← Configuration (FULL_DIR, OUTPUT_DIR…)
├── MAKEMKV_KEY.txt      ← Clé beta MakeMKV courante
└── FULL/                ← Sources ISO/BDMV (non commité)
```

---

**Licence :** Usage personnel uniquement
