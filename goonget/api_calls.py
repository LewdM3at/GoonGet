import requests
import random
from xml.etree import ElementTree
from .settings_handler import get_source

def fetch_posts(api_credentials: str, tags: list[str]) -> str | None:
    # safely parse credentials into a dict
    cred_parts = {}
    for part in api_credentials.split("&"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        cred_parts[key] = value

    # build credential string manually 
    cred_string = "&".join(f"{k}={v}" for k, v in cred_parts.items())

    # build tag string (space-separated for requests)
    tag_string = " ".join(tags)

    # build final URL
    source = get_source()
    if source == "rule34.xxx":
        url = ( 
            f"https://api.{source}/index.php" 
            f"?page=dapi&s=post&q=index&limit=500" 
            f"&tags={tag_string}" 
            f"&{cred_string}" 
        )
    elif source == "gelbooru.com":
        url = ( 
            f"https://{source}/index.php" 
            f"?page=dapi&s=post&q=index&limit=500" 
            f"&tags={tag_string}" 
            f"&{cred_string}" 
        )

    response = requests.get(url, timeout=10)

    # debug: show final API URL
    #print("Final API URL:", response.url)

    if response.status_code != 200:
        raise RuntimeError(f"API returned status {response.status_code}")

    root = ElementTree.fromstring(response.text)
    posts = root.findall("post")
    if not posts:
        return []

    urls = [] 
    for post in posts:
        if source == "rule34.xxx":
            file_url = post.get("file_url")
        elif source == "gelbooru.com":
            file_url = post.find("file_url").text if post.find("file_url") is not None else None
        if not file_url: 
            continue 
        urls.append(file_url) 

    return urls
