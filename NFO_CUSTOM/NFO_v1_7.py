import os
import requests
import PTN
from fractions import Fraction
from pymediainfo import MediaInfo
from. tmdb_helper import get_tmdb_link
from. source_detector import detect_source
from datetime import datetime

# Dictionnaire des langues et leurs traductions
LANGUAGE_MAP = {
    "af": "AFRIKAANS",
    "sq": "ALBANIAN",
    "ar": "ARABIC",
    "hy": "ARMENIAN",
    "bn": "BENGALI",
    "bs": "BOSNIAN",
    "ca": "CATALAN",
    "hr": "CROATIAN",
    "cs": "CZECH",
    "da": "DANISH",
    "nl": "DUTCH",
    "en": "ENGLISH",
    "eo": "ESPERANTO",
    "et": "ESTONIAN",
    "tl": "FILIPINO (TAGALOG)",
    "fi": "FINNISH",
    "fr-FR": "FRENCH",
    "fr-CA": "FRENCH",
    "fr": "FRENCH",
    "fa": "FARSI",
    "de": "GERMAN",
    "el": "GREEK",
    "gu": "GUJARATI",
    "hi": "HINDI",
    "hu": "HUNGARIAN",
    "is": "ICELANDIC",
    "id": "INDONESIAN",
    "it": "ITALIAN",
    "ja": "JAPANESE",
    "jw": "JAVANESE",
    "ka": "GEORGIAN",
    "km": "KHMER",
    "kn": "KANNADA",
    "ko": "KOREAN",
    "la": "LATIN",
    "lv": "LATVIAN",
    "lt": "LITHUANIAN",
    "mk": "MACEDONIAN",
    "ml": "MALAYALAM",
    "mr": "MARATHI",
    "ne": "NEPALI",
    "no": "NORVEGIAN",
    "pl": "POLISH",
    "pt": "PORTUGUESE",
    "pa": "PUNJABI",
    "ro": "ROMANIAN",
    "ru": "RUSSIAN",
    "sr": "SERBIAN",
    "si": "SINHALA",
    "sk": "SLOVAK",
    "sl": "SLOVENIAN",
    "es": "SPANISH",
    "es-419": "SPANISH LATIN AMERICA",
    "su": "SUNDANESE",
    "sw": "SWAHILI",
    "sv": "SWEDISH",
    "ta": "TAMIL",
    "te": "TELUGU",
    "th": "THAI",
    "tr": "TURKISH",
    "uk": "UKRAINIAN",
    "ur": "URDU",
    "vi": "VIETNAMESE",
    "cy": "WELSH",
    "xh": "XHOSA",
    "yi": "YIDDISH",
    "zu": "ZULU",
}

# Fonction pour convertir un ratio en format x:y
def convert_aspect_ratio(ratio):
    try:
        # Convertir le ratio en Fraction
        frac = Fraction(ratio).limit_denominator()
        return f"{frac.numerator}:{frac.denominator}"
    except:
        return "Unknown"

# Fonction pour obtenir le type de sous-titres basé sur le nom du fichier
def get_subtitle_type(subtitle_filename):
    if subtitle_filename:
        subtitle_filename = subtitle_filename.lower()
        if "forced" in subtitle_filename:
            return "FORCED"
        elif "full" in subtitle_filename:
            return "FULL"
        elif "sdh" in subtitle_filename:
            return "SDH"
        elif "commentary" in subtitle_filename:
            return "COMMENTARY"
    return "Unknown"

# Fonction pour récupérer les informations HDR
def get_hdr_info(video_info):
    hdr_info = []
    if 'HDR' in str(video_info.other_hdr_format):
        hdr_info.append(video_info.color_primaries)
        hdr_info.append(str(video_info.other_hdr_format))
    elif 'Dolby Vision' in str(video_info.other_hdr_format):
        hdr_info.append(video_info.color_primaries)
        hdr_info.append(str(video_info.other_hdr_format))
    elif 'DV' in str(video_info.other_hdr_format):
        hdr_info.append(video_info.color_primaries)
        hdr_info.append(str(video_info.other_hdr_format))
    elif 'HDR10' in str(video_info.other_hdr_format):
        hdr_info.append(video_info.color_primaries)
        hdr_info.append("HDR10")
    return hdr_info if hdr_info else None

# Fonction pour remplir le template
def generate_template(file_path, tmdb_link_override=None):
    # Extraire les métadonnées avec MediaInfo
    media_info = MediaInfo.parse(file_path)
    general_info = next(track for track in media_info.tracks if track.track_type == "General")
    video_info = next(track for track in media_info.tracks if track.track_type == "Video")
    
    # Audio et sous-titres peuvent être multiples, donc on les récupère dans des listes
    audio_tracks = [track for track in media_info.tracks if track.track_type == "Audio"]
    subtitle_tracks = [track for track in media_info.tracks if track.track_type == "Text"]
    
    # Récupérer les données principales
    release_name = os.path.basename(file_path).replace(".mkv", "")
    release_size = general_info.other_file_size[0]
    release_date = datetime.now().strftime("%d-%m-%Y")
    
    # Utiliser la fonction de source depuis source_detector.py
    source = detect_source(file_path)
    
    # Informations Vidéo
    title = video_info.title if video_info.title else 'No title in video track'
    video_codec = video_info.format

    # Bitrate format
    if video_info.bit_rate == None:
        bitrate_video = 'Bitrate not found'
    elif video_info.bit_rate > 1000000:
        bitrate_video = f"{round(video_info.bit_rate / 1000000, 2)} Mb/s"
    elif int(video_info.bit_rate) > 1000:
        bitrate_video = f"{video_info.bit_rate // 1000} kb/s"
    else:
        bitrate_video = "Unknown"

    resolution = f"{video_info.width}x{video_info.height}"
    aspect_ratio = video_info.other_display_aspect_ratio[0] or "Unknown"
    fps = video_info.frame_rate or "Unknown"
    #duration = str(datetime.utcfromtimestamp(video_info.duration / 1000).strftime('%H h %M min')) if video_info.duration else "Unknown"
    duration = str(video_info.other_duration[0] if video_info.other_duration else 'N/A')
    
    # Get hdr_info
    hdr_info = get_hdr_info(video_info)

    # Informations Audio (en itérant sur les pistes audio)
    audio_blocks = []
    for index, audio_info in enumerate(audio_tracks, 1):
        audio_language = audio_info.language or "Unknown"
        audio_channels = audio_info.channel_s or "Unknown"
        audio_codec = audio_info.commercial_name

        # Bitrate format
        if audio_info.bit_rate == None:
            bitrate_audio = 'Bitrate not found'
        elif audio_info.bit_rate > 1000000000:
            bitrate_audio = f"{round(audio_info.bit_rate / 1000000000, 2)} Mb/s"
        elif audio_info.bit_rate < 1000000000:
            bitrate_audio = f"{audio_info.bit_rate // 1000} kb/s"
        else:
            bitrate_audio = "Unknown"

        # Format audio language
        try:
            audio_language = LANGUAGE_MAP[audio_language]
        except:
            # Not in LANGUAGE_MAP
            pass

        # Format channels output
        if audio_channels == 1:
            audio_channels = "1.0"
        elif audio_channels == 2:
            audio_channels = "2.0"
        elif audio_channels == 3:
            audio_channels = "2.1"
        elif audio_channels == 6:
            audio_channels = "5.1"
        elif audio_channels == 8:
            audio_channels = "7.1"
        
        if audio_language == 'FRENCH':
            if 'vfi' in audio_info.title.lower():
                a_title = 'VFi'
                audio_lang_title = audio_language + f" ({a_title})"
            elif 'vff' in audio_info.title.lower():
                a_title = 'VFF'
                audio_lang_title = audio_language + f" ({a_title})"
            elif 'vfq' in audio_info.title.lower():
                a_title = 'VFQ'
                audio_lang_title = audio_language + f" ({a_title})"
            elif 'vof' in audio_info.title.lower():
                a_title = 'VOF'
                audio_lang_title = audio_language + f" ({a_title})"
            else:
                audio_lang_title = audio_language
        else:
            audio_lang_title = audio_language
        audio_block = f"""█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ ████▓▓▓▒▒▒░░░                     AUDiO #{str(index).ljust(23)}░░░▒▒▒▓▓▓████ █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
█                                                                               █
█ ■ LANGUAGE........: {audio_lang_title.ljust(58)}█
█ ■ CHANNELS........: {str(audio_channels).ljust(58)}█
█ ■ CODEC...........: {audio_codec.ljust(58)}█
█ ■ BiTRATE.........: {bitrate_audio.ljust(58)}█
█                                                                               █
"""
        audio_blocks.append(audio_block)
    
    # Informations Sous-titres (en itérant sur les pistes de sous-titres)
    subtitle_blocks = []

    # Workaround if no subtitles
    if len(subtitle_tracks) > 0:
        for index, subtitle_info in enumerate(subtitle_tracks, 1):
            if subtitle_info:  # Vérifie si subtitle_info existe
                subtitle_language = subtitle_info.language or "Unknown"  # Utilise "Unknown" si la langue est absente
                subtitle_language = LANGUAGE_MAP.get(subtitle_language, subtitle_language).upper()
                subtitle_type = get_subtitle_type(subtitle_info.title) if hasattr(subtitle_info, 'title') else "Unknown"
                subtitle_format = subtitle_info.other_format[0] if subtitle_info.other_format else "Unknown"
            else:
                subtitle_language = "Unknown"
                subtitle_type = "Unknown"
                subtitle_format = "Unknown"

            # Format subtitle language
            try:
                subtitle_language = LANGUAGE_MAP[subtitle_language]
            except:
                # Not in LANGUAGE_MAP
                pass

            subtitle_format = "■ FORMAT..........: " + subtitle_format

            subtitle_block = f"""█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ ████▓▓▓▒▒▒░░░                   SUBTiTLES #{str(index).ljust(21)}░░░▒▒▒▓▓▓████ █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
█                                                                               █
█ ■ LANGUAGE........: {subtitle_language.ljust(20)}■ TYPE............: {subtitle_type.ljust(18)}█
█{subtitle_format.center(79)}█
█                                                                               █
"""
            subtitle_blocks.append(subtitle_block)

        # Remplacer les codes de langue par les noms complets
        subtitle_language = LANGUAGE_MAP.get(subtitle_language, subtitle_language).upper()

    # Obtenir le lien TMDb à partir du titre
    if tmdb_link_override:
        tmdb_link = tmdb_link_override
    else:
        tmdb_link = get_tmdb_link(title)

    # Notes
    custom_note     = input("Input for custom notes: ")
    custom_note_nfo = f"""█                                                                               █
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ ████▓▓▓▒▒▒░░░                       NOTE                        ░░░▒▒▒▓▓▓████ █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
█                                                                               █
█{custom_note.center(79)}█
█                                                                               █"""

    # Template complet
    ptn_parse        = PTN.parse(release_name)
    try:
        season          = str(ptn_parse['season']).ljust(20)
        episode         = str(ptn_parse['episode']).ljust(18)
        season_episode  = f'\n█ ■ SAiSON..........: {season}■ EPiSODE.........: {episode}█'
    except:
        season_episode = None
    release_name    = release_name.ljust(76)
    release_size    = release_size.ljust(20)
    release_date    = release_date.ljust(18)
    source          = source.ljust(58)
    video_codec     = video_codec.ljust(20)
    bitrate_video   = bitrate_video.ljust(18)
    resolution      = resolution.ljust(20)
    aspect_ratio    = aspect_ratio.ljust(18)
    fps             = (fps + " FPS").ljust(20)
    duration        = duration.ljust(18)

    if hdr_info:
        hdr_info_color  = ("█ ■ COLOR PRiMARiES.: " + hdr_info[0]).ljust(80) + '█'
        hdr_sub         = ''
        for i, j in enumerate(hdr_info[1].split(',')):
            j = j.replace("'", '').replace('[', '').replace(']', '').lstrip()
            if i < len(hdr_info[1].split(',')) - 1:
                hdr_sub = hdr_sub + '█     ' + '-'.rjust(17) + j.ljust(57) + '█' + "\n"
            else:
                hdr_sub = hdr_sub + '█     ' + '-'.rjust(17) + j.ljust(57) + '█'
        hdr_info        = '█' + " ■ HDR.............: ".ljust(79) + '█' + "\n" + hdr_sub

    def justify_and_split(text, width, char):
        # Justifie le texte à gauche pour la première ligne
        justified_text = text.ljust(width)
        
        # Si le texte justifié dépasse la largeur, le diviser en lignes
        if len(justified_text) > width:
            # Diviser le texte en lignes de la largeur spécifiée
            lines = []
            for i in range(0, len(justified_text), width):
                line = justified_text[i:i + width]
                if i == 0:
                    # Justification à gauche pour la première ligne
                    lines.append(char + line + "       " + char)
                else:
                    # Justification à droite pour les lignes suivantes
                    lines.append(char +  "  " + line.center(width) + "     " + char)
            return "\n".join(lines)
        else:
            return char + justified_text + char

    newline = "\n"
    template = f"""
▄█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█▄
█ ▄████████████████████▓▓▓▒▒▒░░░      TEAM      ░░░▒▒▒▓▓▓█████████████████████▄ █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄                            ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
█                                                                               █
█              ██████╗ ███████╗██████╗ ██╗██████╗ ████████╗██╗  ██╗             █
█              ██╔══██╗██╔════╝██╔══██╗██║██╔══██╗╚══██╔══╝██║  ██║             █
█              ██████╔╝█████╗  ██████╔╝██║██████╔╝   ██║   ███████║             █
█              ██╔══██╗██╔══╝  ██╔══██╗██║██╔══██╗   ██║   ██╔══██║             █
█              ██║  ██║███████╗██████╔╝██║██║  ██║   ██║   ██║  ██║             █
█              ╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝             █
█                                                                               █
█                                   PRESENTS                                    █
█                                                                               █
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ ████▓▓▓▒▒▒░░░                   RELEASE iNFOS                   ░░░▒▒▒▓▓▓████ █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
█                                                                               █
█ ■ TiTLE...........: {title.ljust(58)}█{ season_episode if season_episode else ''}
█ ■ RELEASE SiZE....: {release_size}■ RELEASE DATE....: {release_date}█
█ ■ SOURCE..........: {source}█
█                                                                               █
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ ████▓▓▓▒▒▒░░░                       ViDEO                       ░░░▒▒▒▓▓▓████ █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
█                                                                               █
█ ■ CODEC...........: {video_codec}■ BiTRATE.........: {bitrate_video}█
█ ■ RESOLUTiON......: {resolution}■ ASPECT RATiO....: {aspect_ratio}█
█ ■ FRAMERATE.......: {fps}■ DURATiON........: {duration}█{newline + hdr_info_color + newline + hdr_info if hdr_info else ''}
█                                                                               █
{''.join(audio_blocks)}{''.join(subtitle_blocks)}█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ ████▓▓▓▒▒▒░░░                       LiNKS                       ░░░▒▒▒▓▓▓████ █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
█                                                                               █
█ ■ TMDB............: {tmdb_link.ljust(58)}█
{custom_note_nfo if custom_note else '█' + ''.ljust(79) + '█'}
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ ████▓▓▓▒▒▒░░░                        THX                        ░░░▒▒▒▓▓▓████ █
█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
█                                                                               █
█                             ■ ManixQC   ■ MenFox                              █
█                                                                               █
█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
█ ▀███▓▓▓▒▒▒░░░                NO RULES! JUST FiLES!              ░░░▒▒▒▓▓▓███▀ █
▀█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█▀
"""
    return template

