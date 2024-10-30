from datetime import datetime
import os
import logging 
from PIL import Image
from .image_utilities import resize_image, MAX_IMAGE_SIZE


def post_text(session, text):
    """
    Post a text message to BlueSky using an authenticated session.

    Args:
        session (BskySession): An authenticated session instance.
        text (str): The content of the text to be posted.

    Returns:
        dict: Server's response as a dictionary.

    Raises:
        ConnectionError: If there's an issue posting the text to BlueSky.
    """
    endpoint = "com.atproto.repo.createRecord"
    now = datetime.now().astimezone().isoformat()
    post_data = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": now,
    }
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
        session (BskySession): Authenticated session instance.
        image_path (str): Path to the image to be uploaded.

    Returns:
        dict: Blob metadata.

    Raises:
        Exception: If image size exceeds the allowed size.
        requests.RequestException: If there's an issue uploading the image.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"{image_path} not found.")
    
    img_bytes = resize_image(image_path)
    
    with Image.open(image_path) as img:
        image_mimetype = img.get_format_mimetype()

    if len(img_bytes) > MAX_IMAGE_SIZE:
        raise ValueError(
            f"Image size remains too large after compression (image_utilities.py). Maximum allowed size is {MAX_IMAGE_SIZE} bytes, "
            f"but after compression, the size is {len(img_bytes)} bytes. Consider using a lower resolution or quality."
        )

    endpoint = "com.atproto.repo.uploadBlob"
    headers = {"Content-Type": image_mimetype, "Authorization": f"Bearer {session.access_token}"}
    
    try:
        resp = session.api_call(endpoint, method='POST', data=img_bytes, headers=headers)
        return resp["blob"]
    except Exception as e:
        logging.error("Error uploading image: %s", e)
        raise


def post_image(session, post_text, image_path, alt_text=""):
    """
    Posts an image to BlueSky with an optional text.

    Args:
        session (BskySession): Authenticated session instance.
        post_text (str): Text to be posted with the image.
        image_path (str): Path to the image to be posted.
        alt_text (str): Alt text for the image. Defaults to an empty string.

    Returns:
        dict: Response from server after creating the post.

    Raises:
        requests.RequestException: If there's an issue posting the image.
    """
    blob = send_image(session, image_path)

    now = datetime.now().astimezone().isoformat()
    post_data = {
        "$type": "app.bsky.feed.post",
        "text": post_text,
        "createdAt": now,
        "embed": {
            "$type": "app.bsky.embed.images",
            "images": [{
                "alt": alt_text,
                "image": blob
            }],
        },
    }

    endpoint = "com.atproto.repo.createRecord"
    json_payload = {
        "repo": session.did,
        "collection": "app.bsky.feed.post",
        "record": post_data,
    }

    return session.api_call(endpoint, method='POST', json=json_payload)
