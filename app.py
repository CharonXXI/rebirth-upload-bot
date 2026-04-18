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

    def run_bdinfo_scan(self, folder_path: str):
        """Lance BDInfoCLI sur folder_path (thread séparé).
        Cherche le dossier BDMV à l'intérieur si nécessaire.
        Sauvegarde le rapport dans BDINFO/<nom>.nfo et l'émet via log.
        """
        threading.Thread(
            target=self._bdinfo_worker,
            args=(folder_path,),
            daemon=True
        ).start()
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
            import re as _re2
            playlist_dir = Path(root) / "BDMV" / "PLAYLIST"
            stream_dir   = Path(root) / "BDMV" / "STREAM"
            if not playlist_dir.exists() or not stream_dir.exists():
                return None

            # Index des tailles M2TS  {"00800": 36349261824, ...}
            m2ts_sizes = {}
            for f in stream_dir.iterdir():
                if f.suffix.upper() == ".M2TS":
                    m2ts_sizes[f.stem.upper()] = f.stat().st_size

            if not m2ts_sizes:
                return None

            best_name, best_size = None, -1
            candidates_list = []
            for mpls_file in sorted(playlist_dir.iterdir()):
                if mpls_file.suffix.upper() != ".MPLS":
                    continue
                try:
                    data = mpls_file.read_bytes()
                    # Pattern "XXXXXM2TS" dans le binaire MPLS
                    clips = set(_re2.findall(rb'([0-9]{5})M2TS', data))
                    total = sum(m2ts_sizes.get(c.decode(), 0) for c in clips)
                    candidates_list.append((mpls_file.name.upper(), total))
                    if total > best_size:
                        best_size = total
                        best_name = mpls_file.name.upper()
                except Exception:
                    continue

            if best_name:
                # Log des 3 plus grosses playlists pour info
                candidates_list.sort(key=lambda x: x[1], reverse=True)
                for pl, sz in candidates_list[:3]:
                    _status("  %s → %.2f GB" % (pl, sz / 1_073_741_824))

            return best_name

        _status("Identification de la playlist principale…")
        try:
            main_pl = _pick_mpls_by_stream_size(scan_root)
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
        import glob as _glob, time as _time

        # Timestamp AVANT le scan pour trouver les fichiers créés/modifiés après
        scan_start = _time.time()

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
            return

        # ── 5. Filtrer : garder uniquement DISC INFO → FILES (exclu) ─────────
        def _extract_disc_info(text):
            lines = text.splitlines()
            result = []
            inside = False
            stop_sections = {"FILES:", "CHAPTERS:", "STREAM DIAGNOSTICS:"}
            for ln in lines:
                stripped = ln.strip()
                if not inside:
                    if stripped == "DISC INFO:":
                        inside = True
                        result.append(ln)
                else:
                    if stripped in stop_sections:
                        break
                    result.append(ln)
            while result and not result[-1].strip():
                result.pop()
            return "\n".join(result)

        filtered = _extract_disc_info(output_text)
        if filtered:
            output_text = filtered

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

    def _create_torrent_rutorrent(self, base, remote_path, announce_urls, private=True):
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

            # ── 3. Récupération du .torrent (cascade A → B → C → D → E) ─────────
            torrent_bytes = None

            # Réponse directe (rare)
            if r.content and r.content.lstrip()[:1] == b"d":
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

            # ── 4. Sauvegarde locale ────────────────────────────────────────────
            if torrent_bytes:
                torrent_name = base + "__" + tk_name + ".torrent"
                (torrents_local / torrent_name).write_bytes(torrent_bytes)
                self._log("  💾 Sauvegardé → TORRENTS/" + torrent_name, "success")
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
