#!/usr/bin/env python3
# coding: utf-8
"""
Remux Tool — GUI PyWebView (style REBiRTH)
Lance avec : python3 gui.py
"""

import os
import re
import sys
import json
import time
import shutil
import threading
import subprocess
from pathlib import Path
from datetime import datetime

import webview

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Imports du projet
from makemkv_extract import (
    analyze_source,
    extract_title,
    get_stream_type,
    is_french_stream,
    is_english_stream,
)
from mkvtoolnix_remux import run_mkvmerge
from mediainfo_parse import parse_mediainfo

# main.py : on importe les helpers (pas main.run_workflow qui est interactif)
import main as _main_mod


CONFIG_FILE = BASE_DIR / "config.py"
HISTORY_FILE = BASE_DIR / "gui_history.json"


# ──────────────────────────────────────────────────────────────────────────
# Capture stdout → log GUI + progress
# ──────────────────────────────────────────────────────────────────────────
class StdoutTee:
    """Redirige sys.stdout : forwarde chaque ligne au log GUI et capte les
    barres de progression (lignes "[####] 45% ETA 02:13") pour les events."""

    PROGRESS_RE = re.compile(r"\[([#\-]+)\]\s*(\d+)%(?:\s*ETA\s*(\d+:\d+))?")

    def __init__(self, original, on_line, on_progress):
        self._orig = original
        self._buf = ""
        self._on_line = on_line
        self._on_progress = on_progress

    def write(self, data):
        try:
            self._orig.write(data)
        except Exception:
            pass
        # Découpe par \r ET \n pour capter les barres rafraîchies en place
        chunks = re.split(r"[\r\n]", data)
        # Le dernier chunk peut être incomplet, on le bufferise
        self._buf += chunks[0]
        if len(chunks) == 1:
            return
        # Premier chunk fini → on flush
        self._flush_line(self._buf)
        self._buf = ""
        # Chunks intermédiaires
        for c in chunks[1:-1]:
            self._flush_line(c)
        # Dernier
        self._buf = chunks[-1]
        if "\r" in data and self._buf:
            self._flush_line(self._buf)
            self._buf = ""

    def _flush_line(self, line):
        if not line:
            return
        m = self.PROGRESS_RE.search(line)
        if m:
            try:
                pct = int(m.group(2))
                eta = m.group(3) or ""
                self._on_progress(pct, eta)
                return
            except Exception:
                pass
        # Ligne de log normale
        clean = line.rstrip()
        if clean:
            level = "info"
            low = clean.lower()
            if "[erreur]" in low or "error" in low or "echec" in low:
                level = "error"
            elif "[ok]" in low or "termine" in low or "✓" in clean:
                level = "success"
            elif "warning" in low or "[warn" in low:
                level = "warn"
            self._on_line(clean, level)

    def flush(self):
        try:
            self._orig.flush()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────────
# Helpers de scoring/détection (reprend la logique de main.py)
# ──────────────────────────────────────────────────────────────────────────

# Code ISO 639-2/639-1 → nom français de la langue
LANG_FR = {
    "eng": "Anglais", "en": "Anglais",
    "fre": "Français", "fra": "Français", "fr": "Français",
    "spa": "Espagnol", "es": "Espagnol",
    "ger": "Allemand", "deu": "Allemand", "de": "Allemand",
    "ita": "Italien", "it": "Italien",
    "por": "Portugais", "pt": "Portugais",
    "jpn": "Japonais", "ja": "Japonais",
    "chi": "Chinois", "zho": "Chinois", "zh": "Chinois",
    "kor": "Coréen", "ko": "Coréen",
    "rus": "Russe", "ru": "Russe",
    "nld": "Néerlandais", "dut": "Néerlandais", "nl": "Néerlandais",
    "pol": "Polonais", "pl": "Polonais",
    "swe": "Suédois", "sv": "Suédois",
    "nor": "Norvégien", "no": "Norvégien",
    "dan": "Danois", "da": "Danois",
    "fin": "Finnois", "fi": "Finnois",
    "ara": "Arabe", "ar": "Arabe",
    "tur": "Turc", "tr": "Turc",
    "hun": "Hongrois", "hu": "Hongrois",
    "ces": "Tchèque", "cze": "Tchèque", "cs": "Tchèque",
    "gre": "Grec", "ell": "Grec", "el": "Grec",
    "heb": "Hébreu", "he": "Hébreu",
    "hin": "Hindi", "hi": "Hindi",
    "tha": "Thaï", "th": "Thaï",
    "vie": "Vietnamien", "vi": "Vietnamien",
    "ukr": "Ukrainien", "uk": "Ukrainien",
    "ron": "Roumain", "rum": "Roumain", "ro": "Roumain",
    "bul": "Bulgare", "bg": "Bulgare",
    "slv": "Slovène", "sl": "Slovène",
    "slk": "Slovaque", "slo": "Slovaque", "sk": "Slovaque",
    "hrv": "Croate", "hr": "Croate",
    "srp": "Serbe", "sr": "Serbe",
    "isl": "Islandais", "ice": "Islandais", "is": "Islandais",
    "cat": "Catalan", "ca": "Catalan",
    "ind": "Indonésien", "id": "Indonésien",
}


def _lang_label(lang_code: str, lang_name: str) -> str:
    """Retourne le nom français de la langue à partir d'un code ou d'un nom."""
    if lang_code:
        c = lang_code.lower().strip()
        # Couper sur "-" (fr-CA → fr) pour fallback
        for variant in (c, c.split("-")[0]):
            if variant in LANG_FR:
                return LANG_FR[variant]
    if lang_name:
        # MakeMKV retourne déjà parfois le nom anglais ("French", "Spanish"…)
        m = lang_name.lower().strip()
        en_to_fr = {
            "english": "Anglais", "french": "Français", "spanish": "Espagnol",
            "german": "Allemand", "italian": "Italien", "portuguese": "Portugais",
            "japanese": "Japonais", "chinese": "Chinois", "korean": "Coréen",
            "russian": "Russe", "dutch": "Néerlandais", "polish": "Polonais",
            "swedish": "Suédois", "norwegian": "Norvégien", "danish": "Danois",
            "finnish": "Finnois", "arabic": "Arabe", "turkish": "Turc",
            "hungarian": "Hongrois", "czech": "Tchèque", "greek": "Grec",
            "hebrew": "Hébreu", "hindi": "Hindi", "thai": "Thaï",
            "vietnamese": "Vietnamien", "ukrainian": "Ukrainien",
            "romanian": "Roumain", "bulgarian": "Bulgare", "slovenian": "Slovène",
            "slovak": "Slovaque", "croatian": "Croate", "serbian": "Serbe",
            "icelandic": "Islandais", "catalan": "Catalan", "indonesian": "Indonésien",
        }
        if m in en_to_fr:
            return en_to_fr[m]
        return lang_name
    return "?"


def _detect_vf_extended(stream: dict) -> str:
    """VFF / VFQ / VFi / VOF / AD — étendu avec VOF + AD (Audiodescription)."""
    name = (stream.get("name") or stream.get("Title") or "").upper()
    lang = (stream.get("lang_code") or stream.get("Language") or "").lower()
    more = (stream.get("Language_More") or "").upper()
    desc = (stream.get("description") or "").upper()
    meta = (stream.get("metadata") or "").upper()
    blob = f"{name} {more} {desc} {meta}"
    # AD = audio-description (priorité haute pour pas être avalé par "VFF")
    if (re.search(r"\bAD\b", blob) or "AUDIO DESCRIPTION" in blob
            or "AUDIODESCRIPTION" in blob or "DESCRIPTION AUDIO" in blob
            or "MALVOYANT" in blob or "VISUALLY IMPAIRED" in blob):
        return "AD"
    if "VOF" in blob:
        return "VOF"
    if "VFF" in blob or "FRANCE" in blob or lang in ("fr-fr",):
        return "VFF"
    if ("VFQ" in blob or "QUEBEC" in blob or "QUÉBEC" in blob
            or "CANADA" in blob or lang in ("fr-ca",)):
        return "VFQ"
    if "VFI" in blob or "INTERNATIONAL" in blob:
        return "VFi"
    return ""