def process_directory(directory_path):
    """
    Parcourt un répertoire pour créer des fichiers .nfo pour chaque fichier vidéo trouvé.
    :param directory_path: Chemin du répertoire
    """
    supported_extensions = [".mp4", ".mkv"]
    for root, _, files in os.walk(directory_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(root, file)
                print(f"Traitement du fichier : {file_path}")
                try:
                  template = generate_template(file_path)
                  nfo_name = os.path.splitext(file)[0] + ".nfo"
                  nfo_path = os.path.join(root, nfo_name)

                  with open(nfo_path, "w", encoding="utf-8") as nfo_file:
                      nfo_file.write(template)
                      print(f"Le fichier .nfo a été créé à : {nfo_path}")
                except Exception as e:
                    print(f"Erreur lors du traitement du fichier {file_path}: {e}")

def process_file(filepath, tmdb_link_override=None):
    """
    Crée un fichier .nfo pour le fichier vidéo spécifié.
    :param filepath: Chemin du fichier vidéo
    """
    supported_extensions = [".mp4", ".mkv"]
    
    # Vérifier si l'extension du fichier est supportée
    if any(filepath.lower().endswith(ext) for ext in supported_extensions):
        print(f"Traitement du fichier : {filepath}")
        try:
            template = generate_template(filepath, tmdb_link_override)
            nfo_name = os.path.splitext(os.path.basename(filepath))[0] + "_custom.nfo"
            nfo_path = os.path.join(os.path.dirname(filepath), nfo_name)

            with open(nfo_path, "w", encoding="utf-8") as nfo_file:
                nfo_file.write(template)
            #print(f"Le fichier .nfo a été créé à : {nfo_path}")
            return nfo_path
        except Exception as e:
            print(f"Erreur lors du traitement du fichier {filepath}: {e}")
    else:
        print(f"Extension non supportée pour le fichier {filepath}")


if __name__ == '__main__':
    # Exemple d'utilisation
    directory = "./FILMS"
    process_directory(directory)
