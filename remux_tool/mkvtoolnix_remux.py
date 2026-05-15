#!/usr/bin/env python3
"""
MKVToolNix Remux - Remux avec pistes sélectionnées
"""

import subprocess
import os
import re
import shutil
import json
import time
import sys
import glob
from typing import List, Dict, Any, Optional

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


def _find_mkvmerge() -> str:
    for name in ["mkvmerge.exe", "mkvmerge"]:
        found = _find_in_tools(name)
        if found:
            return found
    path = shutil.which("mkvmerge")
    if path:
        return path
    candidates = [r"C:\Program Files\MKVToolNix\mkvmerge.exe", "/opt/homebrew/bin/mkvmerge"]
    for p in candidates:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError("mkvmerge introuvable.")


def _lang3(code: str) -> str:
    if not code:
        return "und"
    code = code.lower().strip()
    if len(code) == 3 and code.isalpha():
        return code
    mapping = {
        "en": "eng", "fr": "fra", "es": "spa", "de": "deu",
        "it": "ita", "pt": "por", "ja": "jpn", "ko": "kor",
        "zh": "zho", "ru": "rus", "nl": "nld", "pl": "pol",
        "ar": "ara", "hi": "hin", "th": "tha", "sv": "swe",
        "no": "nor", "da": "dan", "fi": "fin", "cs": "ces",
        "hu": "hun", "tr": "tur", "uk": "ukr", "he": "heb",
    }
    return mapping.get(code, "und")


def _normalize_lang(lang: str) -> str:
    if not lang:
        return ""
    lang = lang.lower().strip()
    mapping = {
        # Anglais
        "eng": "en", "english": "en",
        # Français
        "fra": "fr", "fre": "fr", "french": "fr", "français": "fr",
        # Japonais
        "jpn": "ja", "japanese": "ja", "japonais": "ja",
        # Espagnol
        "spa": "es", "spanish": "es", "espagnol": "es",
        # Allemand
        "deu": "de", "ger": "de", "german": "de", "deutsch": "de", "allemand": "de",
        # Italien
        "ita": "it", "italian": "it", "italiano": "it", "italien": "it",
        # Portugais
        "por": "pt", "portuguese": "pt", "portugais": "pt",
        # Coréen
        "kor": "ko", "korean": "ko", "coréen": "ko", "coreen": "ko",
        # Chinois
        "zho": "zh", "chi": "zh", "chinese": "zh", "chinois": "zh",
        # Russe
        "rus": "ru", "russian": "ru", "russe": "ru",
        # Néerlandais
        "nld": "nl", "dut": "nl", "dutch": "nl", "néerlandais": "nl",
        # Polonais
        "pol": "pl", "polish": "pl", "polonais": "pl",
        # Arabe
        "ara": "ar", "arabic": "ar", "arabe": "ar",
        # Hindi
        "hin": "hi", "hindi": "hi",
        # Thaï
        "tha": "th", "thai": "th",
        # Suédois
        "swe": "sv", "swedish": "sv", "suédois": "sv",
        # Norvégien
        "nor": "no", "norwegian": "no", "norvégien": "no",
        # Danois
        "dan": "da", "danish": "da", "danois": "da",
        # Finnois
        "fin": "fi", "finnish": "fi", "finnois": "fi",
        # Tchèque
        "ces": "cs", "cze": "cs", "czech": "cs", "tchèque": "cs",
        # Hongrois
        "hun": "hu", "hungarian": "hu", "hongrois": "hu",
        # Turc
        "tur": "tr", "turkish": "tr", "turc": "tr",
        # Ukrainien
        "ukr": "uk", "ukrainian": "uk",
        # Hébreu
        "heb": "he", "hebrew": "he",
    }
    return mapping.get(lang, lang[:2] if len(lang) >= 2 else lang)


