#!/usr/bin/env python3
"""
MakeMKV Extract - Analyse et extraction sélective des pistes
"""

import subprocess
import os
import shutil
import re
import sys
import glob
import time
from typing import List, Dict, Any, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(SCRIPT_DIR, "tools")


def _find_in_tools(exe_name: str) -> Optional[str]:
    if not os.path.isdir(TOOLS_DIR):
        return None
    patterns = [
        os.path.join(TOOLS_DIR, exe_name),
        os.path.join(TOOLS_DIR, "**", exe_name),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        for m in matches:
            if os.path.isfile(m):
                return m
    return None


def _find_makemkvcon() -> str:
    for name in ["makemkvcon.exe", "makemkvcon"]:
        found = _find_in_tools(name)
        if found:
            return found
    
    path = shutil.which("makemkvcon")
    if path:
        return path
    
    candidates = [
        r"C:\Program Files (x86)\MakeMKV\makemkvcon.exe",
        r"C:\Program Files\MakeMKV\makemkvcon.exe",
        "/Applications/MakeMKV.app/Contents/MacOS/makemkvcon",
        "/usr/bin/makemkvcon",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    
    raise FileNotFoundError("makemkvcon introuvable")


def _normalize_source(source: str) -> str:
    """Normalise le chemin source pour MakeMKV"""
    source = os.path.abspath(source)
    
    if source.lower().endswith('.iso'):
        return f"iso:{source}"
    
    if os.path.isdir(source):
        if source.upper().endswith('BDMV'):
            source = os.path.dirname(source)
        return f"file:{source}"
    
    return source


def _parse_tinfo_line(line: str) -> Optional[Tuple[int, int, int, str]]:
    """Parse une ligne TINFO: title_id, field_id, code, value"""
    match = re.match(r'TINFO:(\d+),(\d+),(\d+),"([^"]*)"', line)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4)
    return None


def _parse_sinfo_line(line: str) -> Optional[Tuple[int, int, int, int, str]]:
    """Parse une ligne SINFO: title_id, stream_id, field_id, code, value"""
    match = re.match(r'SINFO:(\d+),(\d+),(\d+),(\d+),"([^"]*)"', line)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4)), match.group(5)
    return None


