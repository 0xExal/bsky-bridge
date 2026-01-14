# bsky-bridge

A Python library for the BlueSky Social Network API.

[![PyPI version](https://badge.fury.io/py/bsky-bridge.svg)](https://pypi.org/project/bsky-bridge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Simple authentication with automatic session persistence
- Automatic token refresh and rate limit handling
- Post text with mentions, links, and hashtags (auto-detected)
- Post up to 4 images per post with alt text support
- Automatic image optimization (resize, compress, EXIF stripping)
- Language specification for multilingual posts
- Reply controls (threadgate) - restrict who can reply to your posts

## Installation

```bash
pip install bsky-bridge
```

## Quick Start

```python
from bsky_bridge import BskySession, post_text

session = BskySession("your_handle.bsky.social", "your_app_password")
post_text(session, "Hello BlueSky!")
```

## Usage

### Authentication

Create a session using your BlueSky handle and an [App Password](https://bsky.app/settings/app-passwords) (not your main password):

```python
from bsky_bridge import BskySession

session = BskySession("your_handle.bsky.social", "your_app_password")
```

Sessions are automatically saved to `.bsky_sessions/` and reused. To use a custom directory:

```python
session = BskySession("your_handle.bsky.social", "your_app_password", session_dir="/path/to/sessions")
```

### Posting Text

```python
from bsky_bridge import BskySession, post_text

session = BskySession("your_handle.bsky.social", "your_app_password")

# Simple post
post_text(session, "Hello BlueSky!")

# Mentions, links, and hashtags are automatically detected
post_text(session, "Hey @friend.bsky.social check out https://example.com #coding")
```

### Posting a Single Image

```python
from bsky_bridge import BskySession, post_image

session = BskySession("your_handle.bsky.social", "your_app_password")

post_image(
    session,
    "Check out this photo!",
    "/path/to/image.jpg",
    alt_text="A beautiful sunset"
)
```

### Posting Multiple Images

Post up to 4 images in a single post:

```python
from bsky_bridge import BskySession, post_images

session = BskySession("your_handle.bsky.social", "your_app_password")

post_images(session, "My photo gallery!", [
    {"path": "/path/to/image1.jpg", "alt": "First image"},
    {"path": "/path/to/image2.jpg", "alt": "Second image"},
    {"path": "/path/to/image3.jpg", "alt": "Third image"},
    {"path": "/path/to/image4.jpg", "alt": "Fourth image"},
])
```

### Specifying Languages

Help BlueSky's feed algorithms by specifying post languages:

```python
from bsky_bridge import post_text, post_image

# Multilingual text post
post_text(session, "Bonjour! Hello!", langs=["fr", "en-US"])

# Image post with languages
post_image(
    session,
    "Belle photo! Beautiful photo!",
    "/path/to/image.jpg",
    alt_text="Landscape",
    langs=["fr", "en-US"]
)
```

### Reply Controls (Threadgate)

Control who can reply to your posts using the `reply_to` parameter:

```python
from bsky_bridge import post_text

# No one can reply
post_text(session, "This is a statement.", reply_to="nobody")

# Only mentioned users can reply
post_text(session, "Hey @friend.bsky.social what do you think?", reply_to="mentions")

# Only people you follow can reply
post_text(session, "Question for my friends", reply_to="following")

# Only your followers can reply
post_text(session, "Followers only discussion", reply_to="followers")

# Combine multiple rules
post_text(session, "Limited discussion", reply_to=["mentions", "following"])
```

Available options:

| Option | Description |
|--------|-------------|
| `None` | Anyone can reply (default) |
| `"nobody"` | No one can reply |
| `"mentions"` | Only mentioned users |
| `"following"` | Only people you follow |
| `"followers"` | Only your followers |
| `["option1", "option2"]` | Combine multiple rules |

Works with all post functions (`post_text`, `post_image`, `post_images`).

### Making Custom API Calls

Use the session to make authenticated calls to any AT Protocol endpoint:

```python
# GET request
profile = session.api_call(
    "app.bsky.actor.getProfile",
    method="GET",
    params={"actor": "someone.bsky.social"}
)

# POST request
session.api_call(
    "com.atproto.repo.createRecord",
    method="POST",
    json={
        "repo": session.did,
        "collection": "app.bsky.feed.like",
        "record": {
            "$type": "app.bsky.feed.like",
            "subject": {"uri": "at://...", "cid": "..."},
            "createdAt": "2024-01-01T00:00:00Z"
        }
    }
)
```

### Logging Out

```python
session.logout()  # Clears tokens and deletes session file
```

## Image Handling

Images are automatically processed before upload:

| Feature | Details |
|---------|---------|
| Max size | 1 MB (auto-compressed if larger) |
| Max dimensions | 3840x2160 (auto-resized if larger) |
| EXIF data | Automatically stripped for privacy |
| Aspect ratio | Preserved and sent to API |
| Formats | JPEG, PNG (transparency preserved) |

## Rate Limiting

The library automatically handles BlueSky's rate limits:

- Detects HTTP 429 responses
- Reads `Retry-After` and `RateLimit-Reset` headers
- Falls back to exponential backoff (1s, 2s, 4s...)
- Retries up to 3 times before raising an error

## API Reference

### BskySession

```python
BskySession(handle: str, app_password: str, session_dir: str = None)
```

| Method | Description |
|--------|-------------|
| `api_call(endpoint, method, json, data, headers, params)` | Make authenticated API call |
| `get_auth_header()` | Get Authorization header dict |
| `logout()` | Clear session and delete stored tokens |

### Functions

| Function | Description |
|----------|-------------|
| `post_text(session, text, langs=None, reply_to=None)` | Post text content |
| `post_image(session, text, image_path, alt_text="", langs=None, reply_to=None)` | Post single image |
| `post_images(session, text, images, langs=None, reply_to=None)` | Post up to 4 images |
| `set_threadgate(session, post_uri, reply_to)` | Set reply controls on existing post |

## Contributing

Contributions are welcome! Please submit issues for bugs and pull requests for new features.

## License

[MIT License](LICENSE)
