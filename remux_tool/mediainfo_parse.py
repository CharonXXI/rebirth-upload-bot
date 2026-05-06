#!/usr/bin/env python3
"""
MediaInfo Parse - Analyse des pistes audio/video/subs
Cherche les outils dans tools/ et ses sous-dossiers
"""

import subprocess
import json
import os
import shutil
import time
import glob
from typing import Tuple, List, Dict, Optional, Any


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(SCRIPT_DIR, "tools")


def _find_in_tools(exe_name: str) -> Optional[str]:
    """Cherche un exe dans tools/ et tous ses sous-dossiers"""
    if not os.path.isdir(TOOLS_DIR):
        return None
    
    # Chercher récursivement
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


def _find_mediainfo() -> Optional[str]:
    """Trouve MediaInfo CLI"""
    
    # 1. tools/ et sous-dossiers
    for name in ["MediaInfo.exe", "mediainfo.exe", "mediainfo"]:
        found = _find_in_tools(name)
        if found:
            return found
    
    # 2. Racine du projet
    for name in ["MediaInfo.exe", "mediainfo.exe"]:
        p = os.path.join(SCRIPT_DIR, name)
        if os.path.isfile(p):
            return p
    
    # 3. PATH
    path = shutil.which("mediainfo")
    if path:
        return path
    
    # 4. Program Files
    candidates = [
        r"C:\Program Files\MediaInfo\MediaInfo.exe",
        r"C:\Program Files\MediaInfo CLI\MediaInfo.exe",
        r"C:\Program Files (x86)\MediaInfo\MediaInfo.exe",
        "/opt/homebrew/bin/mediainfo",
        "/usr/local/bin/mediainfo",
        "/usr/bin/mediainfo",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    
    return None


def _find_ffprobe() -> Optional[str]:
    """Trouve ffprobe"""
    
    # 1. tools/ et sous-dossiers
    for name in ["ffprobe.exe", "ffprobe"]:
        found = _find_in_tools(name)
        if found:
            return found
    
    # 2. Racine du projet
    for name in ["ffprobe.exe"]:
        p = os.path.join(SCRIPT_DIR, name)
        if os.path.isfile(p):
            return p
    
    # 3. PATH
    path = shutil.which("ffprobe")
    if path:
        return path
    
    # 4. Program Files
    candidates = [
        r"C:\Program Files\FFmpeg\bin\ffprobe.exe",
        r"C:\ffmpeg\bin\ffprobe.exe",
        "/opt/homebrew/bin/ffprobe",
        "/usr/local/bin/ffprobe",
        "/usr/bin/ffprobe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    
    return None


def _wait_file_stable(path: str, attempts: int = 10, interval_s: float = 1.0) -> bool:
    last_size = -1
    for _ in range(max(1, attempts)):
        try:
            size = os.path.getsize(path)
        except FileNotFoundError:
            size = -1
        if size > 0 and size == last_size:
            return True
        last_size = size
        time.sleep(interval_s)
    return False


def _normalize_language(lang: str) -> str:
    if not lang:
        return ""
    lang = lang.lower().strip()
    
    # Conserver les variantes régionales (fr-ca, fr-fr, en-us, etc.)
    if "-" in lang:
        return lang  # Garder fr-ca, fr-fr, en-us, en-gb, etc.
    
    mapping = {
        "eng": "en", "english": "en",
        "fra": "fr", "fre": "fr", "french": "fr", "français": "fr", "francais": "fr",
        "spa": "es", "spanish": "es",
        "deu": "de", "ger": "de", "german": "de",
        "ita": "it", "italian": "it",
        "por": "pt", "portuguese": "pt",
        "jpn": "ja", "japanese": "ja",
        "kor": "ko", "korean": "ko",
        "zho": "zh", "chi": "zh", "chinese": "zh",
        "rus": "ru", "russian": "ru",
        "ara": "ar", "arabic": "ar",
        "und": "", "zxx": "",
    }
    
    if len(lang) == 2:
        return lang
    return mapping.get(lang, lang[:2] if len(lang) >= 2 else lang)


def _parse_with_mediainfo(mediainfo: str, file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    cmd = [mediainfo, "--Output=JSON", file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(f"MediaInfo failed: {result.stderr}")
    
    data = json.loads(result.stdout)
    tracks = data.get("media", {}).get("track", [])
    
    video = None
    audio = []
    subs = []
    
    for t in tracks:
        track_type = t.get("@type", "")
        
        if track_type == "Video":
            if "StreamOrder" not in t:
                t["StreamOrder"] = 0
            if t.get("Language"):
                t["Language"] = _normalize_language(t["Language"])
            video = t
            
        elif track_type == "Audio":
            t["Language"] = _normalize_language(t.get("Language", ""))
            if "StreamOrder" not in t:
                t["StreamOrder"] = len(audio) + 1
            audio.append(t)
            
        elif track_type == "Text":
            t["Language"] = _normalize_language(t.get("Language", ""))
            if "StreamOrder" not in t:
                t["StreamOrder"] = len(subs) + 1
            
            # Classifier le type de sous-titre
            title = (t.get("Title") or "").upper()
            forced_flag = (t.get("Forced") or "").lower() == "yes"
            
            # Nombre d'éléments (FORCED = peu, FULL = beaucoup)
            element_count = 0
            try:
                element_count = int(t.get("ElementCount") or t.get("Count") or 0)
            except:
                pass
            
            # Taille du stream
            stream_size = 0
            try:
                stream_size = int(t.get("StreamSize") or 0)
            except:
                pass
            
            # Détection par titre ou flag
            if forced_flag or "FORCED" in title:
                t["SubType"] = "FORCED"
            elif "SDH" in title or "HEARING" in title or "IMPAIRED" in title:
                t["SubType"] = "SDH"
            elif "COMMENT" in title or "DIRECTOR" in title:
                t["SubType"] = "COMMENTARY"
            elif "FULL" in title or "COMPLET" in title:
                t["SubType"] = "FULL"
            else:
                # Pas de type détecté - sera classifié après par comparaison
                t["SubType"] = "_AUTO_"
            
            # Stocker pour classification
            t["ElementCount"] = element_count
            t["StreamSize"] = stream_size
            
            subs.append(t)
    
    # Classification intelligente par comparaison
    _classify_subtitles_by_comparison(subs)
    
    return video, audio, subs


def _classify_subtitles_by_comparison(subs: List[Dict[str, Any]]) -> None:
    """
    Classifie les sous-titres en comparant ceux de même langue.
    - Le plus petit (éléments) = FORCED (dialogues étrangers seulement)
    - Le milieu = FULL (sous-titres complets)
    - Le plus gros = SDH (FULL + descriptions malentendants)
    """
    # Grouper par langue
    by_lang = {}
    for s in subs:
        lang = (s.get("Language") or "unknown").lower()
        if lang not in by_lang:
            by_lang[lang] = []
        by_lang[lang].append(s)
    
    # Classifier chaque groupe
    for lang, tracks in by_lang.items():
        # Filtrer ceux qui ont besoin d'auto-classification
        auto_tracks = [t for t in tracks if t.get("SubType") == "_AUTO_"]
        
        if not auto_tracks:
            continue
        
        # Trier par nombre d'éléments (croissant: petit → gros)
        auto_tracks.sort(key=lambda x: x.get("ElementCount", 0))
        
        if len(auto_tracks) == 1:
            # Un seul sous-titre - deviner par taille
            t = auto_tracks[0]
            elem = t.get("ElementCount", 0)
            size_mb = t.get("StreamSize", 0) / (1024 * 1024)
            
            if elem < 500 or size_mb < 5:
                t["SubType"] = "FORCED"
            else:
                t["SubType"] = "FULL"
        
        elif len(auto_tracks) == 2:
            # Deux sous-titres
            small = auto_tracks[0]
            big = auto_tracks[1]
            
            small_elem = small.get("ElementCount", 0)
            big_elem = big.get("ElementCount", 0)
            
            # Si le petit est vraiment petit (< 30% du gros) → FORCED + FULL
            if big_elem > 0 and small_elem < big_elem * 0.3:
                small["SubType"] = "FORCED"
                big["SubType"] = "FULL"
            else:
                # Les deux sont similaires - probablement FULL et SDH
                small["SubType"] = "FULL"
                big["SubType"] = "SDH"
        
        elif len(auto_tracks) >= 3:
            # 3+ sous-titres. On distingue 3 catégories par taille :
            #  - FORCED : éléments < 20% du plus gros
            #  - FULL   : "full-sized" — élé. ≥ 50% du plus gros
            #  - SDH    : seulement si on a 2+ FULL et que le plus gros sort
            #             vraiment du lot (≥1.20x du 2e plus gros FULL).
            largest_elem = auto_tracks[-1].get("ElementCount", 0)

            full_sized = [t for t in auto_tracks
                          if t.get("ElementCount", 0) >= largest_elem * 0.5]

            for t in auto_tracks:
                e = t.get("ElementCount", 0)
                if largest_elem > 0 and e < largest_elem * 0.2:
                    t["SubType"] = "FORCED"
                else:
                    t["SubType"] = "FULL"

            # SDH ? Comparer le plus gros au 2e plus gros parmi les FULL
            if len(full_sized) >= 2:
                second_largest = full_sized[-2].get("ElementCount", 0)
                if second_largest > 0 and largest_elem >= second_largest * 1.20:
                    auto_tracks[-1]["SubType"] = "SDH"


def _parse_with_ffprobe(ffprobe: str, file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    cmd = [ffprobe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0 or not result.stdout:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    
    info = json.loads(result.stdout)
    streams = info.get("streams", [])
    
    video = None
    audio = []
    subs = []
    
    for s in streams:
        stype = s.get("codec_type")
        tags = s.get("tags", {}) or {}
        
        if stype == "video" and not video:
            video = {
                "@type": "Video",
                "Format": s.get("codec_name"),
                "Height": str(s.get("height", "")),
                "Width": str(s.get("width", "")),
                "HDR_Format": "",
                "StreamOrder": s.get("index", 0),
                "Duration": s.get("duration"),
            }
        elif stype == "audio":
            lang = _normalize_language(tags.get("language", ""))
            a = {
                "@type": "Audio",
                "Language": lang,
                "Format": s.get("codec_name", ""),
                "Format_Commercial_IfAny": s.get("profile", ""),
                "BitRate": s.get("bit_rate", "0"),
                "ChannelLayout": s.get("channel_layout", ""),
                "Channels": str(s.get("channels", "")),
                "Title": tags.get("title", ""),
                "StreamOrder": s.get("index", 0),
            }
            audio.append(a)
        elif stype == "subtitle":
            lang = _normalize_language(tags.get("language", ""))
            t = {
                "@type": "Text",
                "Language": lang,
                "Format": s.get("codec_name", ""),
                "Title": tags.get("title", ""),
                "StreamOrder": s.get("index", 0),
            }
            subs.append(t)
    
    return video, audio, subs


def parse_mediainfo(file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    """Parse un fichier MKV"""
    
    _wait_file_stable(file, attempts=15, interval_s=0.5)
    
    mediainfo = _find_mediainfo()
    if mediainfo:
        print(f"[DEBUG] MediaInfo: {mediainfo}")
        try:
            return _parse_with_mediainfo(mediainfo, file)
        except Exception as e:
            print(f"[WARN] MediaInfo failed: {e}")
    
    ffprobe = _find_ffprobe()
    if ffprobe:
        print(f"[DEBUG] ffprobe: {ffprobe}")
        return _parse_with_ffprobe(ffprobe, file)
    
    raise RuntimeError(
        "MediaInfo/ffprobe introuvable!\n"
        "Place MediaInfo.exe dans tools/ ou un sous-dossier"
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python mediainfo_parse.py <file.mkv>")
        sys.exit(1)
    
    v, a, s = parse_mediainfo(sys.argv[1])
    print(f"\nVideo: {v.get('Format') if v else 'N/A'}")
    print(f"Audio: {len(a)} piste(s)")
    print(f"Subs: {len(s)} piste(s)")
