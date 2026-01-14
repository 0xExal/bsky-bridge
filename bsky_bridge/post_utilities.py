import re
from datetime import datetime
import os
import logging
from typing import Union
from PIL import Image
from .image_utilities import resize_image, MAX_IMAGE_SIZE


# Valid reply control options
REPLY_CONTROLS = {
    "mentions": "app.bsky.feed.threadgate#mentionRule",
    "following": "app.bsky.feed.threadgate#followingRule",
    "followers": "app.bsky.feed.threadgate#followerRule",
}

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
    # Matches @handle at start of text or after whitespace/non-word character
    mention_regex = rb"(?:^|[\s\W])(@([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
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
    # Matches URLs at start of text or after whitespace/non-word character
    url_regex = rb"(?:^|[\s\W])(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
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
    tag_regex = r"(?<!\w)(#[\w]+)"
    
    for match in re.finditer(tag_regex, text, re.UNICODE):
        tag = match.group(1)
        byte_start = len(text[:match.start(1)].encode('utf-8'))
        byte_end = byte_start + len(tag.encode('utf-8'))
        spans.append({
            "start": byte_start,
            "end": byte_end,
            "tag": tag[1:]
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


def set_threadgate(session, post_uri: str, reply_to: Union[str, list, None]):
    """
    Sets who can reply to a post by creating a threadgate record.

    Args:
        session: The session object used to interact with the BlueSky API.
        post_uri (str): The AT URI of the post (e.g., "at://did:plc:.../app.bsky.feed.post/...")
        reply_to: Controls who can reply. Options:
            - None: Anyone can reply (no threadgate created)
            - "nobody": No one can reply
            - "mentions": Only mentioned users can reply
            - "following": Only users you follow can reply
            - "followers": Only your followers can reply
            - List of the above (e.g., ["mentions", "following"])

    Returns:
        dict: The response from the API, or None if no threadgate was created.
    """
    if reply_to is None:
        return None

    # Extract rkey from post URI
    # Format: at://did:plc:xxx/app.bsky.feed.post/rkey
    rkey = post_uri.split("/")[-1]

    # Build allow rules
    allow = []
    if reply_to == "nobody":
        # Empty allow array = no one can reply
        allow = []
    else:
        # Convert single string to list
        rules = [reply_to] if isinstance(reply_to, str) else reply_to

        for rule in rules:
            if rule in REPLY_CONTROLS:
                allow.append({"$type": REPLY_CONTROLS[rule]})
            elif rule.startswith("at://"):
                # It's a list URI
                allow.append({
                    "$type": "app.bsky.feed.threadgate#listRule",
                    "list": rule
                })
            else:
                logging.warning(f"Unknown reply control rule: {rule}")

    now = datetime.now().astimezone().isoformat()

    record = {
        "$type": "app.bsky.feed.threadgate",
        "post": post_uri,
        "allow": allow,
        "createdAt": now,
    }

    json_payload = {
        "repo": session.did,
        "collection": "app.bsky.feed.threadgate",
        "rkey": rkey,
        "record": record,
    }

    return session.api_call("com.atproto.repo.createRecord", method='POST', json=json_payload)


def post_text(session, text: str, langs: list = None, reply_to: Union[str, list, None] = None):
    """
    Posts a text message to BlueSky, including support for mentions, links, and hashtags.
    Optionally includes language information if 'langs' is provided.

    Args:
        session: The session object used to interact with the BlueSky API.
        text (str): The text message to post.
        langs (list, optional): List of language codes to specify manually. If None, the 'langs' field is omitted.
        reply_to: Controls who can reply. Options:
            - None: Anyone can reply (default)
            - "nobody": No one can reply
            - "mentions": Only mentioned users can reply
            - "following": Only users you follow can reply
            - "followers": Only your followers can reply
            - List combining options (e.g., ["mentions", "following"])

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

    response = session.api_call(endpoint, method='POST', json=json_payload)

    # Set threadgate if reply_to is specified
    if reply_to is not None:
        set_threadgate(session, response["uri"], reply_to)

    return response


def post_image(session, post_text: str, image_path: str, alt_text: str = "", langs: list = None, reply_to: Union[str, list, None] = None):
    """
    Posts a single image to BlueSky with accompanying text.
    This is a convenience wrapper around post_images for single image posts.

    Args:
        session: The session object used to interact with the BlueSky API.
        post_text (str): The text message to post with the image.
        image_path (str): The local path to the image file to upload.
        alt_text (str, optional): The alt text for the image.
        langs (list, optional): List of language codes to specify manually. If None, the 'langs' field is omitted.
        reply_to: Controls who can reply (see post_text for options).

    Returns:
        dict: The response from the API after posting the image and text.
    """
    return post_images(session, post_text, [{"path": image_path, "alt": alt_text}], langs, reply_to)


def post_images(session, post_text: str, images: list, langs: list = None, reply_to: Union[str, list, None] = None):
    """
    Posts up to 4 images to BlueSky with accompanying text, including support for mentions, links, and hashtags.
    Optionally includes language information if 'langs' is provided.

    Args:
        session: The session object used to interact with the BlueSky API.
        post_text (str): The text message to post with the images.
        images (list): List of image dicts, each with 'path' (required) and 'alt' (optional) keys.
                       Example: [{"path": "/path/to/img1.jpg", "alt": "Description"}, {"path": "/path/to/img2.jpg"}]
                       Maximum 4 images allowed.
        langs (list, optional): List of language codes to specify manually. If None, the 'langs' field is omitted.
        reply_to: Controls who can reply (see post_text for options).

    Returns:
        dict: The response from the API after posting the images and text.

    Raises:
        ValueError: If more than 4 images are provided.
    """
    if len(images) > 4:
        raise ValueError("Bluesky allows a maximum of 4 images per post.")

    if not images:
        raise ValueError("At least one image is required.")

    now = datetime.now().astimezone().isoformat()
    facets = create_facets(post_text, session)

    # Upload all images and build the images array
    uploaded_images = []
    for img in images:
        image_path = img.get("path") or img.get("image_path")
        alt_text = img.get("alt", "")

        if not image_path:
            raise ValueError("Each image must have a 'path' key.")

        blob, aspect_ratio = send_image(session, image_path)
        uploaded_images.append({
            "alt": alt_text,
            "image": blob,
            "aspectRatio": aspect_ratio
        })

    post_data = {
        "$type": "app.bsky.feed.post",
        "text": post_text,
        "createdAt": now,
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": uploaded_images,
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

    response = session.api_call(endpoint, method='POST', json=json_payload)

    # Set threadgate if reply_to is specified
    if reply_to is not None:
        set_threadgate(session, response["uri"], reply_to)

    return response

def send_image(session, image_path):
    """
    Uploads an image to BlueSky and returns the blob metadata.

    Args:
        session: The session object used to interact with the BlueSky API.
        image_path (str): The local path to the image file to upload.

    Returns:
        tuple: (blob metadata, aspect_ratio dict with width/height)

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the image size exceeds the allowed maximum after resizing.
        Exception: If there is an error while uploading the image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"{image_path} not found.")

    # resize_image now returns (bytes, aspect_ratio) with correct post-resize dimensions
    img_bytes, aspect_ratio = resize_image(image_path)

    # Get mimetype from original image
    with Image.open(image_path) as img:
        image_mimetype = img.get_format_mimetype()

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