# Noms humains → code 2 lettres (détection depuis le titre de piste)
_TITLE_LANG_KEYWORDS = [
    ("ja", ["japonais", "japanese", "japan"]),
    ("es", ["espagnol", "español", "spanish"]),
    ("de", ["allemand", "german", "deutsch"]),
    ("it", ["italien", "italian", "italiano"]),
    ("pt", ["portugais", "portuguese", "português", "bresilien", "brésilien"]),
    ("ko", ["coréen", "coreen", "korean"]),
    ("zh", ["chinois", "chinese", "mandarin", "cantonais", "cantonnais"]),
    ("ru", ["russe", "russian"]),
    ("nl", ["néerlandais", "neerlandais", "dutch", "flamand"]),
    ("pl", ["polonais", "polish"]),
    ("ar", ["arabe", "arabic"]),
    ("hi", ["hindi"]),
    ("th", ["thaï", "thai"]),
    ("sv", ["suédois", "suedois", "swedish"]),
    ("no", ["norvégien", "norvegien", "norwegian"]),
    ("da", ["danois", "danish"]),
    ("fi", ["finnois", "finnish"]),
    ("cs", ["tchèque", "tcheque", "czech"]),
    ("hu", ["hongrois", "hungarian"]),
    ("tr", ["turc", "turkish"]),
    ("uk", ["ukrainien", "ukrainian"]),
    ("he", ["hébreu", "hebreu", "hebrew"]),
]

# Correspondance langue 2-lettres → nom humain (FR)
_LANG_HUMAN_FR = {
    "ja": "Japonais", "es": "Espagnol", "de": "Allemand",
    "it": "Italien",  "pt": "Portugais", "ko": "Coréen",
    "zh": "Chinois",  "ru": "Russe",     "nl": "Néerlandais",
    "pl": "Polonais", "ar": "Arabe",     "hi": "Hindi",
    "th": "Thaï",     "sv": "Suédois",   "no": "Norvégien",
    "da": "Danois",   "fi": "Finnois",   "cs": "Tchèque",
    "hu": "Hongrois", "tr": "Turc",      "uk": "Ukrainien",
    "he": "Hébreu",
}


def _lang_from_title(title: str) -> str:
    """Détecte la langue depuis le titre d'une piste (noms FR/EN).
    Retourne un code 2-lettres ou '' si non trouvé."""
    t = (title or "").lower()
    for code, keywords in _TITLE_LANG_KEYWORDS:
        for kw in keywords:
            if kw in t:
                return code
    return ""


def _identify(mkvmerge: str, input_path: str) -> dict:
    proc = subprocess.run([mkvmerge, "-J", input_path], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"mkvmerge -J failed: {proc.stderr}")
    return json.loads(proc.stdout)


def _is_english_track(track: dict) -> bool:
    props = track.get("properties", {})
    lang3 = (props.get("language") or "").lower()
    name = (props.get("track_name") or "").lower()
    return lang3 == "eng" or "english" in name


def _is_french_track(track: dict) -> bool:
    props = track.get("properties", {})
    lang3 = (props.get("language") or "").lower()
    name = (props.get("track_name") or "").lower()
    return (lang3 in ("fra", "fre") or "french" in name or "français" in name or
            any(m in name for m in ["vf", "vff", "vfq", "vfi"]))


def _detect_vf_type(track: dict) -> Optional[str]:
    props = track.get("properties", {})
    name = (props.get("track_name") or "").upper()
    if "VFF" in name or "FRANCE" in name:
        return "VFF"
    if "VFQ" in name or "QUEBEC" in name:
        return "VFQ"
    if "VFI" in name:
        return "VFi"
    return None


def _classify_subtitle(track: dict) -> str:
    props = track.get("properties", {})
    name = (props.get("track_name") or "").upper()
    is_forced = bool(props.get("forced_track")) or "FORCED" in name
    if is_forced:
        return "FORCED"
    if "COMMENT" in name:
        return "COMMENTARY"
    if "SDH" in name:
        return "SDH"
    if "FULL" in name or "COMPLET" in name:
        return "FULL"
    return "NORMAL"


