# /EnglishTutor/app/dependencies.py

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError

# Este esquema informa ao FastAPI para procurar por um 'Bearer Token' no cabeçalho Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# A chave secreta do JWT do seu projeto Supabase
# Você encontra em: Project Settings -> API -> JWT Settings -> JWT Secret
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("SUPABASE_JWT_SECRET não encontrado no .env")


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Decodifica o token JWT para obter o ID do usuário (sub).
    Esta função é uma dependência que pode ser usada em qualquer endpoint.
    """
    try:
        # Decodifica o token usando a chave secreta
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            # ### CORREÇÃO APLICADA AQUI ###
            # Descomentamos e definimos a 'audience' esperada.
            # O Supabase usa 'authenticated' como o público padrão para tokens de acesso.
            audience="authenticated"
        )
        # O ID do usuário está no campo 'sub' (subject) do token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: não foi possível encontrar o ID do usuário.",
            )
        return user_id
    except InvalidTokenError as e:
        # Se o token for inválido (expirado, assinatura errada, audience errada, etc.)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido ou expirado: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )