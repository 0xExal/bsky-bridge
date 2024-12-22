import re
from datetime import datetime
import os
import logging
from PIL import Image
from .image_utilities import resize_image, MAX_IMAGE_SIZE

def parse_mentions(text: str) -> list[dict]:
    """
    Parses mentions (@handle) from the given text and returns their byte positions.

    Args:
        text (str): The input text to parse for mentions.

    Returns:
        list[dict]: A list of dictionaries, each containing the byte start, byte end positions, and the handle for each mention.
    """
    spans = []
    # regex for handles based on Bluesky spec
    mention_regex = rb"[$|\W](@([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
    text_bytes = text.encode("UTF-8")
    for m in re.finditer(mention_regex, text_bytes):
        spans.append({
            "start": m.start(1),
            "end": m.end(1),
            "handle": m.group(1)[1:].decode("UTF-8")
        })
    return spans

def parse_urls(text: str) -> list[dict]:
    """
    Parses URLs from the given text and returns their byte positions.

    Args:
        text (str): The input text to parse for URLs.

    Returns:
        list[dict]: A list of dictionaries, each containing the byte start, byte end positions, and the URL.
    """
    spans = []
    # regex for handles based on Bluesky spec
    url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
    text_bytes = text.encode("UTF-8")
    for m in re.finditer(url_regex, text_bytes):
        spans.append({
            "start": m.start(1),
            "end": m.end(1),
            "url": m.group(1).decode("UTF-8"),
        })
    return spans

def parse_tags(text: str) -> list[dict]:
    """
    Parses hashtags (#tag) from the given text and returns their byte positions.

    Args:
        text (str): The input text to parse for hashtags.

    Returns:
        list[dict]: A list of dictionaries, each containing the byte start, byte end positions, and the tag.
    """
    spans = []
    # regex for hashtags
    tag_regex = rb"[$|\W](#[a-zA-Z0-9_]+)"
    text_bytes = text.encode("UTF-8")
    for m in re.finditer(tag_regex, text_bytes):
        spans.append({
            "start": m.start(1),
            "end": m.end(1),
            "tag": m.group(1)[1:].decode("UTF-8")
        })
    return spans

def create_facets(text: str, session) -> list[dict]:
    """
    Creates facets from the text by parsing mentions, URLs, and hashtags.

    Args:
        text (str): The input text containing mentions, URLs, and hashtags.
        session: The session object used to make API calls for resolving mentions.

    Returns:
        list[dict]: A list of facets where each facet includes information about the mentions, URLs, or hashtags.
    """
    facets = []
    
    # Process mentions
    for m in parse_mentions(text):
        try:
            resp = session.api_call(
                "com.atproto.identity.resolveHandle",
                method='GET',
                params={"handle": m["handle"]}
            )
            did = resp["did"]
            facets.append({
                "index": {
                    "byteStart": m["start"],
                    "byteEnd": m["end"],
                },
                "features": [{"$type": "app.bsky.richtext.facet#mention", "did": did}],
            })
        except Exception as e:
            logging.warning(f"Could not resolve handle {m['handle']}: {e}")
            continue

    # Process URLs
    for u in parse_urls(text):
        facets.append({
            "index": {
                "byteStart": u["start"],
                "byteEnd": u["end"],
            },
            "features": [{
                "$type": "app.bsky.richtext.facet#link",
                "uri": u["url"],
            }]
        })

    # Process hashtags
    for t in parse_tags(text):
        facets.append({
            "index": {
                "byteStart": t["start"],
                "byteEnd": t["end"],
            },
            "features": [{
                "$type": "app.bsky.richtext.facet#tag",
                "tag": t["tag"],
            }]
        })

    return facets

def post_text(session, text: str, langs: list = None):
    """
    Posts a text message to BlueSky, including support for mentions, links, and hashtags.
    Optionally includes language information if 'langs' is provided.

    Args:
        session: The session object used to interact with the BlueSky API.
        text (str): The text message to post.
        langs (list, optional): List of language codes to specify manually. If None, the 'langs' field is omitted.

    Returns:
        dict: The response from the API after posting the text message.
    """
    endpoint = "com.atproto.repo.createRecord"
    now = datetime.now().astimezone().isoformat()
    
    facets = create_facets(text, session)
    
    post_data = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": now,
    }
    
    if langs:
        post_data["langs"] = langs
    
    if facets:
        post_data["facets"] = facets

    json_payload = {
        "repo": session.did,
        "collection": "app.bsky.feed.post",
        "record": post_data,
    }
    
    return session.api_call(endpoint, method='POST', json=json_payload)


def post_image(session, post_text: str, image_path: str, alt_text: str = "", langs: list = None):
    """
    Posts an image to BlueSky with accompanying text, including support for mentions, links, and hashtags.
    Optionally includes language information if 'langs' is provided.

    Args:
        session: The session object used to interact with the BlueSky API.
        post_text (str): The text message to post with the image.
        image_path (str): The local path to the image file to upload.
        alt_text (str, optional): The alt text for the image.
        langs (list, optional): List of language codes to specify manually. If None, the 'langs' field is omitted.

    Returns:
        dict: The response from the API after posting the image and text.
    """
    blob, aspect_ratio = send_image(session, image_path)
    now = datetime.now().astimezone().isoformat()
    facets = create_facets(post_text, session)
    
    post_data = {
        "$type": "app.bsky.feed.post",
        "text": post_text,
        "createdAt": now,
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": [{
                "alt": alt_text,
                "image": blob,
                "aspectRatio": aspect_ratio
            }],
        },
    }
    
    if langs:
        post_data["langs"] = langs
    
    if facets:
        post_data["facets"] = facets

    endpoint = "com.atproto.repo.createRecord"
    json_payload = {
        "repo": session.did,
        "collection": "app.bsky.feed.post",
        "record": post_data,
    }
    
    return session.api_call(endpoint, method='POST', json=json_payload)

def send_image(session, image_path):
    """
    Uploads an image to BlueSky and returns the blob metadata.

    Args:
        session: The session object used to interact with the BlueSky API.
        image_path (str): The local path to the image file to upload.

    Returns:
        dict: The metadata of the uploaded image, including the blob information.
    
    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image size exceeds the allowed maximum after resizing.
        Exception: If there is an error while uploading the image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"{image_path} not found.")

    img_bytes = resize_image(image_path)
    with Image.open(image_path) as img:
        image_mimetype = img.get_format_mimetype()
        aspect_ratio = {
            "width": img.width,
            "height": img.height
        }

    if len(img_bytes) > MAX_IMAGE_SIZE:
        raise ValueError(
            f"Image size remains too large after compression. Maximum allowed size is {MAX_IMAGE_SIZE} bytes, "
            f"but after compression, the size is {len(img_bytes)} bytes. Consider using a lower resolution or quality."
        )

    endpoint = "com.atproto.repo.uploadBlob"
    headers = {"Content-Type": image_mimetype, "Authorization": f"Bearer {session.access_token}"}
    
    try:
        resp = session.api_call(endpoint, method='POST', data=img_bytes, headers=headers)
        return resp["blob"], aspect_ratio
    except Exception as e:
        logging.error("Error uploading image: %s", e)
        raise