def _match_track_by_properties(mm_track: dict, mediainfo_track: dict) -> bool:
    """Essaie de faire correspondre une piste mkvmerge avec une piste mediainfo"""
    props = mm_track.get("properties", {})
    
    # Comparer par langue
    mm_lang = (props.get("language") or "").lower()
    mi_lang = _normalize_lang(mediainfo_track.get("Language", ""))
    
    if mm_lang in ("eng",) and mi_lang == "en":
        pass  # OK
    elif mm_lang in ("fra", "fre") and mi_lang == "fr":
        pass  # OK
    elif mm_lang and mi_lang and mm_lang[:2] != mi_lang[:2]:
        return False
    
    # Comparer par titre si disponible
    mm_title = (props.get("track_name") or "").lower()
    mi_title = (mediainfo_track.get("Title") or "").lower()
    
    if mm_title and mi_title:
        # Si les deux ont un titre, ils doivent correspondre partiellement
        if mm_title in mi_title or mi_title in mm_title:
            return True
    
    # Comparer par nombre de canaux (audio)
    mm_channels = props.get("audio_channels")
    mi_channels = mediainfo_track.get("Channels")
    if mm_channels and mi_channels:
        try:
            if int(mm_channels) == int(mi_channels):
                return True
        except:
            pass
    
    return True  # Par défaut, accepter si langue correspond


