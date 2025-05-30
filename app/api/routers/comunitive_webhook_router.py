# app/api/endpoints/notifications.py

import logging
import traceback
from fastapi import APIRouter, HTTPException, status
from app.services.slack import send_slack_message
from app.api.schemas.scorm_postback import ScormRegistrationPostback

from app.usecases.process_scorm_postback import (
    ProcessScormPostbackUseCase,
    MappingNotFoundError,
    ComunitiveNotificationError,
    ScormPostbackProcessingError
)
from app.services.gcs_mapper import gcs_mapper
from app.services.comunitive import notificacao_curso

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Comunitive Webhook"])

@router.post("/scorm-comunitive")
async def receber_postback(postback_data: ScormRegistrationPostback):
    
    use_case = ProcessScormPostbackUseCase(
        gcs_mapper=gcs_mapper,
        slack_messenger=send_slack_message,
        comunitive_notifier=notificacao_curso
    )

    try:
        response = await use_case.execute(postback_data)
        return response
    
    except MappingNotFoundError as e:
        logger.warning(f"Erro de mapeamento no postback SCORM: {e}")
        return {
            "status": "warning",
            "detail": f"Postback recebido, mas sem mapeamento para Comunitive para o curso {e.course_id}. {e.message}"
        }
    except ComunitiveNotificationError as e:
        logger.error(f"Erro ao notificar Comunitive via webhook: {e}")
        send_slack_message(f"❌ ERRO: Falha ao notificar Comunitive na URI `{e.uri}`. Status: `{e.status_code}`. Detalhes: `{e.detail}`")
        raise HTTPException(
            status_code=e.status_code if e.status_code >= 400 else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar dados para o webhook da Comunitive: {e.detail}"
        )
    except ScormPostbackProcessingError as e:
        logger.error(f"Erro no processamento do postback SCORM: {e}")
        send_slack_message(f"🚨 ERRO INESPERADO: No processamento do postback SCORM: `{e.message}`. Original: `{e.original_exception}`")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no processamento do postback SCORM: {e.message}"
        )
    except Exception as ex:
        tb = traceback.format_exc()
        logger.error(f"Erro geral e não tratado no webhook /scorm-comunitive: {ex}\n{tb}")
        
        debug_info = f"Erro geral no webhook /scorm-comunitive:\n{ex}\n{tb}\n"
        if 'postback_data' in locals() and postback_data:
            debug_info += f"Payload recebido (validado): {postback_data.model_dump(indent=4)}"
        else:
            debug_info += "Payload não pôde ser validado ou está ausente."
        
        send_slack_message(debug_info)
        
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno no servidor: {ex}")
    