from fastapi import APIRouter, HTTPException, Request
from app.settings import settings
import httpx


router = APIRouter("/notifications", tags=["webhook"])

@router.post("/notificacao_curso")
async def notificacao_curso(request: Request):
    body = await request.json()
    
    # Pegue os campos do corpo da notificação
    user_email = body.get("user_email")
    codigo_curso = body.get("codigo_curso")
    pontuacao = body.get("pontuacao", 0)
    
    if not user_email or not codigo_curso:
        raise HTTPException(status_code=400, detail="user_email e codigo_curso são obrigatórios.")
    
    # Monta o payload conforme exigido pela Comunitive
    payload = {
        "user": user_email,
        "points": pontuacao,
        "data": {
            "codigo_curso": codigo_curso
        }
    }
    
    # Faz a chamada POST para o webhook da Comunitive
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.comunitive_api_url, json=payload)
        if response.status_code not in [200, 201, 204]:
            raise HTTPException(
                status_code=502,
                detail=f"Erro ao notificar Comunitive: {response.status_code} - {response.text}"
            )
    
    return {"status": "sucesso", "detalhe": "Notificação enviada à Comunitive."}