def _norm_lang(s: str) -> str:
    """Normalise un code langue : 'eng'/'en-US'/'English' → 'en'."""
    s = (s or "").lower().strip()
    if not s:
        return ""
    s = s.split("-")[0]  # fr-CA → fr
    mapping = {
        "eng": "en", "english": "en",
        "fra": "fr", "fre": "fr", "french": "fr", "français": "fr", "francais": "fr",
        "spa": "es", "spanish": "es",
        "deu": "de", "ger": "de", "german": "de",
        "ita": "it", "italian": "it",
        "por": "pt", "portuguese": "pt",
        "jpn": "ja", "japanese": "ja",
        "zho": "zh", "chi": "zh", "chinese": "zh",
        "kor": "ko", "korean": "ko",
        "rus": "ru", "russian": "ru",
        "ara": "ar", "arabic": "ar",
    }
    if s in mapping:
        return mapping[s]
    return s[:2] if len(s) >= 2 else s


def _resolve_picks(picks: list, mediainfo_tracks: list, kind: str = "subs") -> list:
    """Mappe les choix utilisateur (depuis la source MakeMKV) aux pistes du
    MKV extrait. Stratégie en deux passes :

      1. Si la position cochée existe dans le MKV ET que la langue concorde,
         on prend cette piste.
      2. Sinon, on prend la première piste de la même langue non encore consommée
         (typique : MakeMKV a filtré 8 → 4 subs, on retombe sur la bonne langue).

    `picks` : liste de dicts {position, lang, is_en, is_fr, override}
    `mediainfo_tracks` : liste des pistes du MKV extrait (audio_tracks ou sub_tracks)
    Retourne les tracks mediainfo enrichies (dans l'ordre des picks)."""
    consumed = set()
    by_lang = {}
    for t in mediainfo_tracks:
        l = _norm_lang(t.get("Language", ""))
        by_lang.setdefault(l, []).append(t)

    kept = []
    for pick in picks:
        pos = pick.get("position", -1)
        want_lang = _norm_lang(pick.get("lang", ""))
        # Si lang absente, déduire depuis is_en/is_fr
        if not want_lang:
            if pick.get("is_fr"):
                want_lang = "fr"
            elif pick.get("is_en"):
                want_lang = "en"
        override = pick.get("override", "")

        # Tentative 1 : par position directe (si dans la plage)
        chosen = None
        if 0 <= pos < len(mediainfo_tracks):
            t = mediainfo_tracks[pos]
            t_lang = _norm_lang(t.get("Language", ""))
            if id(t) not in consumed and (not want_lang or t_lang == want_lang):
                chosen = t

        # Tentative 2 : par langue, premier non consommé
        if chosen is None and want_lang:
            for t in by_lang.get(want_lang, []):
                if id(t) not in consumed:
                    chosen = t
                    break

        if chosen is None:
            # Pas de match → on log et on passe (mieux que de prendre une mauvaise piste)
            print(f"  ⚠ Sub demandé pos={pos} lang={want_lang!r} introuvable dans le MKV extrait — ignoré")
            continue
        consumed.add(id(chosen))

        # Enrichissement
        if kind == "subs":
            chosen["SubLang"] = want_lang or _norm_lang(chosen.get("Language", "")) or "fr"
            if override:
                chosen["SubType"] = override
        else:  # audio
            if override:
                chosen["_user_vf"] = override

        kept.append(chosen)

    # Pour les subs : (1) déduplication STRICTE des vrais doublons, (2) tri par type.
    if kind == "subs":
        # Dédup stricte : il FAUT que (a) la langue soit la même, (b) le nombre
        # d'éléments soit IDENTIQUE (ou ≤ 1% d'écart), (c) la taille de stream
        # soit AUSSI identique (ou ≤ 1% d'écart). Sans StreamSize on ne dédup pas.
        # Cas concret protégé : VF2 avec FR FORCED VFF=68 + FR FORCED VFQ=71 — pas
        # des doublons (≈4.4%) → on les garde tous les deux.
        DEDUP_TOL = 0.01  # 1%

        def _close(a: int, b: int, tol: float) -> bool:
            if not a or not b:
                return False
            return abs(a - b) / max(a, b) <= tol

        deduped = []
        for t in kept:
            t_lang = _norm_lang(t.get("Language", ""))
            t_elem = int(t.get("ElementCount") or 0)
            t_size = int(t.get("StreamSize") or 0)
            is_dup = False
            for kept_t in deduped:
                k_lang = _norm_lang(kept_t.get("Language", ""))
                k_elem = int(kept_t.get("ElementCount") or 0)
                k_size = int(kept_t.get("StreamSize") or 0)
                if k_lang != t_lang:
                    continue
                # Les DEUX critères doivent matcher : elements + size
                if not (_close(t_elem, k_elem, DEDUP_TOL) and _close(t_size, k_size, DEDUP_TOL)):
                    continue
                is_dup = True
                print(f"  · Sub doublon strict ignoré : lang={t_lang} "
                      f"elements={t_elem}≈{k_elem} size={t_size}≈{k_size}")
                break
            if not is_dup:
                deduped.append(t)
        kept = deduped

        # Tri : FULL > SDH > FORCED > COMMENTARY > inconnu
        # Reconnaît aussi les variantes VFF/VFQ/VFi/VOF + suffixe.
        def _sub_priority(t):
            st = (t.get("SubType") or "").upper()
            if "FORCED" in st:    return 2
            if "SDH" in st:       return 1
            if "COMMENT" in st:   return 3
            if "FULL" in st:      return 0
            return 4
        kept.sort(key=_sub_priority)
    return kept


def _classify_sub(stream: dict) -> str:
    """Type d'un sous-titre : FORCED / SDH / COMMENTARY / FULL / "".
    (AD n'existe pas pour les sous-titres — c'est SDH.)
    Retourne "" (= inconnu) si on n'a pas d'info — comme ça le dropdown du GUI
    affiche AUTO par défaut et la classification par comparaison d'éléments
    (post-extraction MediaInfo) fait son boulot correctement.
    """
    name = (stream.get("name") or stream.get("Title") or "").upper()
    blob = f"{name} {(stream.get('metadata') or '').upper()} {(stream.get('description') or '').upper()}"
    elements = stream.get("ElementCount") or stream.get("elements") or 0
    if "FORCED" in blob or "FORCÉ" in blob:
        return "FORCED"
    if ("SDH" in blob or "HEARING" in blob or "MALENTENDANT" in blob
            or "MALVOYANT" in blob or "AUDIO DESCRIPTION" in blob):
        return "SDH"
    if "COMMENT" in blob or "COMMENTAIRE" in blob:
        return "COMMENTARY"
    if "FULL" in blob or "COMPLET" in blob or "INTÉGRAL" in blob or "INTEGRAL" in blob:
        return "FULL"
    # Heuristique sur le nombre d'éléments (uniquement si l'info existe)
    try:
        n = int(elements)
        if n:
            if n < 100:
                return "FORCED"
            if n > 500:
                return "FULL"
    except (TypeError, ValueError):
        pass
    return ""  # inconnu — le dropdown affichera AUTO


