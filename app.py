#!/usr/bin/env python3
# coding: utf-8
"""
REBiRTH Upload Bot — PyWebView GUI
Lance avec : python3 app.py
"""

import os, sys, json, re, subprocess, threading, builtins
from pathlib import Path
from threading import Event

import webview
import requests
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).parent
ENV_FILE  = BASE_DIR / "V1.env"
sys.path.insert(0, str(BASE_DIR))

from gofile import gofile_upload
from NFO_CUSTOM import NFO_v1_7

load_dotenv(ENV_FILE)


class API:
    def __init__(self):
        self.window          = None
        self._tmdb_event     = Event()
        self._tmdb_confirmed = None

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

    def confirm_tmdb(self, data):
        self._tmdb_confirmed = data.get("tmdb_link", "")
        self._tmdb_event.set()
        return {"ok": True}

    def pick_file(self):
        films_dir = BASE_DIR / "FILMS"
        start_dir = str(films_dir) if films_dir.exists() else str(Path.home())
        result = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
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
            fp       = p["file_path"]
            source   = p.get("source", "")
            note     = p.get("note", "")
            trackers = p.get("trackers", "")
            autre    = p.get("autre", "")
            platform = p.get("platform", "b")
            nfo_type    = p.get("nfo_type", "utf8")
            skip_upload = p.get("skip_upload", False)
            nfo_type    = p.get("nfo_type", "utf8")
            skip_upload = p.get("skip_upload", False)
            api_key  = os.getenv("API_KEY", "")
            language = os.getenv("LANGUAGE", "fr-FR")
            bzhv_id  = os.getenv("BUZZHEAVIER_ACC_ID", "")
            os.environ["GOFILE_TOKEN"] = os.getenv("GOFILE_TOKEN", "")

            file_dir = os.path.dirname(fp)
            base     = os.path.basename(os.path.splitext(fp)[0])
            out_utf8 = os.path.join(file_dir, f"(LaCale)-{base}.nfo")
            out_dos  = os.path.splitext(fp)[0] + ".nfo"

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
            mi_name = os.path.basename(fp) + "_mediainfo.nfo"
            subprocess.run(
                f"mediainfo --Output=NFO \"{os.path.basename(fp)}\" > \"{mi_name}\"",
                shell=True, cwd=file_dir
            )
            mi_path = os.path.join(file_dir, mi_name)
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

            os.remove(mi_path)
            os.remove(nfo_custom_path)

            # ── 3. UPLOAD ─────────────────────────────────────────────────────
            dl_url = ""
            if skip_upload:
                self._log("Upload ignoré.", "warn")
            else:
                self._log(f"Upload sur {'BuzzHeavier' if platform == 'b' else 'Gofile'}…")
                files_up = [fp, out_dos, out_utf8]
                if platform == "g":
                    urls   = gofile_upload(path=files_up, to_single_folder=True, verbose=False)
                    dl_url = urls[0] if urls else ""
                else:
                    dl_url = self._upload_bzhv(files_up, bzhv_id)
                self._log(f"URL : {dl_url}", "success")

            # ── 4. DISCORD ────────────────────────────────────────────────────
            self._log("Envoi Discord…")
            self._discord(dl_url, os.path.basename(fp), source, note,
                          trackers, autre, tmdb_link, imdb_link, poster_url)
            self._log("Message Discord envoyé !", "success")

            # ── 5. DOSSIER FINAL + SEEDBOX ────────────────────────────────────
            fb_url      = os.getenv("SFTP_HOST", "")
            fb_user     = os.getenv("SFTP_USER", "")
            fb_pass     = os.getenv("SFTP_PASS", "")
            remote_base = os.getenv("SFTP_PATH", "/rtorrent/REBiRTH")

            if fb_url and fb_user and fb_pass:
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

                # Creer les .torrent et envoyer a ruTorrent
                announces = {
                    "ABN":    os.getenv("TRACKER_ABN", ""),
                    "TOS":    os.getenv("TRACKER_TOS", ""),
                    "C411":   os.getenv("TRACKER_C411", ""),
                    "TORR9":  os.getenv("TRACKER_TORR9", ""),
                    "LACALE": os.getenv("TRACKER_LACALE", ""),
                }
                active = {k: v for k, v in announces.items() if v}
                if active:
                    self._log("Creation des .torrent...")
                    self._create_and_send_torrent(final_dir, base, active, remote_path)
            else:
                self._log("Seedbox non configuree - upload ignore.", "warn")

            self._emit("done", {"url": dl_url})

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
        import ftplib, time
        host     = os.getenv("SFTP_HOST_FTP", "")
        port     = int(os.getenv("SFTP_PORT", "23421"))
        user     = os.getenv("SFTP_USER", "")
        password = os.getenv("SFTP_PASS", "")

        self._log("Connexion FTP vers " + host + "...")
        ftp = ftplib.FTP_TLS()
        ftp.connect(host, port)
        ftp.login(user, password)
        ftp.prot_p()

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

            if filesize > 1073741824:
                size_str = str(round(filesize / 1073741824, 2)) + " GiB"
            else:
                size_str = str(round(filesize / 1048576, 1)) + " MiB"

            self._log("Envoi FTP : " + fname + " (" + size_str + ")...")

            def progress(data):
                uploaded[0] += len(data)
                elapsed = time.time() - start
                speed = uploaded[0] / elapsed / 1048576 if elapsed > 0 else 0
                pct = int(uploaded[0] * 100 / filesize) if filesize > 0 else 0
                h, r = divmod(int(elapsed), 3600)
                m, s = divmod(r, 60)
                e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                self._emit("upload_progress", {
                    "filename": fname,
                    "elapsed": e_str + " — " + str(pct) + "% — " + str(round(speed, 1)) + " MB/s"
                })

            with open(f, "rb") as fh:
                ftp.storbinary("STOR " + fname, fh, 8192, progress)

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

    def _create_and_send_torrent(self, final_dir, base, announce_urls, remote_path):
        import torf, ssl, xmlrpc.client
        import time

        torrent_dir = os.path.join(str(BASE_DIR), "TORRENTS")
        os.makedirs(torrent_dir, exist_ok=True)

        rt_url  = os.getenv("RUTORRENT_URL", "")
        rt_user = os.getenv("RUTORRENT_USER", "")
        rt_pass = os.getenv("RUTORRENT_PASS", "")

        for tk_name, announce in announce_urls.items():
            if not announce:
                continue
            self._log("Creation torrent pour " + tk_name + "...")
            t = torf.Torrent()
            t.name       = base
            t.private    = True
            t.piece_size = 4 * 1024 * 1024
            t.trackers   = [[announce]]
            t.path       = final_dir

            torrent_path = os.path.join(torrent_dir, base + "_" + tk_name + ".torrent")
            t.generate()
            t.write(torrent_path)
            self._log("  .torrent cree : " + os.path.basename(torrent_path), "success")

            # Envoyer a ruTorrent
            if rt_url and rt_user and rt_pass:
                with open(torrent_path, "rb") as f:
                    torrent_data = f.read()
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                transport = xmlrpc.client.SafeTransport(context=ctx)
                full_url = rt_url.replace("://", "://" + rt_user + ":" + rt_pass + "@") + "/plugins/httprpc/action.php"
                server = xmlrpc.client.ServerProxy(full_url, transport=transport)
                server.load.raw_start("", xmlrpc.client.Binary(torrent_data), "d.directory.set=" + remote_path)
                self._log("  Torrent envoye a ruTorrent !", "success")

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
            start    = time.time()
            stop_flag = [False]

            def progress_timer(fn, st, sf):
                while not sf[0]:
                    elapsed = time.time() - st
                    h, r = divmod(int(elapsed), 3600)
                    m, s = divmod(r, 60)
                    e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                    self._emit("upload_progress", {"filename": fn, "elapsed": e_str})
                    time.sleep(2)

            t = threading.Thread(target=progress_timer, args=(filename, start, stop_flag), daemon=True)
            t.start()

            mod.upload_big_file(f, info["id"], account_id)

            stop_flag[0] = True
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
