#!/usr/bin/env python3
"""
Remux Tool - Extraction Blu-ray (ISO/BDMV) → Remux MKV
Mode AUTO (--auto) ou MANUEL (interactif avec choix)

Workflow:
1. Analyse du disque (rapide ~30s)
2. Affichage et sélection des pistes VIDEO/AUDIO/SOUS-TITRES
3. Extraction MakeMKV des pistes sélectionnées
4. Remux MKVToolNix avec métadonnées
"""

import os
import sys
import shutil
import platform
import glob
import argparse
from typing import List, Optional, Dict, Any

# ===== Configuration =====
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from config import RELEASE_GROUP, FULL_DIR, OUTPUT_DIR, TOOLS_DIR, KEEP_ENGLISH_SUBS, IS_CUSTOM
    TOOLS_DIR = os.path.join(SCRIPT_DIR, TOOLS_DIR) if not os.path.isabs(TOOLS_DIR) else TOOLS_DIR
    FULL_DIR = os.path.join(SCRIPT_DIR, FULL_DIR) if not os.path.isabs(FULL_DIR) else FULL_DIR
    OUTPUT_ROOT = os.path.join(SCRIPT_DIR, OUTPUT_DIR) if not os.path.isabs(OUTPUT_DIR) else OUTPUT_DIR
except ImportError:
    RELEASE_GROUP = ""
    TOOLS_DIR = os.path.join(SCRIPT_DIR, "tools")
    FULL_DIR = os.path.join(SCRIPT_DIR, "FULL")
    OUTPUT_ROOT = os.path.join(SCRIPT_DIR, "OUTPUT")
    KEEP_ENGLISH_SUBS = 1
    IS_CUSTOM = 0

AUTO_MODE = False


def _is_windows():
    return platform.system().lower().startswith("win")


def _find_in_tools(exe_name: str) -> Optional[str]:
    if not os.path.isdir(TOOLS_DIR):
        return None
    for pattern in [os.path.join(TOOLS_DIR, exe_name), os.path.join(TOOLS_DIR, "**", exe_name)]:
        matches = glob.glob(pattern, recursive=True)
        for m in matches:
            if os.path.isfile(m):
                return m
    return None


def _find_tool(name: str, candidates: List[str]) -> Optional[str]:
    found = _find_in_tools(name + (".exe" if _is_windows() else ""))
    if found:
        return found
    path = shutil.which(name)
    if path:
        return path
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def detect_tools() -> dict:
    found = {
        "makemkvcon": _find_tool("makemkvcon", [
            r"C:\Program Files (x86)\MakeMKV\makemkvcon.exe",
            r"C:\Program Files\MakeMKV\makemkvcon.exe",
        ]),
        "mkvmerge": _find_tool("mkvmerge", [
            r"C:\Program Files\MKVToolNix\mkvmerge.exe",
        ]),
    }
    
    print("\n==============================")
    print("Detection des outils")
    print("==============================")
    for k, p in found.items():
        print(f"  [{'OK' if p else 'X'}] {k}")
    
    return found


from makemkv_extract import analyze_source, extract_title, get_stream_type, is_french_stream, is_english_stream
from mkvtoolnix_remux import run_mkvmerge


# ===== Helpers =====

def _to_title_case_dotted(raw_name: str) -> str:
    name = os.path.splitext(raw_name)[0]
    name = name.replace("_", " ").replace(".", " ")
    parts = name.split()
    titled = [p.capitalize() for p in parts if p]
    return ".".join(titled)


def _list_movies() -> List[str]:
    if not os.path.isdir(FULL_DIR):
        os.makedirs(FULL_DIR, exist_ok=True)
        return []
    entries = os.listdir(FULL_DIR)
    return [e for e in entries if os.path.isdir(os.path.join(FULL_DIR, e)) or e.lower().endswith('.iso')]


def _get_source_path(entry: str) -> str:
    base = os.path.join(FULL_DIR, entry)
    if os.path.isfile(base) and entry.lower().endswith('.iso'):
        return base
    if os.path.isdir(base):
        isos = [f for f in os.listdir(base) if f.lower().endswith('.iso')]
        if isos:
            return os.path.join(base, isos[0])
        bdmv = os.path.join(base, 'BDMV')
        if os.path.isdir(bdmv):
            return bdmv
    raise FileNotFoundError(f"Source introuvable pour {entry}")


def _select_multiple(prompt: str, max_val: int, default: List[int] = None) -> List[int]:
    """Parse une sélection multiple (ex: '1,3,4' ou '1-3' ou 'all')"""
    choice = input(prompt).strip().lower()
    if not choice:
        return default or []
    if choice == 'all':
        return list(range(1, max_val + 1))
    if choice == 'none' or choice == '0':
        return []
    
    selected = []
    parts = choice.replace(' ', '').split(',')
    for p in parts:
        if '-' in p:
            try:
                start, end = p.split('-')
                for i in range(int(start), int(end) + 1):
                    if 1 <= i <= max_val and i not in selected:
                        selected.append(i)
            except:
                pass
        elif p.isdigit():
            i = int(p)
            if 1 <= i <= max_val and i not in selected:
                selected.append(i)
    return selected


