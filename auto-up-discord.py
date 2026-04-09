#!/usr/bin/env python3

# python3 -m venv && source venv/bin/activate
# pip install requests requests_toolbelt tqdm

import os
import subprocess
import sys
import requests
import json
import re
from dotenv import load_dotenv
from pathlib import Path
from gofile import gofile_upload
from NFO_CUSTOM import NFO_v1_7
import uuid
from typing import Tuple, List, Dict, Optional
from requests_toolbelt import MultipartEncoder
from tqdm import tqdm

# Variables globales
load_dotenv()
GOFILE_TOKEN = os.getenv("GOFILE_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
API_KEY = os.getenv("API_KEY")
LANGUAGE = os.getenv("LANGUAGE")
BUZZHEAVIER_ACC_ID = os.getenv("BUZZHEAVIER_ACC_ID")

def check_mkv_file(file_path):
    """Vérifie si le fichier est un fichier .mkv"""
    if not file_path.lower().endswith(".mkv"):
        print(f"Erreur: Le fichier {file_path} n'est pas un fichier .mkv.")
        sys.exit(1)
    if not os.path.isfile(file_path):
        print(f"Erreur: Le fichier {file_path} n'existe pas.")
        sys.exit(1)

def create_nfo_file(file_path):
    """Crée un fichier .nfo avec les informations du fichier .mkv sans afficher le chemin complet"""
    nfo_filename = os.path.basename(file_path) + "_mediainfo.nfo"
    
    # Extraction du répertoire du fichier
    file_dir = os.path.dirname(file_path)
    
    # Vérification si mediainfo est installé
    try:
        command = f"mediainfo --Output=NFO {os.path.basename(file_path)} > {nfo_filename}"
        subprocess.run(
            command, 
            shell=True, 
            cwd=file_dir
        )
        print(f"Fichier NFO créé: {nfo_filename}")
    except FileNotFoundError:
        print("Erreur: au niveau de mediainfo")
        sys.exit(1)
    return nfo_filename

def upload_files_gofiles(files):
    try:
        if not files or not isinstance(files, list):
            raise ValueError("La liste des fichiers est vide ou invalide.")
        
        os.environ["GOFILE_TOKEN"] = GOFILE_TOKEN

        urls = gofile_upload(
            path=files, 
            to_single_folder=True,
            verbose=True,
            export=False,
            open_urls=False
        )

        if not urls:
            print("Erreur: Aucune URL récupérée après l'upload.")
            sys.exit(1)

        print(f"URL obtenue: {urls[0]}")
        return urls[0]

    except Exception as e:
        print(f"Erreur lors de l'upload: {e}")
        sys.exit(1)

###

def get_root_id(account_id: str) -> str:
    headers = {"Authorization": f"Bearer {account_id}"}
    response = requests.get("https://buzzheavier.com/api/fs", headers=headers)
    response.raise_for_status()
    return response.json()['data']['id']

def list_root_contents(account_id: str) -> Tuple[List[dict], List[dict]]:
    headers = {"Authorization": f"Bearer {account_id}"}
    response = requests.get("https://buzzheavier.com/api/fs", headers=headers)
    response.raise_for_status()
    
    data = response.json()
    directories = []
    files = []
    
    if data.get('code') == 200 and 'children' in data.get('data', {}):
        for item in data['data']['children']:
            if item.get('isDirectory'):
                directories.append(item)
            else:
                files.append(item)
    
    return directories, files

def get_directory_id_by_name(account_id: str, dir_name: str) -> Optional[str]:
    directories, _ = list_root_contents(account_id)
    for directory in directories:
        if directory['name'] == dir_name:
            return directory['id']
    return None

def generate_unique_dirname(existing_dirs: List[dict]) -> str:
    existing_names = [d['name'] for d in existing_dirs]
    while True:
        new_name = uuid.uuid4().hex
        if new_name not in existing_names:
            return new_name

def create_unique_directory(account_id: str) -> dict:
    try:
        parent_id = get_root_id(account_id)
        existing_dirs, _ = list_root_contents(account_id)
        dir_name = generate_unique_dirname(existing_dirs)
        
        headers = {
            "Authorization": f"Bearer {account_id}",
            "Content-Type": "application/json"
        }
        payload = {
            "name": dir_name,
            "parentId": parent_id
        }
        
        response = requests.post(
            f"https://buzzheavier.com/api/fs/{parent_id}",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        
        directory_id = get_directory_id_by_name(account_id, dir_name)
        if not directory_id:
            raise Exception("Impossible de récupérer l'ID du nouveau dossier")
        
        return {
            "id": directory_id,
            "name": dir_name
        }
    
    except requests.exceptions.HTTPError as e:
        error_details = e.response.json().get('error', 'Pas de détails supplémentaires')
        raise Exception(f"Erreur {e.response.status_code} - {error_details}")
    except Exception as e:
        raise Exception(f"Création échouée: {str(e)}")

def upload_file(file_path: str, directory_id: str, account_id: str) -> str:
    try:
        headers = {"Authorization": f"Bearer {account_id}"}
        
        with open(file_path, 'rb') as f:
            filename = os.path.basename(file_path)
            response = requests.put(
                f"https://w.buzzheavier.com/{directory_id}/{filename}",
                headers=headers,
                data=f
            )
            response.raise_for_status()
            
        return f"https://w.buzzheavier.com/{directory_id}/{filename}"
    
    except Exception as e:
        raise Exception(f"Échec de l'upload pour {file_path}: {str(e)}")

def upload_big_file(file_path: str, directory_id: str, account_id: str, progress_fn=None) -> str:
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    url = f'https://w.buzzheavier.com/{directory_id}/{filename}'
    uploaded = [0]

    headers = {
        'Authorization': f'Bearer {account_id}',
        'Content-Length': str(file_size),
        'Content-Type': 'application/octet-stream'
    }

    with tqdm(
        total=file_size,
        unit='B',
        unit_scale=True,
        desc=f"Upload {filename}",
        dynamic_ncols=True
    ) as pbar:

        import time as _time
    _last_emit = [0.0]
    with open(file_path, 'rb') as f:
            class ReadProgress:
                def __init__(self, file_obj, progress_bar):
                    self.file_obj = file_obj
                    self.progress_bar = progress_bar

                def read(self, size=-1):
                    data = self.file_obj.read(size)
                    if data:
                        uploaded[0] += len(data)
                        self.progress_bar.update(len(data))
                        if progress_fn:
                            now = _time.time()
                            if now - _last_emit[0] >= 1.0:
                                _last_emit[0] = now
                                progress_fn(uploaded[0], file_size)
                    return data

            response = requests.put(
                url,
                headers=headers,
                data=ReadProgress(f, pbar),
                timeout=30
            )
    
    response.raise_for_status()
    return url

def upload_files_buzzheavier(files: List[str], account_id: str) -> Dict:
    try:
        directory_info = create_unique_directory(account_id)
        print(f"Dossier créé avec succès : {directory_info['name']} (ID: {directory_info['id']})")
        
        file_urls = []
        for file_path in files:
            if not os.path.isfile(file_path):
                print(f"Fichier ignoré : {file_path} (introuvable)")
                continue
            
            try:
                download_url = upload_big_file(file_path, directory_info['id'], account_id)
                file_urls.append(download_url)
                print(f"Upload réussi pour : {os.path.basename(file_path)}")
            except Exception as upload_error:
                print(f"Échec de l'upload pour {file_path} : {str(upload_error)}")
        
        return {
            "directory_id": directory_info['id'],
            "directory_name": directory_info['name'],
            "file_urls": file_urls,
            "directory_url": f"https://buzzheavier.com/{directory_info['id']}"
        }
    
    except Exception as e:
        raise Exception(f"Erreur globale : {str(e)}")

###

def get_tmdb_search_name(file_path):
    path = Path(file_path)
    filename = path.name
    filename_parts = filename.split(".")
    breaking_search_keywords = ['complete', 'integral', 'integrale', 'intégrale', 'french', 'truefrench', 'multi', 'english', 'vostf', 'vostfr', 'vff', 'vfq', 'vf2', 'web', 'web-dl']
    search_parts = []

    for part in filename_parts:
        if re.search(r'^S(\d+)(?:E(\d+))?|\d{4}(?:-(\d{2}))?(?:-(\d{2}))?|\d{3,4}p$', part) or any(keyword in part.lower() for keyword in breaking_search_keywords):
            break
        search_parts.append(part)
    
    search_terms = " ".join(search_parts).strip()
    return search_terms

def search_tmdb(search_name):
    url = f"https://api.themoviedb.org/3/search/multi"
    params = {
        "api_key": API_KEY,
        "query": search_name,
        "language": LANGUAGE,
    }
    response = requests.get(url, params=params)
    return response.json()

def get_id_from_tmdb(data):
    if data.get('results'):
        result = data['results'][0]
        media_type = result.get('media_type')
        tmdb_id = result.get('id')
        title = result.get('title') or result.get('name')

        if media_type == 'movie':
            release_date = result.get('release_date')
            year = release_date.split('-')[0] if release_date else 'N/A'
        elif media_type == 'tv':
            first_air_date = result.get('first_air_date')
            year = first_air_date.split('-')[0] if first_air_date else 'N/A'
        else:
            year = 'N/A'

        return tmdb_id, title, media_type, year

    return None, None, None, None

def get_tmdb_link(media_type, tmdb_id):
    return f"https://www.themoviedb.org/{media_type}/{tmdb_id}"

def get_external_ids(tmdb_id):
    url = f'https://api.themoviedb.org/3/movie/{tmdb_id}/external_ids'
    params = {'api_key': API_KEY}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        external_ids = response.json()
        imdb_id = external_ids.get('imdb_id')
        if imdb_id:
            return f'https://www.imdb.com/title/{imdb_id}/'
    return None

def get_poster_url(tmdb_id):
    url = f'https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={API_KEY}&language={LANGUAGE}'
    response = requests.get(url)

    if response.status_code == 200:
        movie_data = response.json()
        if 'poster_path' in movie_data:
            poster_path = movie_data['poster_path']
            return f'https://image.tmdb.org/t/p/w500{poster_path}'
    return None

def send_discord_webhook(url, filename, source=None, note=None, tk_to_up=None, tmdb_link=None, imdb_link=None, poster_url=None, autre_info=None):
    if not WEBHOOK_URL:
        print("Erreur: URL du webhook Discord manquante.")
        sys.exit(1)

    embed_fields = []
    if tmdb_link:
        embed_fields.append({"name": "TMDB", "value": tmdb_link, "inline": False})
    if imdb_link:
        embed_fields.append({"name": "IMDb", "value": imdb_link, "inline": False})
    if source:
        embed_fields.append({"name": "Source", "value": source, "inline": False})
    if note:
        embed_fields.append({"name": "Note", "value": note, "inline": False})
    if tk_to_up:
        embed_fields.append({"name": "Trackers sur lesquels uploader :", "value": tk_to_up, "inline": False})
    if autre_info:
        embed_fields.append({"name": "Autre info", "value": autre_info, "inline": False})

    filename_without_extension = os.path.splitext(filename)[0]

    message = {
        "content": "### Nouveau fichier à uploader ! <@393798272495386636>",
        "embeds": [
            {
                "title": filename_without_extension, 
                "description": url,
                "fields": embed_fields,
                "color": 0xffa500,
                "image": {
                  "url": poster_url
                }
            }
        ]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=message)
        if response.status_code == 204:
            print("Message envoyé au webhook Discord.")
        else:
            print(f"Erreur lors de l'envoi du webhook Discord: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi de la requête HTTP au webhook Discord: {e}")
        sys.exit(1)

def main():
    if not all([GOFILE_TOKEN, WEBHOOK_URL, API_KEY, LANGUAGE, BUZZHEAVIER_ACC_ID]):
        raise ValueError("Certaines variables d'environnement ne sont pas définies. Vérifie ton fichier .env")

    print(f"GOFILE_TOKEN: {GOFILE_TOKEN[:5]}*** (masqué)")
    print(f"WEBHOOK_URL: {WEBHOOK_URL[:20]}*** (masqué)")
    print(f"API_KEY: {API_KEY[:5]}*** (masqué)")
    print(f"LANGUAGE: {LANGUAGE}")
    print(f"BUZZHEAVIER_ACC_ID: {BUZZHEAVIER_ACC_ID[:5]}*** (masqué)")

    if len(sys.argv) < 2:
        print("Usage: python auto-up-discord.py <chemin_du_fichier.mkv>")
        sys.exit(1)

    file_path = sys.argv[1]
    check_mkv_file(file_path)

    # Créer le fichier NFO (mediainfo)
    nfo_filename_mediainfo = create_nfo_file(file_path)
    file_dir = os.path.dirname(file_path)
    nfo_mediainfo = os.path.join(file_dir, nfo_filename_mediainfo)
    content_mediainfo = ""
    with open(nfo_mediainfo, 'r', encoding='utf-8') as f:
        content_mediainfo = f.read()
    
    # Créer le fichier NFO (custom)
    nfo_custom = NFO_v1_7.process_file(file_path)
    content_custom = ""
    with open(nfo_custom, 'r', encoding='utf-8') as f:
        content_custom = f.read()

    final_content = content_custom + "\n\n" + content_mediainfo

    base = os.path.basename(os.path.splitext(file_path)[0])
    output_filename_utf8 = os.path.join(os.path.dirname(file_path), f"(LaCale)-{base}.nfo")
    output_filename_dos = os.path.splitext(file_path)[0] + ".nfo"

    # Version UTF-8 pour LaCale
    with open(output_filename_utf8, 'w', encoding='utf-8') as file:
        file.write(final_content)

    # Version CP437 pour ABN/TOS
    with open(output_filename_dos, 'w', encoding='cp437', errors='replace') as file:
        file.write(final_content)

    print(f"NFO UTF-8 créé : {output_filename_utf8}")
    print(f"NFO CP437 créé : {output_filename_dos}")

    # Supprimer les fichiers intermédiaires
    os.remove(nfo_mediainfo)
    os.remove(nfo_custom)

    # Récupérer le nom pour la recherche TMDB
    search_name = get_tmdb_search_name(file_path)
    print(f"Nom de recherche TMDB: {search_name}")

    # Recherche sur TMDB
    tmdb_data = search_tmdb(search_name)
    tmdb_id, tmdb_title, media_type, year = get_id_from_tmdb(tmdb_data)

    if tmdb_id:
        tmdb_link = get_tmdb_link(media_type, tmdb_id)
        print(f"Lien TMDB trouvé: {tmdb_link}")
        print(f"Année : {year}")
        confirmation = input("Confirmez-vous ce lien TMDB ? (Y/N): ").strip()
        if confirmation.lower() != 'y':
            print("Changement de l'ID.")
            tmdb_id = input("Quel ID veux-tu mettre ? ").strip()
            tmdb_link = f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
        poster_url = get_poster_url(tmdb_id)
        if poster_url:
            print(f"URL du poster récupéré.")
        else:
            print("Aucun poster trouvé.")
            poster_url = "https://upload.wikimedia.org/wikipedia/commons/a/a3/Image-not-found.png"
        
        imdb_link = get_external_ids(tmdb_id)
        if imdb_link:
            print(f"Lien IMDb récupéré : {imdb_link}")
        else:
            print("Aucun lien IMDb trouvé.")
    else:
        print("Aucun résultat TMDB trouvé.")
        tmdb_link = input("Quel lien veux-tu mettre ? (doit commencer par https) ").strip()
        poster_url = "https://upload.wikimedia.org/wikipedia/commons/a/a3/Image-not-found.png"
        imdb_link = None

    source = input("Source (laisser vide si aucun): ").strip()
    note = input("Note (laisser vide si aucune): ").strip()
    tk_to_up = input("Trackers sur lesquels uploader ? ").strip()
    autre_info = input("Autre info (n'est pas une note ; ex: c'est un animé) : ").strip()

    files_to_upload = [file_path, output_filename_dos]

    platform_choice = input("Sur quelle plateforme souhaitez-vous uploader les fichiers ? (Gofile -> \"g\" ou BuzzHeavier -> \"b\") : ").strip().lower()
    if platform_choice == "g":
        download_url = upload_files_gofiles(files_to_upload)
    elif platform_choice == "b":
        try:
            result = upload_files_buzzheavier(files_to_upload, BUZZHEAVIER_ACC_ID)
            print("\nRésultat de l'upload:")
            bzhv_dir_name = result['directory_name']
            download_url = result['directory_url']
            print(f"- Nom du dossier: {bzhv_dir_name}")
            print(f"- URL du dossier buzzheavier : {download_url}")
        except Exception as e:
            print(f"Erreur lors de l'upload buzzheavier : {str(e)}")
    else:
        print("Choix de plateforme invalide. Veuillez choisir entre 'g' et 'b'.")
        exit(1)

    send_discord_webhook(download_url, os.path.basename(file_path), source, note, tk_to_up, tmdb_link, imdb_link, poster_url, autre_info)

if __name__ == "__main__":
    main()
