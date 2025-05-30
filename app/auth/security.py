# app/auth/security.py

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError # pip install python-jose[cryptography]
from passlib.context import CryptContext # pip install passlib[bcrypt]
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.api.schemas.authentication import User
from app.settings import settings

# --- Configuração de Hashing de Senha ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera o hash de uma senha em texto plano."""
    return pwd_context.hash(password)

# --- Configuração JWT ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token") # Endpoint onde o cliente obtém o token

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um token de acesso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decodifica e valida um token de acesso JWT."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- Funções de Dependência FastAPI para Autenticação ---
ADMIN_USER_PASSWORD_HASHED = get_password_hash(settings.ADMIN_USER_PASSWORD) # Mude para uma senha segura!

async def get_user_by_email(email: str) -> Optional[User]:
    """Simula a busca de um usuário no banco de dados."""
    if email == settings.ADMIN_USER_EMAIL:
        return User(username=settings.ADMIN_USER_EMAIL)
    return None

async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Autentica o usuário verificando a senha."""
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, ADMIN_USER_PASSWORD_HASHED):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dependência para obter o usuário logado a partir do token."""
    payload = decode_access_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido", headers={"WWW-Authenticate": "Bearer"})
    
    user = await get_user_by_email(username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado ou inativo", headers={"WWW-Authenticate": "Bearer"})
    
    return user