def _tmdb_lookup(query: str, year: str = "", language: str = "fr-FR") -> dict:
    """Recherche TMDB → retourne {ok, title, original_title, year, id, url, poster}.
    Utilise la clé API définie dans NFO_CUSTOM/tmdb_helper.py."""
    try:
        # NFO_CUSTOM/ du bot (dossier parent du remux_tool/)
        sys.path.insert(0, str(BASE_DIR.parent / "NFO_CUSTOM"))
        from tmdb_helper import TMDB_API_KEY  # type: ignore
    except Exception as e:
        return {"ok": False, "error": f"TMDB key indisponible : {e}"}

    if not query.strip():
        return {"ok": False, "error": "requête vide"}

    try:
        import requests
        params = {
            "api_key": TMDB_API_KEY,
            "query": query.strip(),
            "language": language,
            "include_adult": "false",
        }
        if year:
            params["year"] = str(year).strip()
        resp = requests.get("https://api.themoviedb.org/3/search/movie", params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as e:
        return {"ok": False, "error": str(e)}

    if not results:
        # Retry sans l'année si rien trouvé
        if year:
            return _tmdb_lookup(query, "", language)
        return {"ok": False, "error": "aucun résultat TMDB"}

    r = results[0]
    movie_id = r.get("id")
    return {
        "ok": True,
        "title": r.get("title") or r.get("original_title") or query,
        "original_title": r.get("original_title") or "",
        "year": (r.get("release_date") or "")[:4],
        "id": movie_id,
        "url": f"https://www.themoviedb.org/movie/{movie_id}" if movie_id else "",
        "poster": f"https://image.tmdb.org/t/p/w185{r.get('poster_path')}" if r.get("poster_path") else "",
        "overview": r.get("overview") or "",
    }


def _clean_movie_title(name: str):
    """À partir d'un nom de dossier 'Scary.Movie.2.2001.1080p.FRA.Blu-ray.AVC...',
    extrait (titre_propre_pointé, année).
        ('Scary.Movie.2', '2001')"""
    base = name
    if base.lower().endswith(".iso"):
        base = base[:-4]
    parts = [p for p in re.split(r"[._\s]+", base) if p]
    year = ""
    title_parts = []
    for p in parts:
        if year:
            break
        if re.fullmatch(r"(19|20)\d{2}", p):
            year = p
        else:
            title_parts.append(p)
    if not title_parts and parts:
        # Pas d'année trouvée → on prend tout
        title_parts = parts
    title = ".".join(t.capitalize() for t in title_parts if t)
    return title, year


def _audio_quality(stream: dict) -> int:
    codec = (stream.get("codec") or stream.get("Format_Commercial_IfAny") or stream.get("Format") or "").upper()
    score = 0
    if "DTS-HD" in codec or "MASTER" in codec:
        score = 500
    elif "TRUEHD" in codec or "ATMOS" in codec:
        score = 450
    elif "FLAC" in codec:
        score = 400
    elif "PCM" in codec or "LPCM" in codec:
        score = 350
    elif "DTS" in codec:
        score = 300
    elif "AC-3" in codec or "AC3" in codec or "E-AC" in codec or "DD" in codec:
        score = 200
    elif "AAC" in codec:
        score = 100
    return score


def _stream_to_dict(s: dict) -> dict:
    """Format stream pour le front."""
    stype = get_stream_type(s)
    is_en = is_english_stream(s) if stype in ("audio", "subtitle") else False
    is_fr = is_french_stream(s) if stype in ("audio", "subtitle") else False
    # Sous-catégorie VF (VFF/VFQ/VFi/VOF/AD) — pour audio FR (et anglais aussi : AD EN)
    vf = ""
    if stype == "audio":
        vf = _detect_vf_extended(s) or ("VF" if is_fr else "")
    # Type de sous-titre (FULL/FORCED/SDH/AD/COMMENTARY)
    sub_type = _classify_sub(s) if stype == "subtitle" else ""
    # Label humain (Anglais, Espagnol, Italien…)
    lang_label = _lang_label(s.get("lang_code") or "", s.get("lang") or "")
    return {
        "id": s.get("id"),
        "type": stype,
        "codec": s.get("codec") or "",
        "lang": s.get("lang") or "",
        "lang_code": s.get("lang_code") or "",
        "lang_label": lang_label,
        "name": s.get("name") or "",
        "info": s.get("info") or s.get("resolution") or "",
        "is_en": bool(is_en),
        "is_fr": bool(is_fr),
        "vf_type": vf,
        "sub_type": sub_type,
        "score": _audio_quality(s),
    }


# ──────────────────────────────────────────────────────────────────────────
# Lecture / écriture du config.py
# ──────────────────────────────────────────────────────────────────────────
def _read_config_file() -> dict:
    cfg = {
        "RELEASE_GROUP": "",
        "FULL_DIR": "FULL",
        "OUTPUT_DIR": "OUTPUT",
        "TOOLS_DIR": "tools",
        "KEEP_ENGLISH_SUBS": 1,
        "IS_CUSTOM": 0,
    }
    if not CONFIG_FILE.exists():
        return cfg
    txt = CONFIG_FILE.read_text(encoding="utf-8")
    for key in cfg.keys():
        m = re.search(rf'^{key}\s*=\s*(.+?)\s*$', txt, re.MULTILINE)
        if not m:
            continue
        raw = m.group(1).strip()
        if raw.startswith('"') or raw.startswith("'"):
            cfg[key] = raw.strip('"\'')
        else:
            try:
                cfg[key] = int(raw)
            except ValueError:
                cfg[key] = raw
    return cfg


def _write_config_file(new_cfg: dict):
    txt = CONFIG_FILE.read_text(encoding="utf-8") if CONFIG_FILE.exists() else ""
    for key, value in new_cfg.items():
        if isinstance(value, str):
            repl = f'{key} = "{value}"'
        else:
            repl = f'{key} = {value}'
        if re.search(rf'^{key}\s*=', txt, re.MULTILINE):
            txt = re.sub(rf'^{key}\s*=.*$', repl, txt, count=1, flags=re.MULTILINE)
        else:
            txt += "\n" + repl + "\n"
    CONFIG_FILE.write_text(txt, encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────
# API exposée à JS
# ──────────────────────────────────────────────────────────────────────────
class API:
    def __init__(self):
        self.window = None
        self._lock = threading.Lock()
        self._cancel = threading.Event()
        self._busy = False

    # ---- bridge ----------------------------------------------------------
    def _emit(self, event: str, data):
        try:
            # Préfixe "rmx_" pour éviter les collisions avec les events du bot upload
            prefixed = "rmx_" + event
            payload = json.dumps(data, default=str)
            payload = payload.replace("\\", "\\\\").replace("'", "\\'")
            if self.window:
                self.window.evaluate_js(f"window._emit('{prefixed}', JSON.parse('{payload}'))")
        except Exception as e:
            # Bypasse StdoutTee pour éviter toute récursion vers _log → _emit
            try:
                sys.__stdout__.write(f"[emit error] {e}\n")
            except Exception:
                pass

    def _log(self, msg: str, level: str = "info"):
        self._emit("log", {"msg": msg, "level": level, "ts": datetime.now().strftime("%H:%M:%S")})

    # ---- méthodes appelables depuis JS -----------------------------------
    def detect_tools(self):
        """Utilise les vrais finders des modules (gère le chemin .app sur macOS)."""
        tools = {}
        # makemkvcon
        try:
            from makemkv_extract import _find_makemkvcon
            tools["makemkvcon"] = bool(_find_makemkvcon())
        except Exception:
            tools["makemkvcon"] = False
        # mkvmerge (lève FileNotFoundError si introuvable)
        try:
            from mkvtoolnix_remux import _find_mkvmerge  # type: ignore
            tools["mkvmerge"] = bool(_find_mkvmerge())
        except FileNotFoundError:
            tools["mkvmerge"] = False
        except Exception:
            tools["mkvmerge"] = bool(shutil.which("mkvmerge"))
        # mediainfo
        try:
            from mediainfo_parse import _find_mediainfo
            tools["mediainfo"] = bool(_find_mediainfo())
        except Exception:
            tools["mediainfo"] = False
        return {"ok": True, "tools": tools}

    def list_movies(self):
        cfg = _read_config_file()
        full_dir = cfg["FULL_DIR"]
        if not os.path.isabs(full_dir):
            full_dir = str(BASE_DIR / full_dir)
        if not os.path.isdir(full_dir):
            os.makedirs(full_dir, exist_ok=True)
            return {"ok": True, "movies": [], "full_dir": full_dir}
        entries = sorted(os.listdir(full_dir))
        movies = []
        for e in entries:
            if e.startswith("."):
                continue
            full = os.path.join(full_dir, e)
            if os.path.isdir(full) or e.lower().endswith(".iso"):
                kind = "iso" if e.lower().endswith(".iso") else "folder"
                size = 0
                try:
                    if kind == "iso":
                        size = os.path.getsize(full)
                    else:
                        for root, _, files in os.walk(full):
                            for f in files:
                                try:
                                    size += os.path.getsize(os.path.join(root, f))
                                except OSError:
                                    pass
                except Exception:
                    pass
                movies.append({"name": e, "kind": kind, "size_gb": round(size / (1024 ** 3), 2)})
        return {"ok": True, "movies": movies, "full_dir": full_dir}

    def get_config(self):
        return {"ok": True, "config": _read_config_file()}

    def save_config(self, cfg):
        try:
            _write_config_file(cfg)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def open_folder(self, path: str = ""):
        cfg = _read_config_file()
        if not path:
            path = cfg["OUTPUT_DIR"]
        if not os.path.isabs(path):
            path = str(BASE_DIR / path)
        os.makedirs(path, exist_ok=True)
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", path])
            elif sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "path": path}

    def history(self):
        if not HISTORY_FILE.exists():
            return {"ok": True, "items": []}
        try:
            return {"ok": True, "items": json.loads(HISTORY_FILE.read_text(encoding="utf-8"))}
        except Exception:
            return {"ok": True, "items": []}

    def _save_history(self, entry: dict):
        try:
            items = []
            if HISTORY_FILE.exists():
                items = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            entry["date"] = datetime.now().isoformat(timespec="seconds")
            items.insert(0, entry)
            items = items[:50]
            HISTORY_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            self._log(f"⚠ historique : {e}", "warn")

    def cancel(self):
        self._cancel.set()
        self._log("🛑 Annulation demandée — arrêt après l'étape en cours.", "warn")
        return {"ok": True}

    def test_makemkv(self):
        """Diagnostic : lance makemkvcon en mode info-version pour vérifier
        que la licence est valide et que le binaire répond."""
        try:
            from makemkv_extract import _find_makemkvcon
            mkv = _find_makemkvcon()
        except Exception as e:
            self._log(f"❌ makemkvcon introuvable : {e}", "error")
            return {"ok": False, "error": str(e)}

        self._log(f"🧪 Test : {mkv}")
        try:
            proc = subprocess.run(
                [mkv, "-r", "info", "disc:99999"],
                capture_output=True, text=True, timeout=15
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            for line in out.splitlines()[:40]:
                level = "info"
                if "MSG:5021" in line or "expired" in line.lower():
                    level = "error"
                elif "MSG:1005" in line or "version" in line.lower():
                    level = "success"
                self._log(line, level)
            self._log(f"  → exit code = {proc.returncode}", "success" if proc.returncode in (0, 1, 6) else "warn")
            return {"ok": True}
        except subprocess.TimeoutExpired:
            self._log("⏰ Timeout (15 s) — makemkvcon ne répond pas. Licence expirée ?", "error")
            return {"ok": False, "error": "timeout"}
        except Exception as e:
            self._log(f"❌ {e}", "error")
            return {"ok": False, "error": str(e)}

    def extract_screenshots(self, mkv_path: str = "", count: int = 4):
        """Extrait N screenshots aléatoires depuis un MKV.
        Si mkv_path est vide, prend le dernier remux de l'historique.
        Les screenshots sont sauvegardés dans PICS/<titre_du_film>/ à la racine du bot."""
        if self._busy:
            return {"ok": False, "error": "Une opération est déjà en cours."}

        film_name = ""
        if not mkv_path:
            try:
                if HISTORY_FILE.exists():
                    items = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                    if items:
                        mkv_path = items[0].get("path", "")
                        # Dériver le nom propre depuis le nom source dans l'historique
                        raw = items[0].get("movie", "")
                        guessed, _ = _clean_movie_title(raw)
                        film_name = guessed.replace(".", " ") if guessed else raw
            except Exception:
                pass

        # Si on a un chemin mais pas encore le nom, le dériver du nom de fichier MKV
        if not film_name and mkv_path:
            base = os.path.splitext(os.path.basename(mkv_path))[0]
            guessed, _ = _clean_movie_title(base)
            film_name = guessed.replace(".", " ") if guessed else base

        if not mkv_path or not os.path.isfile(mkv_path):
            return {"ok": False, "error": f"MKV introuvable : {mkv_path or '(aucun)'}"}

        try:
            count = max(1, min(20, int(count)))
        except Exception:
            count = 4

        self._busy = True
        threading.Thread(target=self._screenshot_worker, args=(mkv_path, count, film_name), daemon=True).start()
        return {"ok": True, "started": True, "count": count, "path": mkv_path}

    def _screenshot_worker(self, mkv_path: str, count: int, film_name: str = ""):
        import random
        try:
            ffprobe = self._find_bin("ffprobe", ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe"])
            ffmpeg  = self._find_bin("ffmpeg",  ["/opt/homebrew/bin/ffmpeg",  "/usr/local/bin/ffmpeg"])
            if not ffprobe or not ffmpeg:
                self._log("❌ ffmpeg/ffprobe introuvable — installe avec `brew install ffmpeg`", "error")
                self._emit("screenshots_done", {"ok": False, "error": "ffmpeg/ffprobe introuvable"})
                return

            self._log(f"📸 Extraction de {count} screenshots depuis : {os.path.basename(mkv_path)}")

            # 1. Durée totale
            proc = subprocess.run(
                [ffprobe, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", mkv_path],
                capture_output=True, text=True, timeout=30,
            )
            try:
                duration = float((proc.stdout or "0").strip())
            except ValueError:
                duration = 0.0
            if duration <= 0:
                self._log("❌ Impossible de lire la durée du MKV", "error")
                self._emit("screenshots_done", {"ok": False, "error": "durée illisible"})
                return

            self._log(f"  Durée : {int(duration//60)} min {int(duration%60)} s")

            # 2. N timestamps aléatoires entre 10% et 90% de la durée
            start_excl = duration * 0.10
            end_excl   = duration * 0.90
            timestamps = sorted([random.uniform(start_excl, end_excl) for _ in range(count)])

            # 3. Extraction des frames → PICS/<film_name>/ à la racine du bot
            pics_root = BASE_DIR.parent / "PICS"
            folder_name = film_name if film_name else os.path.splitext(os.path.basename(mkv_path))[0]
            output_dir = str(pics_root / folder_name)
            os.makedirs(output_dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(mkv_path))[0]
            paths = []
            for i, ts in enumerate(timestamps, 1):
                out = os.path.join(output_dir, f"{base}_screen_{i:02d}.png")
                # -ss avant -i pour seek rapide, -frames:v 1 pour 1 frame
                # -q:v 2 = qualité quasi-lossless pour PNG
                rc = subprocess.run(
                    [ffmpeg, "-y", "-ss", f"{ts:.3f}", "-i", mkv_path,
                     "-frames:v", "1", "-q:v", "2", out],
                    capture_output=True, text=True, timeout=60,
                )
                h, m, s = int(ts // 3600), int((ts % 3600) // 60), int(ts % 60)
                if rc.returncode == 0 and os.path.isfile(out):
                    self._log(f"  ✓ [{h:02d}:{m:02d}:{s:02d}] → {os.path.basename(out)}", "success")
                    paths.append(out)
                else:
                    self._log(f"  ✗ [{h:02d}:{m:02d}:{s:02d}] échec ffmpeg", "error")

            self._log(f"📸 Terminé : {len(paths)}/{count} screenshots dans {output_dir}", "success")
            self._emit("screenshots_done", {
                "ok": True, "count": len(paths), "paths": paths, "dir": output_dir,
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._log(f"❌ {e}", "error")
            self._emit("screenshots_done", {"ok": False, "error": str(e)})
        finally:
            self._busy = False

    @staticmethod
    def _find_bin(name: str, candidates: list = None):
        p = shutil.which(name)
        if p:
            return p
        for c in (candidates or []):
            if os.path.isfile(c):
                return c
        return None

    def tmdb_search(self, query: str, year: str = ""):
        """Recherche TMDB depuis le GUI (bouton 🔍 TMDB). Retourne le résultat
        directement (pas asynchrone — la requête HTTP est rapide)."""
        return _tmdb_lookup(query, year, language="fr-FR")

    def reset_makemkv_settings(self):
        """Supprime un settings.conf créé par une ancienne version du tool, pour
        revenir aux défauts internes MakeMKV (qui marchent généralement mieux
        qu'un +sel:all minimaliste sans contexte)."""
        from makemkv_extract import _makemkv_settings_path
        cfg = _makemkv_settings_path()
        if not os.path.isfile(cfg):
            return {"ok": True, "msg": "Pas de settings.conf à supprimer"}
        try:
            content = open(cfg, "r", encoding="utf-8").read()
        except Exception as e:
            return {"ok": False, "error": str(e)}
        # Si le fichier ne contient QUE app_DefaultSelectionString = "+sel:all" → c'est nous qui l'avons créé
        if content.strip() == 'app_DefaultSelectionString = "+sel:all"':
            try:
                os.remove(cfg)
                # tente aussi de retirer le backup
                bak = cfg + ".remux_tool.bak"
                if os.path.isfile(bak):
                    os.remove(bak)
                return {"ok": True, "msg": f"settings.conf supprimé (était minimaliste). MakeMKV utilisera ses défauts."}
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return {"ok": True, "msg": f"settings.conf existant non touché (contenu personnalisé) : {cfg}"}

    # ----- analyse (asynchrone : retourne tout de suite, émet 'analyzed') -
    def analyze(self, movie_entry: str):
        if self._busy:
            return {"ok": False, "error": "Une opération est déjà en cours."}
        self._busy = True
        threading.Thread(target=self._analyze_worker, args=(movie_entry,), daemon=True).start()
        return {"ok": True, "started": True}

    def _analyze_worker(self, movie_entry: str):
        cfg = _read_config_file()
        full_dir = cfg["FULL_DIR"]
        if not os.path.isabs(full_dir):
            full_dir = str(BASE_DIR / full_dir)

        original_stdout = sys.stdout
        original_stderr = sys.stderr
        _last_prog_ts = [0.0]

        def on_progress(pct, eta):
            now = time.time()
            if pct != 100 and now - _last_prog_ts[0] < 0.5:
                return   # throttle : max 2 émissions/s
            _last_prog_ts[0] = now
            self._emit("progress", {"step": "analyze", "pct": pct, "eta": eta})

        def on_line(line, level):
            self._log(line, level)

        sys.stdout = StdoutTee(original_stdout, on_line, on_progress)
        sys.stderr = StdoutTee(original_stderr, on_line, on_progress)

        # Heartbeat : ping toutes les 3 s pour montrer que c'est vivant
        hb_stop = threading.Event()

        def _heartbeat():
            t0 = time.time()
            i = 0
            while not hb_stop.wait(3.0):
                i += 1
                elapsed = int(time.time() - t0)
                self._emit("analyze_status", {
                    "msg": f"⏳ MakeMKV scanne le disque… {elapsed}s écoulées",
                })
                # Toutes les 30 s on log aussi dans la console
                if i % 10 == 0:
                    self._log(f"   ⏳ Toujours en cours ({elapsed}s) — un BDMV peut prendre jusqu'à 5 min", "warn")

        threading.Thread(target=_heartbeat, daemon=True).start()

        try:
            try:
                source_path = self._resolve_source(full_dir, movie_entry)
            except Exception as e:
                self._emit("analyzed", {"ok": False, "error": str(e)})
                return

            self._log(f"🔍 Analyse du disque : {movie_entry}")
            self._emit("analyze_status", {"msg": "Scan MakeMKV en cours… (30 s à 2 min selon le disque)"})

            try:
                info = analyze_source(source_path)
            except Exception as e:
                self._log(f"❌ Échec analyse : {e}", "error")
                self._emit("analyzed", {"ok": False, "error": str(e)})
                return

            titles = info.get("titles", [])
            if not titles:
                self._emit("analyzed", {"ok": False, "error": "Aucun titre trouvé sur ce disque."})
                return

            def _parse_dur(d):
                try:
                    parts = (d or "0:0:0").split(":")
                    if len(parts) == 3:
                        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    if len(parts) == 2:
                        return int(parts[0]) * 60 + int(parts[1])
                    return int(parts[0])
                except Exception:
                    return 0

            out_titles = []
            max_dur = 0
            max_idx = 0
            for i, t in enumerate(titles):
                streams = t.get("streams", [])
                # Ajouter une 'position' (index dans la liste de son type) pour le mapping post-extraction
                video = []
                for pos, s in enumerate([s for s in streams if get_stream_type(s) == "video"]):
                    d = _stream_to_dict(s); d["position"] = pos; video.append(d)
                audio = []
                for pos, s in enumerate([s for s in streams if get_stream_type(s) == "audio"]):
                    d = _stream_to_dict(s); d["position"] = pos; audio.append(d)
                subs = []
                for pos, s in enumerate([s for s in streams if get_stream_type(s) == "subtitle"]):
                    d = _stream_to_dict(s); d["position"] = pos; subs.append(d)
                dur_sec = _parse_dur(t.get("duration", ""))
                if dur_sec > max_dur:
                    max_dur = dur_sec
                    max_idx = i
                out_titles.append({
                    "idx": i,
                    "id": t.get("id"),
                    "name": t.get("name") or f"title_{t.get('id')}",
                    "duration": t.get("duration") or "",
                    "size_gb": round((t.get("size_bytes") or 0) / (1024 ** 3), 2),
                    "chapters": t.get("chapters") or 0,
                    "video": video,
                    "audio": audio,
                    "subs": subs,
                })

            main = out_titles[max_idx]
            defaults = self._compute_defaults(main)

            # Détection titre/année depuis le nom du dossier
            guessed_title, guessed_year = _clean_movie_title(movie_entry)
            human_title = guessed_title.replace(".", " ") if guessed_title else movie_entry

            # Lookup TMDB pour récupérer le titre français
            tmdb_info = {}
            if human_title:
                self._log(f"🔍 TMDB : recherche de « {human_title} » {guessed_year or ''}…")
                tmdb_info = _tmdb_lookup(human_title, guessed_year, language="fr-FR")
                if tmdb_info.get("ok"):
                    fr_title = tmdb_info["title"]
                    self._log(f"  → TMDB : « {fr_title} » ({tmdb_info.get('year','?')})", "success")
                    if fr_title and fr_title.lower() != human_title.lower():
                        human_title = fr_title
                else:
                    self._log(f"  ⚠ TMDB : {tmdb_info.get('error', 'inconnu')}", "warn")

            self._log(f"  → Titre principal détecté : #{max_idx + 1} ({main['duration']})", "success")
            self._emit("analyzed", {
                "ok": True,
                "movie": movie_entry,
                "source": source_path,
                "main_title": max_idx,
                "titles": out_titles,
                "defaults": defaults,
                "guessed_title": guessed_title,
                "guessed_year": guessed_year,
                "human_title": human_title,
                "tmdb": tmdb_info if tmdb_info.get("ok") else None,
            })
        finally:
            hb_stop.set()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            self._busy = False

    def _compute_defaults(self, title: dict) -> dict:
        """Calcule la sélection par défaut (meilleure VO + VF par type, FR forced/full).
        On renvoie les IDs MakeMKV ET les positions pour le mapping post-extraction."""
        audio = title["audio"]
        en = sorted([a for a in audio if a["is_en"]], key=lambda x: -x["score"])
        fr = sorted([a for a in audio if a["is_fr"]], key=lambda x: -x["score"])
        chosen_audio = []
        if en:
            chosen_audio.append(en[0]["id"])
        seen_vf = set()
        for a in fr:
            v = a["vf_type"] or "VFF"
            if v not in seen_vf:
                seen_vf.add(v)
                chosen_audio.append(a["id"])

        cfg = _read_config_file()
        keep_en_subs = bool(cfg.get("KEEP_ENGLISH_SUBS", 1))
        chosen_subs = []
        for s in title["subs"]:
            if s["is_fr"]:
                chosen_subs.append(s["id"])
            elif s["is_en"] and keep_en_subs:
                chosen_subs.append(s["id"])

        chosen_video = [v["id"] for v in title["video"][:1]]
        return {"video": chosen_video, "audio": chosen_audio, "subs": chosen_subs}

    @staticmethod
    def _resolve_source(full_dir: str, entry: str) -> str:
        base = os.path.join(full_dir, entry)
        if os.path.isfile(base) and entry.lower().endswith(".iso"):
            return base
        if os.path.isdir(base):
            isos = [f for f in os.listdir(base) if f.lower().endswith(".iso")]
            if isos:
                return os.path.join(base, isos[0])
            bdmv = os.path.join(base, "BDMV")
            if os.path.isdir(bdmv):
                return bdmv
        raise FileNotFoundError(f"Source introuvable pour {entry}")

    # ----- workflow remux -------------------------------------------------
    def run_remux(self, params: dict):
        if self._busy:
            return {"ok": False, "error": "Un remux est déjà en cours."}
        self._busy = True
        self._cancel.clear()
        threading.Thread(target=self._workflow, args=(params,), daemon=True).start()
        return {"ok": True}

    def _workflow(self, p: dict):
        cfg = _read_config_file()
        full_dir = cfg["FULL_DIR"]
        out_dir_root = cfg["OUTPUT_DIR"]
        if not os.path.isabs(full_dir):
            full_dir = str(BASE_DIR / full_dir)
        if not os.path.isabs(out_dir_root):
            out_dir_root = str(BASE_DIR / out_dir_root)

        movie_entry = p["movie"]
        title_idx = int(p["title_idx"])
        sel_video = list(p.get("video", []))
        sel_audio = list(p.get("audio", []))
        sel_subs = list(p.get("subs", []))
        # Positions (legacy) — gardées pour rétrocompat / fallback
        audio_positions = list(p.get("audio_positions", []))
        sub_positions   = list(p.get("sub_positions", []))
        # Picks structurés : {position, lang, is_en, is_fr, override}
        audio_picks = list(p.get("audio_picks", []))
        sub_picks   = list(p.get("sub_picks", []))
        # Overrides legacy : {position: type}
        _vf_raw  = p.get("vf_overrides")  or {}
        _sub_raw = p.get("sub_overrides") or {}
        vf_overrides  = {int(k): str(v) for k, v in _vf_raw.items()  if v}
        sub_overrides = {int(k): str(v) for k, v in _sub_raw.items() if v}
        year = str(p.get("year") or "").strip()
        # Le tag VF du nom de fichier est désormais 100% dérivé des overrides
        # par piste (VFF/VFQ → VF2, etc.) — plus de tag global.
        # Titre humain pour mkvmerge --title et la piste vidéo
        title_human = (p.get("title_human") or "").strip()
        is_custom = bool(int(cfg.get("IS_CUSTOM", 0)))

        movie_name = os.path.splitext(movie_entry)[0] if movie_entry.lower().endswith(".iso") else movie_entry
        # Si pas d'année reçue → on tente de la deviner depuis le nom du dossier
        if not year:
            _, guessed_year = _clean_movie_title(movie_entry)
            year = guessed_year or "2025"

        output_dir = out_dir_root
        os.makedirs(output_dir, exist_ok=True)

        # Redirection stdout pour capter logs + progress
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        cur_step = {"name": ""}
        _last_prog_ts2 = [0.0]

        def on_progress(pct, eta):
            now = time.time()
            if pct != 100 and now - _last_prog_ts2[0] < 0.5:
                return   # throttle : max 2 émissions/s
            _last_prog_ts2[0] = now
            self._emit("progress", {"step": cur_step["name"], "pct": pct, "eta": eta})

        def on_line(line, level):
            self._log(line, level)

        sys.stdout = StdoutTee(original_stdout, on_line, on_progress)
        sys.stderr = StdoutTee(original_stderr, on_line, on_progress)

        try:
            # --------- 1. analyse ---------
            cur_step["name"] = "analyze"
            self._emit("step", {"n": 1, "total": 4, "label": "Analyse du disque"})
            source_path = self._resolve_source(full_dir, movie_entry)
            info = analyze_source(source_path)
            titles = info.get("titles", [])
            if not titles or title_idx < 0 or title_idx >= len(titles):
                raise RuntimeError("Titre invalide")
            selected_title = titles[title_idx]
            title_id = selected_title["id"]

            if self._cancel.is_set():
                raise RuntimeError("Annulé par l'utilisateur")

            # --------- 2. extract ---------
            cur_step["name"] = "extract"
            self._emit("step", {"n": 2, "total": 4, "label": "Extraction MakeMKV"})
            self._emit("progress", {"step": "extract", "pct": 0, "eta": ""})

            selected_streams_ids = sel_video + sel_audio + sel_subs
            mkv_path = extract_title(
                source=source_path,
                title_id=title_id,
                output_dir=output_dir,
                selected_streams=selected_streams_ids,
            )
            self._emit("progress", {"step": "extract", "pct": 100, "eta": ""})

            if self._cancel.is_set():
                raise RuntimeError("Annulé après extraction")

            # --------- 3. mediainfo ---------
            cur_step["name"] = "mediainfo"
            self._emit("step", {"n": 3, "total": 4, "label": "Analyse MediaInfo"})

            # Dump direct via mkvmerge -J (plus fiable que MediaInfo pour le diag)
            # On utilise print() pour que ça apparaisse dans le terminal ET dans le GUI
            try:
                from mkvtoolnix_remux import _find_mkvmerge, _identify
                _info_mm = _identify(_find_mkvmerge(), mkv_path)
                _tr = _info_mm.get("tracks", [])
                _v = sum(1 for t in _tr if t.get("type") == "video")
                _a = sum(1 for t in _tr if t.get("type") == "audio")
                _s = sum(1 for t in _tr if t.get("type") == "subtitles")
                print(f"  📋 mkvmerge -J : {_v} vid, {_a} aud, {_s} sub")
                for t in _tr:
                    if t.get("type") == "subtitles":
                        p = t.get("properties", {}) or {}
                        print(
                            f"    sub mm[{t.get('id')}] lang={p.get('language','?')!r} "
                            f"name={p.get('track_name','')!r} forced={p.get('forced_track')} "
                            f"codec={t.get('codec','?')}"
                        )
            except Exception as e:
                print(f"  ⚠ mkvmerge -J : {e}")

            video_info, audio_tracks, sub_tracks = parse_mediainfo(mkv_path)
            print(f"  📊 MediaInfo : {len(audio_tracks)} audio, {len(sub_tracks)} sous-titre(s) dans le MKV extrait")
            for k, t in enumerate(audio_tracks):
                fmt = t.get("Format_Commercial_IfAny") or t.get("Format") or "?"
                lang = t.get("Language") or "?"
                title = t.get("Title") or ""
                ch = t.get("Channels") or "?"
                print(f"    audio[{k}] lang={lang!r} fmt={fmt} ch={ch} title={title!r}")
            for k, t in enumerate(sub_tracks):
                fmt = t.get("Format") or "?"
                lang = t.get("Language") or "?"
                title = t.get("Title") or ""
                elements = t.get("ElementCount") or t.get("elements") or "?"
                print(f"    sub[{k}] lang={lang!r} fmt={fmt} elements={elements} title={title!r}")
            if sub_positions and not sub_tracks:
                print(
                    "  ⚠ Tu avais coché des sous-titres mais MakeMKV n'en a extrait aucun.\n"
                    "    Configure MakeMKV.app → Preferences → Languages :\n"
                    "    - Preferred subtitle language : fre (ou nolang)\n"
                    "    - 'Default subtitle selection' adapté à tes besoins"
                )

            # ───── détection résolution / codec / hdr ─────
            resolution = "1080p"
            codec = "AVC"
            is_uhd = False
            hdr = ""
            if video_info:
                # Espaces normaux ET espaces fines insécables (MediaInfo formate
                # parfois "2 160" / "1 080" avec U+202F).
                height = str(video_info.get("Height", "")).replace(" ", "").replace(" ", "")
                width = str(video_info.get("Width", "")).replace(" ", "").replace(" ", "")
                scan = (video_info.get("ScanType", "") or "").strip().lower()

                fmt = (video_info.get("Format", "") or "").upper()
                if "HEVC" in fmt or "265" in fmt:
                    codec = "HEVC"
                elif "AVC" in fmt or "264" in fmt:
                    codec = "AVC"
                elif "AV1" in fmt:
                    codec = "AV1"
                elif "VC-1" in fmt or "VC1" in fmt:
                    codec = "VC-1"

                if "2160" in height or "3840" in width or "4k" in height.lower():
                    # UHD/4K → 2160p obligatoire, quel que soit le scan type.
                    resolution = "2160p"
                    is_uhd = True
                elif "1080" in height:
                    # 1080 : on distingue progressif (1080p) vs entrelacé (1080i)
                    # via le ScanType réel de MediaInfo (pas le nom de dossier).
                    resolution = "1080i" if "interlac" in scan else "1080p"

                # Le codec confirme/corrige la résolution :
                # HEVC = toujours UHD (2160p) ; AVC/VC-1 = toujours Blu-ray
                # standard (1080p ou 1080i), jamais 2160p.
                if codec == "HEVC":
                    resolution = "2160p"
                    is_uhd = True
                elif codec in ("AVC", "VC-1") and resolution == "2160p":
                    resolution = "1080i" if "interlac" in scan else "1080p"
                    is_uhd = False
                # MediaInfo expose HDR_Format (le format primaire) ET
                # HDR_Format_Compatibility (les formats compatibles, ex "HDR10")
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

            # ───── Sélection des pistes par POSITION ─────
            # On respecte ce que l'utilisateur a coché dans le GUI : on prend
            # les pistes mediainfo aux positions correspondantes (l'ordre est
            # conservé entre MakeMKV et le MKV extrait).
            def _detect_vf(t):
                title = (t.get("Title") or "").upper()
                lang = (t.get("Language") or "").lower()
                more = (t.get("Language_More") or "").upper()
                if "VFF" in title or "FRANCE" in title or "FRANCE" in more or lang == "fr-fr":
                    return "VFF"
                if "VFQ" in title or "QUEBEC" in title or "QUÉBEC" in title or "CANADA" in more or lang == "fr-ca":
                    return "VFQ"
                if "VFI" in title or "INTERNATIONAL" in title:
                    return "VFi"
                return None

            def _is_en(t):
                lang = (t.get("Language") or "").lower()
                title = (t.get("Title") or "").upper()
                return lang in ("en", "eng", "english", "en-us", "en-gb") or "ENGLISH" in title or title.startswith("VO")

            def _is_fr(t):
                lang = (t.get("Language") or "").lower()
                title = (t.get("Title") or "").upper()
                if lang in ("fr", "fra", "fre", "french", "fr-fr", "fr-ca", "fr-be", "fr-ch"):
                    return True
                return any(x in title for x in ["FRENCH", "FRANÇAIS", "FRANCAIS", "VFF", "VFQ", "VFI", "VF2"])

            if audio_picks:
                kept_audio = _resolve_picks(audio_picks, audio_tracks, kind="audio")
                self._log(f"  Pistes audio gardées (mapping picks) : {len(kept_audio)} sur {len(audio_picks)} demandées", "success")
            elif audio_positions:
                kept_audio = []
                for i in audio_positions:
                    if 0 <= i < len(audio_tracks):
                        t = audio_tracks[i]
                        if i in vf_overrides:
                            t["_user_vf"] = vf_overrides[i]
                        kept_audio.append(t)
                self._log(f"  Pistes audio gardées (positions {audio_positions}) : {len(kept_audio)}", "success")
            else:
                # Fallback : meilleure EN + une par type VF
                en_tr = sorted([t for t in audio_tracks if _is_en(t)], key=_audio_quality, reverse=True)
                fr_tr = sorted([t for t in audio_tracks if _is_fr(t)], key=_audio_quality, reverse=True)
                kept_audio = []
                if en_tr:
                    kept_audio.append(en_tr[0])
                seen = set()
                for t in fr_tr:
                    v = _detect_vf(t) or "VFF"
                    if v not in seen:
                        seen.add(v)
                        kept_audio.append(t)

            # Pose les hints pour mkvtoolnix_remux : nom humain de la langue + VF auto
            for t in kept_audio:
                t["_detected_vf"] = _detect_vf(t)
                # Label humain (utilisé par mkvmerge pour les langues non-FR/non-EN)
                t["_lang_human"] = _lang_label(
                    (t.get("Language") or ""),
                    (t.get("Language_String") or t.get("Language_String3") or ""),
                )

            # Pour le tag du nom de fichier on utilise en priorité l'override user
            # (_user_vf), sinon ce qu'on a auto-détecté (_detected_vf).
            # Les pistes AD (AD VFF / AD VFQ / AD VFi / AD) sont ignorées pour
            # le tag : seule la VF principale du film compte.
            def _track_vf(t):
                return (t.get("_user_vf") or t.get("_detected_vf") or "").strip()
            def _is_ad(v):
                return v.upper().startswith("AD")
            vf_types_found = [
                _track_vf(t) for t in kept_audio
                if _is_fr(t) and _track_vf(t) and not _is_ad(_track_vf(t))
            ]
            has_en = any(_is_en(t) for t in kept_audio)
            has_fr = any(_is_fr(t) for t in kept_audio)
            # Présence d'au moins une piste audio dans une langue autre que le
            # français (anglais, arabe, espagnol, japonais...) — sert à détecter
            # MULTi pour les films dont la VO n'est pas anglaise (ex: VO arabe +
            # doublage VFi -> MULTi.VFi).
            has_other = any(not _is_fr(t) for t in kept_audio)

            # Tag VF — dérivé 100% des overrides (et auto-détection en fallback)
            uniq = set(vf_types_found)
            if "VFF" in uniq and "VFQ" in uniq:
                vf_tag = "VF2"
            elif "VFF" in uniq:
                vf_tag = "VFF"
            elif "VFQ" in uniq:
                vf_tag = "VFQ"
            elif "VFi" in uniq:
                vf_tag = "VFi"
            elif "VOF" in uniq:
                vf_tag = "VOF"
            else:
                vf_tag = "VFF" if has_fr else ""

            lang_tag = (f"MULTi.{vf_tag}" if vf_tag else "MULTi") if (has_other and has_fr) else (
                vf_tag or ("FRENCH" if has_fr else "ENGLISH" if has_en else "")
            )

            # Codec audio principal — convention: AC3 / EAC3 / DTS-HD.MA / TrueHD
            # On choisit la piste de référence = piste FR avec le plus gros débit
            # (évite de prendre une 2.0 en tête de liste quand une 5.1 existe)
            audio_codec_str = ""
            if kept_audio:
                def _br(t):
                    try:
                        return int(t.get("BitRate") or 0)
                    except Exception:
                        return 0
                def _ch(t):
                    try:
                        return int(t.get("Channels") or 0)
                    except Exception:
                        return 0
                # Piste la plus lourde toutes langues confondues
                t = max(kept_audio, key=lambda x: (_br(x), _ch(x)))
                fmt = (t.get("Format_Commercial_IfAny") or t.get("Format") or "").upper()
                if "DTS-HD" in fmt or "MASTER" in fmt:
                    af = "DTS-HD.MA"
                elif "TRUEHD" in fmt:
                    af = "TrueHD.Atmos" if "ATMOS" in fmt else "TrueHD"
                elif "DTS" in fmt:
                    af = "DTS"
                elif "DD+" in fmt or "E-AC" in fmt or "PLUS" in fmt or "DDP" in fmt:
                    af = "EAC3"
                elif "AC3" in fmt or "AC-3" in fmt or "DOLBY DIGITAL" in fmt or "DD" in fmt:
                    af = "AC3"
                else:
                    af = ""
                ch = t.get("Channels")
                ch_num = int(ch) if str(ch).isdigit() else 0
                ach = "7.1" if ch_num >= 8 else "5.1" if ch_num >= 6 else "2.0" if ch_num >= 2 else ""
                audio_codec_str = f"{af}.{ach}" if af and ach else af

            # Sous-titres : mapping par picks (lang-aware, fallback hors-plage)
            keep_en_subs = bool(int(cfg.get("KEEP_ENGLISH_SUBS", 1)))
            if sub_picks:
                kept_subs = _resolve_picks(sub_picks, sub_tracks, kind="subs")
                self._log(f"  Sous-titres gardés (mapping picks) : {len(kept_subs)} sur {len(sub_picks)} demandés", "success")
            elif sub_positions:
                kept_subs = []
                for i in sub_positions:
                    if 0 <= i < len(sub_tracks):
                        t = sub_tracks[i]
                        lang = (t.get("Language") or "").lower()
                        title = (t.get("Title") or "").lower()
                        t["SubLang"] = "en" if (lang in ("en", "eng", "english") or "english" in title) else "fr"
                        if i in sub_overrides:
                            t["SubType"] = sub_overrides[i]
                        kept_subs.append(t)
                self._log(f"  Sous-titres gardés (positions {sub_positions}) : {len(kept_subs)}", "success")
            else:
                # Fallback : FR + EN si activé
                kept_subs = []
                for t in sub_tracks:
                    lang = (t.get("Language") or "").lower()
                    title = (t.get("Title") or "").lower()
                    is_fr = lang in ("fr", "fra", "fre", "french") or any(x in title for x in ["french", "français"])
                    is_en = lang in ("en", "eng", "english") or "english" in title
                    if is_fr:
                        t["SubLang"] = "fr"
                        kept_subs.append(t)
                    elif is_en and keep_en_subs:
                        t["SubLang"] = "en"
                        kept_subs.append(t)

            # ── NOM DU FICHIER ──
            # TOUJOURS dérivé du nom de DOSSIER source (jamais du titre humain TMDB).
            # Convention scene/release : titre original anglais pointillé, sans
            # caractères spéciaux ni accents.
            cleaned_title, _ignored_year = _clean_movie_title(movie_entry)
            if not cleaned_title:
                cleaned_title = _main_mod._to_title_case_dotted(movie_name)
            final_name = _main_mod.build_final_name(
                movie=cleaned_title,
                year=year,
                lang_tag=lang_tag,
                resolution=resolution,
                is_uhd=is_uhd,
                codec=codec,
                hdr=hdr,
                audio_codec=audio_codec_str,
                is_custom=is_custom,
            )
            final_path = os.path.join(output_dir, final_name)

            # ── TITRE MKV (métadonnées General + piste vidéo SEULEMENT) ──
            # Le titre humain TMDB (ex: "Hurlevent", "Goat : Rêver Plus Haut") va
            # ICI uniquement, jamais dans le nom du fichier.
            mkv_human_title = title_human or cleaned_title.replace(".", " ")
            self._log(f"📛 Nom final : {final_name}", "success")
            self._log(f"🎞 Titre MKV  : {mkv_human_title}", "info")

            if self._cancel.is_set():
                raise RuntimeError("Annulé avant remux")

            # --------- 4. remux ---------
            cur_step["name"] = "remux"
            self._emit("step", {"n": 4, "total": 4, "label": "Remux MKVToolNix"})
            self._emit("progress", {"step": "remux", "pct": 0, "eta": ""})

            track_selection = {
                "selected_audio": kept_audio,
                "selected_subs": kept_subs,
                "vf_tag": vf_tag,
                # Overrides reconnus par notre patch de mkvtoolnix_remux
                "mkv_title": mkv_human_title,
                "video_track_name": mkv_human_title,
            }
            rc = run_mkvmerge(mkv_path, track_selection, final_path)
            if rc != 0 or not os.path.isfile(final_path):
                raise RuntimeError(f"Remux échoué (code {rc})")
            self._emit("progress", {"step": "remux", "pct": 100, "eta": ""})

            # cleanup
            try:
                if os.path.abspath(mkv_path) != os.path.abspath(final_path):
                    os.remove(mkv_path)
            except Exception:
                pass

            file_size = os.path.getsize(final_path)
            size_gb = file_size / (1024 ** 3)

            # NFO géré par le bot upload (app.py) une fois le .mkv dans FILMS/
            nfo_path = ""

            self._save_history({
                "movie": movie_entry,
                "final_name": final_name,
                "size_gb": round(size_gb, 2),
                "lang_tag": lang_tag,
                "resolution": resolution,
                "codec": codec,
                "hdr": hdr,
                "vf_tag": vf_tag,
                "path": final_path,
            })

            self._emit("done", {
                "ok": True,
                "file": final_name,
                "size_gb": round(size_gb, 2),
                "path": final_path,
                "nfo": os.path.basename(nfo_path) if nfo_path else "",
                "dir": output_dir,
            })
            self._log(f"✅ Terminé : {final_name} ({size_gb:.1f} GB)", "success")

        except Exception as e:
            import traceback
            self._log(f"❌ {e}", "error")
            traceback.print_exc(file=original_stdout)
            self._emit("done", {"ok": False, "error": str(e)})
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            self._busy = False


# ──────────────────────────────────────────────────────────────────────────
# Lancement
# ──────────────────────────────────────────────────────────────────────────
def main():
    api = API()
    html_path = BASE_DIR / "gui_index.html"
    if not html_path.exists():
        print(f"[ERREUR] {html_path} introuvable.")
        sys.exit(1)
    html = html_path.read_text(encoding="utf-8")

    window = webview.create_window(
        "Remux Tool — Blu-ray → MKV",
        html=html,
        js_api=api,
        width=1200,
        height=820,
        min_size=(1000, 680),
        background_color="#0a0a0a",
    )
    api.window = window
    webview.start(debug=False)


if __name__ == "__main__":
    main()
