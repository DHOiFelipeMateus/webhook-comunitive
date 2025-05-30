# app/api/routers/auth_router.py

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Para autenticação de formulário padrão

from app.api.schemas.authentication import Token # Importe o modelo de token
from app.auth.security import authenticate_user, create_access_token # Importe as funções de segurança

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint para autenticação de usuário e geração de token de acesso.
    Recebe username (email) e password via formulário OAuth2.
    """
    logger.info(f"Tentativa de login para o usuário: {form_data.username}")
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Falha de autenticação para o usuário: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais incorretas (usuário ou senha)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    logger.info(f"Token gerado com sucesso para o usuário: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}