def _detect_vf_type(stream: dict) -> Optional[str]:
    name = (stream.get("name") or "").upper()
    lang = (stream.get("lang") or "").upper()
    combined = f"{name} {lang}"
    
    if "VFF" in combined or "FRANCE" in combined:
        return "VFF"
    if "VFQ" in combined or "QUEBEC" in combined or "QUÉBEC" in combined:
        return "VFQ"
    if "VFI" in combined:
        return "VFi"
    return None


def _classify_subtitle(stream: dict) -> str:
    name = (stream.get("name") or "").upper()
    if "FORCED" in name:
        return "FORCED"
    if "COMMENT" in name:
        return "COMMENTARY"
    if "SDH" in name:
        return "SDH"
    if "FULL" in name or "COMPLET" in name:
        return "FULL"
    return "NORMAL"


def _format_duration(dur_str: str) -> str:
    """Format duration string"""
    if not dur_str:
        return "?"
    return dur_str


def _format_size(size_bytes: int) -> str:
    """Format size in GB"""
    if not size_bytes:
        return "?"
    return f"{size_bytes / (1024**3):.1f} GB"


def build_final_name(movie: str, year: str, lang_tag: str, resolution: str,
                     is_uhd: bool, codec: str, hdr: str, audio_codec: str = "",
                     is_custom: bool = False) -> str:
    """
    Format: Film.Titre.ANNEE.[CUSTOM].LANGUE.RESOLUTION.SOURCE.[HDR].AUDIO.CODEC[-GROUP].mkv
    Exemple: Largo.Winch.2024.CUSTOM.MULTi.VFF.2160p.UHD.BluRay.REMUX.HDR10+.TrueHD.7.1.HEVC-REBiRTH.mkv
    """
    parts = [movie, year]
    
    # CUSTOM (optionnel)
    if is_custom:
        parts.append("CUSTOM")
    
    if lang_tag:
        parts.append(lang_tag)
    parts.append(resolution)
    
    if is_uhd:
        parts.append("UHD.BluRay.REMUX")
    else:
        parts.append("BluRay.REMUX")

    # HDR AVANT Audio. Sur UHD sans Dolby Vision ni HDR → SDR explicite.
    # Sur 1080p Blu-ray on n'ajoute rien (SDR implicite).
    if hdr:
        parts.append(hdr)
    elif is_uhd:
        parts.append("SDR")
    
    # Codec audio (ex: TrueHD.7.1)
    if audio_codec:
        parts.append(audio_codec)
    
    # Codec vidéo
    parts.append(codec)
    
    name = ".".join(parts)
    if RELEASE_GROUP:
        name += f"-{RELEASE_GROUP}"
    name += ".mkv"
    while ".." in name:
        name = name.replace("..", ".")
    return name


# ===== Workflow =====

