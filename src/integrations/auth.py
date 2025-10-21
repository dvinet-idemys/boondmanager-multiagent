"""BoondManager JWT authentication token generation."""

from datetime import datetime
from typing import Literal

from jose import jwt

from src.config import config


def new_token(
    user_token: str = None,
    client_token: str = None,
    client_key: str = None,
    mode: Literal["normal", "god"] = "normal",
) -> str:
    """Generate new JWT token for BoondManager API authentication.

    Args:
        mode: Authentication mode, defaults to "normal"

    Returns:
        Encoded JWT token string

    Example:
        >>> token = new_token()
        >>> # Use token in Authorization header: f"Bearer {token}"
    """
    timestamp = datetime.now().timestamp()

    if user_token is None:
        user_token = config.boond_user_token

    if client_token is None:
        client_token = config.boond_client_token

    if client_key is None:
        client_key = config.boond_client_key

    payload = {
        "userToken": user_token,
        "clientToken": client_token,
        "time": timestamp,
        "mode": mode,
    }

    token = jwt.encode(payload, client_key, algorithm="HS256")

    return token
