import os
import requests

# Votre clé API TMDb
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

def get_tmdb_link(title, media_type="movie"):
    """
    Obtenir un lien TMDb basé sur le titre.
    
    Args:
        title (str): Le titre du film ou de la série.
        media_type (str): "movie" ou "tv".
    
    Returns:
        str: URL vers la page TMDb du contenu.
    """
    result = search_tmdb(title, media_type)
    if result:
        media_id = result.get("id")
        base_url = "https://www.themoviedb.org/"
        return f"{base_url}{media_type}/{media_id}"
    return "https://www.themoviedb.org/"