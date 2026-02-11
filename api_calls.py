import requests
import random
from xml.etree import ElenmentTree

API_ENDPOINT = "https://api.rule34.xxx/index.php"

def fetch_posts(api_credentials: str, tags: list[str]) -> str | None:
    # convert API Access Credentials into a dict
    cred_parts = dict(pair.split("=", 1) for pair in apli_credentials.split("&"))

    # build tag string
    tag_string = " ".join(tags)

    params = {
        "page": "dapi",
        "s": "post",
        "q": "index",
        "limit": "200",
        "tags": tag_string
        **cred_parts
    }

    response = requests.get(API_ENDPOINT, params=params, timeout=10)

    if response.status_code != 200:
        raise RuntimeError(f"API returned status {response.status_code}")

    root = ElementTree.fromstring(response.text)
    posts = root.findall("post")
    if not posts:
        return None

    # pick a random post
    post = random.choice(posts)

    # extract the file url
    return post.attrib.get("file_url")