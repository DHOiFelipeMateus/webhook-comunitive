# app/schemas/auth.py

from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    # Isso representa um usuário no seu sistema, pode ser mais complexo
    # Ex: email, id, roles, etc.
    username: str

class UserLogin(BaseModel):
    # Modelo para a requisição de login
    email: str
    password: str
