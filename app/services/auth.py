from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token


def authenticate_demo_user(username: str, password: str) -> str:
    if username != settings.DEMO_USERNAME or password != settings.DEMO_PASSWORD:
        raise AuthenticationError("Username or password is incorrect")
    return create_access_token(subject=username)
