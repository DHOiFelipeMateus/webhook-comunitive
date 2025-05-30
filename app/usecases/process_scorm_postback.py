# app/usecases/process_scorm_postback.py

import logging
from typing import Dict, Any

from fastapi import HTTPException

from app.api.schemas.scorm_postback import ScormRegistrationPostback # Ajuste o caminho se necessário
from app.services.gcs_mapper import GCSMapper, GCSMapperError
from app.services.slack import send_slack_message # Função para enviar mensagens para o Slack
from app.services.comunitive import notificacao_curso # Função do serviço Comunitive

from app.errors import MappingNotFoundError, ComunitiveNotificationError, ScormPostbackProcessingError

logger = logging.getLogger(__name__)

class ProcessScormPostbackUseCase:
    """
    Args:
        gcs_mapper (GCSMapper): Instância responsável por carregar os mapeamentos de cursos do GCS.
        slack_messenger (callable, opcional): Função para enviar mensagens ao Slack. **Default**: `send_slack_message`.
        comunitive_notifier (callable, opcional): Função para notificar a Comunitive sobre a conclusão do curso. **Default**: `notificacao_curso`.
        - Verifica se o status de conclusão da atividade é "completed".
        - Obtém a URI do webhook da Comunitive correspondente ao curso.
        - Notifica a Comunitive sobre a conclusão do curso.
        - Envia mensagens de sucesso ou aviso ao Slack.
        - Lida com exceções específicas e inesperadas, levantando erros apropriados.
    """
    def __init__(self, 
                 gcs_mapper: GCSMapper, 
                 slack_messenger: callable = send_slack_message, 
                 comunitive_notifier: callable = notificacao_curso):
        self.gcs_mapper = gcs_mapper
        self.slack_messenger = slack_messenger
        self.comunitive_notifier = comunitive_notifier # Função para notificar a Comunitive

    async def execute(self, postback_data: ScormRegistrationPostback) -> Dict[str, Any]:
        logger.info(f"Iniciando processamento do postback para curso ID: {postback_data.course.id}")

        # Validação de conclusão
        completion_status = postback_data.activityDetails.activityCompletion
        if not completion_status or completion_status.lower() != "completed":
            logger.info(f"Postback recebido, mas status de conclusão não é 'completed' ou está ausente: {completion_status}")
            return {
                "status": "success",
                "detail": f"Postback recebido, mas a conclusão da atividade não é 'completed' ou está ausente. Status: {completion_status}"
            }

        course_id = postback_data.course.id
        learner_email = postback_data.learner.id

        # Obtém a URI do webhook
        comunitive_webhook_uri = await self._get_comunitive_webhook_uri(course_id)

        # Chama o serviço da Comunitive
        try:
            response = await self.comunitive_notifier(
                user_email=learner_email,
                comunitive_webhook_uri=comunitive_webhook_uri
            )
            
            self.slack_messenger(f"✅ SUCESSO: Postback do SCORM para `{course_id}` processado e enviado para Comunitive: `{comunitive_webhook_uri}`.")
            return response

        except HTTPException as e:
            raise ComunitiveNotificationError(
                uri=comunitive_webhook_uri,
                status_code=e.status_code,
                detail=e.detail,
                message=f"Falha ao notificar Comunitive para o curso {course_id}."
            ) from e
        except Exception as e:
            raise ScormPostbackProcessingError(
                message=f"Erro inesperado ao chamar o notificador da Comunitive para o curso {course_id}.",
                original_exception=e
            ) from e

    async def _get_comunitive_webhook_uri(self, course_id: str) -> str:
        """
        Obtém a URI do webhook da Comunitive para um determinado curso.
        Este método tenta recuperar a URI do webhook da Comunitive a partir do mapeamento carregado pelo `GCSMapper`.
        Se não encontrar a URI correspondente ao `course_id` fornecido, envia um aviso para o Slack e levanta uma exceção `MappingNotFoundError`.
        Em caso de erro ao carregar os mapeamentos ou qualquer outra exceção inesperada, levanta uma exceção `ScormPostbackProcessingError`.
        Args:
            course_id (str): **ID do curso** para o qual se deseja obter a URI do webhook da Comunitive.
        Returns:
            str: **URI do webhook** da Comunitive associada ao `course_id` informado.
        
        Raises:
            MappingNotFoundError: Se não houver URI mapeada para o `course_id`.
            ScormPostbackProcessingError: Se ocorrer erro ao carregar os mapeamentos ou qualquer exceção inesperada.
        """
        try:
            mappings = await self.gcs_mapper.load_mappings()
            comunitive_webhook_uri = mappings.get(course_id)

            if not comunitive_webhook_uri:
                # Envia um aviso para o Slack antes de levantar a exceção
                self.slack_messenger(
                    f"⚠️ AVISO: Postback do SCORM para curso `{course_id}` recebido, mas NENHUMA URI da Comunitive encontrada no mapeamento do GCS. Postback não será enviado à Comunitive."
                    )
                raise MappingNotFoundError(course_id=course_id)
            
            return comunitive_webhook_uri
        
        except GCSMapperError as e:
            # Re-lança GCSMapperError como uma exceção do Use Case para manter a consistência
            raise ScormPostbackProcessingError(
                message=f"Erro ao carregar mapeamentos do GCS para course_id {course_id}.",
                original_exception=e
            ) from e
        
        except Exception as e:
            # Captura qualquer outra exceção inesperada
            raise ScormPostbackProcessingError(
                message=f"Erro inesperado ao obter URI do webhook da Comunitive para curso {course_id}.",
                original_exception=e
            ) from e
