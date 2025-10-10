"""BoondManager JWT authentication token generation."""

from typing import Literal
from datetime import datetime

from jose import jwt

from src.config import config


def create_payload(
    user_token: str,
    client_token: str,
    time: float,
    mode: Literal["normal", "god"],
) -> dict[str, str | float]:
    """Create JWT payload for BoondManager authentication.

    Args:
        user_token: User authentication token
        client_token: Client authentication token
        time: Unix timestamp
        mode: Authentication mode ("normal" or "god")

    Returns:
        JWT payload dictionary
    """
    return {
        "userToken": user_token,
        "clientToken": client_token,
        "time": time,
        "mode": mode,
    }


def new_token(mode: Literal["normal", "god"] = "normal") -> str:
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
    payload = create_payload(
        config.boond_user_token,
        config.boond_client_token,
        timestamp,
        mode,
    )

    token = jwt.encode(payload, config.boond_client_key, algorithm="HS256")

    return token
