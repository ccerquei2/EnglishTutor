# /app/dependencies.py

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError

# Este esquema informa ao FastAPI para procurar por um 'Bearer Token' no cabeçalho Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# A chave secreta do JWT do seu projeto Supabase
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("SUPABASE_JWT_SECRET não encontrado no .env")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Decodifica o token JWT para obter o ID do usuário (sub).
    Esta função é uma dependência que pode ser usada em qualquer endpoint.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica o token usando a chave secreta
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            # A correção da 'audience' é mantida pois é essencial para o funcionamento
            audience="authenticated"
        )
        # O ID do usuário está no campo 'sub' (subject) do token
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except InvalidTokenError:
        # Se o token for inválido (expirado, assinatura errada, audience errada, etc.)
        raise credentials_exception