import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "V1.env"))

# Clé API TMDb lue depuis V1.env (variable API_KEY)
TMDB_API_KEY = os.getenv("API_KEY", "")

def search_tmdb(title, media_type="movie", language="fr"):
    """
    Recherche un film ou une série sur TMDb.
    
    Args:
        title (str): Le titre du film ou de la série.
        media_type (str): "movie" pour les films, "tv" pour les séries.
        language (str): Langue des résultats (ex: "fr").
        
    Returns:
        dict: Informations sur le film ou la série trouvée.
    """
    url = f"https://api.themoviedb.org/3/search/{media_type}"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": language,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # Vérifie les erreurs HTTP

    data = response.json()
    if data.get("results"):
        return data["results"][0]  # Premier résultat trouvé
    return None

def get_tmdb_link(title, media_type="movie", fallback_titles=None):
    """
    Obtenir un lien TMDb basé sur le titre.
    Essaie title en premier, puis chaque titre dans fallback_titles.

    Args:
        title (str): Le titre principal (ex: depuis la piste vidéo MKV).
        media_type (str): "movie" ou "tv".
        fallback_titles (list|None): Titres alternatifs à essayer si le premier échoue
                                     (ex: titre General du conteneur, titre PTN du fichier).

    Returns:
        str: URL vers la page TMDb du contenu.
    """
    _SKIP = {"", "No title in video track", None}
    titles_to_try = [title] + (fallback_titles or [])
    for t in titles_to_try:
        if t in _SKIP:
            continue
        result = search_tmdb(t, media_type)
        if result:
            media_id = result.get("id")
            return f"https://www.themoviedb.org/{media_type}/{media_id}"
    return "https://www.themoviedb.org/"