import logging
import requests

class BskySession:
    """
    Represents a session with the BlueSky social network. 
    The session handles authentication and provides methods for making authenticated requests.
    
    Attributes:
        handle (str): The user handle (e.g., username) used for authentication.
        app_password (str): The application-specific password for authentication.
        access_token (str): Token provided by BlueSky after successful authentication.
        did (str): A unique identifier for the session.
    """
    
    BASE_URL = "https://bsky.social/xrpc"

    def __init__(self, handle, app_password):
        """
        Initializes a BlueSky session.

        Args:
            handle (str): User handle for authentication.
            app_password (str): Application-specific password for authentication.
        """
        self.handle = handle
        self.app_password = app_password
        self.access_token, self.did = self._create_session()

    def _create_session(self):
        """
        Creates a session with BlueSky.

        Returns:
            tuple: Access token and DID for the session.
        """
        url = f"{self.BASE_URL}/com.atproto.server.createSession"
        try:
            resp = requests.post(url, json={"identifier": self.handle, "password": self.app_password}, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            logging.error("Error %s: %s", resp.status_code, resp.text)
            raise ConnectionError(f"Error creating session: {resp.text}") from e

        session = resp.json()
        return session["accessJwt"], session["did"]

    def get_auth_header(self):
        """
        Generates the authentication header using the session's access token.

        Returns:
            dict: Authorization header for authenticated API requests.
        """
        return {"Authorization": f"Bearer {self.access_token}"}

    def api_call(self, endpoint, method='GET', json=None, data=None, headers=None, params=None):
        """
        Makes an authenticated API call to the specified endpoint.

        Args:
            endpoint (str): The API endpoint to call.
            method (str): The HTTP method to use for the request.
            json (dict): The JSON payload to send with the request.
            data (bytes): The data to send with the request.
            headers (dict): Additional headers to send with the request.
            params (dict): Parameters to include in the query string.

        Returns:
            dict: The server's response as a dictionary.
        """
        url = f"{self.BASE_URL}/{endpoint}"
        if params:
            from urllib.parse import urlencode
            url = f"{url}?{urlencode(params)}"
        
        headers = headers or {}
        headers.update(self.get_auth_header())
        
        try:
            resp = requests.request(method, url, headers=headers, json=json, data=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logging.error("Error in API call: %s", e)
            raise