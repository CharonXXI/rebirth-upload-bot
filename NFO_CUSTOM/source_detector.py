import os

def detect_source(filepath):
    """Detect the source and region of the file based on tags in its name."""
    filename = os.path.basename(filepath)
    source = "WEB"

    # Known streaming platforms
    platform_map = {
            ".NF.": "Netflix",
            ".AMZN.": "Amazon Prime Vidéo",
            ".HMAX.": "HBO Max",
            ".CR.": "CRUNCHYROLL",
            ".CRITERION.": "The Criterion Collection",
            ".HULU.": "HULU",
            ".ADN.": "Anime Digital Network",
            ".DSNP.": "Disney+",
            ".HULU.": "Hulu",
            ".APPLTV.": "Apple TV+",
            ".ATVP.": "Apple TV+",
            ".PCOK.": "Peacock",
            ".iT.": "iTunes",
            ".CNLP.": "Canal+",
            ".PMTP.": "Paramount+",
            ".PRIME.": "Amazon Prime Vidéo",
            }

    flag = False
    for code, platform in platform_map.items():
        if code in filename.upper():
            source += f" ({platform})"
            flag = True
            break

    # Check for BluRay
    if flag == False:
        source = input("Input for other source than WEB: ")

    return source