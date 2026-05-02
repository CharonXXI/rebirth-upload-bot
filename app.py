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
        self._bdinfo_input_queue = None   # queue.Queue() créé à chaque scan

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
            "TRACKER_HDT":        os.getenv("TRACKER_HDT", ""),
            "SFTP_PATH_HDT":      os.getenv("SFTP_PATH_HDT", "/home/rtorrent/rtorrent/download/FULL BD"),
            "WEBHOOK_HDT_URL":    os.getenv("WEBHOOK_HDT_URL", ""),
            "BDINFO_CLI_PATH":    os.getenv("BDINFO_CLI_PATH", ""),
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
        """Retourne la liste des entrées présentes dans SFTP_PATH.
        Port 22 → SFTP via paramiko. Autre port → FTP TLS legacy."""
        host     = os.getenv("SFTP_HOST_FTP", "")
        port     = int(os.getenv("SFTP_PORT", "22"))
        user     = os.getenv("SFTP_USER", "")
        password = os.getenv("SFTP_PASS", "")
        path     = os.getenv("SFTP_PATH", "/home/rtorrent/rtorrent/download/REBiRTH")

        if not host:
            return {"error": "SFTP_HOST_FTP non configuré"}

        # ── SFTP via SSH (port 22) ─────────────────────────────────────────────
        if port == 22:
            try:
                import paramiko
            except ImportError:
                import subprocess as _sp
                _sp.run([sys.executable, "-m", "pip", "install", "paramiko",
                         "--break-system-packages", "--quiet"], capture_output=True)
                import paramiko  # noqa: F811
            try:
                transport = paramiko.Transport((host, port))
                transport.connect(username=user, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
                try:
                    entries = sftp.listdir_attr(path)
                    names = sorted([e.filename for e in entries
                                    if e.filename not in (".", "..")],
                                   key=lambda x: x.lower())
                    return {"files": names, "path": path}
                except FileNotFoundError:
                    return {"error": f"Dossier introuvable : {path}"}
                finally:
                    sftp.close()
                    transport.close()
            except Exception as e:
                return {"error": str(e)}

        # ── FTP TLS legacy (ancien port != 22) ────────────────────────────────
        import ftplib
        try:
            ftp = ftplib.FTP_TLS()
            ftp.connect(host, port, timeout=10)
            ftp.login(user, password)
            ftp.prot_p()
            for part in path.strip("/").split("/"):
                ftp.cwd(part)
            entries = []
            ftp.retrlines("LIST", entries.append)
            ftp.quit()
            folders = []
            for entry in entries:
                parts_e = entry.split()
                if parts_e and parts_e[-1] not in (".", ".."):
                    folders.append(parts_e[-1])
            folders.sort(key=lambda x: x.lower())
            return {"files": folders, "path": path}
        except Exception as e:
            return {"error": str(e)}

    def list_seedbox_files_hdt(self):
        """Retourne la liste des entrées présentes dans SFTP_PATH_HDT (FULL BD).
        Port 22 → SFTP via paramiko. Autre port → FTP TLS legacy."""
        host     = os.getenv("SFTP_HOST_FTP", "")
        port     = int(os.getenv("SFTP_PORT", "22"))
        user     = os.getenv("SFTP_USER", "")
        password = os.getenv("SFTP_PASS", "")
        path     = os.getenv("SFTP_PATH_HDT", "/home/rtorrent/rtorrent/download/FULL BD")

        if not host:
            return {"error": "SFTP_HOST_FTP non configuré"}

        if port == 22:
            try:
                import paramiko
            except ImportError:
                import subprocess as _sp
                _sp.run([sys.executable, "-m", "pip", "install", "paramiko",
                         "--break-system-packages", "--quiet"], capture_output=True)
                import paramiko  # noqa: F811
            try:
                transport = paramiko.Transport((host, port))
                transport.connect(username=user, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
                try:
                    entries = sftp.listdir_attr(path)
                    names = sorted([e.filename for e in entries
                                    if e.filename not in (".", "..")],
                                   key=lambda x: x.lower())
                    return {"files": names, "path": path}
                except FileNotFoundError:
                    return {"error": f"Dossier introuvable : {path}"}
                finally:
                    sftp.close()
                    transport.close()
            except Exception as e:
                return {"error": str(e)}

        import ftplib
        try:
            ftp = ftplib.FTP_TLS()
            ftp.connect(host, port, timeout=10)
            ftp.login(user, password)
            ftp.prot_p()
            for part in path.strip("/").split("/"):
                ftp.cwd(part)
            entries = []
            ftp.retrlines("LIST", entries.append)
            ftp.quit()
            folders = []
            for entry in entries:
                parts_e = entry.split()
                if parts_e and parts_e[-1] not in (".", ".."):
                    folders.append(parts_e[-1])
            folders.sort(key=lambda x: x.lower())
            return {"files": folders, "path": path}
        except Exception as e:
            return {"error": str(e)}

    def get_seedbox_space(self):
        """Retourne l'espace utilisé/disponible/total sur la seedbox via SSH df."""
        try:
            import paramiko
        except ImportError:
            return {"error": "paramiko absent"}
        host = os.getenv("SFTP_HOST_FTP", "")
        port = int(os.getenv("SFTP_PORT", "22"))
        user = os.getenv("SFTP_USER", "")
        pwd  = os.getenv("SFTP_PASS", "")
        path = os.getenv("SFTP_PATH", "/home/rtorrent/rtorrent/download/REBiRTH")
        if not host or not user:
            return {"error": "SSH non configuré"}
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port=port, username=user, password=pwd,
                           timeout=10, allow_agent=False, look_for_keys=False)
            # -P (POSIX) : une ligne par fs, pas de wrap même si nom long
            # On prend le filesystem avec le plus grand espace total
            # (ignore tmpfs/devtmpfs/overlay/udev qui sont des pseudo-fs)
            cmd = ("df -B1 -P | awk 'NR>1 && "
                   "$1 !~ /tmpfs|devtmpfs|overlay|udev/ "
                   "{print $2, $3, $4, $1}' | sort -k1 -rn | head -1")
            _, out, _ = client.exec_command(cmd, timeout=10)
            line = out.read().decode("utf-8", errors="replace").strip()
            client.close()
            if not line:
                return {"error": "df vide"}
            parts = line.split()
            # total used avail filesystem
            total_b = int(parts[0])
            avail_b = int(parts[2])
            # Calculer used = total - avail (comme ruTorrent)
            # df "Used" exclut les blocs réservés root, total-avail les inclut
            used_b  = total_b - avail_b
            def fmt(b):
                for unit in ("o", "Kio", "Mio", "Gio", "Tio"):
                    if b < 1024 or unit == "Tio":
                        return f"{b:.2f} {unit}" if unit != "o" else f"{b} {unit}"
                    b /= 1024
            return {"used": fmt(used_b), "avail": fmt(avail_b), "total": fmt(total_b)}
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

            # Toujours dériver base depuis remote_path s'il est fourni,
            # sinon depuis filename — jamais .stem qui coupe le dernier segment
            if remote_path:
                base = Path(remote_path).name
            else:
                base = Path(filename).name
                remote_base = os.getenv("SFTP_PATH", "/home/rtorrent/rtorrent/download/REBiRTH")
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

    # ──────────────────────────────────────────────────────────────────────────
    # BD Info
    # ──────────────────────────────────────────────────────────────────────────

    def browse_folder_bdinfo(self):
        """Ouvre le Finder pour sélectionner un dossier BDMV (ou son parent)."""
        films_dir = BASE_DIR / "FILMS"
        start_dir = str(films_dir) if films_dir.exists() else str(Path.home())
        result = self.window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=start_dir
        )
        if result and result[0]:
            return {"path": result[0]}
        return {"path": ""}

    def load_existing_bdinfo(self):
        """Charge et traite le rapport BDInfo le plus récent dans le dossier BDINFO/."""
        import re as _re

        # Tuer BDInfo/Wine s'il tourne encore
        _wp = getattr(self, '_wine_proc', None)
        if _wp is not None:
            try:
                if _wp.poll() is None:
                    _wp.terminate()
                    self._emit("bdinfo_status", {"msg": "🛑 BDInfo fermé"})
            except Exception:
                pass
            self._wine_proc = None

        _nfo_dir = BASE_DIR / "BDINFO"
        _nfo_dir.mkdir(exist_ok=True)

        _candidates = (
            list(_nfo_dir.glob("*.rtf"))
            + list(_nfo_dir.glob("*.txt"))
            + list(_nfo_dir.glob("*.nfo"))
        )
        if not _candidates:
            self._emit("bdinfo_status", {"msg": "✖ Aucun rapport dans BDINFO/", "level": "error"})
            return

        _src = sorted(_candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        self._emit("bdinfo_status", {"msg": "📂 Lecture : %s" % _src.name})

        with open(_src, "r", encoding="utf-8", errors="replace") as _f:
            nfo_raw = _f.read()

        # Conversion RTF si nécessaire
        if _src.suffix.lower() == ".rtf":
            nfo_raw = _re.sub(r'\\par\b', '\n', nfo_raw)
            nfo_raw = _re.sub(r'\\line\b', '\n', nfo_raw)
            nfo_raw = _re.sub(r'\\[a-zA-Z]+\-?[0-9]*\s?', '', nfo_raw)
            nfo_raw = nfo_raw.replace('{', '').replace('}', '').replace('\\', '')
            nfo_raw = _re.sub(r'\n{3,}', '\n\n', nfo_raw).strip()

        # Extraire depuis "DISC INFO:" (ou "Disc Title:" si pas de header) jusqu'à SUBTITLES inclus
        _STOP = r'(?=\nFILES:|\nCHAPTERS:|\nSTREAM DIAGNOSTICS:|\n\[/code\]|\nQUICK SUMMARY:|\n\*{10,}|\Z)'
        _m = _re.search(r'(DISC INFO:.*?)' + _STOP, nfo_raw, _re.DOTALL)
        if not _m:
            # Pas de "DISC INFO:" → partir du premier "Disc Title:" ou "Disc Label:"
            _start = _re.search(r'^Disc (?:Title|Label):', nfo_raw, _re.MULTILINE)
            if _start:
                _m = _re.search(r'(.+?)' + _STOP, nfo_raw[_start.start():], _re.DOTALL)
        nfo_content = _m.group(1).strip() + "\n" if _m else nfo_raw.strip() + "\n"

        # Disc label (Label prioritaire sur Title)
        _disc_label = None
        for _pri in ('Label', 'Title'):
            for _line in nfo_content.splitlines():
                _mm = _re.match(r'^Disc\s+' + _pri + r'\s*:\s*(.+)', _line, _re.IGNORECASE)
                if _mm:
                    _disc_label = _mm.group(1).strip().replace(" ", "_")
                    break
            if _disc_label:
                break
        if not _disc_label:
            _disc_label = _src.stem

        # Sauvegarder .txt + .nfo
        _out_txt = _nfo_dir / (_disc_label + ".txt")
        _out_nfo = _nfo_dir / (_disc_label + ".nfo")
        for _out in (_out_txt, _out_nfo):
            with open(_out, "w", encoding="utf-8") as _of:
                _of.write(nfo_content)
        if _src not in (_out_txt, _out_nfo):
            try: _src.unlink()
            except Exception: pass

        self._bdi_last_nfo = str(_out_nfo)   # expose pour upload_bdinfo_nfo

        # Chercher le dossier COMPLETE.BLURAY dans FILMS/ seulement si pas déjà set par un scan
        if not getattr(self, "_bdi_last_folder", ""):
            _films_dir = BASE_DIR / "FILMS"
            _matched_folder = ""
            if _films_dir.exists():
                for _d in _films_dir.iterdir():
                    if _d.is_dir() and (_disc_label.upper() in _d.name.upper() or _d.name.upper() in _disc_label.upper()):
                        _matched_folder = str(_d)
                        break
            if _matched_folder:
                self._bdi_last_folder = _matched_folder
                self._emit("bdinfo_status", {"msg": "📁 Dossier FILMS détecté : %s" % Path(_matched_folder).name})
            else:
                self._emit("bdinfo_status", {"msg": "⚠ Dossier COMPLETE.BLURAY introuvable dans FILMS/ — seul le NFO sera uploadé", "level": "warning"})

        self._emit("bdinfo_status", {"msg": "💾 %s (.txt + .nfo)" % _disc_label, "level": "success"})
        self._emit("bdinfo_done", {
            "ok":       True,
            "content":  nfo_content,
            "nfo_name": _out_nfo.name,
            "lines":    len(nfo_content.splitlines()),
        })

    def browse_iso_bdinfo(self):
        """Ouvre un sélecteur de fichier pour choisir un .iso Blu-ray."""
        films_dir = BASE_DIR / "FILMS"
        start_dir = str(films_dir) if films_dir.exists() else str(Path.home())
        try:
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                directory=start_dir,
                file_types=("ISO (*.iso)",)
            )
        except Exception:
            # Fallback sans filtre si pywebview ne supporte pas file_types
            result = self.window.create_file_dialog(
                webview.OPEN_DIALOG,
                directory=start_dir
            )
        if result and result[0]:
            return {"path": result[0]}
        return {"path": ""}

    # ------------------------------------------------------------------
    # Helpers montage / démontage ISO (cross-platform)
    # ------------------------------------------------------------------

    @staticmethod
    def _mount_iso(iso_path):
        """Monte un fichier ISO et retourne (mount_point, mount_info).
        mount_info est un dict utilisé par _unmount_iso pour nettoyer.
        Supporte macOS (hdiutil), Linux (udisksctl) et Windows (PowerShell).
        """
        import subprocess as _sp
        import platform as _platform
        import re as _re2

        sys_name = _platform.system()

        if sys_name == "Darwin":
            # hdiutil attach — pas besoin de sudo, mount point dans la sortie
            out = _sp.check_output(
                ["hdiutil", "attach", "-nobrowse", "-noverify", iso_path],
                stderr=_sp.DEVNULL
            ).decode("utf-8", errors="replace")
            # Dernière ligne : /dev/diskXsN  Apple_HFS  /Volumes/NAME
            for line in reversed(out.splitlines()):
                parts = line.split("\t")
                if len(parts) >= 3:
                    mount_pt = parts[-1].strip()
                    dev      = parts[0].strip()
                    if mount_pt.startswith("/Volumes/"):
                        return mount_pt, {"sys": "darwin", "dev": dev, "mount": mount_pt}
            raise RuntimeError("hdiutil : mount point introuvable dans :\n" + out)

        elif sys_name == "Linux":
            # udisksctl loop-setup (pas besoin de sudo)
            out_loop = _sp.check_output(
                ["udisksctl", "loop-setup", "-f", iso_path],
                stderr=_sp.PIPE
            ).decode("utf-8", errors="replace")
            # "Mapped file ... as /dev/loop0."
            m = _re2.search(r"as (/dev/loop\S+)\.", out_loop)
            if not m:
                raise RuntimeError("udisksctl loop-setup : " + out_loop.strip())
            loop_dev = m.group(1).rstrip(".")

            out_mnt = _sp.check_output(
                ["udisksctl", "mount", "-b", loop_dev],
                stderr=_sp.PIPE
            ).decode("utf-8", errors="replace")
            # "Mounted /dev/loop0 at /run/media/user/NAME."
            m2 = _re2.search(r"at (/\S+)\.", out_mnt)
            if not m2:
                raise RuntimeError("udisksctl mount : " + out_mnt.strip())
            mount_pt = m2.group(1).rstrip(".")
            return mount_pt, {"sys": "linux", "loop": loop_dev, "mount": mount_pt}

        elif sys_name == "Windows":
            iso_path_w = iso_path.replace("/", "\\")
            # Monter
            _sp.check_call(
                ["powershell", "-Command",
                 'Mount-DiskImage -ImagePath "%s"' % iso_path_w],
                stdout=_sp.DEVNULL, stderr=_sp.DEVNULL
            )
            # Récupérer la lettre de lecteur
            out = _sp.check_output(
                ["powershell", "-Command",
                 '(Get-DiskImage -ImagePath "%s" | Get-Volume).DriveLetter' % iso_path_w],
                stderr=_sp.DEVNULL
            ).decode("utf-8", errors="replace").strip()
            if not out:
                raise RuntimeError("PowerShell : lettre de lecteur introuvable")
            drive = out[0].upper() + ":\\"
            return drive, {"sys": "windows", "iso": iso_path_w, "mount": drive}

        else:
            raise RuntimeError("OS non supporté pour le montage ISO : " + sys_name)

    @staticmethod
    def _unmount_iso(mount_info):
        """Démonte un ISO précédemment monté par _mount_iso."""
        import subprocess as _sp

        sys_name = mount_info.get("sys", "")

        if sys_name == "darwin":
            _sp.call(["hdiutil", "detach", "-force", mount_info["dev"]],
                     stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)

        elif sys_name == "linux":
            _sp.call(["udisksctl", "unmount", "-b", mount_info["loop"]],
                     stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
            _sp.call(["udisksctl", "loop-delete", "-b", mount_info["loop"]],
                     stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)

        elif sys_name == "windows":
            _sp.call(
                ["powershell", "-Command",
                 'Dismount-DiskImage -ImagePath "%s"' % mount_info["iso"]],
                stdout=_sp.DEVNULL, stderr=_sp.DEVNULL
            )

    def run_bdinfo_scan(self, folder_path: str):
        """Lance BDInfoCLI sur folder_path (thread séparé).
        Cherche le dossier BDMV à l'intérieur si nécessaire.
        Sauvegarde le rapport dans BDINFO/<nom>.nfo et l'émet via log.
        """
        import queue as _q
        self._bdinfo_input_queue = _q.Queue()
        threading.Thread(
            target=self._bdinfo_worker,
            args=(folder_path,),
            daemon=True
        ).start()
        return {"ok": True}

    def send_bdinfo_input(self, text: str):
        """Envoie une réponse à BDInfoCLI en cours (appelé depuis le frontend)."""
        if self._bdinfo_input_queue is not None:
            self._bdinfo_input_queue.put(str(text))
        return {"ok": True}

    def _bdinfo_worker(self, folder_path: str):
        """Sélectionne le MPLS principal via makemkvcon (ou --list),
        puis scanne ce MPLS avec BDInfoCLI pour produire un vrai rapport BDInfo.
        """
        import subprocess, re as _re

        def _status(msg, level="info"):
            self._emit("bdinfo_status", {"msg": msg, "level": level})
        def _output(line):
            self._emit("bdinfo_output", {"line": line})

        # Mémoriser le dossier source pour l'upload ultérieur
        self._bdi_last_folder = folder_path

        _status("▶ " + Path(folder_path).name)

        # ── 0. Montage ISO si nécessaire ─────────────────────────────────────
        iso_mount_info = None   # sera peuplé si on monte un ISO
        if folder_path.lower().endswith(".iso"):
            _status("📀 ISO détecté — montage en cours…")
            try:
                mounted_root, iso_mount_info = self._mount_iso(folder_path)
                _status("✔ ISO monté : " + mounted_root)
                # On travaille sur le point de montage comme si c'était un dossier
                folder_path = mounted_root
            except Exception as e_iso:
                err = "Impossible de monter l'ISO : %s" % e_iso
                _status("✖ " + err, "error")
                self._emit("bdinfo_done", {"ok": False, "error": err})
                return

        # ── 1. Trouver le dossier racine contenant BDMV ───────────────────────
        scan_root = folder_path
        folder_path_obj = Path(folder_path)

        if folder_path_obj.name.upper() == "BDMV":
            scan_root = str(folder_path_obj.parent)
        else:
            found_bdmv = None
            for depth in range(1, 4):
                matches = list(folder_path_obj.glob("/".join(["*"]*depth) + "/BDMV"))
                if matches:
                    found_bdmv = matches[0].parent
                    break
            if not found_bdmv and (folder_path_obj / "BDMV").exists():
                found_bdmv = folder_path_obj
            if found_bdmv:
                scan_root = str(found_bdmv)

        # nfo_dir défini tôt pour Wine (réutilisé aussi en section 4)
        nfo_dir = BASE_DIR / "BDINFO"
        nfo_dir.mkdir(exist_ok=True)

        # ── 1b. Wine / Whisky — BDInfo.exe Windows (résultats exacts) ───────────
        #
        # Variables d'environnement requises :
        #   BDINFO_WIN_EXE  = chemin absolu vers BDInfo.exe  (ex: ~/Wine/BDInfo.exe)
        #
        # Installation sur macOS :
        #   brew install --cask wine-stable          (ou utiliser Whisky)
        #   export BDINFO_WIN_EXE="$HOME/Wine/BDInfo.exe"
        #
        # BDInfo.exe v0.7.5.5 est une app GUI WinForms. Sous Wine, elle nécessite
        # un display (XQuartz sur macOS, ou DISPLAY=:0). Whisky configure cela
        # automatiquement. L'exe accepte le chemin du disque en argument et génère
        # un rapport dans le répertoire de sortie.
        # ─────────────────────────────────────────────────────────────────────────
        import shutil as _shutil_wine, time as _time_wine
        _is_windows = (os.name == "nt")

        # Chercher BDInfo.exe :
        #   Windows → BASE_DIR/BDInfo_v0/BDInfo.exe (lancement direct, pas de Wine)
        #   macOS   → variable BDINFO_WIN_EXE + Wine/Whisky
        if _is_windows:
            _bdinfo_win_exe = str(BASE_DIR / "BDInfo_v0" / "BDInfo.exe")
            _wine_bin = None   # inutile sur Windows
        else:
            _bdinfo_win_exe = os.getenv("BDINFO_WIN_EXE", "")
            _whisky_wine = str(Path.home() /
                "Library/Application Support/com.isaacmarovitz.Whisky"
                "/Libraries/Wine/bin/wine64")
            _wine_bin = (
                _shutil_wine.which("wine64")
                or (_whisky_wine if Path(_whisky_wine).exists() else None)
                or _shutil_wine.which("wine")
            )

        _bdinfo_ready = Path(_bdinfo_win_exe).exists() if _bdinfo_win_exe else False

        if _bdinfo_ready and (_is_windows or _wine_bin):
            if _is_windows:
                _status("💿 BDInfo.exe détecté — lancement direct…")
            else:
                _status("🍷 Wine détecté — lancement de BDInfo.exe…")

            def _posix_to_wine(p: str) -> str:
                """Convertit /chemin/posix → Z:\\chemin\\windows"""
                return "Z:" + p.replace("/", "\\")

            wine_env = os.environ.copy()

            if _is_windows:
                # Windows : lancement direct, chemins natifs
                wine_cmd = [_bdinfo_win_exe, str(scan_root), str(nfo_dir)]
            else:
                # macOS : conversion chemins POSIX → Wine Z:\...
                z_scan = "Z:" + str(scan_root).replace("/", "\\")
                z_nfo  = "Z:" + str(nfo_dir).replace("/", "\\")
                wine_env["WINEDEBUG"] = "-all"
                # WINEPREFIX Whisky
                _whisky_prefix = Path.home() / \
                    "Library/Application Support/com.isaacmarovitz.Whisky/Bottles"
                _whisky_bottle = None
                if _whisky_prefix.exists():
                    _bottles = sorted(_whisky_prefix.iterdir())
                    if _bottles:
                        _whisky_bottle = str(_bottles[0])
                wine_env["WINEPREFIX"] = (
                    _whisky_bottle
                    or os.getenv("WINEPREFIX", str(Path.home() / ".wine"))
                )
                if "DISPLAY" not in wine_env:
                    wine_env["DISPLAY"] = ":0"
                wine_cmd = [_wine_bin, _bdinfo_win_exe, z_scan, z_nfo]

            _status("→ " + " ".join(wine_cmd))

            WINE_TIMEOUT = int(os.getenv("BDINFO_WINE_TIMEOUT", "1800"))  # 30 min par défaut
            _wine_nfo_before = (
                set(str(p) for p in Path(nfo_dir).glob("*.txt"))
                | set(str(p) for p in Path(nfo_dir).glob("*.nfo"))
                | set(str(p) for p in Path(nfo_dir).glob("*.rtf"))
            )

            try:
                wine_proc = subprocess.Popen(
                    wine_cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    env=wine_env
                )
                self._wine_proc = wine_proc   # exposé pour kill depuis load_existing_bdinfo

                _wine_nfo_file = None
                _wine_done    = False
                _wine_start   = _time_wine.time()
                _wine_tick    = 0

                def _wine_reader():
                    nonlocal _wine_nfo_file, _wine_done
                    for ln in wine_proc.stdout:
                        ln = ln.rstrip()
                        if any(ln.startswith(pfx) for pfx in
                               ("fixme:", "err:", "warn:", "trace:", "wine:")):
                            continue
                        if ln:
                            _output(ln)
                    _wine_done = True

                _wine_th = threading.Thread(target=_wine_reader, daemon=True)
                _wine_th.start()

                # Mode manuel : l'utilisateur clique lui-même sur Scan Bitrates
                # puis View Report dans la fenêtre BDInfo, et sauvegarde dans nfo_dir.
                _status("🖱 BDInfo ouvert — clique Scan Bitrates puis View Report…")
                _status("💾 Sauvegarde le rapport dans : %s" % str(nfo_dir))

                # Polling principal : attendre qu'un fichier .txt / .nfo apparaisse
                while _time_wine.time() - _wine_start < WINE_TIMEOUT:
                    _time_wine.sleep(2)
                    _wine_tick += 2

                    # Chercher un nouveau rapport (.txt, .nfo ou .rtf depuis TextEdit)
                    _now_files = (
                        set(str(p) for p in Path(nfo_dir).glob("*.txt"))
                        | set(str(p) for p in Path(nfo_dir).glob("*.nfo"))
                        | set(str(p) for p in Path(nfo_dir).glob("*.rtf"))
                    )
                    _new = _now_files - _wine_nfo_before
                    if _new:
                        _wine_nfo_file = sorted(
                            _new,
                            key=lambda x: Path(x).stat().st_mtime,
                            reverse=True
                        )[0]
                        break

                    # Si le processus est déjà sorti sans créer de fichier
                    if _wine_done and wine_proc.poll() is not None:
                        break

                # Terminer le processus Wine si encore actif (BDInfo GUI reste ouvert)
                if wine_proc.poll() is None:
                    try: wine_proc.terminate()
                    except Exception: pass

                if _wine_nfo_file:
                    with open(_wine_nfo_file, "r", encoding="utf-8", errors="replace") as _nf:
                        nfo_raw = _nf.read()

                    # Convertir RTF en texte brut si nécessaire (TextEdit sauvegarde en RTF)
                    import re as _re
                    if _wine_nfo_file.endswith(".rtf"):
                        _rtf = nfo_raw
                        _rtf = _re.sub(r'\\par\b', '\n', _rtf)
                        _rtf = _re.sub(r'\\line\b', '\n', _rtf)
                        _rtf = _re.sub(r'\\[a-zA-Z]+\-?[0-9]*\s?', '', _rtf)
                        _rtf = _rtf.replace('{', '').replace('}', '').replace('\\', '')
                        _rtf = _re.sub(r'\n{3,}', '\n\n', _rtf)
                        nfo_raw = _rtf.strip()
                        # Supprimer les débris de font-table en début de fichier
                        _fd = _re.search(r'^Disc\s+(?:Title|Label)\s*:', nfo_raw, _re.MULTILINE)
                        if _fd:
                            nfo_raw = nfo_raw[_fd.start():]

                    # ── Post-traitement : garder seulement la playlist principale ──
                    # 1. Extraire le nom du disque — préférer Disc Label (ex: THE_STRANGERS_CHAPTER_3_BD)
                    _disc_label = None
                    for _priority in ('Label', 'Title'):
                        for _line in nfo_raw.splitlines():
                            _m = _re.match(r'^Disc\s+' + _priority + r'\s*:\s*(.+)', _line, _re.IGNORECASE)
                            if _m:
                                _disc_label = _m.group(1).strip().replace(" ", "_")
                                break
                        if _disc_label:
                            break
                    if not _disc_label:
                        # fallback : utiliser le nom du fichier brut sans extension
                        _disc_label = Path(_wine_nfo_file).stem

                    # 2. Découper le rapport en sections par playlist
                    #    Chaque section commence par "PLAYLIST:" ou "Name:" + .MPLS
                    _sections = _re.split(
                        r'(?=^\*{3,}\nPLAYLIST:|\bPLAYLIST:\s+\S+\.MPLS|^Name:\s+\S+\.MPLS)',
                        nfo_raw, flags=_re.MULTILINE)
                    _header = _sections[0] if _sections else ""
                    _playlist_secs = _sections[1:] if len(_sections) > 1 else []

                    # 3. Choisir la playlist principale :
                    #    - préférer 00001.MPLS s'il existe
                    #    - sinon prendre celle avec la plus longue durée (HH:MM:SS)
                    def _parse_duration(sec_text):
                        _dm = _re.search(
                            r'Length\s*:\s*(\d+):(\d+):(\d+)', sec_text, _re.IGNORECASE)
                        if _dm:
                            return int(_dm.group(1))*3600 + int(_dm.group(2))*60 + int(_dm.group(3))
                        return 0

                    _main_sec = None
                    for _s in _playlist_secs:
                        if _re.search(r'(?:PLAYLIST|Name)\s*:\s*00001\.MPLS', _s, _re.IGNORECASE):
                            _main_sec = _s
                            break
                    if _main_sec is None and _playlist_secs:
                        _main_sec = max(_playlist_secs, key=_parse_duration)

                    nfo_content = (_header.rstrip() + "\n\n" + _main_sec.strip() + "\n"
                                   if _main_sec else nfo_raw)

                    # 4. Sauvegarder .txt ET .nfo avec le nom du disque
                    _out_stem = _disc_label
                    _out_txt  = nfo_dir / (_out_stem + ".txt")
                    _out_nfo  = nfo_dir / (_out_stem + ".nfo")
                    for _out_path in (_out_txt, _out_nfo):
                        with open(_out_path, "w", encoding="utf-8") as _of:
                            _of.write(nfo_content)
                    _status("💾 Rapport sauvegardé : %s (.txt + .nfo)" % _out_stem)
                    # Supprimer le fichier brut généré par BDInfo si différent
                    _wine_nfo_path_obj = Path(_wine_nfo_file)
                    if _wine_nfo_path_obj not in (_out_txt, _out_nfo):
                        try: _wine_nfo_path_obj.unlink()
                        except Exception: pass

                    _status("✔ BDInfo.exe (Wine) — rapport généré en %ds" %
                            int(_time_wine.time() - _wine_start))
                    self._emit("bdinfo_done", {
                        "ok":       True,
                        "content":  nfo_content,
                        "nfo_name": _out_nfo.name,
                        "lines":    len(nfo_content.splitlines()),
                    })
                    if iso_mount_info:
                        try: self._unmount_iso(iso_mount_info)
                        except Exception: pass
                    return
                else:
                    rc = wine_proc.returncode if wine_proc.returncode is not None else "?"
                    err_msg = "BDInfo.exe (Wine) n'a produit aucun rapport (code=%s)" % rc
                    _status("✖ " + err_msg, "error")
                    self._emit("bdinfo_done", {"ok": False, "error": err_msg})
                    if iso_mount_info:
                        try: self._unmount_iso(iso_mount_info)
                        except Exception: pass
                    return

            except Exception as e_wine:
                err_msg = "Erreur Wine : %s" % e_wine
                _status("✖ " + err_msg, "error")
                self._emit("bdinfo_done", {"ok": False, "error": err_msg})
                if iso_mount_info:
                    try: self._unmount_iso(iso_mount_info)
                    except Exception: pass
                return

        # ── 2. Localiser dotnet et BDInfo.dll ────────────────────────────────
        bdinfo_dll = os.getenv("BDINFO_CLI_PATH", "")
        if not bdinfo_dll:
            candidates = [
                Path.home() / "BDInfoCLI/BDInfo/bin/Release/net8.0/osx-arm64/BDInfo.dll",
                Path.home() / "BDInfoCLI/BDInfo/bin/Release/net8.0/linux-x64/BDInfo.dll",
                Path.home() / "BDInfoCLI/BDInfo/bin/Release/net8.0/win-x64/BDInfo.dll",
                BASE_DIR / "BDInfoCLI/BDInfo/bin/Release/net8.0/osx-arm64/BDInfo.dll",
            ]
            for c in candidates:
                if c.exists():
                    bdinfo_dll = str(c)
                    break

        if not bdinfo_dll:
            _status("✖ BDInfo.dll introuvable — configurez BDINFO_CLI_PATH", "error")
            self._emit("bdinfo_done", {"ok": False, "error": "BDInfo.dll introuvable"})
            if iso_mount_info:
                try: self._unmount_iso(iso_mount_info)
                except Exception: pass
            return

        dotnet_candidates = [
            "/opt/homebrew/opt/dotnet@8/bin/dotnet",
            "/opt/homebrew/bin/dotnet",
            "/usr/local/bin/dotnet",
            "/usr/bin/dotnet",
            "dotnet",
        ]
        dotnet_bin = "dotnet"
        for dc in dotnet_candidates:
            if dc == "dotnet" or Path(dc).exists():
                dotnet_bin = dc
                break

        # DOTNET_ROOT Homebrew (sans GCHeapHardLimit qui provoque lui-même le SIGKILL)
        env = os.environ.copy()
        if "DOTNET_ROOT" not in env:
            dotnet_root = "/opt/homebrew/opt/dotnet@8/libexec"
            if Path(dotnet_root).exists():
                env["DOTNET_ROOT"] = dotnet_root
        env.setdefault("DOTNET_GCConserveMemory",  "7")   # agressif en conservation
        env.setdefault("DOTNET_GCHighMemPercent",  "90")  # GC déclenché à 90% RAM

        import shutil, re as _re

        use_yes = shutil.which("yes") is not None

        def _run_bdinfo(extra_args, label):
            """Lance BDInfoCLI avec réponse automatique aux prompts OOM.
            Retourne (output_lines, returncode)."""
            cmd_run = [dotnet_bin, bdinfo_dll] + extra_args + [scan_root]
            _status(label)
            p_yes = None
            try:
                if use_yes:
                    p_yes = subprocess.Popen(
                        ["yes"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL
                    )
                    stdin_src = p_yes.stdout
                else:
                    stdin_src = subprocess.PIPE

                p = subprocess.Popen(
                    cmd_run,
                    stdin=stdin_src,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    env=env
                )
                if use_yes:
                    p_yes.stdout.close()
                else:
                    def _feed():
                        import time
                        try:
                            while p.poll() is None:
                                p.stdin.write("y\n"); p.stdin.flush()
                                time.sleep(0.2)
                        except Exception:
                            pass
                        finally:
                            try: p.stdin.close()
                            except Exception: pass
                    threading.Thread(target=_feed, daemon=True).start()

                lines = []
                for ln in p.stdout:
                    ln = ln.rstrip()
                    if "Continue scanning?" not in ln:
                        lines.append(ln)
                        _output(ln)
                p.wait()
                return lines, p.returncode
            except Exception as e_run:
                raise Exception(label + " : " + str(e_run))
            finally:
                if p_yes:
                    try: p_yes.kill()
                    except Exception: pass

        # ── 3. Identifier le MPLS principal (lecture directe des binaires) ──────
        # Les fichiers MPLS contiennent les références de clips sous la forme
        # "00800M2TS" (5 chiffres ASCII + "M2TS"). On cherche ces patterns,
        # on somme les tailles des M2TS dans BDMV/STREAM/, et on prend le plus
        # gros. Aucun outil externe — même logique que BDInfo en interne.
        main_pl = None

        def _pick_mpls_by_stream_size(root):
            """
            Lit les MPLS binaires, cherche les clips "XXXXXM2TS",
            additionne les tailles M2TS dans BDMV/STREAM/.
            Retourne (mpls_name, total_bytes, [m2ts_paths_triés]).
            """
            import re as _re2
            playlist_dir = Path(root) / "BDMV" / "PLAYLIST"
            stream_dir   = Path(root) / "BDMV" / "STREAM"
            if not playlist_dir.exists() or not stream_dir.exists():
                return None, 0, []

            # Index M2TS : {"00800": (size, Path), ...}
            m2ts_info = {}
            for f in stream_dir.iterdir():
                if f.suffix.upper() == ".M2TS":
                    m2ts_info[f.stem.upper()] = (f.stat().st_size, f)

            if not m2ts_info:
                return None, 0, []

            best_name, best_size, best_clips = None, -1, []
            candidates_list = []
            for mpls_file in sorted(playlist_dir.iterdir()):
                if mpls_file.suffix.upper() != ".MPLS":
                    continue
                try:
                    data  = mpls_file.read_bytes()
                    clips = set(_re2.findall(rb'([0-9]{5})M2TS', data))
                    total = sum(m2ts_info[c.decode()][0]
                                for c in clips if c.decode() in m2ts_info)
                    paths = sorted(m2ts_info[c.decode()][1]
                                   for c in clips if c.decode() in m2ts_info)
                    candidates_list.append((mpls_file.name.upper(), total))
                    if total > best_size:
                        best_size  = total
                        best_name  = mpls_file.name.upper()
                        best_clips = paths
                except Exception:
                    continue

            if best_name:
                candidates_list.sort(key=lambda x: x[1], reverse=True)
                for pl, sz in candidates_list[:3]:
                    _status("  %s → %.2f GB" % (pl, sz / 1_073_741_824))

            return best_name, best_size, best_clips

        _status("Identification de la playlist principale…")
        main_pl       = None
        main_pl_bytes = 0
        main_pl_clips = []
        try:
            main_pl, main_pl_bytes, main_pl_clips = _pick_mpls_by_stream_size(scan_root)
            if main_pl:
                _status("Playlist principale : " + main_pl)
            else:
                _status("⚠ Lecture MPLS échouée → essai 00000.MPLS", "warn")
                main_pl = "00000.MPLS"
        except Exception as e_pl:
            _status("⚠ " + str(e_pl) + " → essai 00000.MPLS", "warn")
            main_pl = "00000.MPLS"

        # ── 3c. Préparer le fichier de sortie NFO ────────────────────────────
        # BDInfoCLI sauvegarde le rapport dans un fichier, pas sur stdout.
        # On lui passe le chemin exact comme 2e argument positionnel.
        nfo_dir = BASE_DIR / "BDINFO"
        nfo_dir.mkdir(exist_ok=True)
        folder_name = Path(scan_root).name or Path(folder_path).name
        nfo_path = nfo_dir / (folder_name + ".nfo")

        # Réinitialiser le preview pour le vrai scan
        self._emit("bdinfo_reset_output", {})

        # ── 3d. Scan -m 00003.MPLS <disc> <output.nfo> → rapport complet ─────
        # Le stdout contient seulement la progression/erreurs.
        # Le vrai rapport est écrit dans nfo_path.
        def _run_bdinfo_to_file(extra_args, out_dir, label):
            """Comme _run_bdinfo mais passe out_dir (dossier sortie) en 2e arg positionnel."""
            cmd_run = ([dotnet_bin, bdinfo_dll]
                       + extra_args
                       + [scan_root, str(out_dir)])
            _status(label)
            p_yes = None
            try:
                if use_yes:
                    p_yes = subprocess.Popen(
                        ["yes"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL
                    )
                    stdin_src = p_yes.stdout
                else:
                    stdin_src = subprocess.PIPE

                p = subprocess.Popen(
                    cmd_run,
                    stdin=stdin_src,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace",
                    env=env
                )
                if use_yes:
                    p_yes.stdout.close()
                else:
                    def _feed2():
                        import time
                        try:
                            while p.poll() is None:
                                p.stdin.write("y\n"); p.stdin.flush()
                                time.sleep(0.2)
                        except Exception:
                            pass
                        finally:
                            try: p.stdin.close()
                            except Exception: pass
                    threading.Thread(target=_feed2, daemon=True).start()

                # Afficher la progression (stdout = erreurs/status, pas le rapport)
                for ln in p.stdout:
                    ln = ln.rstrip()
                    if "Continue scanning?" not in ln and ln:
                        _output(ln)
                p.wait()
                return p.returncode
            except Exception as e2:
                raise Exception(label + " : " + str(e2))
            finally:
                if p_yes:
                    try: p_yes.kill()
                    except Exception: pass

        # BDInfoCLI attend un DOSSIER (pas un fichier) comme 2e arg positionnel.
        # Il crée lui-même le fichier rapport à l'intérieur.
        import glob as _glob, time as _time, queue as _queue

        # ── 3e. Scan interactif via PTY ────────────────────────────────────────
        # BDInfoCLI utilise Console.KeyAvailable() → exige un vrai terminal.
        # On ouvre un PTY. Quand BDInfoCLI attend une entrée, on émet
        # bdinfo_waiting_input vers le frontend : l'utilisateur tape la réponse
        # (numéro de playlist, "y" pour scanner, etc.).
        # Fallback automatique -m si le module pty n'est pas disponible (Windows).
        import queue as _q

        # _pl_number sera écrasé dès qu'on voit la ligne du listing BDInfoCLI
        # Format : "N  G  XXXXX.MPLS  HH:MM:SS  bytes  -"
        # Valeur initiale = "1" (jamais utilisée si le listing est parsé)
        _pl_number = "1"

        def _run_bdinfo_interactive_pty(label):
            """PTY hybride :
            - 'Select (q when finished):' → auto-envoie le numéro du MPLS, puis 'q'
            - 'Continue scanning?'        → demande confirmation à l'utilisateur
            - Tout autre prompt inconnu   → demande à l'utilisateur
            """
            import pty as _pty, os as _os, select as _sel
            try:
                import termios as _termios
                _has_termios = True
            except ImportError:
                _has_termios = False

            master_fd, slave_fd = _pty.openpty()
            if _has_termios:
                try:
                    t = _termios.tcgetattr(slave_fd)
                    t[3] &= ~_termios.ECHO
                    _termios.tcsetattr(slave_fd, _termios.TCSANOW, t)
                except Exception:
                    pass

            cmd = [dotnet_bin, bdinfo_dll, scan_root, str(nfo_dir)]
            _status(label)
            try:
                p = subprocess.Popen(
                    cmd, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
                    close_fds=True, env=env
                )
                _os.close(slave_fd)
            except Exception as e_pty:
                _os.close(slave_fd); _os.close(master_fd); raise e_pty

            buf              = b""
            playlist_added   = False   # True après avoir envoyé le numéro
            waiting_user     = False   # True quand on attend la saisie UI

            def _send(text):
                _os.write(master_fd, (text + "\n").encode())

            while True:
                if p.poll() is not None:
                    try:
                        r2, _, _ = _sel.select([master_fd], [], [], 2)
                        if r2:
                            buf += _os.read(master_fd, 65536)
                    except OSError:
                        pass
                    break

                try:
                    r, _, _ = _sel.select([master_fd], [], [], 2)
                except (ValueError, OSError):
                    break

                if not r:
                    # Pas de nouvelles données depuis 2 s
                    if waiting_user:
                        # Vérifier si l'utilisateur a répondu
                        try:
                            user_text = self._bdinfo_input_queue.get_nowait()
                            _send(user_text)
                            waiting_user = False
                            self._emit("bdinfo_hide_input", {})
                            _status("→ « " + user_text + " » envoyé")
                        except _q.Empty:
                            pass
                    else:
                        # Inspecter le fragment courant
                        prompt_raw = buf.decode("utf-8", errors="replace")
                        prompt = _re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", prompt_raw).strip()
                        prompt_low = prompt.lower()

                        if "select" in prompt_low and "when finished" in prompt_low:
                            # Prompt de sélection de playlist
                            if not playlist_added:
                                _send(_pl_number)
                                playlist_added = True
                                _status("→ Playlist #" + _pl_number + " (" + main_pl + ") auto-sélectionnée")
                            else:
                                # Déjà sélectionnée → quitter la boucle
                                _send("q")
                                _status("→ q (fin de sélection)")

                        elif "continue" in prompt_low and "scanning" in prompt_low:
                            # "Continue scanning? [y/N]" → toujours y (scan complet)
                            _send("y")
                            _status("→ y (scan M2TS complet)")

                        elif prompt:
                            # Prompt inconnu → demander à l'utilisateur
                            self._emit("bdinfo_waiting_input", {"prompt": prompt})
                            waiting_user = True
                            _status("⌨ En attente de ta saisie…")
                    continue

                try:
                    data = _os.read(master_fd, 8192)
                except OSError:
                    break
                if not data:
                    break

                buf += data
                text = buf.decode("utf-8", errors="replace")
                buf  = b""
                text = _re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", text)
                # \r\n → newline ; \r seul (mise à jour de progression) → newline aussi
                text = text.replace("\r\n", "\n").replace("\r", "\n")

                lines = text.split("\n")
                buf   = lines[-1].encode()

                for ln in lines[:-1]:
                    ln = ln.rstrip()
                    if not ln:
                        continue

                    # Ligne de progression M2TS "XXXXX.M2TS  HH:MM:SS  HH:MM:SS"
                    # → status (mise à jour en temps réel, pas dans le rapport)
                    if _re.search(r'\.M2TS\s+\d+:\d+:\d+', ln, _re.IGNORECASE):
                        _status("⏱ " + ln.strip())
                        continue

                    # Parser le listing pour trouver le vrai numéro de main_pl
                    # Format : "N  G  XXXXX.MPLS  HH:MM:SS  bytes  -"
                    if not playlist_added and main_pl.upper() in ln.upper():
                        mpls_pos = ln.upper().index(main_pl.upper())
                        pre_nums = _re.findall(r"\b(\d+)\b", ln[:mpls_pos])
                        if pre_nums:
                            _pl_number = pre_nums[0]
                            _status("→ %s = #%s dans le listing BDInfoCLI"
                                    % (main_pl, _pl_number))

                    _output(ln)

                if waiting_user:
                    self._emit("bdinfo_hide_input", {})
                    waiting_user = False

            try:
                _os.close(master_fd)
            except OSError:
                pass
            if p.poll() is None:
                p.wait()
            self._emit("bdinfo_hide_input", {})
            return p.returncode

        def _run_bdinfo_winpty(label):
            """Windows ConPTY via pywinpty : même logique interactive que le PTY Unix.
            Un thread lecteur alimente une queue ; la boucle principale détecte les
            prompts par silence de 2 s (identique au chemin Unix).
            """
            from winpty import PtyProcess
            import threading as _threading

            nonlocal _pl_number

            cmd_str = " ".join(
                '"%s"' % c if " " in c else c
                for c in [dotnet_bin, bdinfo_dll, scan_root, str(nfo_dir)]
            )
            _status(label)

            # Largeur généreuse pour ne pas tronquer les lignes de listing
            proc = PtyProcess.spawn(
                [dotnet_bin, bdinfo_dll, scan_root, str(nfo_dir)],
                env=env,
                dimensions=(50, 260),
            )

            read_q   = _q.Queue()
            eof_evt  = _threading.Event()

            def _reader():
                while True:
                    try:
                        chunk = proc.read(8192)
                        if chunk:
                            read_q.put(chunk)
                        if not proc.isalive():
                            break
                    except EOFError:
                        break
                    except Exception:
                        break
                eof_evt.set()

            _threading.Thread(target=_reader, daemon=True).start()

            buf            = ""
            playlist_added = False
            waiting_user   = False

            def _send(text):
                proc.write(text + "\r\n")

            while True:
                # ── Lire avec timeout 2 s ──────────────────────────────────────
                try:
                    chunk = read_q.get(timeout=2)
                except _q.Empty:
                    chunk = None

                if chunk is not None:
                    buf += chunk
                    # Décoder ANSI + normaliser fins de ligne
                    text = _re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", buf)
                    text = text.replace("\r\n", "\n").replace("\r", "\n")
                    lines = text.split("\n")
                    buf   = lines[-1]           # fragment incomplet → réserver

                    for ln in lines[:-1]:
                        ln = ln.rstrip()
                        if not ln:
                            continue

                        # Ligne de progression M2TS "XXXXX.M2TS  HH:MM:SS  HH:MM:SS"
                        if _re.search(r'\.M2TS\s+\d+:\d+:\d+', ln, _re.IGNORECASE):
                            _status("⏱ " + ln.strip())
                            continue

                        # Parser le listing → trouver le numéro du bon MPLS
                        if not playlist_added and main_pl.upper() in ln.upper():
                            mpls_pos = ln.upper().index(main_pl.upper())
                            pre_nums = _re.findall(r"\b(\d+)\b", ln[:mpls_pos])
                            if pre_nums:
                                _pl_number = pre_nums[0]
                                _status("→ %s = #%s dans le listing BDInfoCLI"
                                        % (main_pl, _pl_number))

                        _output(ln)

                    if waiting_user:
                        self._emit("bdinfo_hide_input", {})
                        waiting_user = False

                else:
                    # ── Timeout 2 s — aucune donnée ───────────────────────────
                    if eof_evt.is_set() and read_q.empty():
                        break   # processus terminé + queue vide

                    if waiting_user:
                        try:
                            user_text = self._bdinfo_input_queue.get_nowait()
                            _send(user_text)
                            waiting_user = False
                            self._emit("bdinfo_hide_input", {})
                            _status("→ « " + user_text + " » envoyé")
                        except _q.Empty:
                            pass
                    else:
                        prompt     = _re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", buf).strip()
                        prompt_low = prompt.lower()

                        if "select" in prompt_low and "when finished" in prompt_low:
                            if not playlist_added:
                                _send(_pl_number)
                                playlist_added = True
                                _status("→ Playlist #" + _pl_number
                                        + " (" + main_pl + ") auto-sélectionnée")
                            else:
                                _send("q")
                                _status("→ q (fin de sélection)")

                        elif "continue" in prompt_low and "scanning" in prompt_low:
                            # Toujours scanner complètement
                            _send("y")
                            _status("→ y (scan M2TS complet)")

                        elif prompt:
                            self._emit("bdinfo_waiting_input", {"prompt": prompt})
                            waiting_user = True
                            _status("⌨ En attente de ta saisie…")

            try:
                proc.close()
            except Exception:
                pass
            self._emit("bdinfo_hide_input", {})
            rc = proc.exitstatus
            return rc if rc is not None else 0

        # Timestamp AVANT le scan pour trouver les fichiers créés/modifiés après
        scan_start = _time.time()

        try:
            _status("Scan interactif %s via PTY…" % main_pl)
            rc = _run_bdinfo_interactive_pty("BDInfoCLI en cours…")
        except ImportError:
            # Pas de pty Unix → essayer pywinpty (Windows ConPTY)
            try:
                _status("Scan interactif %s via WinPTY…" % main_pl)
                rc = _run_bdinfo_winpty("BDInfoCLI (WinPTY) en cours…")
            except ImportError:
                # Aucun PTY dispo → fallback -m + patch bitrates
                _status("⚠ PTY non dispo → -m + calcul bitrates")
                rc = _run_bdinfo_to_file(["-m", main_pl], nfo_dir,
                                         "Scan -m " + main_pl + "…")

        # ── 4. Lire le rapport généré par BDInfoCLI ───────────────────────────
        # Chercher le fichier le plus récent dans nfo_dir modifié APRÈS scan_start
        # (gère aussi le cas où le fichier existait déjà — rescan du même film)
        _time.sleep(1)
        output_text = ""
        src_file = None

        # 4a. Fichier modifié après scan_start dans nfo_dir
        candidates_nfo = sorted(
            _glob.glob(str(nfo_dir / "*.txt")) + _glob.glob(str(nfo_dir / "*.nfo")),
            key=lambda f: Path(f).stat().st_mtime, reverse=True
        )
        for c in candidates_nfo:
            if Path(c).stat().st_mtime >= scan_start - 2:   # -2s de marge
                src_file = Path(c)
                output_text = src_file.read_text(encoding="utf-8", errors="replace")
                _status("💾 BDINFO/" + src_file.name, "success")
                break

        if not src_file:
            # 4b. Fallback : chercher dans scan_root
            candidates_root = sorted(
                _glob.glob(str(Path(scan_root) / "*.txt"))
                + _glob.glob(str(Path(scan_root) / "BDINFO*.txt")),
                key=lambda f: Path(f).stat().st_mtime, reverse=True
            )
            for c in candidates_root:
                if Path(c).stat().st_mtime >= scan_start - 2:
                    src_file = Path(c)
                    output_text = src_file.read_text(encoding="utf-8", errors="replace")
                    _status("💾 depuis " + src_file.name, "success")
                    break

        if not output_text:
            err_msg = "BDInfoCLI n'a produit aucun rapport"
            _status("✖ " + err_msg, "error")
            self._emit("bdinfo_done", {"ok": False, "error": err_msg})
            if iso_mount_info:
                try: self._unmount_iso(iso_mount_info)
                except Exception: pass
            return

        # ── 5. Parser STREAM DIAGNOSTICS avant filtrage ──────────────────────
        # BDInfoCLI v0.8.0.0 calcule le bitrate vidéo sur les bytes PES payload
        # (trop bas). BDInfo v0.7.5.5 utilise : packets × 184 × 8 / durée / 1000
        # (184 = taille payload TS = 188 - 4 bytes header).
        # On recalcule ici depuis les données de STREAM DIAGNOSTICS qui sont exactes.
        import re as _re_sd
        video_pid      = 0x1011   # défaut Blu-ray
        sd_kbps_exact  = None     # bitrate recalculé depuis STREAM DIAGNOSTICS

        # Format : "FICHIER  PID (0xHEX)  TYPE  CODEC  LANG  SECONDES  BITRATE  BYTES  PAQUETS"
        _sd_video = _re_sd.search(
            r'(\w+\.M2TS)\s+(\d+)\s+\(0x[\dA-Fa-f]+\)\s+'   # fichier, PID
            r'0x(?:1[Bb]|24|EA)\s+'                            # type vidéo AVC/HEVC/VC-1
            r'\S+\s+'                                           # codec
            r'\S*\s*'                                           # langue (optionnel)
            r'([\d.]+)\s+'                                      # secondes
            r'[\d,]+\s+'                                        # bitrate (PES — ignoré)
            r'[\d,]+\s+'                                        # bytes PES (ignoré)
            r'([\d,]+)',                                         # paquets TS ← la vraie donnée
            output_text, _re_sd.IGNORECASE
        )
        if _sd_video:
            video_pid   = int(_sd_video.group(2))
            sd_dur      = float(_sd_video.group(3))
            sd_pkts     = int(_sd_video.group(4).replace(',', ''))
            if sd_dur > 0 and sd_pkts > 0:
                # BDInfo v0.7.5.5 : paquets × 184 × 8 / durée / 1000
                # (184 = 188 bytes TS − 4 bytes header)
                sd_kbps_exact = round(sd_pkts * 184 * 8 / sd_dur / 1000)
                _status("→ STREAM DIAG PID %d : %d paquets × 184 B / %.3f s = %d kbps"
                        % (video_pid, sd_pkts, sd_dur, sd_kbps_exact))

        # ── 5b. Filtrer : garder uniquement DISC INFO (ou Disc Title) → SUBTITLES ──
        def _extract_disc_info(text):
            import re as _re2
            _STOP = r'(?=\nFILES:|\nCHAPTERS:|\nSTREAM DIAGNOSTICS:|\n\[/code\]|\nQUICK SUMMARY:|\n\*{10,}|\Z)'
            _m = _re2.search(r'(DISC INFO:.*?)' + _STOP, text, _re2.DOTALL)
            if not _m:
                _start = _re2.search(r'^Disc (?:Title|Label):', text, _re2.MULTILINE)
                if _start:
                    _m = _re2.search(r'(.+?)' + _STOP, text[_start.start():], _re2.DOTALL)
            return _m.group(1).strip() if _m else ""

        filtered = _extract_disc_info(output_text)
        if filtered:
            output_text = filtered

        # ── 5c. Mesure exacte du bitrate vidéo par comptage de paquets TS ────
        # Même algorithme que BDInfo : pour chaque paquet TS du PID vidéo,
        # on cumule 188 octets. bitrate = (total_bytes × 8) / durée / 1000.
        # Numpy utilisé pour la vitesse (fallback pur Python si absent).

        def _measure_video_kbps_ts(paths, dur_sec, pid):
            """Compte les paquets TS du PID vidéo dans les fichiers M2TS.
            Retourne le bitrate en kbps (int) ou None."""
            if dur_sec <= 0 or not paths:
                return None
            total_video_bytes = 0
            for path in paths:
                path = str(path)
                if not os.path.exists(path):
                    continue
                _status("⏱ Comptage paquets TS : %s…" % os.path.basename(path))
                try:
                    with open(path, 'rb') as f:
                        probe = f.read(384)
                        f.seek(0)
                        if len(probe) >= 192 and probe[4] == 0x47:
                            pkt_size, ts_off = 192, 4
                        else:
                            pkt_size, ts_off = 188, 0
                        try:
                            import numpy as _np
                            CHUNK   = 64 * 1024 * 1024   # 64 MB
                            leftover = b""
                            while True:
                                raw = leftover + f.read(CHUNK)
                                if not raw:
                                    break
                                arr = _np.frombuffer(raw, dtype=_np.uint8)
                                n = len(arr) // pkt_size
                                if n == 0:
                                    leftover = bytes(arr)
                                    continue
                                m = arr[:n * pkt_size].reshape(n, pkt_size)
                                sync = m[:, ts_off] == 0x47
                                hi   = (m[:, ts_off + 1].astype(_np.uint16) & 0x1F) << 8
                                lo   =  m[:, ts_off + 2].astype(_np.uint16)
                                pids = hi | lo
                                total_video_bytes += int(_np.sum(sync & (pids == pid))) * 184
                                leftover = bytes(arr[n * pkt_size:])
                        except ImportError:
                            # Fallback pur Python — plus lent
                            CHUNK    = 8 * 1024 * 1024
                            leftover = b""
                            while True:
                                raw = leftover + f.read(CHUNK)
                                if not raw:
                                    break
                                n = len(raw) // pkt_size
                                if n == 0:
                                    leftover = raw
                                    continue
                                for i in range(n):
                                    b = i * pkt_size + ts_off
                                    if raw[b] != 0x47:
                                        continue
                                    p = ((raw[b+1] & 0x1F) << 8) | raw[b+2]
                                    if p == pid:
                                        total_video_bytes += 184
                                leftover = raw[n * pkt_size:]
                except Exception as e_ts:
                    _status("⚠ Comptage TS erreur : %s" % e_ts, "warning")
                    continue
            if total_video_bytes == 0:
                return None
            kbps = round(total_video_bytes * 8 / dur_sec / 1000)
            _status("✔ Bitrate vidéo mesuré (TS) : %d kbps" % kbps)
            return kbps

        def _get_video_kbps_mediainfo(m2ts_paths):
            """
            Lit le bitrate vidéo réel depuis les fichiers M2TS via pymediainfo.
            Retourne le bitrate en kbps (int) ou None en cas d'échec.
            """
            try:
                from pymediainfo import MediaInfo
            except ImportError:
                _status("⚠ pymediainfo non disponible", "warning")
                return None

            paths = [str(p) for p in m2ts_paths if os.path.exists(str(p))]
            _status("→ MediaInfo : analyse de %d fichier(s) M2TS…" % len(paths))
            if not paths:
                _status("✖ Aucun fichier M2TS accessible", "warning")
                return None

            for path in paths:
                fname = path.replace("\\", "/").split("/")[-1]
                try:
                    _status("→ MediaInfo parse : %s…" % fname)
                    mi = MediaInfo.parse(path)
                    for track in mi.tracks:
                        if track.track_type == "Video":
                            br = getattr(track, "bit_rate", None)
                            if br:
                                kbps = round(int(str(br).strip()) / 1000)
                                if kbps > 500:   # sanity check minimal
                                    _status("→ Bitrate vidéo (MediaInfo) : %d kbps" % kbps)
                                    return kbps
                            _status("⚠ track Video sans bit_rate (br=%r)" % br, "warning")
                except Exception as e_mi:
                    _status("✖ MediaInfo erreur sur %s : %s" % (fname, e_mi), "warning")
            return None

        def _patch_bitrates(text, total_bytes, m2ts_paths):
            import re as _re2

            lines = text.splitlines()

            # Durée depuis "Length: H:MM:SS.ms"
            duration_sec = 0.0
            for ln in lines:
                dm = _re2.search(r'Length:\s+(\d+):(\d+):([\d.]+)', ln)
                if dm:
                    duration_sec = (int(dm.group(1)) * 3600
                                    + int(dm.group(2)) * 60
                                    + float(dm.group(3)))
                    break
            if not duration_sec or not total_bytes:
                return text, False

            total_mbps = total_bytes * 8 / duration_sec / 1_000_000
            size_str   = "{:,}".format(total_bytes)

            # ── Patch Size: 0 et Total Bitrate: 0.00 ─────────────────────────
            result = []
            for ln in lines:
                if _re2.search(r'\bSize:\s+0 bytes', ln):
                    ln = ln.replace("0 bytes", size_str + " bytes")
                elif _re2.search(r'Total Bitrate:\s+0\.00 Mbps', ln):
                    ln = _re2.sub(r'0\.00 Mbps', "%.2f Mbps" % total_mbps, ln)
                result.append(ln)
            lines = result

            # ── Détection scan partiel : sum(streams kbps entiers) << total ──
            total_kbps = total_mbps * 1000
            for ln in lines:
                tm = _re2.search(r'Total Bitrate:\s+([\d.]+)\s*Mbps', ln)
                if tm:
                    total_kbps = float(tm.group(1)) * 1000
                    break

            # Ne sommer que les valeurs entières (audio/vidéo) ; les sous-titres
            # ont des valeurs décimales (ex: "37.605 kbps") ignorées ici.
            stream_kbps = 0.0
            for ln in lines:
                bm = _re2.search(r'\b(\d{3,})\s+kbps\b', ln)
                if bm:
                    stream_kbps += float(bm.group(1))

            unaccounted_pct = (
                100 * (total_kbps - stream_kbps) / total_kbps
                if total_kbps > 0 else 0
            )
            # Détection overcounting : streams > total → BDInfoCLI a surestimé la vidéo
            overcounting = (total_kbps > 0 and stream_kbps > total_kbps * 1.02)
            _status("→ Vérif : total=%.0f kbps, streams=%.0f kbps, manquant=%.0f%%%s"
                    % (total_kbps, stream_kbps, unaccounted_pct,
                       " ⚠OVERCOUNTING" if overcounting else ""))

            needs_fix = (unaccounted_pct > 20 or overcounting)

            video_fixed = False
            if needs_fix and m2ts_paths and duration_sec > 0:
                if overcounting:
                    _status("⚙ Overcounting (streams %.0f kbps > total %.0f kbps) → MediaInfo…"
                            % (stream_kbps, total_kbps))
                else:
                    _status("⚙ Scan partiel (%.0f%% manquant) → MediaInfo…" % unaccounted_pct)
                corrected = _get_video_kbps_mediainfo(m2ts_paths)
                if corrected:
                    result2 = []
                    for ln in lines:
                        if not video_fixed:
                            vm = _re2.match(
                                r'^(\s*\S.*?\s+Video\s+)(\d[\d,]*)\s*(kbps)(.*)',
                                ln, _re2.IGNORECASE
                            )
                            if vm:
                                ln = (vm.group(1) + str(corrected)
                                      + " " + vm.group(3) + vm.group(4))
                                video_fixed = True
                                _status("✔ Ligne vidéo patchée : %d kbps" % corrected)
                        result2.append(ln)
                    lines = result2
                    if not video_fixed:
                        _status("⚠ Ligne vidéo non trouvée (regex no-match)", "warning")
            else:
                _status("→ Bitrates OK (scan complet)")

            return "\n".join(lines), video_fixed

        # ── 5d. Corriger Size/Bitrate à zéro si nécessaire ────────────────────
        if main_pl_bytes > 0:
            output_text, _ = _patch_bitrates(output_text, main_pl_bytes, main_pl_clips)

        # ── 5e. Corriger le bitrate vidéo ─────────────────────────────────────
        # BDInfoCLI v0.8.0.0 calcule le bitrate sur les bytes PES payload au lieu
        # de paquets × 184 bytes (payload TS = 188 - 4 header).
        # Méthode 1 (prioritaire, instantanée) : recalculer depuis STREAM DIAGNOSTICS
        # Méthode 2 (fallback) : lire les fichiers M2TS et compter les paquets

        def _apply_video_kbps(kbps, label):
            """Remplace la ligne vidéo kbps dans output_text."""
            nonlocal output_text
            import re as _re_v2
            _lines = output_text.splitlines()
            for _i, _ln in enumerate(_lines):
                _vm = _re_v2.match(
                    r'^(\s*\S.*?\s+Video\s+)(\d[\d,]*)\s*(kbps)(.*)',
                    _ln, _re_v2.IGNORECASE
                )
                if _vm:
                    _lines[_i] = (_vm.group(1) + str(kbps)
                                  + " " + _vm.group(3) + _vm.group(4))
                    output_text = "\n".join(_lines)
                    _status("✔ %s : %d kbps" % (label, kbps), "success")
                    return True
            _status("⚠ Ligne vidéo introuvable dans le rapport", "warning")
            return False

        if sd_kbps_exact:
            # Méthode 1 : depuis STREAM DIAGNOSTICS (paquets × 184 × 8 / durée / 1000)
            _apply_video_kbps(sd_kbps_exact, "Bitrate vidéo (paquets TS × 184)")

        elif main_pl_clips:
            # Méthode 2 : lire les fichiers M2TS — fallback si STREAM DIAGNOSTICS absent
            # Extraire la durée du rapport
            _dur_sec = 0.0
            import re as _re_dur
            _dm = _re_dur.search(r'Length:\s+(\d+):(\d+):([\d.]+)', output_text)
            if _dm:
                _dur_sec = (int(_dm.group(1)) * 3600
                            + int(_dm.group(2)) * 60
                            + float(_dm.group(3)))
            if _dur_sec > 0:
                _status("⏱ Comptage paquets TS (fallback)…")
                ts_kbps = _measure_video_kbps_ts(main_pl_clips, _dur_sec, video_pid)
                if ts_kbps:
                    _apply_video_kbps(ts_kbps, "Bitrate vidéo (comptage M2TS)")
                else:
                    _status("⚠ Comptage TS échoué — valeur BDInfoCLI conservée", "warning")
            else:
                _status("⚠ Durée introuvable — valeur BDInfoCLI conservée", "warning")

        # Réécrire .nfo ET le fichier source (.txt ou autre) avec la version filtrée
        nfo_path.write_text(output_text, encoding="utf-8")
        if src_file and src_file != nfo_path:
            src_file.write_text(output_text, encoding="utf-8")

        # Envoyer le contenu dans la preview (remplace la progression)
        self._emit("bdinfo_reset_output", {})
        for ln in output_text.splitlines():
            _output(ln)

        # Mémoriser le dernier NFO pour l'upload
        self._bdi_last_nfo = str(nfo_path)

        output_lines = output_text.splitlines()
        self._emit("bdinfo_done", {
            "ok":       True,
            "nfo_path": str(nfo_path),
            "nfo_name": nfo_path.name,
            "lines":    len(output_lines),
            "content":  output_text,
        })

        # ── Démontage ISO ─────────────────────────────────────────────────────
        if iso_mount_info:
            try:
                self._unmount_iso(iso_mount_info)
                _status("✔ ISO démonté")
            except Exception as e_umount:
                _status("⚠ Démontage ISO : %s" % e_umount, "warning")

    def upload_bdinfo_nfo(self, platform: str):
        """Compresse dossier film + NFO en ZIP puis upload vers Gofile/BuzzHeavier."""
        import zipfile as _zipfile

        def _worker():
            nfo    = getattr(self, "_bdi_last_nfo",    "")
            folder = getattr(self, "_bdi_last_folder", "")

            if not nfo or not Path(nfo).exists():
                self._emit("bdinfo_upload_done", {
                    "ok": False, "error": "Aucun NFO disponible — lancez d'abord un scan"
                })
                return

            # ── Collecter les fichiers (dossier + NFO) ────────────────────────
            files = []   # list of (abs_path, arcname)
            folder_name = Path(folder).name if folder else "BLURAY"

            if folder and Path(folder).exists():
                for f in sorted(Path(folder).rglob("*")):
                    if not f.is_file():
                        continue
                    if f.name.startswith(".") or f.name.startswith("._"):
                        continue
                    if "BACKUP" in f.parts:
                        continue
                    rel = f.relative_to(Path(folder).parent)   # inclut le dossier parent
                    files.append((str(f), str(rel)))

            # NFO dans le dossier racine de l'archive
            nfo_arc = folder_name + "/" + Path(nfo).name
            files.append((nfo, nfo_arc))

            # ── Créer le ZIP (ZIP_STORED — M2TS déjà compressé) ──────────────
            zip_path = BASE_DIR / "BDINFO" / (folder_name + ".zip")
            total_size  = sum(Path(f).stat().st_size for f, _ in files)
            done_size   = 0
            CHUNK       = 4 * 1024 * 1024   # 4 MB

            self._emit("bdinfo_upload_status", {
                "msg": f"Compression… 0 % — {len(files)} fichiers"
            })

            try:
                with _zipfile.ZipFile(str(zip_path), "w",
                                      compression=_zipfile.ZIP_STORED,
                                      allowZip64=True) as zf:
                    for abs_path, arc_name in files:
                        file_size = Path(abs_path).stat().st_size
                        with open(abs_path, "rb") as fh:
                            zinfo = _zipfile.ZipInfo(arc_name)
                            zinfo.compress_type = _zipfile.ZIP_STORED
                            with zf.open(zinfo, "w", force_zip64=True) as dest:
                                while True:
                                    chunk = fh.read(CHUNK)
                                    if not chunk:
                                        break
                                    dest.write(chunk)
                                    done_size += len(chunk)
                                    pct = int(done_size * 100 / total_size) if total_size else 0
                                    self._emit("bdinfo_upload_status", {
                                        "msg": f"Compression… {pct} %"
                                    })
            except Exception as e_zip:
                self._emit("bdinfo_upload_done", {
                    "ok": False, "error": "ZIP : " + str(e_zip)
                })
                return

            # ── Upload du ZIP ─────────────────────────────────────────────────
            label = "BuzzHeavier" if platform == "b" else "Gofile"
            self._emit("bdinfo_upload_status", {"msg": f"Upload vers {label}…"})

            try:
                if platform == "g":
                    urls = gofile_upload(
                        path=[str(zip_path)], to_single_folder=True,
                        verbose=False, progress_fn=None
                    )
                    url = urls[0] if urls else ""
                else:
                    bzhv_id = os.getenv("BUZZHEAVIER_ACC_ID", "")
                    url = self._upload_bzhv([str(zip_path)], bzhv_id)

                self._emit("bdinfo_upload_done", {
                    "ok": True, "url": url, "platform": platform
                })
            except Exception as e_up:
                self._emit("bdinfo_upload_done", {
                    "ok": False, "error": str(e_up)
                })
            finally:
                # Supprimer le ZIP après upload
                try:
                    zip_path.unlink()
                except Exception:
                    pass

        threading.Thread(target=_worker, daemon=True).start()
        return {"ok": True}

    def _sftp_upload_folder(self, sftp, local_dir: str, remote_dir: str):
        """Upload récursif d'un dossier local vers la seedbox via SFTP.
        Crée les sous-dossiers distants à la volée.
        Exclut tout fichier/dossier dont un composant du chemin relatif commence par '.'
        (resource forks ._*, .DS_Store, .Spotlight-V100/, .fseventsd/, etc.)
        NE filtre PAS BACKUP/ — mktorrent en a besoin pour la vérification du torrent.
        """
        import time as _time

        local_path = Path(local_dir)

        def _mkdir_p(sftp_client, path):
            parts = path.strip("/").split("/")
            cur = ""
            for part in parts:
                cur += "/" + part
                try:
                    sftp_client.stat(cur)
                except FileNotFoundError:
                    sftp_client.mkdir(cur)
                    self._log("  [SFTP] Dossier créé : " + cur)

        # Créer le dossier racine distant
        _mkdir_p(sftp, remote_dir)

        # Lister tous les fichiers à uploader (hors éléments cachés macOS)
        files_to_upload = []
        skipped = []
        total_bytes = 0
        for local_f in sorted(local_path.rglob("*")):
            if not local_f.is_file():
                continue
            rel = local_f.relative_to(local_path)
            # Ignorer tout composant du chemin commençant par '.'
            # (._*, .DS_Store, .Spotlight-V100/, .fseventsd/, .Trashes/, etc.)
            if any(part.startswith(".") for part in rel.parts):
                skipped.append((rel, local_f.stat().st_size))
                continue
            files_to_upload.append((local_f, rel))
            total_bytes += local_f.stat().st_size

        skipped_bytes = sum(s for _, s in skipped)
        total_gib   = round(total_bytes / 1073741824, 2)
        skipped_mib = round(skipped_bytes / 1048576, 1)

        msg_scan = (f"Scan : {len(files_to_upload)} fichiers — {total_gib} GiB à uploader"
                    + (f" | {len(skipped)} cachés ignorés ({skipped_mib} MiB)" if skipped else ""))
        self._log(f"  [SFTP] {msg_scan}")
        self._emit("bdinfo_hdt_status", {"msg": msg_scan})
        for rel_s, sz_s in skipped:
            self._log(f"  [SFTP] ⤼ ignoré : {rel_s} ({round(sz_s/1048576,1)} MiB)")

        uploaded_bytes = 0
        for local_f, rel in files_to_upload:

            remote_f      = remote_dir.rstrip("/") + "/" + str(rel).replace("\\", "/")
            remote_parent = remote_dir.rstrip("/") + "/" + str(rel.parent).replace("\\", "/")

            # Créer les sous-dossiers intermédiaires
            if rel.parent != Path("."):
                _mkdir_p(sftp, remote_parent)

            filesize = local_f.stat().st_size
            size_str = (str(round(filesize / 1073741824, 2)) + " GiB"
                        if filesize > 1073741824
                        else str(round(filesize / 1048576, 1)) + " MiB")
            self._log(f"  [SFTP] ↑ {rel} ({size_str})…")
            self._emit("bdinfo_hdt_status", {"msg": f"Upload {local_f.name} ({size_str})…"})

            start     = _time.time()
            last_emit = [0.0]

            def _cb(sent, total, _f=local_f.name, _fs=filesize, _st=start, _le=last_emit):
                now = _time.time()
                if now - _le[0] < 1.0:
                    return
                _le[0] = now
                elapsed = now - _st
                speed = sent / elapsed / 1048576 if elapsed > 0 else 0
                pct   = int(sent * 100 / total) if total > 0 else 0
                self._emit("bdinfo_hdt_status", {
                    "msg": f"Upload {_f} — {pct}% — {round(speed, 1)} MB/s"
                })

            sftp.put(str(local_f), remote_f, callback=_cb)

            uploaded_bytes += filesize
            elapsed = _time.time() - start
            m, s = divmod(int(elapsed), 60)
            self._log(f"  [SFTP] ✓ {rel} — {m:02d}m{s:02d}s", "success")

        done_gib = round(uploaded_bytes / 1073741824, 2)
        msg_done = f"Upload terminé : {done_gib} GiB envoyés"
        self._log(f"  [SFTP] {msg_done}", "success")
        self._emit("bdinfo_hdt_status", {"msg": msg_done})

    def torrent_bdinfo_hdt(self):
        """Upload le dossier FULL BD sur la seedbox puis crée le torrent HD-Torrents.
        1. SFTP upload récursif du dossier local vers SFTP_PATH_HDT/<nom>
        2. Création du torrent via mktorrent (SSH) + chargement ruTorrent
        """
        def _worker():
            try:
                bdi_folder = getattr(self, "_bdi_last_folder", "")
                if not bdi_folder:
                    self._emit("bdinfo_hdt_done", {
                        "ok": False, "error": "Aucune source — sélectionne et scanne d'abord un dossier BDMV"
                    })
                    return

                # Pour la seedbox : chercher en priorité dans FILMS/
                # (le dossier scanné peut être sur un disque externe ou ailleurs)
                folder_name = Path(bdi_folder).name
                films_candidate = BASE_DIR / "FILMS" / folder_name
                if films_candidate.exists() and films_candidate.is_dir():
                    folder = str(films_candidate)
                    self._log(f"  [HDT] Source FILMS/ : {folder}")
                elif Path(bdi_folder).exists():
                    folder = bdi_folder
                    self._log(f"  [HDT] Source (scan) : {folder}")
                else:
                    self._emit("bdinfo_hdt_done", {
                        "ok": False,
                        "error": f"Dossier introuvable dans FILMS/ ni à l'emplacement scanné : {folder_name}"
                    })
                    return

                hdt_announce = os.getenv("TRACKER_HDT", "")
                if not hdt_announce:
                    self._emit("bdinfo_hdt_done", {
                        "ok": False, "error": "TRACKER_HDT non configuré dans le .env"
                    })
                    return

                base          = Path(folder).name
                hdt_sftp_base = os.getenv("SFTP_PATH_HDT", "/home/rtorrent/rtorrent/download/FULL BD")
                hdt_remote_path = hdt_sftp_base.rstrip("/") + "/" + base

                self._log(f"▶ BD Info HDT : {base}")
                self._log(f"  dossier local  : {folder}")
                self._log(f"  seedbox target : {hdt_remote_path}")

                # ── 1. SFTP upload récursif du dossier ─────────────────────────
                try:
                    import paramiko
                except ImportError:
                    import subprocess as _sp
                    _sp.run([sys.executable, "-m", "pip", "install", "paramiko",
                             "--break-system-packages", "--quiet"], capture_output=True)
                    import paramiko  # noqa: F811

                host     = os.getenv("SFTP_HOST_FTP", "")
                port     = int(os.getenv("SFTP_PORT", "22"))
                user     = os.getenv("SFTP_USER", "")
                password = os.getenv("SFTP_PASS", "")

                self._emit("bdinfo_hdt_status", {"msg": f"Connexion SFTP vers {host}…"})
                transport = paramiko.Transport((host, port))
                transport.window_size              = 67108864
                transport.packetizer.REKEY_BYTES   = pow(2, 40)
                transport.packetizer.REKEY_PACKETS = pow(2, 40)
                transport.connect(username=user, password=password)
                sftp = paramiko.SFTPClient.from_transport(transport)
                sftp.MAX_REQUEST_SIZE = 1048576

                self._sftp_upload_folder(sftp, folder, hdt_remote_path)

                sftp.close()
                transport.close()
                self._log("  [SFTP] ✅ Dossier uploadé", "success")

                # ── 2. Créer le torrent et démarrer le seeding ─────────────────
                self._emit("bdinfo_hdt_status", {"msg": "Création torrent HDT…"})
                self._create_torrent_rutorrent(base, hdt_remote_path, {"HDT": hdt_announce}, private=True, auto_start=False)

                self._emit("bdinfo_hdt_done", {
                    "ok": True, "base": base, "path": hdt_remote_path
                })

            except Exception as e:
                import traceback
                traceback.print_exc()
                self._emit("bdinfo_hdt_done", {"ok": False, "error": str(e)})

        threading.Thread(target=_worker, daemon=True).start()
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
        """Upload vers la seedbox. Port 22 → SFTP paramiko. Autre → FTP TLS legacy."""
        import time
        host     = os.getenv("SFTP_HOST_FTP", "")
        port     = int(os.getenv("SFTP_PORT", "22"))
        user     = os.getenv("SFTP_USER", "")
        password = os.getenv("SFTP_PASS", "")

        # ── SFTP via SSH (port 22) ─────────────────────────────────────────────
        if port == 22:
            try:
                import paramiko
            except ImportError:
                import subprocess as _sp
                _sp.run([sys.executable, "-m", "pip", "install", "paramiko",
                         "--break-system-packages", "--quiet"], capture_output=True)
                import paramiko  # noqa: F811

            self._log("Connexion SFTP vers " + host + "…")
            transport = paramiko.Transport((host, port))
            # ── Optimisations débit SFTP ──────────────────────────────────────
            transport.window_size        = 67108864   # 64 MB (défaut 2 MB)
            transport.packetizer.REKEY_BYTES   = pow(2, 40)  # évite rekey en cours d'upload
            transport.packetizer.REKEY_PACKETS = pow(2, 40)
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.MAX_REQUEST_SIZE = 1048576  # paquets 1 MB (défaut 32 KB)

            # Créer le dossier distant récursivement
            parts = remote_path.strip("/").split("/")
            cur = ""
            for part in parts:
                cur += "/" + part
                try:
                    sftp.stat(cur)
                except FileNotFoundError:
                    sftp.mkdir(cur)
                    self._log("Dossier SFTP créé : " + cur)

            for f in files:
                fname    = os.path.basename(f)
                filesize = os.path.getsize(f)
                start    = time.time()
                uploaded = [0]
                last_emit = [0.0]

                size_str = (str(round(filesize / 1073741824, 2)) + " GiB"
                            if filesize > 1073741824
                            else str(round(filesize / 1048576, 1)) + " MiB")
                self._log("Envoi SFTP : " + fname + " (" + size_str + ")…")

                def _progress(sent, total, _f=fname, _fs=filesize, _st=start,
                               _up=uploaded, _le=last_emit):
                    _up[0] = sent
                    now = time.time()
                    if now - _le[0] < 1.0:
                        return
                    _le[0] = now
                    elapsed = now - _st
                    speed = sent / elapsed / 1048576 if elapsed > 0 else 0
                    pct = int(sent * 100 / total) if total > 0 else 0
                    h, r2 = divmod(int(elapsed), 3600)
                    m, s = divmod(r2, 60)
                    e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                    self._emit("upload_progress", {
                        "filename": _f, "pct": pct,
                        "elapsed": e_str + " — " + str(pct) + "% — " + str(round(speed, 1)) + " MB/s"
                    })

                sftp.put(f, remote_path.rstrip("/") + "/" + fname, callback=_progress)

                elapsed = time.time() - start
                h, r2 = divmod(int(elapsed), 3600)
                m, s = divmod(r2, 60)
                e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                self._log("  ✓ " + fname + " — " + e_str, "success")

            sftp.close()
            transport.close()
            return

        # ── FTP TLS legacy (ancien port != 22) ────────────────────────────────
        import ftplib, socket
        self._log("Connexion FTP vers " + host + "...")
        ftp = ftplib.FTP_TLS()
        ftp.connect(host, port)
        ftp.login(user, password)
        ftp.prot_p()
        try:
            ftp.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8 * 1024 * 1024)
        except Exception:
            pass

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

            size_str = (str(round(filesize / 1073741824, 2)) + " GiB"
                        if filesize > 1073741824
                        else str(round(filesize / 1048576, 1)) + " MiB")
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
                h, r2 = divmod(int(elapsed), 3600)
                m, s = divmod(r2, 60)
                e_str = (str(h) + "h " if h else "") + str(m).zfill(2) + "m " + str(s).zfill(2) + "s"
                self._emit("upload_progress", {
                    "filename": fname, "pct": pct,
                    "elapsed": e_str + " — " + str(pct) + "% — " + str(round(speed, 1)) + " MB/s"
                })

            with open(f, "rb") as fh:
                ftp.storbinary("STOR " + fname, fh, 1048576, progress)

            elapsed = time.time() - start
            h, r2 = divmod(int(elapsed), 3600)
            m, s = divmod(r2, 60)
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

    # ──────────────────────────────────────────────────────────────────────────
    # Méthode A : HTTP GET sur le plugin create (aucun accès FTP requis)
    # ──────────────────────────────────────────────────────────────────────────
    def _poll_via_http_api(self, create_url, rt_user, rt_pass, base, timeout=60):
        """Poll l'API HTTP du plugin create ruTorrent.
        GET /plugins/create/action.php → liste des tâches + statut.
        Bail rapide si le plugin retourne toujours [] (ne supporte pas le GET).
        """
        import time
        deadline       = time.time() + timeout
        poll_interval  = 5
        empty_streak   = 0   # nb de polls consécutifs avec liste vide
        MAX_EMPTY      = 3   # abandon si [] 3 fois de suite
        self._log("  [HTTP] Polling create plugin API (max " + str(timeout) + "s)…")

        while time.time() < deadline:
            time.sleep(poll_interval)
            try:
                r = requests.get(create_url, auth=(rt_user, rt_pass),
                                 verify=False, timeout=10)
                self._log("  [HTTP] " + str(r.status_code) + " : " +
                           r.text[:200].replace("\n", " "))

                if r.status_code == 200:
                    try:
                        data  = r.json()
                        tasks = data if isinstance(data, list) else []

                        if not tasks:
                            empty_streak += 1
                            if empty_streak >= MAX_EMPTY:
                                raise Exception(
                                    "GET retourne [] — le plugin create ne supporte "
                                    "pas le polling HTTP, passage à SFTP")
                            continue

                        empty_streak = 0
                        for task in tasks:
                            t_name   = str(task.get("name",     task.get("n",  "")))
                            t_status = str(task.get("status",   task.get("s",  ""))).lower()
                            t_id     = str(task.get("id",       task.get("taskid", "")))
                            t_prog   = str(task.get("progress", task.get("proc", ""))).strip()
                            self._log("  [HTTP] tâche " + t_id + " '" + t_name +
                                      "' status=" + t_status + " prog=" + t_prog)
                            if base.lower() in t_name.lower():
                                done = (t_status in ("done", "finished", "complete", "1") or
                                        t_prog in ("100", "1.0", "1"))
                                if done:
                                    for suffix in [
                                        "?action=download&taskid=" + t_id,
                                        "?download=1&id=" + t_id,
                                        "?id=" + t_id + "&action=getfile",
                                    ]:
                                        try:
                                            dl = requests.get(
                                                create_url + suffix,
                                                auth=(rt_user, rt_pass),
                                                verify=False, timeout=30)
                                            if dl.content and dl.content.lstrip()[:1] == b"d":
                                                self._log("  [HTTP] ✅ .torrent OK ("
                                                          + suffix + ")", "success")
                                                return dl.content
                                            self._log("  [HTTP] " + suffix + " → " +
                                                      dl.content[:80].decode(
                                                          "utf-8", errors="replace"))
                                        except Exception as e_dl:
                                            self._log("  [HTTP] dl err : " + str(e_dl))
                    except Exception as e_j:
                        raise   # re-lève pour le except externe
            except Exception as e:
                self._log("  [HTTP] " + str(e))
                if "ne supporte pas" in str(e):
                    raise   # bail rapide
            poll_interval = min(poll_interval + 3, 30)

        raise Exception("[HTTP] Timeout " + str(timeout) + "s")

    # ──────────────────────────────────────────────────────────────────────────
    # Méthode B : XML-RPC execute.nothrow.bg + FTP (pas de chroot problem)
    # ──────────────────────────────────────────────────────────────────────────
    def _fetch_via_xmlrpc_exec(self, rt_url, rt_user, rt_pass, base,
                               ftp_host, ftp_port, ftp_user, ftp_pass,
                               fb_url="", announce="", remote_path=""):
        """Récupère le .torrent de session via rtorrent XML-RPC + FTP :
        1. download_list + system.multicall(d.name) → hash du torrent
        2. session.path → chemin de la session rtorrent
        3. execute.nothrow.bg cp {session}/{hash}.torrent {home}/rtorrent/temp_{hash16}.torrent
        4. FTP RETR rtorrent/temp_{hash16}.torrent
        5. execute.nothrow.bg rm {dest}  (nettoyage)
        Le répertoire rtorrent/ est accessible via FTP (racine Filebrowser confirmée).
        """
        import time, ftplib, io
        import xmlrpc.client as _xrpc

        rpc_url = rt_url.rstrip("/") + "/plugins/httprpc/action.php"
        self._log("  [XRPC] Attente du torrent dans rtorrent (seeding)…")

        # ── 1. Trouver le hash par nom (retry jusqu'à ce qu'il apparaisse) ──
        found_hash = None
        for attempt in range(24):          # max ~2 min
            time.sleep(5)
            try:
                r = requests.post(
                    rpc_url,
                    data=('<?xml version="1.0"?><methodCall>'
                          '<methodName>download_list</methodName>'
                          '<params><param><value><string></string></value></param>'
                          '</params></methodCall>'),
                    auth=(rt_user, rt_pass), verify=False, timeout=15)
                hashes = _xrpc.loads(r.text)[0][0]
                self._log("  [XRPC] " + str(len(hashes)) + " torrents")

                calls_xml = "".join(
                    '<value><struct>'
                    '<member><name>methodName</name>'
                    '<value><string>d.name</string></value></member>'
                    '<member><name>params</name><value><array><data>'
                    '<value><string>' + h + '</string></value>'
                    '</data></array></value></member>'
                    '</struct></value>'
                    for h in hashes
                )
                r_mc = requests.post(
                    rpc_url,
                    data=('<?xml version="1.0"?><methodCall>'
                          '<methodName>system.multicall</methodName><params>'
                          '<param><value><array><data>'
                          + calls_xml +
                          '</data></array></value></param>'
                          '</params></methodCall>'),
                    auth=(rt_user, rt_pass), verify=False, timeout=30)
                results = _xrpc.loads(r_mc.text)[0][0]
                for i, h in enumerate(hashes):
                    try:
                        name = (results[i][0]
                                if isinstance(results[i], (list, tuple))
                                else results[i])
                        if base.lower() in name.lower():
                            found_hash = h
                            self._log("  [XRPC] hash : " + h + " (" + name + ")")
                            break
                    except Exception:
                        pass
                if found_hash:
                    break
            except Exception as e_xrpc:
                self._log("  [XRPC] tentative " + str(attempt + 1) + " : " + str(e_xrpc))

        if not found_hash:
            raise Exception("[XRPC] hash non trouvé pour '" + base + "'")

        # ── 2. session.path ──────────────────────────────────────────────────
        try:
            r_sp = requests.post(
                rpc_url,
                data=('<?xml version="1.0"?><methodCall>'
                      '<methodName>session.path</methodName>'
                      '<params></params></methodCall>'),
                auth=(rt_user, rt_pass), verify=False, timeout=10)
            session_path = _xrpc.loads(r_sp.text)[0][0].rstrip("/")
            self._log("  [XRPC] session : " + session_path)
        except Exception as e_sp:
            raise Exception("[XRPC] session.path : " + str(e_sp))

        # Dériver le home utilisateur depuis session_path
        # Ex : /sdc/wydg/config/rtorrent/rtorrent_sess → home = /sdc/wydg
        parts = session_path.strip("/").split("/")
        home = ""
        for i, p in enumerate(parts):
            if p.lower() in ("config", ".config"):
                home = "/" + "/".join(parts[:i])
                break
        if not home:
            home = "/" + "/".join(parts[:2])

        # ── 2b. d.base_path → répertoire réel du contenu sur le serveur ─────
        base_path_srv = ""
        try:
            r_bp = requests.post(
                rpc_url,
                data=('<?xml version="1.0"?><methodCall>'
                      '<methodName>d.base_path</methodName>'
                      '<params><param><value><string>' + found_hash
                      + '</string></value></param></params></methodCall>'),
                auth=(rt_user, rt_pass), verify=False, timeout=10)
            base_path_srv = _xrpc.loads(r_bp.text)[0][0]
            self._log("  [XRPC] d.base_path : " + base_path_srv)
        except Exception as e_bp:
            self._log("  [XRPC] d.base_path : " + str(e_bp))

        # ── 2c. d.tied_to_file → chemin exact du .torrent chargé ────────────
        tied_file = ""
        try:
            r_ttf = requests.post(
                rpc_url,
                data=('<?xml version="1.0"?><methodCall>'
                      '<methodName>d.tied_to_file</methodName>'
                      '<params><param><value><string>' + found_hash
                      + '</string></value></param></params></methodCall>'),
                auth=(rt_user, rt_pass), verify=False, timeout=10)
            tied_file = _xrpc.loads(r_ttf.text)[0][0]
            self._log("  [XRPC] d.tied_to_file : " + (tied_file or "(vide)"))
        except Exception as e_ttf:
            self._log("  [XRPC] d.tied_to_file : " + str(e_ttf))

        tmp_name = "temp_" + found_hash[:16] + ".torrent"
        # Destination dans tmp/ (accessible via FTP et Filebrowser)
        tmp_dest = home.rstrip("/") + "/tmp/" + tmp_name
        self._log("  [XRPC] home=" + home + "  tmp_dest=" + tmp_dest)

        # Helper : échappement XML (& → &amp; pour éviter -503 malformed XML)
        def _xe(s):
            return (s.replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;"))

        def _exec_sh(cmd_str, label="sh"):
            """Lance /bin/sh -c cmd_str via execute.nothrow.bg.
            Retourne True si HTTP 200 sans fault XML."""
            cmd_xml = _xe(cmd_str)
            self._log("  [XRPC] " + label + " : " + cmd_str[:120])
            for exec_method in ("execute.nothrow.bg", "execute.nothrow"):
                for with_target in (True, False):
                    try:
                        target_xml = ('<param><value><string></string></value></param>'
                                      if with_target else "")
                        r = requests.post(
                            rpc_url,
                            data=('<?xml version="1.0"?><methodCall>'
                                  '<methodName>' + exec_method + '</methodName><params>'
                                  + target_xml +
                                  '<param><value><string>/bin/sh</string></value></param>'
                                  '<param><value><string>-c</string></value></param>'
                                  '<param><value><string>' + cmd_xml
                                  + '</string></value></param>'
                                  '</params></methodCall>'),
                            auth=(rt_user, rt_pass), verify=False, timeout=30)
                        resp = r.text[:200].replace("\n", " ")
                        self._log("  [XRPC] " + exec_method
                                  + (" +t" if with_target else "")
                                  + " → HTTP " + str(r.status_code) + " " + resp)
                        if r.status_code == 200 and "<fault>" not in r.text:
                            return True
                    except Exception as e_sh:
                        self._log("  [XRPC] " + exec_method + " : " + str(e_sh))
            return False

        # ── 3a. mktorrent direct → tmp/temp_HASH.torrent ────────────────────
        # Créer le .torrent directement dans tmp/ (accessible FTP+FB) sans
        # passer par la session rtorrent. L'announce ne modifie pas l'infohash.
        exec_ok = False
        if announce and base_path_srv:
            # Source = base_path_srv (répertoire ou fichier du contenu)
            # Si c'est un fichier, prendre le parent (pour nom correct)
            import os as _os
            content_dir = (base_path_srv if _os.path.basename(base_path_srv) == base
                           else _os.path.dirname(base_path_srv) or base_path_srv)
            for mkt_bin in ("/usr/bin/mktorrent", "/usr/local/bin/mktorrent",
                            "/bin/mktorrent"):
                mkt_cmd = ("{mkt} -o '{out}' -a '{ann}' -l 22 -p '{src}'"
                           .format(mkt=mkt_bin, out=tmp_dest,
                                   ann=announce, src=base_path_srv))
                exec_ok = _exec_sh(mkt_cmd, "mktorrent")
                if exec_ok:
                    break

        # ── 3b. cp+chmod depuis tied_to_file ou session → tmp/ ──────────────
        if not exec_ok:
            src_session = session_path + "/" + found_hash + ".torrent"
            sources = []
            if tied_file:
                sources.append(tied_file)
            sources.append(src_session)
            for src in sources:
                cp_cmd = ("cp '{s}' '{d}' && chmod 644 '{d}'"
                          .format(s=src, d=tmp_dest))
                exec_ok = _exec_sh(cp_cmd, "cp")
                if exec_ok:
                    break

        if not exec_ok:
            self._log("  [XRPC] ⚠ toutes les méthodes execute ont échoué", "warn")

        def _cleanup_exec():
            """Supprime le fichier temporaire via execute.nothrow.bg."""
            try:
                _exec_sh("rm -f '" + tmp_dest + "'", "cleanup")
            except Exception:
                pass

        # ── 4. FTP RETR — essaie tmp/ en priorité puis rtorrent/ et watch/ ──
        # tmp/ est le répertoire de sortie de mktorrent, rtorrent/ est le fallback.
        ftp_dirs_to_try = ["tmp"]
        for extra in ["rtorrent", "watch", ""]:
            if extra not in ftp_dirs_to_try:
                ftp_dirs_to_try.append(extra)

        for wait_s in (3, 5, 8, 12):
            time.sleep(wait_s)
            ftp = None
            for try_dir in ftp_dirs_to_try:
                try:
                    ftp = ftplib.FTP_TLS()
                    ftp.connect(ftp_host, ftp_port, timeout=15)
                    ftp.login(ftp_user, ftp_pass)
                    ftp.prot_p()
                    if try_dir:
                        for part in [x for x in try_dir.split("/") if x]:
                            ftp.cwd(part)
                    # NLST
                    try:
                        nlst = ftp.nlst()
                        has_file = any(tmp_name in f for f in nlst)
                        self._log("  [XRPC] FTP " + (try_dir or "/") + "/ NLST : "
                                  + str(len(nlst)) + " entrées, présent=" + str(has_file))
                        if not has_file:
                            ftp.quit(); ftp = None; continue
                    except Exception as e_nlst:
                        self._log("  [XRPC] NLST " + (try_dir or "/") + " : " + str(e_nlst))
                    buf = io.BytesIO()
                    ftp.retrbinary("RETR " + tmp_name, buf.write)
                    ftp.quit(); ftp = None
                    data = buf.getvalue()
                    if data and data.lstrip()[:1] == b"d":
                        self._log("  [XRPC] ✅ FTP " + (try_dir or "/")
                                  + " OK (" + str(len(data)) + " o)", "success")
                        _cleanup_exec()
                        return data
                    self._log("  [XRPC] FTP non-bencoded (" + str(len(data)) + " o)")
                except Exception as e_ftp:
                    self._log("  [XRPC] FTP " + (try_dir or "/") + " wait="
                              + str(wait_s) + "s : " + str(e_ftp))
                finally:
                    if ftp:
                        try: ftp.quit()
                        except Exception: pass
                        ftp = None

        # ── 4b. Fallback Filebrowser API — essaie tmp/ et rtorrent/ ─────────
        if fb_url:
            self._log("  [XRPC] Fallback Filebrowser : " + fb_url)
            try:
                r_login = requests.post(
                    fb_url.rstrip("/") + "/api/login",
                    json={"username": ftp_user, "password": ftp_pass},
                    verify=False, timeout=15)
                if r_login.status_code == 200:
                    fb_token = r_login.text.strip().strip('"')
                    for fb_dir in ["tmp", "rtorrent"]:
                        fb_path = "/" + fb_dir + "/" + tmp_name
                        r_dl = requests.get(
                            fb_url.rstrip("/") + "/api/raw" + fb_path,
                            headers={"X-Auth": fb_token},
                            params={"auth": fb_token},
                            verify=False, timeout=30)
                        self._log("  [XRPC] FB GET " + fb_path
                                  + " → HTTP " + str(r_dl.status_code))
                        if r_dl.status_code == 200:
                            fb_data = r_dl.content
                            if fb_data and fb_data.lstrip()[:1] == b"d":
                                self._log("  [XRPC] ✅ Filebrowser OK ("
                                          + str(len(fb_data)) + " o)", "success")
                                _cleanup_exec()
                                return fb_data
                            self._log("  [XRPC] FB non-bencoded ("
                                      + str(len(fb_data)) + " o)")
                else:
                    self._log("  [XRPC] FB login : HTTP " + str(r_login.status_code))
            except Exception as e_fb:
                self._log("  [XRPC] FB fallback : " + str(e_fb))

        # ── 4c. Fallback FTP direct session rtorrent_sess/HASH.torrent ───────
        sess_rel = session_path.strip("/")
        home_rel = home.strip("/")
        if sess_rel.startswith(home_rel + "/"):
            sess_rel = sess_rel[len(home_rel) + 1:]
        torrent_filename = found_hash + ".torrent"
        self._log("  [XRPC] Fallback FTP session : " + sess_rel + "/" + torrent_filename)
        ftp2 = None
        try:
            ftp2 = ftplib.FTP_TLS()
            ftp2.connect(ftp_host, ftp_port, timeout=15)
            ftp2.login(ftp_user, ftp_pass)
            ftp2.prot_p()
            for part in [x for x in sess_rel.split("/") if x]:
                ftp2.cwd(part)
            buf2 = io.BytesIO()
            ftp2.retrbinary("RETR " + torrent_filename, buf2.write)
            ftp2.quit(); ftp2 = None
            data2 = buf2.getvalue()
            if data2 and data2.lstrip()[:1] == b"d":
                self._log("  [XRPC] ✅ FTP session OK (" + str(len(data2)) + " o)", "success")
                return data2
            self._log("  [XRPC] FTP session non-bencoded (" + str(len(data2)) + " o)")
        except Exception as e_fs:
            self._log("  [XRPC] FTP session : " + str(e_fs))
        finally:
            if ftp2:
                try: ftp2.quit()
                except Exception: pass

        raise Exception("[XRPC] impossible de télécharger " + tmp_name)

    # ──────────────────────────────────────────────────────────────────────────
    # Méthode C : Filebrowser API (HTTP, aucune dépendance supplémentaire)
    # ──────────────────────────────────────────────────────────────────────────
    def _poll_via_filebrowser(self, fb_url, fb_user, fb_pass, rt_user,
                              before_ts, timeout=600):
        """Récupère temp.torrent via l'API du Filebrowser (seedbox web).
        POST /api/login → JWT token
        Découverte automatique du chemin tasks/ depuis la racine FB.
        """
        import time
        fb_base       = fb_url.rstrip("/")
        deadline      = time.time() + timeout
        poll_interval = 5

        self._log("  [FB] Filebrowser API : " + fb_base)

        # ── Authentification ────────────────────────────────────────────────
        try:
            r_login = requests.post(
                fb_base + "/api/login",
                json={"username": fb_user, "password": fb_pass},
                verify=False, timeout=10
            )
            self._log("  [FB] login : HTTP " + str(r_login.status_code))
            if r_login.status_code != 200:
                raise Exception("Login échoué : " + str(r_login.status_code))
            token = r_login.text.strip().strip('"')
            self._log("  [FB] token OK (" + str(len(token)) + " chars)")
        except Exception as e_login:
            raise Exception("[FB] " + str(e_login))

        headers = {"X-Auth": token}

        # ── Découverte de la racine Filebrowser ─────────────────────────────
        # Le FB peut être chroot à différents niveaux.
        # On liste la racine et on tente plusieurs chemins candidats.
        tasks_path = None
        try:
            r_root = requests.get(fb_base + "/api/resources/",
                                  headers=headers, verify=False, timeout=10)
            self._log("  [FB] racine HTTP " + str(r_root.status_code))
            if r_root.status_code == 200:
                root_items = [i.get("name", "") for i in r_root.json().get("items", [])]
                self._log("  [FB] racine : " + str(root_items[:15]))
        except Exception as e_root:
            self._log("  [FB] racine : " + str(e_root))

        # Chemin absolu connu : /sdc/wydg/config/rutorrent/share/users/{user}/settings/tasks
        # Candidats selon la racine du FB (skip des préfixes)
        tail = "config/rutorrent/share/users/" + rt_user + "/settings/tasks"
        candidates = [
            tail,                                              # FB root = /sdc/wydg/
            "sdc/" + rt_user + "/" + tail,                    # FB root = /
            rt_user + "/" + tail,                              # FB root = /sdc/
            tail.replace("config/rutorrent", ".config/rutorrent"),
        ]

        for cand in candidates:
            try:
                r_test = requests.get(fb_base + "/api/resources/" + cand + "/",
                                      headers=headers, verify=False, timeout=8)
                self._log("  [FB] test " + cand + " → HTTP " + str(r_test.status_code))
                if r_test.status_code == 200:
                    tasks_path = cand
                    self._log("  [FB] tasks path trouvé : " + tasks_path)
                    break
            except Exception as e_cand:
                self._log("  [FB] " + cand + " : " + str(e_cand))

        if not tasks_path:
            raise Exception("[FB] Impossible de localiser tasks/ — racine FB inconnue")

        self._log("  [FB] polling " + tasks_path + "/ …")

        while time.time() < deadline:
            time.sleep(poll_interval)
            try:
                r_ls = requests.get(fb_base + "/api/resources/" + tasks_path + "/",
                                    headers=headers, verify=False, timeout=10)
                if r_ls.status_code != 200:
                    self._log("  [FB] ls " + str(r_ls.status_code))
                    poll_interval = min(poll_interval + 5, 30)
                    continue

                items     = r_ls.json().get("items", [])
                new_tasks = sorted(
                    [i.get("name", "") for i in items if i.get("isDir", False)],
                    reverse=True
                )
                self._log("  [FB] " + str(len(new_tasks)) + " tâches")

                if not new_tasks:
                    self._log("  [FB] Attente… (" +
                              str(int(deadline - time.time())) + "s restantes)")
                    poll_interval = min(poll_interval + 2, 20)
                    continue

                for task_id in new_tasks:
                    raw_url = (fb_base + "/api/raw/" + tasks_path + "/"
                               + task_id + "/temp.torrent")
                    try:
                        dl = requests.get(raw_url, headers=headers,
                                          verify=False, timeout=30)
                        self._log("  [FB] tâche " + task_id + " : HTTP " +
                                  str(dl.status_code) + " (" +
                                  str(len(dl.content)) + " o)")
                        if dl.content and dl.content.lstrip()[:1] == b"d":
                            self._log("  [FB] ✅ temp.torrent OK — tâche "
                                      + task_id + " (" + str(len(dl.content))
                                      + " o)", "success")
                            return dl.content
                        if dl.status_code == 200 and len(dl.content) < 10:
                            self._log("  [FB] tâche " + task_id + " : hashage en cours…")
                    except Exception as e_dl:
                        self._log("  [FB] tâche " + task_id + " dl : " + str(e_dl))
                    break

            except Exception as e:
                self._log("  [FB] erreur : " + str(e))
            poll_interval = min(poll_interval + 3, 30)

        raise Exception("[FB] Timeout " + str(timeout) + "s")

    # ──────────────────────────────────────────────────────────────────────────
    # Méthode C : SFTP via paramiko (SSH, pas de chroot FTP)
    # ──────────────────────────────────────────────────────────────────────────
    def _poll_via_sftp(self, ssh_host, ssh_port, sftp_user, sftp_pass,
                       rt_user, before_ts, timeout=600):
        """Récupère temp.torrent via SFTP (SSH) — accès illimité au filesystem.
        Chemin : {home}/config/rutorrent/share/users/{rt_user}/settings/tasks/
        """
        try:
            import paramiko
        except ImportError:
            self._log("  [SFTP] paramiko absent — installation automatique…")
            import subprocess, sys
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "paramiko",
                     "--break-system-packages", "--quiet"],
                    check=True, capture_output=True
                )
            except subprocess.CalledProcessError:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "paramiko", "--quiet"],
                    check=True, capture_output=True
                )
            import paramiko   # noqa: F811
            self._log("  [SFTP] paramiko installé ✓")

        import time, io
        deadline     = time.time() + timeout
        poll_interval = 5
        self._log("  [SFTP] SSH " + ssh_host + ":" + str(ssh_port) + "…")

        while time.time() < deadline:
            time.sleep(poll_interval)
            transport = None
            try:
                transport = paramiko.Transport((ssh_host, ssh_port))
                transport.connect(username=sftp_user, password=sftp_pass)
                sftp      = paramiko.SFTPClient.from_transport(transport)
                home      = sftp.normalize(".")
                tasks_dir = (home + "/config/rutorrent/share/users/"
                             + rt_user + "/settings/tasks")
                self._log("  [SFTP] tasks dir : " + tasks_dir)

                try:
                    all_ids = sftp.listdir(tasks_dir)
                except Exception as e_ls:
                    self._log("  [SFTP] listdir : " + str(e_ls))
                    transport.close()
                    poll_interval = min(poll_interval + 3, 30)
                    continue

                new_tasks = []
                for tid in all_ids:
                    try:
                        st = sftp.stat(tasks_dir + "/" + tid)
                        if st.st_mtime >= before_ts - 60:
                            new_tasks.append(tid)
                    except Exception:
                        pass

                if not new_tasks:
                    self._log("  [SFTP] Attente… (" +
                              str(int(deadline - time.time())) + "s restantes)")
                    transport.close()
                    transport = None
                    poll_interval = min(poll_interval + 2, 20)
                    continue

                for task_id in sorted(new_tasks, reverse=True):
                    task_file = tasks_dir + "/" + task_id + "/temp.torrent"
                    try:
                        st = sftp.stat(task_file)
                        if st.st_size > 100:
                            buf = io.BytesIO()
                            with sftp.file(task_file, "rb") as f:
                                buf.write(f.read())
                            data = buf.getvalue()
                            if data and data.lstrip()[:1] == b"d":
                                transport.close()
                                self._log("  [SFTP] ✅ temp.torrent OK — tâche "
                                          + task_id + " (" + str(len(data)) + " o)",
                                          "success")
                                return data
                        self._log("  [SFTP] tâche " + task_id + " : " +
                                  str(st.st_size) + " o (hashage en cours…)")
                    except IOError:
                        self._log("  [SFTP] tâche " + task_id +
                                  " : temp.torrent pas encore créé")
                    break

            except Exception as e:
                self._log("  [SFTP] erreur : " + str(e))
            finally:
                if transport:
                    try:
                        transport.close()
                    except Exception:
                        pass
            poll_interval = min(poll_interval + 3, 30)

        raise Exception("[SFTP] Timeout " + str(timeout) + "s")

    # ──────────────────────────────────────────────────────────────────────────
    # Méthode C : FTP tasks dir (chemin configurable via RUTORRENT_TASKS_PATH)
    # ──────────────────────────────────────────────────────────────────────────
    def _poll_via_ftp_tasks(self, ftp_host, ftp_port, ftp_user, ftp_pass,
                            tasks_rel_path, before_tasks, timeout=600):
        """Récupère temp.torrent via FTP depuis un chemin configuré manuellement.
        Configurer RUTORRENT_TASKS_PATH dans le .env (ex: config/rutorrent/share/users/wydg/settings/tasks)
        """
        import ftplib, io, time
        parts = [p for p in tasks_rel_path.strip("/").split("/") if p]
        deadline = time.time() + timeout
        poll_interval = 5
        self._log("  [FTP] Polling " + tasks_rel_path + "…")

        while time.time() < deadline:
            time.sleep(poll_interval)
            ftp = None
            try:
                ftp = ftplib.FTP_TLS()
                ftp.connect(ftp_host, ftp_port, timeout=15)
                ftp.login(ftp_user, ftp_pass)
                ftp.prot_p()
                for p in parts:
                    ftp.cwd(p)

                current   = set(e for e in ftp.nlst() if e not in (".", ".."))
                new_tasks = current - before_tasks

                if not new_tasks:
                    self._log("  [FTP] Attente… (" +
                              str(int(deadline - time.time())) + "s restantes)")
                    try:
                        ftp.quit()
                    except Exception:
                        pass
                    ftp = None
                    poll_interval = min(poll_interval + 2, 20)
                    continue

                for task_id in sorted(new_tasks, reverse=True):
                    try:
                        ftp.cwd(task_id)
                        buf = io.BytesIO()
                        ftp.retrbinary("RETR temp.torrent", buf.write)
                        data = buf.getvalue()
                        if data and data.lstrip()[:1] == b"d":
                            try:
                                ftp.quit()
                            except Exception:
                                pass
                            ftp = None
                            self._log("  [FTP] ✅ temp.torrent OK — tâche " + task_id +
                                      " (" + str(len(data)) + " o)", "success")
                            return data
                        self._log("  [FTP] tâche " + task_id + " : " +
                                  str(len(data)) + " o (hashage en cours…)")
                    except Exception as et:
                        self._log("  [FTP] tâche " + task_id + " : " + str(et))
                    break

            except Exception as e:
                self._log("  [FTP] erreur : " + str(e))
            finally:
                if ftp:
                    try:
                        ftp.quit()
                    except Exception:
                        pass
            poll_interval = min(poll_interval + 3, 30)

        raise Exception("[FTP] Timeout " + str(timeout) + "s")

    # ──────────────────────────────────────────────────────────────────────────
    # Méthode F : Création locale du .torrent par streaming FTP (fallback ultime)
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _bencode(obj):
        """Encodage bencode minimal (bytes/str/int/list/dict)."""
        if isinstance(obj, bytes):
            return str(len(obj)).encode() + b":" + obj
        if isinstance(obj, str):
            enc = obj.encode("utf-8")
            return str(len(enc)).encode() + b":" + enc
        if isinstance(obj, int):
            return b"i" + str(obj).encode() + b"e"
        if isinstance(obj, list):
            return b"l" + b"".join(API._bencode(i) for i in obj) + b"e"
        if isinstance(obj, dict):
            # Les clés doivent être triées en tant que bytes (standard bencode)
            def _key_bytes(k):
                return k if isinstance(k, bytes) else k.encode("utf-8")
            items = sorted(obj.items(), key=lambda x: _key_bytes(x[0]))
            return b"d" + b"".join(
                API._bencode(k) + API._bencode(v) for k, v in items
            ) + b"e"
        raise TypeError("_bencode: type non supporté : " + type(obj).__name__)

    def _ftp_list_recursive(self, ftp, ftp_abs_path):
        """Liste récursivement les fichiers sous ftp_abs_path.
        Retourne liste de (rel_path, ftp_abs_path, size) triée par rel_path.
        Essaie MLSD en premier, fallback NLST + SIZE.
        """
        results = []

        def _recurse(abs_dir, rel_prefix):
            # ── Essai MLSD (RFC 3659, métadonnées fiables) ──────────────────
            try:
                entries = list(ftp.mlsd(abs_dir, ["type", "size"]))
                for fname, facts in entries:
                    if fname in (".", ".."):
                        continue
                    rel = (rel_prefix + "/" + fname).lstrip("/") if rel_prefix else fname
                    full = abs_dir.rstrip("/") + "/" + fname
                    ftype = facts.get("type", "file")
                    if ftype == "dir":
                        _recurse(full, rel)
                    else:
                        size = int(facts.get("size", 0))
                        results.append((rel, full, size))
                return
            except Exception:
                pass

            # ── Fallback NLST ────────────────────────────────────────────────
            try:
                items = ftp.nlst(abs_dir)
            except Exception as e_nl:
                self._log("  [LOCAL] NLST " + abs_dir + " : " + str(e_nl))
                return

            for item in items:
                fname = item.rstrip("/").split("/")[-1]
                if fname in (".", ".."):
                    continue
                rel = (rel_prefix + "/" + fname).lstrip("/") if rel_prefix else fname
                full = abs_dir.rstrip("/") + "/" + fname
                # Tenter CWD pour détecter dossier
                try:
                    ftp.cwd(full)
                    ftp.cwd("/")            # revenir à la racine
                    _recurse(full, rel)
                except Exception:
                    size = 0
                    try:
                        size = ftp.size(full)
                    except Exception:
                        pass
                    results.append((rel, full, size))

        _recurse(ftp_abs_path, "")
        results.sort(key=lambda x: x[0])
        return results

    # ──────────────────────────────────────────────────────────────────────────
    # Méthode SSH : mktorrent côté seedbox + SFTP + chargement ruTorrent
    # ──────────────────────────────────────────────────────────────────────────
    def _create_torrent_via_ssh(self, base, remote_path, announce, private, tk_name, auto_start=True):
        """Crée un torrent via SSH+mktorrent directement sur la seedbox.
        1. SSH connect (paramiko)
        2. Vérifie/installe mktorrent
        3. Lance mktorrent sur le chemin distant
        4. SFTP download du .torrent
        5. HTTP upload dans ruTorrent pour seeding immédiat
        """
        try:
            import paramiko
        except ImportError:
            self._log("  [SSH] paramiko absent — installation…")
            import subprocess as _sp
            _sp.run([sys.executable, "-m", "pip", "install", "paramiko",
                     "--break-system-packages", "--quiet"],
                    capture_output=True)
            import paramiko  # noqa: F811

        import io, urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        ssh_host = os.getenv("SFTP_HOST_FTP", "")
        ssh_port = int(os.getenv("SFTP_PORT", "22"))
        ssh_user = os.getenv("SFTP_USER", "")
        ssh_pass = os.getenv("SFTP_PASS", "")
        rt_url   = os.getenv("RUTORRENT_URL", "")
        rt_user  = os.getenv("RUTORRENT_USER", "")
        rt_pass  = os.getenv("RUTORRENT_PASS", "")

        if not ssh_host or not ssh_user:
            raise Exception("SSH non configuré (SFTP_HOST_FTP / SFTP_USER)")

        tmp_remote = f"/tmp/{base}__{tk_name}.torrent"

        # ── 1. Connexion SSH ───────────────────────────────────────────────────
        self._log(f"  [SSH] Connexion {ssh_user}@{ssh_host}:{ssh_port}…")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ssh_host, port=ssh_port,
                       username=ssh_user, password=ssh_pass,
                       timeout=30, allow_agent=False, look_for_keys=False)
        self._log("  [SSH] Connecté ✓")

        def _exec(cmd, timeout=300):
            _, out, err = client.exec_command(cmd, timeout=timeout)
            o = out.read().decode("utf-8", errors="replace").strip()
            e = err.read().decode("utf-8", errors="replace").strip()
            return o, e

        # ── 2. Vérifier/installer mktorrent ───────────────────────────────────
        mk_path, _ = _exec("which mktorrent")
        if not mk_path:
            self._log("  [SSH] mktorrent absent — installation en cours…")
            o, e = _exec("sudo apt-get install -y mktorrent 2>&1", timeout=120)
            self._log("  [SSH] " + (o or e)[:300])
            mk_path, _ = _exec("which mktorrent")
            if not mk_path:
                raise Exception("mktorrent introuvable même après tentative d'installation")
        self._log(f"  [SSH] mktorrent : {mk_path}")

        # ── 3. Lancer mktorrent ───────────────────────────────────────────────
        # -s (source) rend l'info hash unique par tracker et permet le
        # cross-seeding immédiat si le tracker utilise ce champ pour matcher.
        SOURCE_TAGS = {
            "TOS":    "TheOldSchool",
            "ABN":    "ABN",
            "C411":   "C411",
            "TORR9":  "Torr9",
            "LACALE": "LaCale",
            "HDT":    "HD-Torrents",
        }
        source_tag = SOURCE_TAGS.get(tk_name.upper(), tk_name)
        priv_flag = "-p " if private else ""
        cmd = (f"mktorrent {priv_flag}-l 22 "
               f"-a '{announce}' "
               f"-s '{source_tag}' "
               f"-o '{tmp_remote}' "
               f"'{remote_path}' 2>&1")
        self._log(f"  [SSH] {cmd}")
        o, _ = _exec(cmd, timeout=600)
        if o:
            self._log("  [SSH] " + o[:400])

        # ── 4. SFTP download du .torrent (sans supprimer — gardé pour rtxmlrpc) ──
        sftp = client.open_sftp()
        try:
            try:
                st = sftp.stat(tmp_remote)
            except FileNotFoundError:
                raise Exception(f"mktorrent n'a pas produit de fichier → {tmp_remote}")
            if st.st_size < 64:
                raise Exception(f"Fichier .torrent trop petit ({st.st_size} o) — échec mktorrent")
            buf = io.BytesIO()
            sftp.getfo(tmp_remote, buf)
            torrent_bytes = buf.getvalue()
        finally:
            sftp.close()
        # Ne pas fermer client ici — on en a besoin pour rtxmlrpc (step 5)

        if not torrent_bytes or torrent_bytes.lstrip()[:1] != b"d":
            _exec(f"rm -f '{tmp_remote}'")
            client.close()
            raise Exception("Contenu .torrent invalide (pas bencoded)")
        self._log(f"  [SSH] ✅ .torrent OK — {len(torrent_bytes):,} octets")

        # ── 5. Charger dans rtorrent ──────────────────────────────────────────
        # Stratégie : rtxmlrpc via SSH (SCGI direct, aucun proxy PHP)
        # → les slashes du chemin ne sont jamais touchés.
        # Fallback : HTTP XML-RPC via ruTorrent /RPC2 si rtxmlrpc absent.
        import hashlib as _hl, time as _t

        # Chemin parent via opération string pure (Path() sur Windows convertit en \)
        parent_dir = remote_path.rstrip("/").rsplit("/", 1)[0] or "/"

        # ── Extraire l'info hash (SHA1 du dict info bencoded) ─────────────────
        def _info_hash(tb):
            marker = b"4:info"
            idx = tb.find(marker)
            if idx < 0:
                return None
            pos = idx + len(marker)
            if tb[pos:pos+1] != b"d":
                return None
            depth = 0
            while pos < len(tb):
                c = chr(tb[pos])
                if c in ("d", "l"):
                    depth += 1; pos += 1
                elif c == "e":
                    depth -= 1; pos += 1
                    if depth == 0:
                        break
                elif c == "i":
                    pos = tb.index(b"e", pos + 1) + 1
                elif c.isdigit():
                    colon = tb.index(b":", pos)
                    slen  = int(tb[pos:colon])
                    pos   = colon + 1 + slen
                else:
                    return None
            return _hl.sha1(tb[idx + len(marker):pos]).hexdigest().upper()

        info_hash = _info_hash(torrent_bytes)
        self._log(f"  [SSH] info_hash = {info_hash or '(erreur)'}")

        # ── Détection de rtxmlrpc ──────────────────────────────────────────────
        rxtool, _ = _exec("which rtxmlrpc 2>/dev/null || echo ''")
        rxtool = rxtool.strip()
        self._log(f"  [SSH] rtxmlrpc = {rxtool or '(absent)'}")

        loaded_ok = False

        if rxtool and info_hash:
            try:
                # 5a. Charger sans démarrer (load.normal = load sans start)
                o, e = _exec(f"{rxtool} load.normal '' '{tmp_remote}'", timeout=30)
                self._log(f"  [SSH] rtxmlrpc load.normal → {(o or e or 'ok')[:200]}")

                _t.sleep(1)  # rtorrent enregistre le torrent

                # 5b. Définir le répertoire — SCGI direct, aucune sanitisation
                o, e = _exec(
                    f"{rxtool} d.directory.set {info_hash} '{parent_dir}'", timeout=10)
                self._log(f"  [SSH] rtxmlrpc d.directory.set → {(o or e or 'ok')[:200]}")
                self._log(f"  [SSH] directory = {parent_dir}")

                # 5c. Démarrer le seeding (optionnel)
                if auto_start:
                    o, e = _exec(f"{rxtool} d.start {info_hash}", timeout=10)
                    self._log(f"  [SSH] rtxmlrpc d.start → {(o or e or 'ok')[:200]}")
                    self._log("  [SSH] ✅ Torrent chargé et seeding démarré", "success")
                else:
                    self._log("  [SSH] ✅ Torrent chargé (en pause — seed manuel requis)", "success")

                loaded_ok = True

            except Exception as e_rxt:
                self._log(f"  [SSH] ⚠ rtxmlrpc : {e_rxt}", "warn")

        if not loaded_ok and rt_url:
            # Fallback HTTP XML-RPC via ruTorrent /RPC2
            # Note : le proxy PHP peut modifier les slashes du chemin —
            # si le répertoire est toujours mauvais, vérifier que rtxmlrpc est dispo.
            self._log("  [ruT] Fallback HTTP XML-RPC…", "warn")
            try:
                import base64 as _b64
                torrent_b64 = _b64.b64encode(torrent_bytes).decode()
                rpc_url   = rt_url.rstrip("/") + "/RPC2"
                ct        = {"Content-Type": "text/xml"}
                auth_pair = (rt_user, rt_pass)

                xml_load = (
                    '<?xml version="1.0"?>'
                    '<methodCall><methodName>load.raw</methodName>'
                    '<params>'
                    '<param><value><string></string></value></param>'
                    f'<param><value><base64>{torrent_b64}</base64></value></param>'
                    '<param><value><string>d.custom1.set=REBiRTH</string></value></param>'
                    '</params></methodCall>'
                )
                resp_load = requests.post(rpc_url, data=xml_load, headers=ct,
                                          auth=auth_pair, verify=False, timeout=30)
                self._log(f"  [ruT] load.raw → HTTP {resp_load.status_code}")
                _t.sleep(1)

                if info_hash:
                    xml_dir = (
                        '<?xml version="1.0"?>'
                        '<methodCall><methodName>d.directory.set</methodName>'
                        '<params>'
                        f'<param><value><string>{info_hash}</string></value></param>'
                        f'<param><value><string>{parent_dir}</string></value></param>'
                        '</params></methodCall>'
                    )
                    resp_dir = requests.post(rpc_url, data=xml_dir, headers=ct,
                                             auth=auth_pair, verify=False, timeout=10)
                    self._log(f"  [ruT] d.directory.set → HTTP {resp_dir.status_code} — {parent_dir}")

                    if auto_start:
                        xml_start = (
                            '<?xml version="1.0"?>'
                            '<methodCall><methodName>d.start</methodName>'
                            '<params>'
                            f'<param><value><string>{info_hash}</string></value></param>'
                            '</params></methodCall>'
                        )
                        resp_start = requests.post(rpc_url, data=xml_start, headers=ct,
                                                   auth=auth_pair, verify=False, timeout=10)
                        self._log(f"  [ruT] d.start → HTTP {resp_start.status_code}")
                    else:
                        self._log("  [ruT] d.start ignoré (auto_start=False — seed manuel requis)")

            except Exception as e_rut:
                self._log(f"  [ruT] ⚠ : {e_rut}", "warn")

        # Suppression du fichier tmp sur la seedbox
        _exec(f"rm -f '{tmp_remote}'")
        client.close()

        return torrent_bytes

    def _create_torrent_local_ftp(self, ftp_host, ftp_port, ftp_user, ftp_pass,
                                  ftp_content_path, name, announce,
                                  piece_size=4194304, private=True):
        """Crée un .torrent localement en streamant le contenu via FTP TLS.
        Parcourt ftp_content_path, calcule les SHA1 pièce par pièce sans tout
        stocker en mémoire. Retourne les octets bencoded du .torrent.
        """
        import ftplib, hashlib

        self._log("  [LOCAL] Streaming FTP → " + ftp_content_path)

        ftp = ftplib.FTP_TLS()
        ftp.connect(ftp_host, ftp_port, timeout=30)
        ftp.login(ftp_user, ftp_pass)
        ftp.prot_p()

        # ── Construire le chemin absolu FTP ──────────────────────────────────
        abs_path = "/" + ftp_content_path.strip("/")

        # ── Détecter fichier vs dossier ──────────────────────────────────────
        is_dir = True
        try:
            ftp.cwd(abs_path)
        except ftplib.error_perm:
            is_dir = False

        # ── Lister les fichiers ───────────────────────────────────────────────
        if is_dir:
            files = self._ftp_list_recursive(ftp, abs_path)
        else:
            # Fichier unique — aller dans le parent
            parts = abs_path.strip("/").split("/")
            leaf = parts[-1]
            parent = "/" + "/".join(parts[:-1]) if len(parts) > 1 else "/"
            size = 0
            try:
                ftp.cwd("/")
                size = ftp.size(abs_path)
            except Exception:
                pass
            files = [(leaf, abs_path, size)]

        if not files:
            ftp.quit()
            raise Exception("[LOCAL] Aucun fichier dans " + ftp_content_path)

        total_size = sum(s for _, _, s in files)
        self._log("  [LOCAL] " + str(len(files)) + " fichier(s), "
                  + str(total_size) + " o au total")

        # ── Hasher les pièces en streaming ───────────────────────────────────
        class _PieceHasher:
            def __init__(self, ps):
                self.ps     = ps
                self.buf    = bytearray()
                self.hashes = b""
            def feed(self, chunk):
                self.buf.extend(chunk)
                while len(self.buf) >= self.ps:
                    self.hashes += hashlib.sha1(bytes(self.buf[:self.ps])).digest()
                    del self.buf[:self.ps]
            def finalize(self):
                if self.buf:
                    self.hashes += hashlib.sha1(bytes(self.buf)).digest()
                return self.hashes

        hasher = _PieceHasher(piece_size)
        ftp.cwd("/")        # revenir à la racine avant RETR absolus

        for idx, (rel_path, full_path, size) in enumerate(files):
            self._log("  [LOCAL] [" + str(idx + 1) + "/" + str(len(files))
                      + "] " + rel_path + " (" + str(size) + " o)")
            try:
                ftp.retrbinary("RETR " + full_path, hasher.feed)
            except Exception as e_retr:
                ftp.quit()
                raise Exception("[LOCAL] RETR " + full_path + " : " + str(e_retr))

        piece_hashes = hasher.finalize()
        ftp.quit()

        self._log("  [LOCAL] " + str(len(piece_hashes) // 20)
                  + " pièce(s) de " + str(piece_size // 1048576) + " MiB")

        # ── Construire le dictionnaire info (bencode) ─────────────────────────
        if len(files) == 1 and not is_dir:
            info = {
                "length":       files[0][2],
                "name":         name,
                "piece length": piece_size,
                "pieces":       piece_hashes,
            }
        else:
            file_list = []
            for rel_path, _, size in files:
                path_parts = [p for p in rel_path.replace("\\", "/").split("/") if p]
                file_list.append({"length": size, "path": path_parts})
            info = {
                "files":        file_list,
                "name":         name,
                "piece length": piece_size,
                "pieces":       piece_hashes,
            }

        if private:
            info["private"] = 1

        torrent_dict = {
            "announce":    announce,
            "created by":  "REBiRTH",
            "info":        info,
        }

        result = self._bencode(torrent_dict)
        self._log("  [LOCAL] ✅ .torrent créé localement ("
                  + str(len(result)) + " o)", "success")
        return result

    def _create_torrent_rutorrent(self, base, remote_path, announce_urls, private=True, auto_start=True):
        """Crée les torrents via le plugin create de ruTorrent (hash côté seedbox).
        Piece size 4 MiB. Récupère le .torrent en cascade :
          A) HTTP GET sur le plugin create (bail rapide si retourne [])
          B) XML-RPC execute.nothrow.bg — copie session→rtorrent/, récupère via FTP
          C) Filebrowser API (HTTP, SFTP_HOST = URL Filebrowser)
          D) SFTP via paramiko (SSH, pas de chroot)
          E) FTP tasks dir (si RUTORRENT_TASKS_PATH est configuré dans le .env)
        """
        import urllib3, time
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        rt_url         = os.getenv("RUTORRENT_URL", "")
        rt_user        = os.getenv("RUTORRENT_USER", "")
        rt_pass        = os.getenv("RUTORRENT_PASS", "")
        ftp_host       = os.getenv("SFTP_HOST_FTP", "")
        ftp_port       = int(os.getenv("SFTP_PORT", "21"))
        ftp_user       = os.getenv("SFTP_USER", "")
        ftp_pass       = os.getenv("SFTP_PASS", "")
        fb_url         = os.getenv("SFTP_HOST", "")      # Filebrowser URL
        ssh_host       = ftp_host                         # SSH = même host que FTP
        ssh_port       = int(os.getenv("SFTP_SSH_PORT", "22"))
        tasks_path_env = os.getenv("RUTORRENT_TASKS_PATH", "")

        if not rt_url:
            raise Exception("ruTorrent URL non configurée dans le .env")

        create_url     = rt_url.rstrip("/") + "/plugins/create/action.php"
        torrents_local = BASE_DIR / "TORRENTS"
        torrents_local.mkdir(exist_ok=True)

        for tk_name, announce in announce_urls.items():
            if not announce:
                continue
            self._log("Création torrent SB pour " + tk_name + "…")

            # ── 1. Snapshot FTP tasks/ (best-effort, pour méthode C) ───────────
            before_tasks = set()
            before_ts    = time.time()
            if tasks_path_env:
                try:
                    import ftplib
                    ftp_s = ftplib.FTP_TLS()
                    ftp_s.connect(ftp_host, ftp_port, timeout=15)
                    ftp_s.login(ftp_user, ftp_pass)
                    ftp_s.prot_p()
                    for p in [x for x in tasks_path_env.strip("/").split("/") if x]:
                        ftp_s.cwd(p)
                    before_tasks = set(e for e in ftp_s.nlst() if e not in (".", ".."))
                    ftp_s.quit()
                    self._log("  [FTP] snapshot : " + str(len(before_tasks)) + " tâches")
                except Exception as e_snap:
                    self._log("  [FTP] snapshot échoué : " + str(e_snap), "warn")

            # ── 2. POST au plugin create ────────────────────────────────────────
            post_data = {
                "name":         base,
                "dir":          remote_path.rstrip("/") + "/",
                "piece_size":   "4194304",   # 4 MiB
                "startSeeding": "on",
                "tracker[0]":   announce,
            }
            if private:
                post_data["private"] = "on"

            self._log("  POST → " + create_url)
            self._log("  dir  = " + post_data["dir"])
            r = requests.post(create_url, data=post_data,
                              auth=(rt_user, rt_pass), verify=False, timeout=120)
            self._log("  HTTP " + str(r.status_code) + " — " + str(len(r.content)) + " o")
            if r.content:
                preview = r.content[:120].decode("utf-8", errors="replace").replace("\n", " ")
                self._log("  Réponse POST : " + preview)

            if r.status_code != 200:
                raise Exception(
                    "Plugin create ruTorrent — HTTP " + str(r.status_code) +
                    " pour " + tk_name +
                    " (vérifier que le plugin 'create' est installé)"
                )

            # ── 3. Récupération du .torrent (SSH → cascade A → B → C → D → E) ──
            torrent_bytes = None

            # SSH primary) mktorrent côté seedbox via SSH (port 22)
            if ftp_port == 22:
                try:
                    torrent_bytes = self._create_torrent_via_ssh(
                        base, remote_path, announce, bool(private), tk_name,
                        auto_start=auto_start)
                except Exception as e_ssh:
                    self._log("  ⚠ [SSH] " + str(e_ssh), "warn")

            # Réponse directe du plugin create (rare)
            if not torrent_bytes and r.content and r.content.lstrip()[:1] == b"d":
                torrent_bytes = r.content
                self._log("  📦 .torrent reçu directement dans la réponse POST", "success")

            # A) HTTP GET polling du plugin create (bail rapide si retourne [])
            if not torrent_bytes:
                try:
                    torrent_bytes = self._poll_via_http_api(
                        create_url, rt_user, rt_pass, base, timeout=60)
                except Exception as e_http:
                    self._log("  ⚠ [HTTP] " + str(e_http), "warn")

            # B) XML-RPC execute.nothrow.bg + FTP rtorrent/ (copie session → rtorrent/)
            if not torrent_bytes and ftp_host:
                try:
                    torrent_bytes = self._fetch_via_xmlrpc_exec(
                        rt_url, rt_user, rt_pass, base,
                        ftp_host, ftp_port, ftp_user, ftp_pass,
                        fb_url=fb_url,
                        announce=announce,
                        remote_path=remote_path)
                except Exception as e_xrpc:
                    self._log("  ⚠ [XRPC] " + str(e_xrpc), "warn")

            # C) Filebrowser API (HTTP, SFTP_HOST = URL Filebrowser)
            if not torrent_bytes and fb_url:
                try:
                    torrent_bytes = self._poll_via_filebrowser(
                        fb_url, ftp_user, ftp_pass,
                        rt_user, before_ts, timeout=600)
                except Exception as e_fb:
                    self._log("  ⚠ [FB] " + str(e_fb), "warn")

            # D) SFTP via paramiko (SSH host = même host que FTP)
            if not torrent_bytes and ssh_host:
                try:
                    torrent_bytes = self._poll_via_sftp(
                        ssh_host, ssh_port, ftp_user, ftp_pass,
                        rt_user, before_ts, timeout=600)
                except Exception as e_sftp:
                    self._log("  ⚠ [SFTP] " + str(e_sftp), "warn")

            # E) FTP tasks dir — seulement si RUTORRENT_TASKS_PATH configuré
            if not torrent_bytes and tasks_path_env:
                try:
                    torrent_bytes = self._poll_via_ftp_tasks(
                        ftp_host, ftp_port, ftp_user, ftp_pass,
                        tasks_path_env, before_tasks, timeout=600)
                except Exception as e_ftp:
                    self._log("  ⚠ [FTP] " + str(e_ftp), "warn")

            # F) Création locale via streaming FTP (fallback ultime — py3createtorrent)
            if not torrent_bytes and ftp_host and remote_path:
                self._log("  [LOCAL] Tentative création locale (streaming FTP)…")
                try:
                    # remote_path = chemin FTP relatif vers le contenu
                    # ex: "rtorrent/REBiRTH/Nom.Du.Film..."
                    torrent_bytes = self._create_torrent_local_ftp(
                        ftp_host, ftp_port, ftp_user, ftp_pass,
                        remote_path, base, announce,
                        piece_size=4194304, private=bool(private))
                except Exception as e_local:
                    self._log("  ⚠ [LOCAL] " + str(e_local), "warn")

            # ── 4. Sauvegarde locale dans TORRENTS/<tracker>/ ──────────────────
            if torrent_bytes:
                tk_dir = torrents_local / tk_name
                tk_dir.mkdir(exist_ok=True)
                torrent_name = base + ".torrent"
                (tk_dir / torrent_name).write_bytes(torrent_bytes)
                self._log(f"  💾 Sauvegardé → TORRENTS/{tk_name}/{torrent_name}", "success")
            else:
                self._log("  ⚠ .torrent non récupéré — seeding actif sur la SB", "warn")

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


    def discord_search_tmdb(self, query: str):
        """Recherche un film sur TMDB et retourne les résultats via _emit."""
        def _run():
            try:
                api_key = os.getenv("API_KEY", "")
                lang    = os.getenv("LANGUAGE", "fr-FR")
                q = query.strip()
                if q.isdigit():
                    url = (f"https://api.themoviedb.org/3/movie/{q}"
                           f"?api_key={api_key}&language={lang}")
                    r = requests.get(url, timeout=10)
                    data = r.json()
                    results = [data] if "id" in data else []
                else:
                    url = (f"https://api.themoviedb.org/3/search/movie"
                           f"?api_key={api_key}&language={lang}"
                           f"&query={requests.utils.quote(q)}&include_adult=false")
                    r = requests.get(url, timeout=10)
                    results = r.json().get("results", [])[:20]
                self._emit("discord_search_done", {"ok": True, "results": results})
            except Exception as e:
                self._emit("discord_search_done", {"ok": False, "error": str(e)})
        threading.Thread(target=_run, daemon=True).start()
        return {"ok": True}

    def discord_send_notification(self, data: dict):
        """Envoie un embed Discord de notification d'upload."""
        def _run():
            try:
                mode = data.get("mode", "rebirth")
                if mode == "hdt":
                    webhook_url = os.getenv("WEBHOOK_HDT_URL", "")
                    if not webhook_url:
                        self._emit("discord_send_done",
                                   {"ok": False, "error": "WEBHOOK_HDT_URL non configuré dans le .env"})
                        return
                else:
                    webhook_url = os.getenv("WEBHOOK_URL", "")
                    if not webhook_url:
                        self._emit("discord_send_done",
                                   {"ok": False, "error": "WEBHOOK_URL non configuré dans le .env"})
                        return

                movie   = data.get("movie", {})
                rel     = data.get("release_name", "NOM_INCONNU")
                is_maj  = data.get("is_maj", False)
                uploads = data.get("uploads", {})

                title       = movie.get("title", "")
                year        = (movie.get("release_date") or "????")[:4]
                poster_path = movie.get("poster_path")
                film_id     = movie.get("id")
                img_url     = (f"https://image.tmdb.org/t/p/w500{poster_path}"
                               if poster_path else None)

                status_lines = []
                for site, info in uploads.items():
                    s      = info.get("status", "")
                    reason = info.get("reason", "").strip()
                    icon   = (":white_check_mark:" if s == "Uploadé"
                              else (":clock4:" if s == "Pending" else ":x:"))
                    line = f"**{site} :** {icon}"
                    if s != "Uploadé" and reason:
                        line += f" **`[{reason}]`**"
                    status_lines.append(line)

                maj_text     = "🚨 MISE A JOUR 🚨\n" if is_maj else ""
                upload_block = "\n\n".join(status_lines)

                desc = (f"ID TMDB : **{film_id}**\n\n"
                        f"**Nom de la Release :**\n"
                        f"```fix\n{rel}```\n"
                        f"**Statut des Uploads :**\n"
                        f"{maj_text}\n"
                        + upload_block)

                embed = {
                    "title":       f"🎬 {title} ({year})",
                    "description": desc,
                    "color":       16776960 if is_maj else 15548997,
                }
                if img_url:
                    embed["thumbnail"] = {"url": img_url}

                resp = requests.post(
                    webhook_url,
                    json={"content": "@everyone", "embeds": [embed]},
                    timeout=10
                )
                if resp.status_code in (200, 204):
                    self._emit("discord_send_done", {"ok": True})
                else:
                    self._emit("discord_send_done",
                               {"ok": False, "error": f"HTTP {resp.status_code}"})
            except Exception as e:
                self._emit("discord_send_done", {"ok": False, "error": str(e)})
        threading.Thread(target=_run, daemon=True).start()
        return {"ok": True}

    # ── Gestionnaire de fichiers seedbox ──────────────────────────────────────

    _SBF_ROOT = "/home/rtorrent/rtorrent/download"

    def list_seedbox_dir(self, path: str):
        """Liste le contenu d'un répertoire seedbox via SFTP.
        Restreint à /home/rtorrent/rtorrent/download et ses sous-dossiers."""
        import stat as _stat
        if not path.startswith(self._SBF_ROOT) or ".." in path:
            return {"error": "Chemin non autorisé"}

        host     = os.getenv("SFTP_HOST_FTP", "")
        port     = int(os.getenv("SFTP_PORT", "22"))
        user     = os.getenv("SFTP_USER", "")
        password = os.getenv("SFTP_PASS", "")
        if not host:
            return {"error": "SFTP_HOST_FTP non configuré"}

        try:
            import paramiko
        except ImportError:
            import subprocess as _sp
            _sp.run([sys.executable, "-m", "pip", "install", "paramiko",
                     "--break-system-packages", "--quiet"], capture_output=True)
            import paramiko  # noqa: F811
        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            try:
                entries = sftp.listdir_attr(path)
                result = []
                for e in entries:
                    if e.filename in (".", ".."):
                        continue
                    is_dir = bool(e.st_mode and _stat.S_ISDIR(e.st_mode))
                    result.append({
                        "name":   e.filename,
                        "is_dir": is_dir,
                        "size":   e.st_size or 0,
                    })
                result.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
                return {"entries": result, "path": path}
            except FileNotFoundError:
                return {"error": f"Dossier introuvable : {path}"}
            finally:
                sftp.close()
                transport.close()
        except Exception as e:
            return {"error": str(e)}

    def delete_seedbox_item(self, path: str):
        """Supprime un fichier ou dossier seedbox via SSH sudo rm -rf."""
        if not path.startswith(self._SBF_ROOT) or ".." in path:
            self._emit("sbf_delete_done", {"ok": False, "error": "Chemin non autorisé"})
            return {"ok": False}

        def _run():
            host     = os.getenv("SFTP_HOST_FTP", "")
            port     = int(os.getenv("SFTP_PORT", "22"))
            user     = os.getenv("SFTP_USER", "")
            password = os.getenv("SFTP_PASS", "")
            if not host:
                self._emit("sbf_delete_done", {"ok": False, "error": "SSH non configuré"})
                return
            try:
                import paramiko
            except ImportError:
                import subprocess as _sp
                _sp.run([sys.executable, "-m", "pip", "install", "paramiko",
                         "--break-system-packages", "--quiet"], capture_output=True)
                import paramiko  # noqa: F811
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(host, port=port, username=user, password=password,
                               timeout=15, allow_agent=False, look_for_keys=False)
                safe = path.replace("'", "'\\''")
                _, stdout, stderr = client.exec_command(
                    f"sudo rm -rf '{safe}'", timeout=120
                )
                exit_code = stdout.channel.recv_exit_status()
                err_msg   = stderr.read().decode("utf-8", errors="replace").strip()
                client.close()
                if exit_code == 0:
                    self._emit("sbf_delete_done", {"ok": True, "path": path})
                else:
                    self._emit("sbf_delete_done",
                               {"ok": False,
                                "error": err_msg or f"exit {exit_code}"})
            except Exception as e:
                self._emit("sbf_delete_done", {"ok": False, "error": str(e)})

        threading.Thread(target=_run, daemon=True).start()
        return {"ok": True}


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
