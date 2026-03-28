#!/usr/bin/env python3
# coding: utf-8

import argparse
import json
import mimetypes
import os
import sys
import time
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Optional

import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
from tqdm import tqdm
from rich import print as rprint
from rich.panel import Panel

# Endpoints dans l'ordre de priorité — failover automatique en cas d'erreur
UPLOAD_ENDPOINTS = [
    "https://upload.gofile.io/uploadfile",
    "https://upload-eu-par.gofile.io/uploadfile",
    "https://upload-na-phx.gofile.io/uploadfile",
    "https://upload-ap-sgp.gofile.io/uploadfile",
    "https://upload-ap-hkg.gofile.io/uploadfile",
    "https://upload-ap-tyo.gofile.io/uploadfile",
    "https://upload-sa-sao.gofile.io/uploadfile",
]


def upload(file: str, folder_id: Optional[str] = None, guest_token: Optional[str] = None):
    f_obj = Path(file)
    file_size = f_obj.stat().st_size
    token = os.getenv("GOFILE_TOKEN")

    for endpoint in UPLOAD_ENDPOINTS:
        rprint(f"[cyan]Tentative sur :[/cyan] {endpoint}")
        try:
            with open(f_obj, "rb") as f:
                with tqdm(
                    total=file_size,
                    unit="B",
                    unit_scale=True,
                    desc=f"Upload {f_obj.name}",
                ) as progress:
                    def progress_callback(m):
                        progress.n = m.bytes_read
                        progress.refresh()

                    content_type = mimetypes.guess_type(f_obj)[0] or "application/octet-stream"

                    fields = {"file": (f_obj.name, f, content_type)}
                    if folder_id:
                        fields["folderId"] = folder_id
                    # Pour le 2eme fichier on utilise le guestToken du 1er upload
                    if guest_token:
                        fields["token"] = guest_token

                    encoder = MultipartEncoder(fields=fields)
                    monitor = MultipartEncoderMonitor(encoder, progress_callback)
                    headers = {
                        "Content-Type": monitor.content_type,
                    }

                    response = requests.post(endpoint, data=monitor, headers=headers)
                    response.raise_for_status()
                    rprint(f"[green]Upload terminé :[/green] {f_obj.name}")
                    return response

        except requests.exceptions.HTTPError as e:
            rprint(f"[yellow]⚠ Serveur KO ({e.response.status_code}) — passage au suivant…[/yellow]")
            continue
        except requests.exceptions.RequestException as e:
            rprint(f"[yellow]⚠ Erreur réseau — passage au suivant… ({e})[/yellow]")
            continue

    rprint(f"[red]✗ Tous les serveurs Gofile ont échoué pour {f_obj.name}.[/red]")
    sys.exit(1)


def gofile_upload(
    path: list,
    to_single_folder: bool = False,
    verbose: bool = False,
    export: bool = False,
    open_urls: bool = False,
):
    files = []
    for _path in path:
        if not Path(_path).exists():
            rprint(
                f'[red]ERROR: [dim blue]"{Path(_path).absolute()}"[/dim blue] '
                "does not exist! [/red]"
            )
            continue
        if Path(_path).is_dir():
            dir_items = glob(str(Path(f"{_path}/**/*")), recursive=True)
            local_files = [x for x in dir_items if not Path(x).is_dir()]
            files.append(local_files)
        else:
            files.append([_path])

    files = sum(files, [])
    export_data = []
    urls = []
    folder_id = None

    if to_single_folder:
        if not os.getenv("GOFILE_TOKEN"):
            rprint(
                "[red]ERROR: Gofile token is required when passing "
                "`--to-single-folder`![/red]\n[dim red]You can find your "
                "account token on this page: "
                "[u][blue]https://gofile.io/myProfile[/blue][/u]\nCopy it "
                "then export it as `GOFILE_TOKEN`. For example:\n"
                "export GOFILE_TOKEN='xxxxxxxxxxxxxxxxx'[/dim red]"
            )
            sys.exit(1)

    guest_token = None
    for file in files:
        upload_resp = upload(file, folder_id, guest_token).json()
        if to_single_folder and folder_id is None:
            folder_id   = upload_resp["data"]["parentFolder"]
            guest_token = upload_resp["data"].get("guestToken")

        ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        file_abs = str(Path(file).absolute())
        record = {"file": file_abs, "timestamp": ts, "response": upload_resp}
        url = upload_resp["data"]["downloadPage"]
        urls.append(url)

        if verbose:
            rprint(Panel(json.dumps(record, indent=2)))
        elif not to_single_folder:
            rprint(
                Panel.fit(
                    f"[yellow]File:[/yellow] [blue]{file}[/blue]\n"
                    f"[yellow]Download page:[/yellow] [u][blue]{url}[/blue][/u]"
                )
            )

        if export:
            export_data.append(record)

    if not urls:
        sys.exit()

    if to_single_folder:
        files = "\n".join([str(Path(x).absolute()) for x in files])
        rprint(
            Panel.fit(
                f"[yellow]Files:[/yellow]\n[blue]{files}[/blue]\n"
                "[yellow]Download page:[/yellow] "
                f"[u][blue]{urls[0]}[/blue][/u]"
            )
        )

    if export:
        export_fname = f"gofile_export_{int(time.time())}.json"
        with open(export_fname, "w") as j:
            json.dump(export_data, j, indent=4)
        rprint("[green]Exported data to:[/green] " f"[magenta]{export_fname}[/magenta]")

    return urls


def opts():
    parser = argparse.ArgumentParser(
        description="Example: gofile <file/folder_path>"
    )
    parser.add_argument("-s", "--to-single-folder", action="store_true")
    parser.add_argument("-o", "--open-urls",        action="store_true")
    parser.add_argument("-e", "--export",           action="store_true")
    parser.add_argument("-vv", "--verbose",         action="store_true")
    parser.add_argument("path", nargs="+", help="Path to the file(s) and/or folder(s)")
    return parser.parse_args()


def main():
    args = opts()
    gofile_upload(
        path=args.path,
        to_single_folder=args.to_single_folder,
        verbose=args.verbose,
        export=args.export,
        open_urls=args.open_urls,
    )


if __name__ == "__main__":
    main()