def run_workflow(movie_entry: str, auto_mode: bool = False):
    print(f"\n{'='*60}")
    print(f"Film: {movie_entry}")
    print(f"Mode: {'AUTO' if auto_mode else 'MANUEL'}")
    print(f"{'='*60}")
    
    source_path = _get_source_path(movie_entry)
    movie_name = os.path.splitext(movie_entry)[0] if movie_entry.lower().endswith('.iso') else movie_entry
    output_dir = os.path.join(OUTPUT_ROOT, movie_name)
    
    # === Étape 1: Analyse ===
    print("\n[ETAPE 1/3] Analyse du disque...")
    
    info = analyze_source(source_path)
    titles = info.get("titles", [])
    
    if not titles:
        print("[ERREUR] Aucun titre trouve!")
        return
    
    # === Sélection du titre ===
    print(f"\n{'='*60}")
    print("TITRES DISPONIBLES")
    print(f"{'='*60}")
    
    for i, title in enumerate(titles, 1):
        dur = _format_duration(title.get("duration", ""))
        size = _format_size(title.get("size_bytes", 0))
        chaps = title.get("chapters", 0)
        name = title.get("name", f"title_{title['id']}")
        
        # Compter les streams
        streams = title.get("streams", [])
        n_video = len([s for s in streams if get_stream_type(s) == "video"])
        n_audio = len([s for s in streams if get_stream_type(s) == "audio"])
        n_subs = len([s for s in streams if get_stream_type(s) == "subtitle"])
        
        print(f"  {i}. {name}")
        print(f"     Duree: {dur} | Taille: {size} | Chapitres: {chaps}")
        print(f"     Pistes: {n_video} video, {n_audio} audio, {n_subs} sous-titres")
    
    # Trouver le titre le plus long (film principal)
    def _parse_duration(dur_str: str) -> int:
        """Convertit durée HH:MM:SS en secondes"""
        if not dur_str:
            return 0
        parts = dur_str.split(':')
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(parts[0])
        except:
            return 0
    
    # Trier par durée et trouver le plus long
    titles_with_dur = [(i+1, t, _parse_duration(t.get("duration", ""))) for i, t in enumerate(titles)]
    longest = max(titles_with_dur, key=lambda x: x[2])
    longest_idx = longest[0]
    longest_dur = longest[1].get("duration", "?")
    
    print(f"\n  [AUTO] Titre principal detecte: #{longest_idx} (duree: {longest_dur})")
    
    if auto_mode:
        selected_title_idx = longest_idx
    else:
        if len(titles) == 1:
            selected_title_idx = 1
        else:
            try:
                choice = input(f"\nSelectionner le titre (1-{len(titles)}) [{longest_idx}]: ").strip()
                selected_title_idx = int(choice) if choice else longest_idx
                if selected_title_idx < 1 or selected_title_idx > len(titles):
                    selected_title_idx = longest_idx
            except:
                selected_title_idx = longest_idx
    
    selected_title = titles[selected_title_idx - 1]
    title_id = selected_title["id"]
    streams = selected_title.get("streams", [])
    
    print(f"\n  -> Titre selectionne: {selected_title.get('name', f'title_{title_id}')}")
    
    # === Sélection des pistes ===
    
    # Séparer par type
    video_streams = [s for s in streams if get_stream_type(s) == "video"]
    audio_streams = [s for s in streams if get_stream_type(s) == "audio"]
    sub_streams = [s for s in streams if get_stream_type(s) == "subtitle"]
    
    # Filtrer audio: EN + FR seulement
    en_audio = [s for s in audio_streams if is_english_stream(s)]
    fr_audio = [s for s in audio_streams if is_french_stream(s)]
    valid_audio = en_audio + fr_audio
    
    # Filtrer subs: FR seulement
    fr_subs = [s for s in sub_streams if is_french_stream(s)]
    
    # === VIDEO ===
    print(f"\n{'='*60}")
    print("VIDEO")
    print(f"{'='*60}")
    
    for i, s in enumerate(video_streams, 1):
        codec = s.get("codec", "?")
        info_str = s.get("info", "") or s.get("resolution", "")
        print(f"  {i}. {codec} {info_str}")
    
    if auto_mode or len(video_streams) == 1:
        selected_video = [video_streams[0]] if video_streams else []
    else:
        indices = _select_multiple(f"  Selectionner video (1-{len(video_streams)}) [1]: ", 
                                   len(video_streams), [1])
        if not indices:
            indices = [1]
        selected_video = [video_streams[i-1] for i in indices]
    
    # Détecter résolution et HDR
    resolution = "1080p"
    codec = "AVC"
    is_uhd = False
    hdr = ""
    
    if selected_video:
        v = selected_video[0]
        info_str = (v.get("info") or v.get("resolution") or "").lower()
        codec_str = (v.get("codec") or "").upper()
        
        if "2160" in info_str or "4k" in info_str or "uhd" in info_str:
            resolution = "2160p"
            is_uhd = True
        
        if "HEVC" in codec_str or "H.265" in codec_str or "H265" in codec_str:
            codec = "HEVC"
        elif "AVC" in codec_str or "H.264" in codec_str or "H264" in codec_str:
            codec = "AVC"
        
        if "dolby vision" in info_str.lower() or "dv" in info_str.lower():
            hdr = "DV.HDR10" if "hdr10" in info_str.lower() else "DV"
        elif "hdr10+" in info_str.lower():
            hdr = "HDR10Plus"
        elif "hdr" in info_str.lower():
            hdr = "HDR10"
    
    # === AUDIO ===
    print(f"\n{'='*60}")
    print("AUDIO (EN + FR)")
    print(f"{'='*60}")
    
    if not valid_audio:
        print("  Aucune piste EN/FR!")
        selected_audio_streams = []
    else:
        # Fonction de score qualité
        def _audio_quality(s):
            codec = (s.get("codec") or "").upper()
            score = 0
            if "DTS-HD" in codec or "MASTER" in codec:
                score = 500
            elif "TRUEHD" in codec or "ATMOS" in codec:
                score = 450
            elif "DTS" in codec:
                score = 300
            elif "DD" in codec or "AC3" in codec or "AC-3" in codec:
                score = 200
            return score
        
        # Trier par qualité
        en_audio.sort(key=_audio_quality, reverse=True)
        fr_audio.sort(key=_audio_quality, reverse=True)
        
        # Afficher toutes les pistes
        all_audio = en_audio + fr_audio
        for i, s in enumerate(all_audio, 1):
            is_en = is_english_stream(s)
            
            codec = s.get("codec", "?")
            name = s.get("name", "")
            info_str = s.get("info", "")
            lang_long = s.get("lang", "")  # "French", "English"
            lang_code = s.get("lang_code", "")  # "fra", "eng", "fr-ca"
            description = s.get("description", "")
            metadata = s.get("metadata", "")
            lang_ext = s.get("lang_ext", "")
            
            # Détecter VF type
            vf_type = _detect_vf_type(s)
            
            # Chercher des indices de région dans tous les champs
            all_text = f"{name} {lang_long} {description} {metadata} {lang_ext}".upper()
            if not vf_type:
                if "CANADA" in all_text or "QUEBEC" in all_text or "QUÉBEC" in all_text or lang_code == "fr-ca":
                    vf_type = "VFQ"
                    s["_detected_vf"] = "VFQ"
                elif "FRANCE" in all_text or lang_code == "fr-fr":
                    vf_type = "VFF"
                    s["_detected_vf"] = "VFF"
            
            # Construire l'affichage
            lang_tag = "[EN]" if is_en else "[FR]"
            vf_str = f"[{vf_type}]" if vf_type else ""
            
            # Afficher le nom le plus descriptif
            display_name = name if name else lang_long
            if description and description != name:
                display_name = f"{display_name} ({description})" if display_name else description
            
            quality = _audio_quality(s)
            best_marker = " *" if (is_en and s == en_audio[0]) or (not is_en and fr_audio and s == fr_audio[0]) else ""
            
            print(f"  {i}. {lang_tag} {codec} {vf_str} - {display_name}{best_marker}".strip())
        
        # Proposer une sélection par défaut
        default_indices = []
        if en_audio:
            default_indices.append(all_audio.index(en_audio[0]) + 1)
        
        # VF: garder une par type (VFF, VFQ, VFi)
        vf_seen = set()
        for s in fr_audio:
            vf_type = _detect_vf_type(s)
            if vf_type not in vf_seen:
                vf_seen.add(vf_type)
                default_indices.append(all_audio.index(s) + 1)
        
        default_str = ",".join(map(str, sorted(default_indices)))
        
        print(f"\n  (* = meilleure qualite par langue/type)")
        choice = input(f"  Selectionner audio (ex: 1,2 ou all) [{default_str}]: ").strip()
        
        if not choice:
            choice = default_str
        
        if choice.lower() == "all":
            selected_audio_streams = all_audio[:]
        else:
            try:
                indices = [int(x.strip()) for x in choice.split(",") if x.strip()]
                selected_audio_streams = [all_audio[i-1] for i in indices if 1 <= i <= len(all_audio)]
            except:
                # Fallback: meilleure EN + meilleure FR
                selected_audio_streams = []
                if en_audio:
                    selected_audio_streams.append(en_audio[0])
                if fr_audio:
                    selected_audio_streams.append(fr_audio[0])
    
    print(f"\n  -> {len(selected_audio_streams)} piste(s) audio selectionnee(s)")
    
    # === SOUS-TITRES ===
    print(f"\n{'='*60}")
    sub_langs = "FR + EN" if KEEP_ENGLISH_SUBS else "FR"
    print(f"SOUS-TITRES ({sub_langs})")
    print(f"{'='*60}")
    
    # Collecter FR
    selected_sub_streams = []
    if fr_subs:
        for s in fr_subs:
            s["SubLang"] = "fr"
            selected_sub_streams.append(s)
        print(f"  [FR] {len(fr_subs)} sous-titre(s)")
    else:
        print("  [FR] Aucun")
    
    # Collecter EN si activé
    en_subs = [s for s in streams if get_stream_type(s) == "subtitle" and is_english_stream(s)]
    if KEEP_ENGLISH_SUBS and en_subs:
        for s in en_subs:
            s["SubLang"] = "en"
            selected_sub_streams.append(s)
        print(f"  [EN] {len(en_subs)} sous-titre(s)")
    elif KEEP_ENGLISH_SUBS:
        print("  [EN] Aucun")
    
    print(f"\n  -> {len(selected_sub_streams)} sous-titre(s) total")
    
    # === Demander l'année et lancer extraction ===
    print(f"\n{'='*60}")
    print("EXTRACTION")
    print(f"{'='*60}")
    
    movie_title = _to_title_case_dotted(movie_name)
    print(f"  Titre: {movie_title}")
    
    year = input(f"  Annee du film: ").strip()
    if not year:
        year = "2025"
    
    if not auto_mode:
        confirm = input("\n  Lancer extraction? [O/n]: ").strip().lower()
        if confirm == 'n':
            print("  Annule.")
            return
    
    # === Étape 2: Extraction ===
    print(f"\n{'='*60}")
    print("[ETAPE 2/4] Extraction MakeMKV")
    print(f"{'='*60}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Collecter les IDs de streams sélectionnés
    selected_stream_ids = []
    for s in selected_video:
        selected_stream_ids.append(s.get("id"))
    for s in selected_audio_streams:
        selected_stream_ids.append(s.get("id"))
    for s in selected_sub_streams:
        selected_stream_ids.append(s.get("id"))
    
    mkv_path = extract_title(
        source=source_path,
        title_id=title_id,
        output_dir=output_dir,
        selected_streams=selected_stream_ids
    )
    
    # === Étape 3: Analyse MediaInfo post-extraction ===
    print(f"\n{'='*60}")
    print("[ETAPE 3/4] Analyse MediaInfo")
    print(f"{'='*60}")
    
    from mediainfo_parse import parse_mediainfo
    video_info, audio_tracks, sub_tracks = parse_mediainfo(mkv_path)
    
    # Détecter résolution et HDR depuis MediaInfo (plus précis)
    if video_info:
        height = str(video_info.get("Height", ""))
        if "2160" in height:
            resolution = "2160p"
            is_uhd = True
        
        codec_str = (video_info.get("Format", "") or "").upper()
        if "HEVC" in codec_str or "265" in codec_str:
            codec = "HEVC"
        elif "AVC" in codec_str or "264" in codec_str:
            codec = "AVC"
        elif "AV1" in codec_str:
            codec = "AV1"
        elif "VP9" in codec_str:
            codec = "VP9"
        
        hdr_info  = video_info.get("HDR_Format", "") or ""
        hdr_compat = video_info.get("HDR_Format_Compatibility", "") or ""
        hdr_blob  = f"{hdr_info} | {hdr_compat}"
        if "Dolby Vision" in hdr_blob:
            if "HDR10+" in hdr_blob or "HDR10Plus" in hdr_blob:
                hdr = "DV.HDR10+"
            elif "HDR10" in hdr_blob:
                hdr = "DV.HDR10"
            else:
                hdr = "DV"
        elif "HDR10+" in hdr_blob or "HDR10Plus" in hdr_blob:
            hdr = "HDR10+"
        elif "HDR10" in hdr_blob or "HDR" in hdr_blob:
            hdr = "HDR10"
    
    # Afficher et analyser les pistes audio
    print(f"\n  Pistes audio:")
    vf_types_found = []
    has_en = False
    has_fr = False
    best_audio_info = None  # Pour le nom du fichier
    
    for t in audio_tracks:
        lang = (t.get("Language") or "").lower()
        lang_string = t.get("Language_String") or t.get("Language_String3") or ""
        lang_more = t.get("Language_More") or ""  # Peut contenir "Canada", "France"
        title = t.get("Title") or ""
        fmt = t.get("Format_Commercial_IfAny") or t.get("Format") or "?"
        chan = t.get("ChannelLayout") or ""
        channels = t.get("Channels") or ""
        
        # Construire le channel string propre
        if chan:
            # Nettoyer le ChannelLayout (ex: "L R C LFE Ls Rs" -> "5.1")
            ch_count = len(chan.split())
            if "LFE" in chan:
                ch_count -= 1
                ch_str = f"{ch_count}.1"
            else:
                ch_str = f"{ch_count}.0"
        elif channels:
            ch_num = int(channels) if str(channels).isdigit() else 0
            if ch_num >= 8:
                ch_str = "7.1"
            elif ch_num >= 6:
                ch_str = "5.1"
            elif ch_num >= 2:
                ch_str = "2.0"
            else:
                ch_str = str(channels)
        else:
            ch_str = ""
        
        # Détecter VF type depuis Title ou Language_More
        vf_type = None
        title_upper = title.upper()
        lang_more_upper = lang_more.upper()
        
        if "VFF" in title_upper or "FRANCE" in title_upper or "FRANCE" in lang_more_upper:
            vf_type = "VFF"
        elif "VFQ" in title_upper or "QUEBEC" in title_upper or "QUÉBEC" in title_upper or \
             "CANADA" in lang_more_upper or "QUEBEC" in lang_more_upper or lang == "fr-ca":
            vf_type = "VFQ"
        elif "VFI" in title_upper or "INTERNATIONAL" in title_upper:
            vf_type = "VFi"
        
        # Stocker le type détecté
        t["_detected_vf"] = vf_type
        
        is_fr = lang in ("fr", "fra", "fre", "french", "fr-fr", "fr-ca") or \
                any(x in title.lower() for x in ["french", "français", "vf"])
        is_en_track = lang in ("en", "eng", "english", "en-us", "en-gb") or "english" in title.lower()
        
        # Garder les infos de la meilleure piste (EN prioritaire, sinon FR)
        if is_en_track and not best_audio_info:
            best_audio_info = t
        elif is_fr and not best_audio_info:
            best_audio_info = t
        
        if is_en_track:
            has_en = True
            # Affichage propre: [EN] TrueHD Atmos 7.1 - Title
            display_title = title if title else lang_string
            print(f"    [EN] {fmt} {ch_str} - {display_title}")
        elif is_fr:
            has_fr = True
            if vf_type:
                vf_types_found.append(vf_type)
            
            vf_str = f"[{vf_type}]" if vf_type else ""
            # Afficher le titre ou la région détectée
            display_title = title if title else (lang_more if lang_more else lang_string)
            print(f"    [FR] {fmt} {ch_str} {vf_str} - {display_title}")
    
    # Construire le codec audio pour le nom du fichier (ex: DTS-HD.MA.7.1)
    audio_codec_str = ""
    if best_audio_info:
        fmt = best_audio_info.get("Format_Commercial_IfAny") or best_audio_info.get("Format") or ""
        fmt = fmt.upper()
        
        # Convertir en format standard (convention : AC3 / EAC3 / DTS-HD.MA / TrueHD)
        if "DTS-HD" in fmt or "MASTER" in fmt:
            audio_fmt = "DTS-HD.MA"
        elif "TRUEHD" in fmt:
            if "ATMOS" in fmt:
                audio_fmt = "TrueHD.Atmos"
            else:
                audio_fmt = "TrueHD"
        elif "DTS" in fmt:
            audio_fmt = "DTS"
        elif "DD+" in fmt or "E-AC" in fmt or "PLUS" in fmt or "DDP" in fmt:
            audio_fmt = "EAC3"
        elif "AC3" in fmt or "AC-3" in fmt or "DOLBY DIGITAL" in fmt or "DD" in fmt:
            audio_fmt = "AC3"
        else:
            audio_fmt = ""
        
        # Canaux
        ch_count = best_audio_info.get("Channels")
        if ch_count:
            ch_num = int(ch_count) if str(ch_count).isdigit() else 0
            if ch_num >= 8:
                audio_ch = "7.1"
            elif ch_num >= 6:
                audio_ch = "5.1"
            elif ch_num >= 2:
                audio_ch = "2.0"
            else:
                audio_ch = ""
        else:
            audio_ch = ""
        
        if audio_fmt and audio_ch:
            audio_codec_str = f"{audio_fmt}.{audio_ch}"
        elif audio_fmt:
            audio_codec_str = audio_fmt
    
    # Déterminer le tag VF
    vf_tag = None
    if has_fr:
        if "VFF" in vf_types_found and "VFQ" in vf_types_found:
            vf_tag = "VF2"
            print(f"\n  -> VF2 detecte (VFF + VFQ)")
        elif "VFF" in vf_types_found:
            vf_tag = "VFF"
            print(f"\n  -> VFF detecte")
        elif "VFQ" in vf_types_found:
            vf_tag = "VFQ"
            print(f"\n  -> VFQ detecte")
        elif "VFi" in vf_types_found:
            vf_tag = "VFi"
            print(f"\n  -> VFi detecte")
        else:
            # Pas détecté - demander
            print(f"\n  Type VF non detecte. Choisir:")
            print(f"    1. VFF (France)")
            print(f"    2. VFQ (Quebec)")
            print(f"    3. VFi (International)")
            print(f"    4. VF2 (VFF + VFQ)")
            choice = input(f"  Choix [1]: ").strip()
            if choice == "2":
                vf_tag = "VFQ"
            elif choice == "3":
                vf_tag = "VFi"
            elif choice == "4":
                vf_tag = "VF2"
            else:
                vf_tag = "VFF"
    
    # Construire le tag langue
    is_multi = has_en and has_fr
    if is_multi:
        lang_tag = f"MULTi.{vf_tag}" if vf_tag else "MULTi"
    else:
        lang_tag = vf_tag or ("FRENCH" if has_fr else "ENGLISH" if has_en else "")
    
    # === Nom final ===
    print(f"\n{'='*60}")
    print("NOM DU FICHIER")
    print(f"{'='*60}")
    
    print(f"  Titre: {movie_title}")
    print(f"  Annee: {year}")
    print(f"  Langue: {lang_tag}")
    print(f"  Resolution: {resolution}")
    print(f"  Audio: {audio_codec_str}")
    if hdr:
        print(f"  HDR: {hdr}")
    
    final_name = build_final_name(
        movie=movie_title,
        year=year,
        lang_tag=lang_tag,
        resolution=resolution,
        is_uhd=is_uhd,
        codec=codec,
        hdr=hdr,
        audio_codec=audio_codec_str,
        is_custom=bool(IS_CUSTOM)
    )
    
    print(f"\n  Nom final: {final_name}")
    
    # === Étape 4: Remux ===
    print(f"\n{'='*60}")
    print("[ETAPE 4/4] Remux MKVToolNix")
    print(f"{'='*60}")
    
    final_path = os.path.join(output_dir, final_name)
    
    # Filtrer: garder seulement EN + FR, et seulement la MEILLEURE par langue
    def audio_quality_score(t):
        """Score de qualité audio (plus haut = meilleur)"""
        fmt = (t.get("Format_Commercial_IfAny") or t.get("Format") or "").upper()
        score = 0
        if "DTS-HD" in fmt or "MASTER" in fmt:
            score = 500
        elif "TRUEHD" in fmt or "ATMOS" in fmt:
            score = 450
        elif "DTS" in fmt and "DTS-HD" not in fmt:
            score = 300
        elif "DD+" in fmt or "E-AC" in fmt or "PLUS" in fmt:
            score = 250
        elif "AC3" in fmt or "AC-3" in fmt or "DD" in fmt:
            score = 200
        
        # Bonus pour plus de canaux
        ch = t.get("Channels")
        if ch:
            try:
                score += int(ch) * 10
            except:
                pass
        return score
    
    en_tracks = []
    fr_tracks = []
    
    for t in audio_tracks:
        lang = (t.get("Language") or "").lower()
        title = (t.get("Title") or "").upper()
        
        # Détection anglais
        is_en = False
        if lang in ("en", "eng", "english", "en-us", "en-gb"):
            is_en = True
        elif "ENGLISH" in title or "VO " in title or title.startswith("VO"):
            is_en = True
        elif not lang and not any(x in title for x in ["FRENCH", "FRANÇAIS", "FRANCAIS", "VF", "QUEBEC", "FRANCE"]):
            # Si pas de langue et pas de marqueur FR, supposer EN (VO)
            is_en = True
        
        # Détection français (toutes variantes)
        is_fr = False
        if lang in ("fr", "fra", "fre", "french", "fr-fr", "fr-ca", "fr-be", "fr-ch"):
            is_fr = True
            # Marquer VFQ si fr-ca (Québec)
            if lang == "fr-ca" and "VFQ" not in title and "QUEBEC" not in title:
                t["_detected_vf"] = "VFQ"
        elif any(x in title for x in ["FRENCH", "FRANÇAIS", "FRANCAIS", "VFF", "VFQ", "VFI", "VF2", "QUEBEC", "QUÉBEC", "FRANCE"]):
            is_fr = True
        
        # Détecter le type VF depuis le titre
        if is_fr and "_detected_vf" not in t:
            if "VFF" in title or "FRANCE" in title or "FR-FR" in title:
                t["_detected_vf"] = "VFF"
            elif "VFQ" in title or "QUEBEC" in title or "QUÉBEC" in title or "FR-CA" in title:
                t["_detected_vf"] = "VFQ"
            elif "VFI" in title or "INTERNATIONAL" in title:
                t["_detected_vf"] = "VFi"
        
        if is_en:
            en_tracks.append(t)
        elif is_fr:
            fr_tracks.append(t)
    
    # Trier par qualité
    en_tracks.sort(key=audio_quality_score, reverse=True)
    fr_tracks.sort(key=audio_quality_score, reverse=True)
    
    # Afficher toutes les pistes disponibles
    all_audio = en_tracks + fr_tracks
    print(f"\n  Pistes audio disponibles:")
    for i, t in enumerate(all_audio, 1):
        lang = (t.get("Language") or "?").upper()
        if lang in ("EN", "ENG", "EN-US", "EN-GB"):
            lang_tag = "EN"
        elif lang in ("FR", "FRA", "FRE", "FR-FR"):
            lang_tag = "FR"
        elif lang == "FR-CA":
            lang_tag = "FR-CA"
        else:
            lang_tag = lang[:2].upper() if lang else "?"
        
        fmt = t.get("Format_Commercial_IfAny") or t.get("Format") or "?"
        title = t.get("Title") or ""
        channels = t.get("Channels") or "?"
        ch_num = int(channels) if str(channels).isdigit() else 0
        if ch_num >= 8:
            ch_str = "7.1"
        elif ch_num >= 6:
            ch_str = "5.1"
        elif ch_num >= 2:
            ch_str = "2.0"
        else:
            ch_str = str(channels)
        
        vf_type = t.get("_detected_vf", "")
        vf_str = f"[{vf_type}]" if vf_type else ""
        
        print(f"    {i}. [{lang_tag}] {fmt} {ch_str} {vf_str} - {title}".strip())
    
    # Proposer une sélection par défaut (meilleure EN + toutes les VF)
    default_indices = []
    
    # Meilleure EN
    if en_tracks:
        idx = all_audio.index(en_tracks[0]) + 1
        default_indices.append(idx)
    
    # Toutes les VF par type
    vf_by_type = {}
    for t in fr_tracks:
        vf_type = t.get("_detected_vf")
        if vf_type not in vf_by_type:
            vf_by_type[vf_type] = t
            idx = all_audio.index(t) + 1
            default_indices.append(idx)
    
    default_str = ",".join(map(str, default_indices))
    
    # Demander à l'utilisateur
    print(f"\n  Selection auto: {default_str} (meilleure EN + VF par type)")
    choice = input(f"  Selectionner audio (ex: 1,2,3 ou all) [{default_str}]: ").strip()
    
    if not choice:
        choice = default_str
    
    if choice.lower() == "all":
        selected_indices = list(range(1, len(all_audio) + 1))
    else:
        try:
            selected_indices = [int(x.strip()) for x in choice.split(",") if x.strip()]
        except:
            selected_indices = default_indices
    
    # Construire la liste filtrée
    filtered_audio = []
    for idx in selected_indices:
        if 1 <= idx <= len(all_audio):
            filtered_audio.append(all_audio[idx - 1])
    
    # Afficher ce qui a été sélectionné
    vf_types_kept = [t.get("_detected_vf") for t in filtered_audio if t.get("_detected_vf")]
    if len(vf_types_kept) >= 2:
        print(f"\n  -> {len(filtered_audio)} piste(s): VO + {' + '.join(sorted(set(vf_types_kept)))}")
    elif vf_types_kept:
        print(f"\n  -> {len(filtered_audio)} piste(s): VO + {vf_types_kept[0]}")
    else:
        print(f"\n  -> {len(filtered_audio)} piste(s) selectionnee(s)")
    
    # Filtrer sous-titres: FR + EN (si activé dans config)
    filtered_subs = []
    for t in sub_tracks:
        lang = (t.get("Language") or "").lower()
        title = (t.get("Title") or "").lower()
        is_fr = lang in ("fr", "fra", "fre", "french") or any(x in title for x in ["french", "français"])
        is_en = lang in ("en", "eng", "english") or "english" in title
        
        if is_fr:
            t["SubLang"] = "fr"
            filtered_subs.append(t)
        elif is_en and KEEP_ENGLISH_SUBS:
            t["SubLang"] = "en"
            filtered_subs.append(t)
    
    # Afficher les sous-titres avec leur type
    if filtered_subs:
        print(f"\n  Sous-titres:")
        for t in filtered_subs:
            sub_type = t.get("SubType", "NORMAL")
            sub_lang = t.get("SubLang", "?").upper()
            title = t.get("Title") or ""
            fmt = t.get("Format") or "?"
            elements = t.get("ElementCount", 0)
            elem_str = f"({elements} elem)" if elements else ""
            print(f"    [{sub_lang}] [{sub_type}] {fmt} {elem_str} - {title}".strip())
    
    track_selection = {
        "selected_audio": filtered_audio,
        "selected_subs": filtered_subs,
        "vf_tag": vf_tag
    }
    
    rc = run_mkvmerge(mkv_path, track_selection, final_path)
    
    if rc != 0 or not os.path.isfile(final_path):
        print("[ERREUR] Remux echoue!")
        return
    
    # Cleanup - supprimer le MKV source
    if os.path.abspath(mkv_path) != os.path.abspath(final_path):
        try:
            os.remove(mkv_path)
        except:
            pass
    
    file_size = os.path.getsize(final_path)
    size_gb = file_size / (1024**3)
    
    # === Générer le NFO ===
    print(f"\n  Generation du NFO...")
    from nfo_generator import generate_nfo
    
    nfo_path = generate_nfo(
        output_path=final_path,
        movie_title=movie_title.replace(".", " "),
        year=year,
        video_info=video_info or {},
        audio_tracks=filtered_audio,
        sub_tracks=filtered_subs,
        file_size_bytes=file_size,
        release_group=RELEASE_GROUP,
        is_custom=bool(IS_CUSTOM)
    )
    
    print(f"  NFO: {os.path.basename(nfo_path)}")
    
    print(f"\n{'='*60}")
    print("TERMINE!")
    print(f"{'='*60}")
    print(f"  Fichier: {final_name}")
    print(f"  NFO:     {os.path.basename(nfo_path)}")
    print(f"  Taille:  {size_gb:.1f} GB")
    print(f"  Chemin:  {final_path}")
    print(f"{'='*60}\n")


def main():
    global AUTO_MODE
    
    parser = argparse.ArgumentParser(description="Remux Tool")
    parser.add_argument("--auto", action="store_true", help="Mode automatique")
    parser.add_argument("--film", type=int, help="Numero du film")
    args = parser.parse_args()
    
    AUTO_MODE = args.auto
    
    tools = detect_tools()
    missing = [k for k, v in tools.items() if not v]
    if missing:
        print(f"\n[ERREUR] Outils manquants: {', '.join(missing)}")
        sys.exit(1)
    
    os.makedirs(FULL_DIR, exist_ok=True)
    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    
    movies = _list_movies()
    if not movies:
        print(f"\n[ERREUR] Aucun film dans {FULL_DIR}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Films disponibles ({len(movies)})")
    print(f"{'='*60}")
    for i, m in enumerate(movies, 1):
        print(f"  {i}. {m}")
    
    if AUTO_MODE:
        selection = args.film if args.film and 1 <= args.film <= len(movies) else 1
        print(f"\n[AUTO] Film: {movies[selection - 1]}")
    else:
        try:
            selection = int(input(f"\nSelectionner un film (1-{len(movies)}): ").strip())
            if selection < 1 or selection > len(movies):
                raise ValueError()
        except:
            print("[ERREUR] Selection invalide")
            sys.exit(1)
    
    run_workflow(movies[selection - 1], auto_mode=AUTO_MODE)


if __name__ == "__main__":
    main()
