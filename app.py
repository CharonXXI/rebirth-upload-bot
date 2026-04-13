#!/usr/bin/env python3
# coding: utf-8
"""
REBiRTH Upload Bot — PyWebView GUI
Lance avec : python3 app.py
"""

import os, sys, json, re, subprocess, threading, builtins
from pathlib import Path
from threading import Event
from datetime import datetime

import webview
import requests
from dotenv import load_dotenv, set_key

BASE_DIR     = Path(__file__).parent
ENV_FILE     = BASE_DIR / "V1.env"
HISTORY_FILE = BASE_DIR / "history.json"
THEME_FILE   = BASE_DIR / "theme.txt"
sys.path.insert(0, str(BASE_DIR))

from gofile import gofile_upload
from NFO_CUSTOM import NFO_v1_7

load_dotenv(ENV_FILE)


class API:
    def __init__(self):
        self.window              = None
        self._tmdb_event         = Event()
        self._tmdb_confirmed     = None
        self._torrent_event      = Event()
        self._torrent_confirmed  = None

    def get_config(self):
        return {
            "GOFILE_TOKEN":       os.getenv("GOFILE_TOKEN", ""),
            "WEBHOOK_URL":        os.getenv("WEBHOOK_URL", ""),
            "API_KEY":            os.getenv("API_KEY", ""),
            "LANGUAGE":           os.getenv("LANGUAGE", "fr-FR"),
            "BUZZHEAVIER_ACC_ID": os.getenv("BUZZHEAVIER_ACC_ID", ""),
            "SFTP_HOST":          os.getenv("SFTP_HOST", ""),
            "SFTP_HOST_FTP":      os.getenv("SFTP_HOST_FTP", ""),
            "SFTP_PORT":          os.getenv("SFTP_PORT", ""),
            "SFTP_USER":          os.getenv("SFTP_USER", ""),
            "SFTP_PASS":          os.getenv("SFTP_PASS", ""),
            "SFTP_PATH":          os.getenv("SFTP_PATH", "/rtorrent/REBiRTH"),
            "RUTORRENT_URL":      os.getenv("RUTORRENT_URL", ""),
            "RUTORRENT_USER":     os.getenv("RUTORRENT_USER", ""),
            "RUTORRENT_PASS":     os.getenv("RUTORRENT_PASS", ""),
            "TRACKER_ABN":        os.getenv("TRACKER_ABN", ""),
            "TRACKER_TOS":        os.getenv("TRACKER_TOS", ""),
            "TRACKER_C411":       os.getenv("TRACKER_C411", ""),
            "TRACKER_TORR9":      os.getenv("TRACKER_TORR9", ""),
            "TRACKER_LACALE":     os.getenv("TRACKER_LACALE", ""),
        }

    def save_config(self, cfg: dict):
        for k, v in cfg.items():
            set_key(str(ENV_FILE), k, v)
            os.environ[k] = v
        return {"ok": True}

    def load_history(self):
        if not HISTORY_FILE.exists():
            return []
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_history_entry(self, entry: dict):
        history = self.load_history()
        history.insert(0, entry)
        history = history[:100]  # garder les 100 dernières entrées
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return {"ok": True}

    def clear_history(self):
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        return {"ok": True}

    def save_theme(self, theme: str):
        THEME_FILE.write_text(theme, encoding="utf-8")
        return {"ok": True}

    def load_theme(self):
        if THEME_FILE.exists():
            return THEME_FILE.read_text(encoding="utf-8").strip()
        return "dark"

    def confirm_torrents(self, data):
        self._torrent_confirmed = data.get("selected", [])
        self._torrent_event.set()
        return {"ok": True}

    def confirm_tmdb(self, data):
        self._tmdb_confirmed = data.get("tmdb_link", "")
        self._tmdb_event.set()
        return {"ok": True}

    def pick_file(self):
        films_dir = BASE_DIR / "FILMS"
        start_dir = str(films_dir) if films_dir.exists() else str(Path.home())
        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG if not hasattr(webview, 'FileDialog') else webview.FileDialog.OPEN,
            directory=start_dir,
            file_types=("Vidéo (*.mkv;*.mp4)",)
        )
        if not result:
            return None
        path = result[0]
        size = os.path.getsize(path)
        if size > 1073741824:
            size_str = str(round(size / 1073741824, 2)) + " GiB"
        elif size > 1048576:
            size_str = str(round(size / 1048576, 1)) + " MiB"
        else:
            size_str = str(round(size / 1024, 1)) + " KiB"
        self.window.evaluate_js("document.getElementById('file-size').textContent = '" + size_str + "';")
        return path

    def run_workflow(self, params: dict):
        threading.Thread(target=self._workflow, args=(params,), daemon=True).start()
        return {"ok": True}

    def list_seedbox_files(self):
        """Retourne la liste des dossiers présents dans SFTP_PATH via FTP."""
        import ftplib
        try:
            host     = os.getenv("SFTP_HOST_FTP", "")
            port     = int(os.getenv("SFTP_PORT", "23421"))
            user     = os.getenv("SFTP_USER", "")
            password = os.getenv("SFTP_PASS", "")
            path     = os.getenv("SFTP_PATH", "/rtorrent/REBiRTH")

            if not host:
                return {"error": "SFTP_HOST_FTP non configuré"}

            ftp = ftplib.FTP_TLS()
            ftp.connect(host, port, timeout=10)
            ftp.login(user, password)
            ftp.prot_p()

            # Naviguer vers le dossier REBiRTH
            parts = path.strip("/").split("/")
            for part in parts:
                ftp.cwd(part)

            # Lister le contenu (dossiers uniquement)
            entries = []
            ftp.retrlines("LIST", entries.append)
            ftp.quit()

            folders = []
            for entry in entries:
                parts_e = entry.split()
                if not parts_e:
                    continue
                name = parts_e[-1]
                # Ignore les entrées . et ..
                if name in (".", ".."):
                    continue
                # Lignes commençant par 'd' = dossier, sinon fichier aussi
                folders.append(name)

            folders.sort(key=lambda x: x.lower())
            return {"files": folders, "path": path}

        except Exception as e:
            return {"error": str(e)}

    def run_torrent_sb(self, params: dict):
        threading.Thread(target=self._torrent_sb, args=(params,), daemon=True).start()
        return {"ok": True}

    def _torrent_sb(self, params):
        try:
            filename    = params.get("filename", "").strip()
            remote_path = params.get("remote_path", "").strip()
            trackers    = params.get("trackers", "")
            private     = params.get("private", True)

            self._log("▶ Torrent SB démarré")
            self._log("  filename    : " + (filename or "(vide)"))
            self._log("  trackers    : " + (trackers or "(vide)"))
            self._log("  remote_path : " + (remote_path or "(auto)"))

            if not filename:
                raise Exception("Aucun nom de fichier spécifié.")

            base = Path(filename).stem  # nom sans extension

            if not remote_path:
                remote_base = os.getenv("SFTP_PATH", "/rtorrent/REBiRTH")
                remote_path = remote_base + "/" + base
                self._log("  remote_path (auto) : " + remote_path)

            announces = {
                "ABN":    os.getenv("TRACKER_ABN", ""),
                "TOS":    os.getenv("TRACKER_TOS", ""),
                "C411":   os.getenv("TRACKER_C411", ""),
                "TORR9":  os.getenv("TRACKER_TORR9", ""),
                "LACALE": os.getenv("TRACKER_LACALE", ""),
            }
            checked = [t.strip().upper() for t in trackers.split() if t.strip()]
            active  = {k: v for k, v in announces.items() if v and k.upper() in checked}

            self._log("  trackers cochés : " + str(checked))
            self._log("  trackers actifs : " + str(list(active.keys())))

            rt_url = os.getenv("RUTORRENT_URL", "")
            self._log("  ruTorrent URL   : " + (rt_url or "(non configuré !)"))

            if not active:
                raise Exception("Aucun tracker configuré pour les cases cochées. Vérifie les announces dans Config.")

            self._create_torrent_rutorrent(base, remote_path, active, private=bool(private))
            self._emit("done", {"nfo_only": False, "url": "Torrents SB créés !"})

        except Exception as e:
            import traceback
            self._log("✗ Erreur : " + str(e), "error")
            traceback.print_exc()
            self._emit("error", {"msg": str(e)})

    def run_batch_nfo(self, data: dict):
        def _run():
            file_paths = data.get("file_paths", [])
            params     = data.get("params", {})
            total      = len(file_paths)
            for i, fp in enumerate(file_paths):
                self._emit("batch_file_start", {
                    "current": i + 1, "total": total,
                    "filename": os.path.basename(fp)
                })
                self._workflow({**params, "file_path": fp, "nfo_only": True})
            self._emit("batch_done", {"total": total})
        threading.Thread(target=_run, daemon=True).start()
        return {"ok": True}

    def pick_files_multi(self):
        films_dir = BASE_DIR / "FILMS"
        start_dir = str(films_dir) if films_dir.exists() else str(Path.home())
        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG if not hasattr(webview, 'FileDialog') else webview.FileDialog.OPEN,
            directory=start_dir,
            allow_multiple=True,
            file_types=("Vidéo (*.mkv;*.mp4)",)
        )
        return list(result) if result else []

    def _emit(self, event: str, data):
        payload = json.dumps(data).replace("'", "\\'")
        self.window.evaluate_js(f"window._emit('{event}', {payload})")

    def _log(self, msg: str, level="info"):
        self._emit("log", {"msg": msg, "level": level})

    def _workflow(self, p: dict):
        caffeinate = None
        if sys.platform == "darwin":
            caffeinate = subprocess.Popen(["caffeinate", "-i"])
        elif sys.platform == "win32":
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)

        try:
            fp          = p["file_path"]
            source      = p.get("source", "")
            note        = p.get("note", "")
            trackers    = p.get("trackers", "")
            autre       = p.get("autre", "")
            platform    = p.get("platform", "b")
            nfo_type    = p.get("nfo_type", "utf8")
            skip_upload = p.get("skip_upload", False)
            nfo_only    = p.get("nfo_only", False)
            api_key     = os.getenv("API_KEY", "")
            language    = os.getenv("LANGUAGE", "fr-FR")
            bzhv_id     = os.getenv("BUZZHEAVIER_ACC_ID", "")
            os.environ["GOFILE_TOKEN"] = os.getenv("GOFILE_TOKEN", "")

            file_dir = os.path.dirname(fp)
            base     = os.path.basename(os.path.splitext(fp)[0])
            out_utf8 = os.path.join(file_dir, f"(UTF8).{base}.nfo")
            out_dos  = os.path.join(file_dir, f"(CP437).{base}.nfo")

            # ── 1. TMDB EN PREMIER ────────────────────────────────────────────
            self._log("Recherche TMDB…")
            tmdb_link  = ""
            poster_url = "https://upload.wikimedia.org/wikipedia/commons/a/a3/Image-not-found.png"
            imdb_link  = None
            score      = 0
            genres     = []
            synopsis   = ""

            sname = self._tmdb_search_name(fp)
            tdata = self._search_tmdb(sname, api_key, language)
            tid, ttitle, mtype, year = self._parse_tmdb(tdata)

            if tid:
                tmdb_link  = f"https://www.themoviedb.org/{mtype}/{tid}"
                poster_url, score, genres, synopsis = self._poster(tid, api_key, language)
                imdb_link  = self._imdb(tid, api_key)
                self._log(f"TMDB : {ttitle} ({year})", "success")
                self._emit("tmdb_result", {
                    "tmdb_link": tmdb_link, "poster_url": poster_url,
                    "imdb_link": imdb_link or "", "title": ttitle, "year": year,
                    "score": score, "genres": genres, "synopsis": synopsis,
                })
                # Confirmation GUI — attendre que l'utilisateur confirme
                self._tmdb_confirmed = None
                self._tmdb_event.clear()
                self._emit("tmdb_confirm", {"tmdb_link": tmdb_link, "title": ttitle, "year": year})
                self._tmdb_event.wait(timeout=120)
                # Si l'utilisateur a changé l'ID
                if self._tmdb_confirmed and self._tmdb_confirmed != tmdb_link:
                    tmdb_link = self._tmdb_confirmed
                    new_tid   = tmdb_link.rstrip("/").split("/")[-1]
                    poster_url, score, genres, synopsis = self._poster(new_tid, api_key, language)
                    imdb_link = self._imdb(new_tid, api_key)
                    # Récupérer le vrai titre du nouveau film
                    new_data = self._get_movie_title(new_tid, api_key, language)
                    if new_data:
                        ttitle = new_data.get("title") or new_data.get("name") or ttitle
                        date   = new_data.get("release_date") or new_data.get("first_air_date") or ""
                        year   = date[:4] or year
                    self._emit("tmdb_result", {
                        "tmdb_link": tmdb_link, "poster_url": poster_url,
                        "imdb_link": imdb_link or "", "title": ttitle, "year": year,
                        "score": score, "genres": genres, "synopsis": synopsis,
                    })
                    self._log("TMDB mis a jour !", "success")
            else:
                self._log("Aucun résultat TMDB.", "warn")

            # ── 2. NFO APRÈS TMDB ─────────────────────────────────────────────
            self._log("Génération NFO mediainfo…")
            mi_path = None
            if sys.platform == "win32":
                # Windows : pymediainfo (MediaInfo.dll embarqué, pas de CLI nécessaire)
                from pymediainfo import MediaInfo as _MI
                mi = _MI.parse(fp)
                sections = []
                for track in mi.tracks:
                    lines = [track.track_type]
                    for k, v in track.to_data().items():
                        if k in ("xml_dom_fragment", "track_type") or v is None:
                            continue
                        lines.append(f"{k.replace('_', ' ').title():<40}: {v}")
                    sections.append("\n".join(lines))
                content_mi = "\n\n".join(sections)
            else:
                # macOS / Linux : CLI mediainfo (installé via brew)
                mi_name = os.path.basename(fp) + "_mediainfo.nfo"
                mi_path = os.path.join(file_dir, mi_name)
                subprocess.run(
                    f"mediainfo --Output=NFO \"{os.path.basename(fp)}\" > \"{mi_name}\"",
                    shell=True, cwd=file_dir
                )
                with open(mi_path, "r", encoding="utf-8") as f:
                    content_mi = f.read()

            self._log("Génération NFO custom…")
            orig_input = builtins.input
            answers = {
                "Input for other source than WEB": source or "WEB",
                "Input for custom notes":          note or "",
            }
            def fake_input(prompt=""):
                for k, v in answers.items():
                    if k in prompt:
                        return v
                return ""
            builtins.input = fake_input
            nfo_custom_path = NFO_v1_7.process_file(fp, tmdb_link_override=tmdb_link)
            builtins.input = orig_input

            with open(nfo_custom_path, "r", encoding="utf-8") as f:
                content_custom = f.read()

            final = content_custom + "\n\n" + content_mi
            self._emit("nfo_preview", {"content": final})

            with open(out_utf8, "w", encoding="utf-8") as f: f.write(final)
            with open(out_dos,  "w", encoding="cp437", errors="replace") as f: f.write(final)
            self._log(f"NFO UTF-8 → {os.path.basename(out_utf8)}", "success")
            self._log(f"NFO CP437 → {os.path.basename(out_dos)}",  "success")

            if mi_path and os.path.exists(mi_path):
                os.remove(mi_path)
            os.remove(nfo_custom_path)

            # ── 3. UPLOAD ─────────────────────────────────────────────────────
            dl_url = ""
            if nfo_only:
                self._log("Mode NFO Batch — upload ignoré.", "warn")
            elif skip_upload:
                self._log("Upload ignoré.", "warn")
            else:
                plat_name = "BuzzHeavier" if platform == "b" else "Gofile"
                self._log(f"Upload sur {plat_name}…")
                files_up = [fp, out_dos, out_utf8]
                if platform == "g":
                    filesize_g = os.path.getsize(fp)
                    start_g    = [__import__("time").time()]

                    def _gofile_progress(uploaded, total, _fs=filesize_g, _st=start_g, _fn=os.path.basename(fp)):
                        import time as _t
                        pct     = int(uploaded * 100 / total) if total else 0
                        elapsed = _t.time() - _st[0]
                        speed   = uploaded / elapsed / 1048576 if elapsed > 0 else 0
                        h, r    = divmod(int(elapsed), 3600)
                        m, s    = divmod(r, 60)
                        e_str   = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                        self._emit("upload_progress", {
                            "filename": _fn, "pct": pct,
                            "elapsed": f"{e_str} — {pct}% — {round(speed, 1)} MB/s"
                        })

                    urls   = gofile_upload(path=files_up, to_single_folder=True, verbose=False, progress_fn=_gofile_progress)
                    dl_url = urls[0] if urls else ""
                else:
                    dl_url = self._upload_bzhv(files_up, bzhv_id)
                self._log(f"URL : {dl_url}", "success")

            # ── 4. DISCORD ────────────────────────────────────────────────────
            if nfo_only:
                pass  # pas de Discord en mode batch NFO
            elif skip_upload:
                self._log("Discord ignoré (upload désactivé).", "warn")
            else:
                self._log("Envoi Discord…")
                self._discord(dl_url, os.path.basename(fp), source, note,
                              trackers, autre, tmdb_link, imdb_link, poster_url)
                self._log("Message Discord envoyé !", "success")

            # ── 5. DOSSIER FINAL + SEEDBOX ────────────────────────────────────
            fb_url      = os.getenv("SFTP_HOST", "")
            fb_user     = os.getenv("SFTP_USER", "")
            fb_pass     = os.getenv("SFTP_PASS", "")
            remote_base = os.getenv("SFTP_PATH", "/rtorrent/REBiRTH")

            if nfo_only:
                self._log("Mode NFO Batch — seedbox ignorée.", "warn")
            elif fb_url and fb_user and fb_pass:
                use_utf8    = (nfo_type == "utf8")
                nfo_to_send = out_utf8 if use_utf8 else out_dos
                nfo_label   = "UTF-8" if use_utf8 else "CP437"

                # Dossier FINAL a la racine du projet
                final_dir = os.path.join(str(BASE_DIR), "FINAL", base)
                os.makedirs(final_dir, exist_ok=True)
                self._log("Creation FINAL/" + base + "/...")

                import shutil
                final_mkv = os.path.join(final_dir, os.path.basename(fp))
                final_nfo = os.path.join(final_dir, os.path.basename(nfo_to_send))
                shutil.copy2(fp, final_mkv)
                shutil.copy2(nfo_to_send, final_nfo)
                self._log("FINAL/" + base + "/ pret avec NFO " + nfo_label, "success")

                remote_path = remote_base + "/" + base

                # Upload dossier complet via FTP
                self._log("Upload dossier FINAL sur la seedbox via FTP...")
                self._ftp_upload([final_mkv, final_nfo], remote_path)
                self._log("Seedbox OK : " + remote_path, "success")
                self._log("➜ Passe sur Torrent SB pour créer les torrents.", "warn")
            elif not nfo_only:
                self._log("Seedbox non configuree - upload ignore.", "warn")

            # ── 6. HISTORIQUE ─────────────────────────────────────────────────
            self.save_history_entry({
                "date":      datetime.now().strftime("%d/%m/%Y %H:%M"),
                "filename":  os.path.basename(fp),
                "title":     ttitle or "",
                "year":      year or "",
                "poster_url": poster_url,
                "tmdb_link": tmdb_link,
                "imdb_link": imdb_link or "",
                "source":    source,
                "trackers":  trackers,
                "url":       dl_url,
                "platform":  "NFO Batch" if nfo_only else ("BuzzHeavier" if platform == "b" else "Gofile" if not skip_upload else "—"),
            })

            self._emit("done", {"url": dl_url, "nfo_only": nfo_only})

        except Exception as e:
            import traceback
            traceback.print_exc()
            self._log(f"Erreur : {e}", "error")
            self._emit("error", {"msg": str(e)})
        finally:
            if caffeinate:
                caffeinate.terminate()
            elif sys.platform == "win32":
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)

    def _tmdb_search_name(self, fp):
        breaking = ['complete','integral','integrale','french','truefrench','multi',
                    'english','vostf','vostfr','vff','vfq','vf2','web','web-dl','bluray','remux']
        parts = []
        for p in Path(fp).name.split("."):
            if re.search(r'^S\d+|^\d{4}$|\d{3,4}p$', p) or any(k in p.lower() for k in breaking):
                break
            parts.append(p)
        return " ".join(parts).strip()

    def _search_tmdb(self, q, key, lang):
        r = requests.get("https://api.themoviedb.org/3/search/multi",
                         params={"api_key": key, "query": q, "language": lang})
        return r.json()

    def _parse_tmdb(self, data):
        if data.get("results"):
            r     = data["results"][0]
            mt    = r.get("media_type")
            tid   = r.get("id")
            title = r.get("title") or r.get("name")
            date  = r.get("release_date") or r.get("first_air_date") or ""
            return tid, title, mt, date[:4] or "N/A"
        return None, None, None, None

    def _poster(self, tid, key, lang):
        r = requests.get(f"https://api.themoviedb.org/3/movie/{tid}",
                         params={"api_key": key, "language": lang})
        if r.status_code == 200:
            data     = r.json()
            pp       = data.get("poster_path")
            poster   = f"https://image.tmdb.org/t/p/w500{pp}" if pp else "https://upload.wikimedia.org/wikipedia/commons/a/a3/Image-not-found.png"
            score    = round(data.get("vote_average", 0), 1)
            genres   = [g["name"] for g in data.get("genres", [])]
            synopsis = data.get("overview", "")
            return poster, score, genres, synopsis
        return "https://upload.wikimedia.org/wikipedia/commons/a/a3/Image-not-found.png", None, [], ""

    def _imdb(self, tid, key):
        r = requests.get(f"https://api.themoviedb.org/3/movie/{tid}/external_ids",
                         params={"api_key": key})
        if r.status_code == 200:
            iid = r.json().get("imdb_id")
            if iid: return f"https://www.imdb.com/title/{iid}/"
        return None

    def _ftp_upload(self, files, remote_path):
        import ftplib, time, socket
        host     = os.getenv("SFTP_HOST_FTP", "")
        port     = int(os.getenv("SFTP_PORT", "23421"))
        user     = os.getenv("SFTP_USER", "")
        password = os.getenv("SFTP_PASS", "")

        self._log("Connexion FTP vers " + host + "...")
        ftp = ftplib.FTP_TLS()
        ftp.connect(host, port)
        ftp.login(user, password)
        ftp.prot_p()
        # Augmenter le buffer TCP pour maximiser le débit
        try:
            ftp.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8 * 1024 * 1024)
        except Exception:
            pass

        # Naviguer vers le chemin distant
        parts = remote_path.strip("/").split("/")
        for part in parts:
            try:
                ftp.cwd(part)
            except ftplib.error_perm:
                ftp.mkd(part)
                ftp.cwd(part)
                self._log("Dossier FTP créé : " + part)

        for f in files:
            fname    = os.path.basename(f)
            filesize = os.path.getsize(f)
            start    = time.time()
            uploaded = [0]
            last_emit = [0.0]

            if filesize > 1073741824:
                size_str = str(round(filesize / 1073741824, 2)) + " GiB"
            else:
                size_str = str(round(filesize / 1048576, 1)) + " MiB"

            self._log("Envoi FTP : " + fname + " (" + size_str + ")...")

            def progress(data):
                uploaded[0] += len(data)
                now = time.time()
                if now - last_emit[0] < 1.0:
                    return
                last_emit[0] = now
                elapsed = now - start
                speed = uploaded[0] / elapsed / 1048576 if elapsed > 0 else 0
                pct = int(uploaded[0] * 100 / filesize) if filesize > 0 else 0
                h, r = divmod(int(elapsed), 3600)
                m, s = divmod(r, 60)
                e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                self._emit("upload_progress", {
                    "filename": fname,
                    "pct": pct,
                    "elapsed": e_str + " — " + str(pct) + "% — " + str(round(speed, 1)) + " MB/s"
                })

            with open(f, "rb") as fh:
                ftp.storbinary("STOR " + fname, fh, 1048576, progress)

            elapsed = time.time() - start
            h, r = divmod(int(elapsed), 3600)
            m, s = divmod(r, 60)
            e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
            self._log("  ✓ " + fname + " — " + e_str, "success")

        ftp.quit()

    def _filebrowser_upload(self, files, remote_path):
        import time
        fb_url  = os.getenv("SFTP_HOST", "")
        user    = os.getenv("SFTP_USER", "")
        password = os.getenv("SFTP_PASS", "")

        # 1. Login — obtenir le token JWT
        self._log("Connexion Filebrowser…")
        r = requests.post(fb_url + "/api/login", json={"username": user, "password": password})
        if r.status_code != 200:
            raise Exception("Filebrowser login failed: " + str(r.status_code))
        token = r.text.strip()
        headers = {"X-Auth": token}

        # 2. Créer le dossier distant si nécessaire
        folder_url = fb_url + "/api/resources" + remote_path + "/"
        r = requests.get(folder_url, headers=headers)
        if r.status_code == 404:
            requests.post(folder_url, headers=headers)
            self._log("Dossier distant créé : " + remote_path)

        # 3. Upload chaque fichier avec streaming chunked
        CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB par chunk

        for f in files:
            fname    = os.path.basename(f)
            filesize = os.path.getsize(f)
            start    = time.time()
            self._log("Envoi vers seedbox : " + fname + " (" + str(round(filesize/1073741824, 2)) + " GiB)…")

            upload_url = fb_url + "/api/resources" + remote_path + "/" + fname + "?override=true"

            def file_chunks(filepath, chunk_size):
                with open(filepath, "rb") as fh:
                    while True:
                        chunk = fh.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk

            upload_headers = dict(headers)
            upload_headers["Content-Length"] = str(filesize)

            r = requests.post(
                upload_url,
                headers=upload_headers,
                data=file_chunks(f, CHUNK_SIZE),
                stream=True
            )
            if r.status_code in (200, 201, 204):
                elapsed = time.time() - start
                h, rem = divmod(int(elapsed), 3600)
                m, s = divmod(rem, 60)
                e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                self._log("  ✓ " + fname + " — " + e_str, "success")
            else:
                raise Exception("Upload Filebrowser échoué pour " + fname + " : " + str(r.status_code))

    def _xmlrpc_call(self, rpc_url, method, params_xml, rt_user, rt_pass):
        """Appel XML-RPC générique, retourne le résultat parsé."""
        import xmlrpc.client as _xrpc
        payload = (
            '<?xml version="1.0"?><methodCall>'
            '<methodName>' + method + '</methodName>'
            '<params>' + params_xml + '</params>'
            '</methodCall>'
        )
        r = requests.post(rpc_url, data=payload,
                          auth=(rt_user, rt_pass), verify=False, timeout=30)
        if r.status_code != 200:
            raise Exception(method + " → HTTP " + str(r.status_code))
        return _xrpc.loads(r.text)[0][0]

    def _fetch_torrent_from_rutorrent(self, base, rt_url, rt_user, rt_pass):
        """Récupère le .torrent via XML-RPC :
           download_list → d.name sur chaque hash → session.path → FTP download.
        """
        import time as _time, ftplib, io
        rpc_url = rt_url.rstrip("/") + "/plugins/httprpc/action.php"

        _time.sleep(5)

        # 1. Lister tous les hashes
        hashes = self._xmlrpc_call(rpc_url, "download_list",
                                   '<param><value><string></string></value></param>',
                                   rt_user, rt_pass)
        self._log("  " + str(len(hashes)) + " torrents dans ruTorrent")

        # 2. Trouver le hash correspondant au nom (system.multicall pour tout en 1 requête)
        import xmlrpc.client as _xrpc
        calls_xml = "".join(
            '<value><struct>'
            '<member><name>methodName</name><value><string>d.name</string></value></member>'
            '<member><name>params</name><value><array><data>'
            '<value><string>' + h + '</string></value>'
            '</data></array></value></member>'
            '</struct></value>'
            for h in hashes
        )
        payload_mc = (
            '<?xml version="1.0"?><methodCall>'
            '<methodName>system.multicall</methodName><params>'
            '<param><value><array><data>' + calls_xml + '</data></array></value></param>'
            '</params></methodCall>'
        )
        r_mc = requests.post(rpc_url, data=payload_mc,
                             auth=(rt_user, rt_pass), verify=False, timeout=60)
        found_hash = None
        if r_mc.status_code == 200:
            try:
                results = _xrpc.loads(r_mc.text)[0][0]
                names_found = []
                for i, h in enumerate(hashes):
                    try:
                        name = results[i][0] if isinstance(results[i], (list, tuple)) else results[i]
                        names_found.append(name)
                        if name.lower() == base.lower():
                            found_hash = h
                            break
                        if not found_hash and base.lower() in name.lower():
                            found_hash = h  # match partiel, on continue au cas où
                    except Exception:
                        pass
                self._log("  Noms dans ruTorrent : " + str(names_found[:10]))
            except Exception as e_mc:
                self._log("  system.multicall parse : " + str(e_mc))

        # Fallback : requête individuelle d.name si system.multicall a échoué
        if not found_hash:
            for h in hashes:
                try:
                    name = self._xmlrpc_call(
                        rpc_url, "d.name",
                        '<param><value><string>' + h + '</string></value></param>',
                        rt_user, rt_pass
                    )
                    if name.lower() == base.lower() or base.lower() in name.lower():
                        found_hash = h
                        self._log("  Match (fallback) : " + name + " → " + h)
                        break
                except Exception:
                    pass

        if not found_hash:
            raise Exception("Torrent '" + base + "' introuvable dans ruTorrent après création.")

        self._log("  Hash : " + found_hash)

        # 3. Récupérer le chemin de session via XML-RPC
        session_path = None
        try:
            session_path = self._xmlrpc_call(rpc_url, "session.path", "", rt_user, rt_pass)
            self._log("  Session path : " + str(session_path))
        except Exception as e_sp:
            self._log("  session.path indisponible : " + str(e_sp))

        # 4a. Téléchargement via FTP depuis le dossier session
        # Le FTP est chroot à la home de l'utilisateur → naviguer dossier par dossier
        if session_path:
            try:
                ftp_host = os.getenv("SFTP_HOST_FTP", "")
                ftp_port = int(os.getenv("SFTP_PORT", "23421"))
                ftp_user = os.getenv("SFTP_USER", "")
                ftp_pass_env = os.getenv("SFTP_PASS", "")
                ftp2 = ftplib.FTP_TLS()
                ftp2.connect(ftp_host, ftp_port, timeout=15)
                ftp2.login(ftp_user, ftp_pass_env)
                ftp2.prot_p()

                # Naviguer dossier par dossier (FTP chroot — pas de chemin absolu)
                # On essaie d'abord le chemin complet, puis on saute les préfixes
                # qui correspondent à la home FTP si inaccessibles
                parts = session_path.strip("/").split("/")
                navigated = []
                for part in parts:
                    try:
                        ftp2.cwd(part)
                        navigated.append(part)
                    except Exception:
                        # Ce dossier n'est pas accessible depuis ici (ex: /sdc/wydg déjà en root)
                        # Réinitialiser et réessayer depuis la racine FTP en sautant ce préfixe
                        pass

                self._log("  FTP navigué : /" + "/".join(navigated))
                buf = io.BytesIO()
                ftp2.retrbinary("RETR " + found_hash + ".torrent", buf.write)
                ftp2.quit()
                data = buf.getvalue()
                if data and data.lstrip()[:1] == b"d":
                    self._log("  FTP session OK — " + str(len(data)) + " octets")
                    return data
                else:
                    self._log("  FTP : données reçues mais pas un .torrent (" +
                              str(len(data)) + " o) — " + data[:40].decode("utf-8", errors="replace"))
            except Exception as e_ftp:
                self._log("  FTP session : " + str(e_ftp))

        # 4b. Endpoint ruTorrent export (certaines versions supportent /export/)
        for ep in [
            rt_url.rstrip("/") + "/php/addtorrent.php?action=get-data&hash=" + found_hash,
            rt_url.rstrip("/") + "/export/" + found_hash + ".torrent",
            rt_url.rstrip("/") + "/php/torrent.php?action=get_torrent&hash=" + found_hash,
        ]:
            try:
                rd = requests.get(ep, auth=(rt_user, rt_pass), verify=False, timeout=30)
                preview = rd.content[:60].decode("utf-8", errors="replace")
                self._log("  GET " + ep.split("?")[0].split("/")[-1] +
                          " → " + str(rd.status_code) + " (" + str(len(rd.content)) +
                          " o) : " + preview)
                if rd.status_code == 200 and rd.content and rd.content.lstrip()[:1] == b"d":
                    return rd.content
            except Exception:
                continue

        raise Exception("Impossible de télécharger le .torrent (hash=" + found_hash + ").")

    def _create_torrent_rutorrent(self, base, remote_path, announce_urls, private=True):
        """Crée les torrents via le plugin create de ruTorrent (côté seedbox, hash SB).
        Piece size fixé à 4 MiB. Le .torrent est ensuite récupéré via XML-RPC et
        sauvegardé localement dans BASE_DIR/TORRENTS/.
        """
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        rt_url  = os.getenv("RUTORRENT_URL", "")
        rt_user = os.getenv("RUTORRENT_USER", "")
        rt_pass = os.getenv("RUTORRENT_PASS", "")

        if not rt_url:
            raise Exception("ruTorrent URL non configurée dans le .env")

        create_url = rt_url.rstrip("/") + "/plugins/create/action.php"
        self._log("  URL create : " + create_url)

        # Dossier local TORRENTS/ à côté du bot
        torrents_local = BASE_DIR / "TORRENTS"
        torrents_local.mkdir(exist_ok=True)

        for tk_name, announce in announce_urls.items():
            if not announce:
                continue
            self._log("Création torrent SB pour " + tk_name + "…")
            data = {
                "name":         base,
                "dir":          remote_path.rstrip("/") + "/",
                "piece_size":   "4194304",   # 4 MiB
                "startSeeding": "on",
                "tracker[0]":   announce,
            }
            if private:
                data["private"] = "on"

            self._log("  POST → " + create_url)
            self._log("  dir  = " + data["dir"])
            r = requests.post(
                create_url,
                data=data,
                auth=(rt_user, rt_pass),
                verify=False,
                timeout=120,
            )
            self._log("  HTTP " + str(r.status_code) + " — " + str(len(r.content)) + " octets reçus")
            if r.content:
                preview = r.content[:120].decode("utf-8", errors="replace").replace("\n", " ")
                self._log("  Réponse : " + preview)

            if r.status_code != 200:
                raise Exception(
                    "Plugin create ruTorrent — erreur HTTP " + str(r.status_code) +
                    " pour " + tk_name +
                    ". Vérifier que le plugin 'create' est installé sur ruTorrent."
                )

            self._log("  ✓ Torrent créé — seeding démarré (" + tk_name + ")", "success")

            torrent_name = base + "__" + tk_name + ".torrent"

            # 1. Le plugin renvoie parfois directement le binaire dans la réponse
            torrent_bytes = None
            if r.content and r.content.lstrip()[:1] == b"d":
                torrent_bytes = r.content
                self._log("  📦 .torrent reçu dans la réponse HTTP", "success")

            # 2. Sinon : récupérer via XML-RPC (hash lookup + download)
            if not torrent_bytes:
                self._log("  Récupération du .torrent via XML-RPC…")
                try:
                    torrent_bytes = self._fetch_torrent_from_rutorrent(
                        base, rt_url, rt_user, rt_pass
                    )
                    self._log("  📦 .torrent récupéré via ruTorrent", "success")
                except Exception as e_rpc:
                    self._log("  ⚠ Récupération XML-RPC échouée : " + str(e_rpc), "warn")

            # 3. Sauvegarder localement
            if torrent_bytes:
                try:
                    (torrents_local / torrent_name).write_bytes(torrent_bytes)
                    self._log("  💾 .torrent sauvegardé → TORRENTS/" + torrent_name, "success")
                except Exception as e_save:
                    self._log("  ⚠ Sauvegarde locale échouée : " + str(e_save), "warn")
            else:
                self._log("  ⚠ .torrent non disponible — seeding actif sur la SB", "warn")

    def _get_movie_title(self, tid, key, lang):
        r = requests.get(f"https://api.themoviedb.org/3/movie/{tid}",
                         params={"api_key": key, "language": lang})
        if r.status_code == 200:
            return r.json()
        # Essayer aussi en tant que série TV
        r = requests.get(f"https://api.themoviedb.org/3/tv/{tid}",
                         params={"api_key": key, "language": lang})
        if r.status_code == 200:
            return r.json()
        return None

    def _upload_bzhv(self, files, account_id):
        import importlib.util, time
        spec = importlib.util.spec_from_file_location(
            "auto_up_discord", BASE_DIR / "auto-up-discord.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        info = mod.create_unique_directory(account_id)
        self._log(f"Dossier BuzzHeavier : {info['name']}")

        for f in files:
            filename = os.path.basename(f)
            filesize = os.path.getsize(f)
            start    = time.time()

            def _bzhv_progress(uploaded, total, fn=filename, fs=filesize, st=start):
                pct     = int(uploaded * 100 / total) if total else 0
                elapsed = time.time() - st
                speed   = uploaded / elapsed / 1048576 if elapsed > 0 else 0
                h, r    = divmod(int(elapsed), 3600)
                m, s    = divmod(r, 60)
                e_str   = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                self._emit("upload_progress", {
                    "filename": fn, "pct": pct,
                    "elapsed": f"{e_str} — {pct}% — {round(speed, 1)} MB/s"
                })

            mod.upload_big_file(f, info["id"], account_id, progress_fn=_bzhv_progress)

            elapsed = time.time() - start
            h, r = divmod(int(elapsed), 3600)
            m, s = divmod(r, 60)
            e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
            self._log("  ✓ " + filename + " — " + e_str, "success")

        return "https://buzzheavier.com/" + info["id"]

    def _discord(self, url, filename, source, note, trackers, autre,
                 tmdb_link, imdb_link, poster_url):
        wh = os.getenv("WEBHOOK_URL", "")
        fields = []
        if tmdb_link: fields.append({"name": "TMDB",     "value": tmdb_link, "inline": False})
        if imdb_link: fields.append({"name": "IMDb",     "value": imdb_link, "inline": False})
        if source:    fields.append({"name": "Source",   "value": source,    "inline": False})
        if note:      fields.append({"name": "Note",     "value": note,      "inline": False})
        if trackers:  fields.append({"name": "Trackers", "value": trackers,  "inline": False})
        if autre:     fields.append({"name": "Autre",    "value": autre,     "inline": False})
        requests.post(wh, json={
            "content": "### Nouveau fichier à uploader ! <@393798272495386636>",
            "embeds": [{
                "title":       os.path.splitext(filename)[0],
                "description": url,
                "fields":      fields,
                "color":       0xffa500,
                "image":       {"url": poster_url},
            }]
        })


if __name__ == "__main__":
    api = API()

    html_path = BASE_DIR / "gui_index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    window = webview.create_window(
        "REBiRTH — Upload Bot",
        html=html,
        js_api=api,
        width=1100,
        height=780,
        min_size=(900, 640),
        background_color="#0d0d0d",
    )
    api.window = window
    webview.start(debug=False)