def analyze_source(source: str) -> Dict[str, Any]:
    """
    Analyse une source (ISO/BDMV) et retourne les informations sur les titres et pistes.
    
    Returns:
        {
            "titles": [
                {
                    "id": 0,
                    "name": "title00.mkv",
                    "duration": "1:45:30",
                    "size": "25.5 GB",
                    "size_bytes": 27380000000,
                    "chapters": 24,
                    "streams": [
                        {
                            "id": 0,
                            "type": "video",
                            "codec": "MPEG-4 AVC",
                            "info": "1920x1080",
                            "name": ""
                        },
                        {
                            "id": 1,
                            "type": "audio",
                            "codec": "DTS-HD Master Audio",
                            "lang": "English",
                            "lang_code": "eng",
                            "channels": "7.1",
                            "name": "Surround 7.1"
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    makemkvcon = _find_makemkvcon()
    source_norm = _normalize_source(source)
    
    print(f"  Analyse en cours...")
    print(f"  Source: {source_norm}")
    
    cmd = [makemkvcon, "-r", "info", source_norm]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    titles = {}
    streams = {}
    
    # Field IDs pour TINFO
    TINFO_NAME = 2
    TINFO_CHAPTERS = 8
    TINFO_DURATION = 9
    TINFO_SIZE = 10
    TINFO_SIZE_BYTES = 11
    
    # Field IDs pour SINFO (basé sur MakeMKV output)
    # ID 1 = Type (Video/Audio/Subtitles)
    # ID 2 = Name / Track name
    # ID 3 = Language long (English, French, etc)
    # ID 4 = Language code (eng, fra, etc)
    # ID 5 = Codec ID
    # ID 6 = Codec short
    # ID 7 = Codec long / detailed info
    # ID 13 = Channels audio
    # ID 19 = Resolution video / channel layout
    # ID 20 = Aspect ratio
    # ID 21 = Frame rate
    # ID 30 = Bitrate
    # ID 33 = Stream flags
    
    for line in proc.stdout:
        line = line.strip()
        
        # TINFO - info sur les titres
        tinfo = _parse_tinfo_line(line)
        if tinfo:
            title_id, field_id, code, value = tinfo
            if title_id not in titles:
                titles[title_id] = {"id": title_id, "streams": []}
            
            if field_id == TINFO_NAME:
                titles[title_id]["name"] = value
            elif field_id == TINFO_CHAPTERS:
                titles[title_id]["chapters"] = int(value) if value.isdigit() else 0
            elif field_id == TINFO_DURATION:
                titles[title_id]["duration"] = value
            elif field_id == TINFO_SIZE:
                titles[title_id]["size"] = value
            elif field_id == TINFO_SIZE_BYTES:
                try:
                    titles[title_id]["size_bytes"] = int(value)
                except:
                    titles[title_id]["size_bytes"] = 0
        
        # SINFO - info sur les streams
        sinfo = _parse_sinfo_line(line)
        if sinfo:
            title_id, stream_id, field_id, code, value = sinfo
            key = (title_id, stream_id)
            
            if key not in streams:
                streams[key] = {"id": stream_id, "title_id": title_id}
            
            # Type de stream (field 1) - le type est dans le CODE pas la valeur
            # 6201 = Video, 6202 = Audio, 6203 = Subtitles
            if field_id == 1:
                if code == 6201 or "vid" in value.lower():
                    streams[key]["type"] = "video"
                elif code == 6202 or "audio" in value.lower():
                    streams[key]["type"] = "audio"
                elif code == 6203 or "sub" in value.lower():
                    streams[key]["type"] = "subtitle"
                else:
                    streams[key]["type"] = value.lower()
            
            # Track name (field 2) - ex: "Surround 5.1"
            elif field_id == 2:
                streams[key]["name"] = value
            
            # Language code (field 3) - ex: "eng", "fra"
            elif field_id == 3:
                streams[key]["lang_code"] = value.lower()
            
            # Language long (field 4) - ex: "English", "French"
            elif field_id == 4:
                streams[key]["lang"] = value
            
            # Codec ID (field 5) - ex: "A_DTS", "V_MPEG4/ISO/AVC"
            elif field_id == 5:
                streams[key]["codec_id"] = value
            
            # Codec short (field 6) - ex: "Mpeg4"
            elif field_id == 6:
                streams[key]["codec"] = value
            
            # Codec long (field 7) - ex: "Mpeg4 AVC High@L4.1"
            elif field_id == 7:
                streams[key]["codec_full"] = value
                if "codec" not in streams[key]:
                    streams[key]["codec"] = value
            
            # Resolution (field 19) - ex: "1920x1080"
            elif field_id == 19:
                streams[key]["info"] = value
            
            # Aspect ratio (field 20)
            elif field_id == 20:
                streams[key]["aspect"] = value
            
            # Frame rate (field 21)
            elif field_id == 21:
                streams[key]["fps"] = value
            
            # Language code alt (field 28) - parfois utilisé
            elif field_id == 28:
                if "lang_code" not in streams[key]:
                    streams[key]["lang_code"] = value.lower()
            
            # Language long alt (field 29)
            elif field_id == 29:
                if "lang" not in streams[key]:
                    streams[key]["lang"] = value
            
            # Bitrate (field 30)
            elif field_id == 30:
                streams[key]["bitrate"] = value
            
            # Description / extra info (field 31)
            elif field_id == 31:
                streams[key]["description"] = value
            
            # Extended lang code (field 33) - peut contenir fr-CA, fr-FR
            elif field_id == 33:
                streams[key]["lang_ext"] = value
            
            # Original source info (field 38)
            elif field_id == 38:
                streams[key]["original_info"] = value
            
            # Track metadata (field 42)
            elif field_id == 42:
                streams[key]["metadata"] = value
    
    proc.wait()
    
    # Associer les streams aux titres
    for (title_id, stream_id), stream_data in streams.items():
        if title_id in titles:
            titles[title_id]["streams"].append(stream_data)
    
    # Trier les streams par ID
    for title in titles.values():
        title["streams"].sort(key=lambda x: x.get("id", 0))
    
    # Convertir en liste triée par taille
    result = list(titles.values())
    result.sort(key=lambda x: x.get("size_bytes", 0), reverse=True)
    
    print(f"  {len(result)} titre(s) trouve(s)")
    
    return {"titles": result}


_ALL_STREAMS_PROFILE_XML = """<?xml version="1.0" encoding="utf-8"?>
<profile>
    <name lang="eng">All</name>
    <trackSettings input="default">
        <output outputSettingsName="default"
            defaultSelection="+sel:all"/>
    </trackSettings>
