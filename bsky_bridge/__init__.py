"""
bsky_bridge Library: A Python interface for interacting with the BlueSky social network's API.

Modules:
    bsky_session: Contains the BskyBridgeSession class for session management and authentication.
    post_utilities: Contains functions to perform various actions like posting content.
    api_utilities: Contains utility function for making API calls.
    image_utilities: Contains utility functions for image processing.
"""

from .bsky_session import BskySession
from .post_utilities import post_text, post_image
