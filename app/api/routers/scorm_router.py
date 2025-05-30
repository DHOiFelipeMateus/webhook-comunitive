# app/api/routers/scorm_router.py

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from app.api.schemas.scorm_data import ScormCourseLinkList, ScormCourseConfiguration
from app.services.gcs_mapper import gcs_mapper, GCSMapperError
from app.settings import settings
from app.services.slack import send_slack_message
from app.services.scorm import ScormService, ScormServiceError
from app.auth.security import get_current_user # Importe a dependência de autenticação
from app.api.schemas.authentication import User # Importe o modelo de usuário, se usar

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scorm", tags=["SCORM Webhook Configuration"])

def get_scorm_service() -> ScormService:
    return ScormService(settings_obj=settings, slack_messenger=send_slack_message)

@router.post("/configure-postback")
async def configure_scorm_course_postback(
    scorm_course_configuration: ScormCourseConfiguration,
    scorm_service: ScormService = Depends(get_scorm_service),
    current_user: User = Depends(get_current_user) 
):
    """
    Configura o postback de registro para um curso específico no SCORM Cloud.
    Esta rota requer autenticação JWT.
    """
    logger.info(f"Requisição recebida no roteador para configurar postback para o curso: {course_id} pelo usuário: {current_user.username}.")
    
    try:
        result = await scorm_service.configure_postback(course_id)
        return result
    
    except ScormServiceError as e:
        logger.error(f"Falha na configuração do postback SCORM para {course_id}: {e}")
        if "Erro de rede" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Não foi possível conectar ao SCORM Cloud: {e}"
            )
            
        elif "Erro da API SCORM" in str(e):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao configurar postback no SCORM Cloud: {e}"
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ocorreu um erro inesperado ao configurar o postback SCORM: {e}"
            )
            
    except Exception as e:
        logger.exception(f"Ocorreu um erro não tratado no roteador para o curso {course_id}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro interno inesperado: {e}"
        )

@router.post("/data")
async def update_course_links(
    course_links: ScormCourseLinkList,
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Requisição para atualizar vínculos SCORM recebida do usuário: {current_user.username}.")
    
    mappings = {link.course_id: str(link.comunitive_webhook_uri) for link in course_links.links}

    try:
        await gcs_mapper.update_mapping(mappings)
        return {"status": "success", "detail": "Vínculos atualizados com sucesso no GCS."}
    
    except GCSMapperError as e:
        logger.error(f"Erro ao salvar vínculos no GCS: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao salvar dados no GCS: {e}")

@router.get("/data")
async def get_course_links(
    current_user: User = Depends(get_current_user)
) -> dict:
    logger.info(f"Requisição para consultar vínculos SCORM recebida do usuário: {current_user.username}.")

    try:
        mappings = await gcs_mapper.load_mappings(force_reload=True)
        return mappings
    
    except GCSMapperError as e:
        logger.error(f"Erro ao carregar vínculos do GCS: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro interno ao carregar dados do GCS: {e}")