def run_mkvmerge(input_file: str, tracks: Dict[str, Any], output_file: str) -> int:
    mkvmerge = _find_mkvmerge()
    print(f"  mkvmerge: {mkvmerge}")
    
    info = _identify(mkvmerge, input_file)
    mm_tracks = info.get("tracks", [])

    # Debug : afficher le mapping mkvmerge id → type/langue
    print("  [DEBUG] mkvmerge tracks:")
    for t in mm_tracks:
        props = t.get("properties", {})
        print(f"    id={t['id']} type={t.get('type')} lang={props.get('language')} name={props.get('track_name')}")

    # === VIDEO ===
    video_tracks = [t for t in mm_tracks if t.get("type") == "video"]
    if not video_tracks:
        raise RuntimeError("Aucune piste video")
    video_id = video_tracks[0]["id"]

    # === AUDIO ===
    selected_audio = tracks.get("selected_audio", [])
    audio_mm = [t for t in mm_tracks if t.get("type") == "audio"]

    audio_ids = []
    audio_details = []

    en_mm = [t for t in audio_mm if _is_english_track(t)]
    fr_mm = [t for t in audio_mm if _is_french_track(t)]

    vf_tag = tracks.get("vf_tag")

    # ── Choix de la piste default selon priorité ──
    # 1. Anglais (VO du film original) > 2. VFF > 3. VFi > 4. VOF > 5. VFQ > 6. autres
    # On retient l'ID Python de l'objet mi_track pour comparer dans la boucle.
    default_audio_oid = None

    def _is_ad_track(mi_track):
        ov = (mi_track.get("_user_vf") or "").upper()
        if ov.startswith("AD"):
            return True
        title = (mi_track.get("Title") or "").upper()
        return ("AUDIO DESCRIPTION" in title or "MALVOYANT" in title
                or re.search(r"\bAD\b", title) is not None)

    # Priorité default audio (sur les dicts MediaInfo, pas mkvmerge) :
    # 1. EN non-AD  2. VFF non-AD  3. VFI/VOF/VFQ/VF non-AD  4. FR non-AD  5. 1ère non-AD

    def _mi_lang(t):
        return _normalize_lang(t.get("Language", ""))

    def _mi_is_en(t):
        return _mi_lang(t) == "en"

    def _mi_is_fr(t):
        return _mi_lang(t) == "fr"

    # 1) première piste EN non-AD
    for t in selected_audio:
        if _mi_is_en(t) and not _is_ad_track(t):
            default_audio_oid = id(t)
            break
    # 2) sinon par priorité VF
    if default_audio_oid is None:
        priority = ["VFF", "VFI", "VOF", "VFQ", "VF"]
        for vf_type in priority:
            for t in selected_audio:
                ov = (t.get("_user_vf") or t.get("_detected_vf") or "").upper()
                if ov == vf_type and not _is_ad_track(t):
                    default_audio_oid = id(t)
                    break
            if default_audio_oid is not None:
                break
    # 3) fallback : 1ère piste FR non-AD
    if default_audio_oid is None:
        for t in selected_audio:
            if _mi_is_fr(t) and not _is_ad_track(t):
                default_audio_oid = id(t)
                break
    # 4) ultime fallback : 1ère piste tout court non-AD
    if default_audio_oid is None:
        for t in selected_audio:
            if not _is_ad_track(t):
                default_audio_oid = id(t)
                break

    for mi_track in selected_audio:
        mi_lang = _normalize_lang(mi_track.get("Language", ""))
        mi_title = (mi_track.get("Title") or "")

        # ── Fallback langue depuis le titre si Language vide ───────────────────
        # Ex: piste sans tag Language mais Title="Japonais TrueHD Atmos 7.1"
        if not mi_lang:
            mi_lang = _lang_from_title(mi_title)

        mi_title_lower = mi_title.lower()

        # ── Matching par StreamOrder (= mkvmerge id) ──────────────────────────
        # StreamOrder de MediaInfo correspond directement à l'id mkvmerge.
        # C'est la méthode fiable quand plusieurs pistes ont la même langue.
        found = None
        stream_order = mi_track.get("StreamOrder")
        print(f"  [DEBUG] Audio MediaInfo: lang={mi_lang} StreamOrder={stream_order} title={mi_title!r}")
        if stream_order is not None:
            so_int = int(stream_order)
            for mm_t in audio_mm:
                if mm_t["id"] == so_int:
                    found = mm_t
                    break
            if found and found["id"] in audio_ids:
                found = mm_t  # Ne pas ignorer — déjà dans audio_ids = doublon, on skip
                found = None

        # ── Fallback langue si StreamOrder ne matche pas ──────────────────────
        if not found:
            search_pool = en_mm if mi_lang == "en" else fr_mm if mi_lang == "fr" else audio_mm
            for mm_t in search_pool:
                if mm_t["id"] in audio_ids:
                    continue
                if _match_track_by_properties(mm_t, mi_track):
                    found = mm_t
                    break
            if not found and search_pool:
                for mm_t in search_pool:
                    if mm_t["id"] not in audio_ids:
                        found = mm_t
                        break
        
        if found:
            audio_ids.append(found["id"])
            
            # Construire le nom avec les infos MediaInfo
            # Format: "VFF DTS-HD MA 5.1 @ 3000 kbps"
            
            # Codec - nettoyer le nom (convention : AC3 / EAC3 / DTS-HD MA / TrueHD)
            fmt = mi_track.get("Format_Commercial_IfAny") or mi_track.get("Format") or ""
            fmt = fmt.replace("DTS-HD Master Audio", "DTS-HD MA")
            fmt = fmt.replace("Dolby Digital Plus", "EAC3")  # DDP / DD+
            fmt = fmt.replace("Dolby Digital", "AC3")        # DD
            fmt = fmt.replace("E-AC-3", "EAC3")
            fmt = fmt.replace("AC-3", "AC3")
            fmt = fmt.replace("Dolby TrueHD", "TrueHD")
            fmt = fmt.replace("with Dolby Atmos", "Atmos")
            
            # Canaux - convertir en format simple (5.1, 7.1, 2.0)
            ch_count = mi_track.get("Channels")
            if ch_count:
                ch_num = int(ch_count) if str(ch_count).isdigit() else 0
                if ch_num >= 8:
                    channels = "7.1"
                elif ch_num >= 6:
                    channels = "5.1"
                elif ch_num >= 2:
                    channels = "2.0"
                elif ch_num == 1:
                    channels = "1.0"
                else:
                    channels = ""
            else:
                channels = ""
            
            # Débit en kbps
            bitrate = mi_track.get("BitRate")
            bitrate_str = ""
            if bitrate:
                try:
                    br_kbps = int(bitrate) // 1000
                    if br_kbps > 0:
                        bitrate_str = f"@ {br_kbps} kbps"
                except:
                    pass
            
            # Tag de langue dans le NOM de la piste MKV.
            user_vf    = (mi_track.get("_user_vf") or "").strip()
            lang_human = (mi_track.get("_lang_human") or "").strip()
            is_ad      = bool(user_vf and user_vf.upper().startswith("AD"))

            mi_title_upper = (mi_track.get("Title") or "").upper()

            if user_vf:
                lang_tag = user_vf  # ex: "VFF", "AD VFQ"
            elif mi_lang == "en":
                lang_tag = "Anglais"
            elif mi_lang == "fr":
                if re.search(r"\bAD\b", mi_title_upper) or "AUDIO DESCRIPTION" in mi_title_upper or "MALVOYANT" in mi_title_upper:
                    lang_tag = "AD VFF"
                    is_ad = True
                elif "VOF" in mi_title_upper:
                    lang_tag = "VOF"
                elif "VFF" in mi_title_upper or "FRANCE" in mi_title_upper:
                    lang_tag = "VFF"
                elif "VFQ" in mi_title_upper or "QUEBEC" in mi_title_upper or "QUÉBEC" in mi_title_upper:
                    lang_tag = "VFQ"
                elif "VFI" in mi_title_upper:
                    lang_tag = "VFi"
                else:
                    lang_tag = vf_tag or "VF"
            elif lang_human:
                lang_tag = lang_human  # "Espagnol", "Allemand", "Italien"… (passé depuis GUI)
            elif mi_lang and mi_lang in _LANG_HUMAN_FR:
                # Langue détectée automatiquement (ex: "ja" → "Japonais")
                lang_tag = _LANG_HUMAN_FR[mi_lang]
            elif mi_lang:
                # Langue connue mais sans nom FR → code en majuscule
                lang_tag = mi_lang.upper()
            else:
                lang_tag = "VO"

            # Default : seulement la piste élue par la priorité globale (et jamais une AD)
            default = (id(mi_track) == default_audio_oid) and not is_ad
            
            # Nom complet: "VFF DTS-HD MA 5.1 @ 3000 kbps"
            name_parts = [lang_tag]
            if fmt:
                name_parts.append(fmt)
            if channels:
                name_parts.append(channels)
            if bitrate_str:
                name_parts.append(bitrate_str)
            
            full_name = " ".join(name_parts)
            
            audio_details.append({
                "id": found["id"],
                "lang": mi_lang,
                "default": default,  # Élu par la priorité globale (EN > VFF > VFQ… jamais AD)
                "name": full_name,
                "mi_track": mi_track  # Garder la référence pour l'affichage
            })
    
    # === SUBTITLES ===
    selected_subs = tracks.get("selected_subs", [])
    sub_mm = [t for t in mm_tracks if t.get("type") == "subtitles"]
    fr_sub_mm = [t for t in sub_mm if _is_french_track(t)]
    en_sub_mm = [t for t in sub_mm if _is_english_track(t)]

    # Pré-pass : par langue, on regarde s'il y a une piste FORCED dans la sélection.
    # Si oui, c'est elle qui prend le flag default (convention : VFF audio + FR FORCED auto).
    forced_present = {}  # {lang: True/False}
    for s in selected_subs:
        l = s.get("SubLang") or _normalize_lang(s.get("Language", ""))
        st = (s.get("SubType") or "").upper()
        if "FORCED" in st:
            forced_present[l] = True

    # Choisir le sub default selon priorité (REBiRTH) :
    # 1. FR FORCED (= doublage VFF principal) > 2. VFF FORCED > 3. VFi FORCED
    # 4. VOF FORCED > 5. VFQ FORCED > 6. EN FORCED > 7. n'importe quel FORCED
    # Si aucun FORCED → 1er FULL par même priorité.
    default_sub_oid = None
    for tag in ["FR FORCED", "VFF FORCED", "VFI FORCED", "VOF FORCED", "VFQ FORCED", "EN FORCED"]:
        for s in selected_subs:
            if (s.get("SubType") or "").upper() == tag:
                default_sub_oid = id(s)
                break
        if default_sub_oid is not None:
            break
    # Fallback : 1er FORCED rencontré
    if default_sub_oid is None:
        for s in selected_subs:
            if "FORCED" in (s.get("SubType") or "").upper():
                default_sub_oid = id(s)
                break
    # Ou 1er FULL FR
    if default_sub_oid is None:
        for tag in ["FR FULL", "VFF FULL", "VFI FULL", "VOF FULL", "VFQ FULL"]:
            for s in selected_subs:
                if (s.get("SubType") or "").upper() == tag:
                    default_sub_oid = id(s)
                    break
            if default_sub_oid is not None:
                break

    sub_ids = []
    sub_details = []

    for mi_track in selected_subs:
        mi_title = (mi_track.get("Title") or "").lower()
        mi_lang = mi_track.get("SubLang") or _normalize_lang(mi_track.get("Language", ""))
        
        # Choisir le pool de recherche selon la langue
        if mi_lang == "en":
            search_pool = en_sub_mm
            lang_name = "English"
            lang_tag2 = "EN"
        else:
            search_pool = fr_sub_mm
            lang_name = "Francais"
            lang_tag2 = "FR"
        
        # ── Matching par StreamOrder (= mkvmerge id) ──────────────────────────
        found = None
        stream_order = mi_track.get("StreamOrder")
        if stream_order is not None:
            so_int = int(stream_order)
            for mm_t in sub_mm:
                if mm_t["id"] == so_int and mm_t["id"] not in sub_ids:
                    found = mm_t
                    break

        # ── Fallback titre/langue si StreamOrder ne matche pas ────────────────
        if not found:
            for mm_t in search_pool:
                if mm_t["id"] in sub_ids:
                    continue
                props = mm_t.get("properties", {})
                mm_title = (props.get("track_name") or "").lower()
                if mi_title and mm_title and (mi_title in mm_title or mm_title in mi_title):
                    found = mm_t
                    break
            if not found:
                for mm_t in search_pool:
                    if mm_t["id"] not in sub_ids:
                        found = mm_t
                        break
        
        if found:
            sub_ids.append(found["id"])
            
            # Utiliser le SubType de MediaInfo si disponible
            mi_sub_type = mi_track.get("SubType", "")
            if mi_sub_type:
                sub_type = mi_sub_type
            else:
                sub_type = _classify_subtitle(found)
            
            # Format des noms : "FR FULL" / "FR FORCED" / "VFQ FULL" / etc.
            # Si SubType est déjà un nom complet préfixé (FR / VFQ / EN /
            # VFF / VFi / VOF) suivi de FULL/FORCED/SDH/COMMENTARY → on le
            # prend tel quel comme nom de piste.
            # Convention : si une FORCED existe pour cette langue, c'est ELLE
            # qui devient default (auto-affichage des dialogues étrangers quand
            # tu écoutes en VF). Sinon, c'est FULL qui prend le default.
            lang_has_forced = forced_present.get(mi_lang, False)
            sub_type_upper = (sub_type or "").upper()
            known_prefixes = ("FR ", "VFF ", "VFQ ", "VFI ", "VOF ", "EN ", "ES ", "DE ", "IT ", "PT ")
            known_types = ("FULL", "FORCED", "SDH", "COMMENTARY")
            is_complete_name = (
                any(sub_type_upper.startswith(p) for p in known_prefixes)
                and any(t in sub_type_upper for t in known_types)
            )

            # Le flag default est UNIQUEMENT donné à la piste élue par la priorité
            # globale (default_sub_oid), peu importe l'ordre dans le MKV.
            is_default_pick = (id(mi_track) == default_sub_oid)

            if is_complete_name:
                # SubType est déjà un nom complet (ex "FR FULL", "VFQ FORCED")
                name = sub_type
                if "FORCED" in sub_type_upper:
                    forced = True; default = is_default_pick; sub_type_norm = "FORCED"
                elif "SDH" in sub_type_upper:
                    forced = False; default = False; sub_type_norm = "SDH"
                elif "COMMENT" in sub_type_upper:
                    forced = False; default = False; sub_type_norm = "COMMENTARY"
                else:  # FULL
                    forced = False; default = is_default_pick; sub_type_norm = "FULL"
                sub_type = sub_type_norm
            elif sub_type == "FORCED":
                name = f"{lang_tag2} FORCED"
                forced = True
                default = is_default_pick
            elif sub_type == "SDH":
                name = f"{lang_tag2} SDH"
                forced = False
                default = False
            elif sub_type == "COMMENTARY":
                name = f"{lang_tag2} COMMENTARY"
                forced = False
                default = False
            elif sub_type == "FULL":
                name = f"{lang_tag2} FULL"
                forced = False
                default = is_default_pick
            else:
                # NORMAL - essayer de deviner par la position
                same_lang_subs = [d for d in sub_details if d.get("lang") == mi_lang]
                existing_types = [d.get("sub_type") for d in same_lang_subs]

                if "FORCED" not in existing_types and len(same_lang_subs) == 0:
                    name = f"{lang_tag2} FORCED"
                    forced = True
                    default = True  # 1ère piste FR sans contexte → FORCED + default
                    sub_type = "FORCED"
                elif "FULL" not in existing_types:
                    name = f"{lang_tag2} FULL"
                    forced = False
                    default = not any(d.get("default") for d in sub_details if d.get("lang") == mi_lang)
                    sub_type = "FULL"
                else:
                    name = lang_tag2
                    forced = False
                    default = False
            
            sub_details.append({
                "id": found["id"],
                "name": name,
                "forced": forced,
                "default": default,
                "sub_type": sub_type,
                "lang": mi_lang
            })
    
    # === Affichage résumé ===
    print(f"\n  Audio: {len(audio_details)} piste(s)")
    for d in audio_details:
        print(f"    - {d['name']}")
    
    print(f"\n  Sous-titres: {len(sub_details)} piste(s)")
    for d in sub_details:
        flags = []
        if d.get("default"):
            flags.append("default")
        if d.get("forced"):
            flags.append("forced")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"    - {d['name']}{flag_str}")
    if not sub_details:
        print("    (aucun)")
    
    # === BUILD COMMAND ===
    # Si le caller fournit un titre humain (depuis le GUI), on l'utilise pour
    # le General/Title ET pour la piste vidéo. Sinon : nom du fichier sans ext.
    mkv_title_override = tracks.get("mkv_title") or ""
    video_track_name   = tracks.get("video_track_name") or ""
    video_title = mkv_title_override or os.path.splitext(os.path.basename(output_file))[0]

    cmd = [mkvmerge, "-o", output_file]
    cmd += ["--title", video_title]
    cmd += ["--no-attachments", "--no-track-tags", "--no-global-tags"]
    cmd += ["--video-tracks", str(video_id)]

    # Titre de la piste vidéo (humain si fourni, vide sinon pour effacer celui de MakeMKV)
    cmd += ["--track-name", f"{video_id}:{video_track_name}"]
    
    if audio_ids:
        cmd += ["--audio-tracks", ",".join(str(x) for x in audio_ids)]
    else:
        cmd += ["-A"]
    
    if sub_ids:
        cmd += ["--subtitle-tracks", ",".join(str(x) for x in sub_ids)]
    else:
        cmd += ["-S"]
    
    # Audio options
    for d in audio_details:
        tid = d["id"]
        cmd += ["--language", f"{tid}:{_lang3(d['lang'])}"]
        cmd += ["--default-track-flag", f"{tid}:{'1' if d.get('default') else '0'}"]
        if d.get("name"):
            cmd += ["--track-name", f"{tid}:{d['name']}"]
    
    # Subtitle options - utiliser la bonne langue
    for d in sub_details:
        tid = d["id"]
        lang_code = _lang3(d.get("lang", "fr"))
        cmd += ["--language", f"{tid}:{lang_code}"]
        cmd += ["--track-name", f"{tid}:{d['name']}"]
        cmd += ["--default-track-flag", f"{tid}:{'1' if d.get('default') else '0'}"]
        cmd += ["--forced-display-flag", f"{tid}:{'1' if d.get('forced') else '0'}"]
    
    cmd.append(input_file)
    
    # === EXECUTE ===
    print(f"\n  Remux en cours...")
    start = time.time()
    
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1) as proc:
        errors = []
        for line in proc.stdout:
            line = line.strip()
            if line.startswith("Progress:") and "%" in line:
                try:
                    pct = int(line.split()[1].rstrip('%'))
                    elapsed = max(0.001, time.time() - start)
                    remain = (100 - pct) / (pct / elapsed) if pct > 0 else 0
                    eta_m, eta_s = int(remain // 60), int(remain % 60)
                    bar = '#' * (pct // 3) + '-' * (33 - pct // 3)
                    sys.stdout.write(f"\r  [{bar}] {pct}% ETA {eta_m:02d}:{eta_s:02d}")
                    sys.stdout.flush()
                except:
                    pass
            elif line:
                errors.append(line)
        
        rc = proc.wait()
        print()
        
        if rc != 0:
            print("  [ERREUR]")
            for e in errors[-5:]:
                print(f"    {e}")
        
        return rc
