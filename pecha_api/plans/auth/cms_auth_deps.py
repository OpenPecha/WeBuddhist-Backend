from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

oauth2_scheme = HTTPBearer()


def get_cms_author_token(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> str:
    return authentication_credential.credentials