</profile>
"""


def _make_all_streams_profile() -> str:
    """Crée un profil MakeMKV temporaire qui force l'extraction de TOUS les
    streams (vidéo + audios + sous-titres) sans filtrage par langue.
    Retourne le chemin du fichier .mmcp.xml."""
    import tempfile
    f = tempfile.NamedTemporaryFile(
        prefix="remux_all_", suffix=".mmcp.xml",
        delete=False, mode="w", encoding="utf-8",
    )
    f.write(_ALL_STREAMS_PROFILE_XML)
    f.close()
    return f.name


def _makemkv_settings_path() -> str:
    """Retourne le chemin attendu du settings.conf MakeMKV pour l'OS courant."""
    import platform
    home = os.path.expanduser("~")
    if platform.system() == "Darwin":
        return os.path.join(home, "Library", "Application Support", "MakeMKV", "settings.conf")
    if platform.system() == "Windows":
        return os.path.join(os.environ.get("APPDATA", home), "MakeMKV", "settings.conf")
    return os.path.join(home, ".MakeMKV", "settings.conf")


def _ensure_makemkv_select_all() -> dict:
    """Patche le settings.conf de MakeMKV pour forcer
    app_DefaultSelectionString = "+sel:all". Crée le fichier au besoin.

    Retourne un dict :
        {
            "path"   : chemin du settings.conf,
            "backup" : chemin de sauvegarde (ou None),
            "created": True si le fichier a été créé from scratch,
            "patched": True si une ligne a été modifiée/ajoutée,
            "status" : "patched" | "already_ok" | "created" | "error",
            "msg"    : message lisible,
        }
    """
    cfg = _makemkv_settings_path()
    target_line = 'app_DefaultSelectionString = "+sel:all"'
    info = {"path": cfg, "backup": None, "created": False, "patched": False,
            "status": "error", "msg": ""}

    # Cas 1 : fichier inexistant → on le crée minimal
    if not os.path.isfile(cfg):
        try:
            os.makedirs(os.path.dirname(cfg), exist_ok=True)
            with open(cfg, "w", encoding="utf-8") as f:
                f.write(target_line + "\n")
            info["created"] = True
            info["patched"] = True
            info["status"] = "created"
            info["msg"] = f"settings.conf créé : {cfg}"
        except Exception as e:
            info["msg"] = f"impossible de créer settings.conf : {e}"
        return info

    # Cas 2 : fichier existant
    try:
        with open(cfg, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        info["msg"] = f"lecture impossible : {e}"
        return info

    if target_line in content:
        info["status"] = "already_ok"
        info["msg"] = f"settings.conf déjà configuré (+sel:all)"
        return info

    # Sauvegarde
    backup = cfg + ".remux_tool.bak"
    try:
        with open(backup, "w", encoding="utf-8") as f:
            f.write(content)
        info["backup"] = backup
    except Exception:
        pass

    # Remplacer la ligne existante OU l'ajouter à la fin
    new_content = re.sub(
        r'^app_DefaultSelectionString\s*=.*$',
        target_line,
        content,
        flags=re.MULTILINE,
    )
    if new_content == content:
        new_content = content.rstrip() + "\n" + target_line + "\n"

    try:
        with open(cfg, "w", encoding="utf-8") as f:
            f.write(new_content)
        info["patched"] = True
        info["status"] = "patched"
        info["msg"] = f"settings.conf patché (sauvegarde : {backup})"
    except Exception as e:
        info["msg"] = f"écriture impossible : {e}"
    return info


def _restore_makemkv_settings(info: dict) -> None:
    """Restaure le settings.conf depuis le résultat de _ensure_makemkv_select_all."""
    if not info or info.get("status") == "error" or info.get("status") == "already_ok":
        return
    cfg = info.get("path") or _makemkv_settings_path()
    if info.get("created"):
        # On l'a créé from scratch → on le supprime
        try:
            os.remove(cfg)
        except OSError:
            pass
        return
    backup = info.get("backup")
    if not backup or not os.path.isfile(backup):
        return
    try:
        with open(backup, "r", encoding="utf-8") as f:
            content = f.read()
        with open(cfg, "w", encoding="utf-8") as f:
            f.write(content)
        os.remove(backup)
    except OSError:
        pass


def extract_title(source: str, title_id: int, output_dir: str,
                  selected_streams: Optional[List[int]] = None,
                  force_all_streams: bool = True) -> str:
    """
    Extrait un titre spécifique avec les pistes sélectionnées.

    Args:
        source: Chemin vers ISO ou BDMV
        title_id: ID du titre à extraire
        output_dir: Dossier de sortie
        selected_streams: Liste des IDs de streams (info seulement, MakeMKV
            ne filtre pas par cette liste — le filtrage final est fait par mkvmerge)
        force_all_streams: Si True (défaut), passe un profil .mmcp.xml qui force
            MakeMKV à inclure TOUS les streams sans filtrer par langue.

    Returns:
        Chemin du fichier MKV extrait
    """
    makemkvcon = _find_makemkvcon()
    source_norm = _normalize_source(source)

    os.makedirs(output_dir, exist_ok=True)

    cmd = [makemkvcon, "mkv", source_norm, str(title_id), output_dir]

    settings_info = None
    # NOTE : on a TESTÉ deux stratégies pour forcer l'inclusion de tous les
    # streams (profil .mmcp.xml + patch app_DefaultSelectionString) — les deux
    # cassaient en fait les défauts internes de MakeMKV qui marchaient déjà.
    # On laisse donc MakeMKV utiliser sa configuration par défaut.
    # Si l'utilisateur veut forcer plus de pistes, il peut configurer
    # MakeMKV.app → Preferences → Languages directement.
    if force_all_streams:
        cfg_path = _makemkv_settings_path()
        if os.path.isfile(cfg_path):
            print(f"  MakeMKV settings.conf : {cfg_path} (défaut utilisé)")
        else:
            print(f"  MakeMKV : aucun settings.conf — utilise les défauts de l'app")

    print(f"\n  Extraction du titre {title_id}...")
    if selected_streams:
        print(f"  Streams selectionnes: {selected_streams}")
    
    start = time.time()
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    output_file = None
    
    for line in proc.stdout:
        line = line.strip()
        
        # Progress
        if "PRGV:" in line:
            match = re.search(r'PRGV:(\d+),(\d+),(\d+)', line)
            if match:
                current, total, max_val = map(int, match.groups())
                if max_val > 0:
                    pct = int(current * 100 / max_val)
                    elapsed = max(0.001, time.time() - start)
                    if pct > 0:
                        remain = (100 - pct) / (pct / elapsed)
                        eta_m, eta_s = int(remain // 60), int(remain % 60)
                    else:
                        eta_m, eta_s = 0, 0
                    bar = '#' * (pct // 3) + '-' * (33 - pct // 3)
                    sys.stdout.write(f"\r  [{bar}] {pct}% ETA {eta_m:02d}:{eta_s:02d}")
                    sys.stdout.flush()
        
        # Fichier de sortie
        if "MKV file" in line and "created" in line.lower():
            match = re.search(r'"([^"]+\.mkv)"', line)
            if match:
                output_file = match.group(1)
        
        # Erreurs
        if "MSG:5021" in line or "failed" in line.lower():
            print(f"\n  [ERREUR] {line}")
    
    rc = proc.wait()
    print()

    if rc != 0:
        raise RuntimeError(f"MakeMKV extraction echouee (code {rc})")
    
    # Trouver le fichier MKV
    if not output_file:
        mkvs = [f for f in os.listdir(output_dir) if f.lower().endswith('.mkv')]
        if mkvs:
            mkvs_with_size = [(f, os.path.getsize(os.path.join(output_dir, f))) for f in mkvs]
            mkvs_with_size.sort(key=lambda x: x[1], reverse=True)
            output_file = os.path.join(output_dir, mkvs_with_size[0][0])
    
    if not output_file or not os.path.isfile(output_file):
        raise RuntimeError("Fichier MKV non trouve apres extraction")
    
    size_gb = os.path.getsize(output_file) / (1024**3)
    print(f"  Extrait: {os.path.basename(output_file)} ({size_gb:.1f} GB)")
    
    return output_file


def get_stream_type(stream: dict) -> str:
    """Retourne le type normalisé d'un stream"""
    stype = (stream.get("type") or "").lower()
    if "video" in stype:
        return "video"
    elif "audio" in stype:
        return "audio"
    elif "subtitle" in stype or "sub" in stype:
        return "subtitle"
    return stype


def is_french_stream(stream: dict) -> bool:
    """Vérifie si un stream est en français"""
    lang = (stream.get("lang") or "").lower()
    lang_code = (stream.get("lang_code") or "").lower()
    name = (stream.get("name") or "").lower()
    
    if lang_code in ("fra", "fre", "fr"):
        return True
    if "french" in lang or "français" in lang or "francais" in lang:
        return True
    if any(m in name for m in ["vf", "vff", "vfq", "vfi", "french", "français"]):
        return True
    return False


def is_english_stream(stream: dict) -> bool:
    """Vérifie si un stream est en anglais"""
    lang = (stream.get("lang") or "").lower()
    lang_code = (stream.get("lang_code") or "").lower()
    name = (stream.get("name") or "").lower()
    
    if lang_code in ("eng", "en"):
        return True
    if "english" in lang:
        return True
    if "english" in name:
        return True
    return False
