# app/services/comunitive.py
import logging
from fastapi import HTTPException
from app.services.slack import send_slack_message
import httpx

logger = logging.getLogger(__name__)

async def notificacao_curso(user_email: str, comunitive_webhook_uri: str):
    """
    Envia uma notificação para a Comunitive através de um webhook.
    """
    if not user_email or not comunitive_webhook_uri:
        raise HTTPException(status_code=400, detail="user_email e comunitive_webhook_uri são obrigatórios.")
    
    # Monta o payload conforme exigido pela Comunitive
    payload = {
        "user": user_email,
    }
    
    # Faz a chamada POST para o webhook da Comunitive
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(comunitive_webhook_uri, json=payload)
            
            response.raise_for_status()  # Lança uma exceção para códigos de status 4xx e 5xx automaticamente

            # Verifica a estrutura esperada da resposta
            response_data = response.json()
            if "id" not in response_data:
                slack_error_message = (
                    f"Comunitive Webhook Erro\n"
                    f"❌ Erro ao notificar Comunitive: `{response.status_code}` - `{response.text}`\n"
                    f"Payload enviado: {payload}"
                )
                send_slack_message(slack_error_message)
                
                raise HTTPException(
                    status_code=400,
                    detail=f"Resposta inválida da Comunitive: {response.status_code} - {response.text}"
                )
            
            logger.info(f"Notificação enviada para a Comunitive com sucesso para o usuário {user_email}.")
            return {"status": "sucesso", "detalhe": "Notificação enviada à Comunitive com sucesso."}

    except httpx.RequestError as e:
        logger.error(f"Erro de rede ao acessar Comunitive: {e}")
        raise HTTPException(status_code=502, detail="Erro de rede ao acessar Comunitive.")

    except HTTPException as e:
        logger.error(f"Erro HTTP ao notificar Comunitive: {e.detail}")
        raise

    except Exception as e:
        logger.error(f"Erro inesperado ao notificar Comunitive: {e}")
        send_slack_message(f"Erro inesperado ao notificar Comunitive: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao notificar Comunitive.")
    