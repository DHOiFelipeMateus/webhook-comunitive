# app/services/scorm.py

import json
import logging
import httpx
import traceback

# Importações necessárias
from app.settings import Settings

# Configura o logger específico para este módulo
logger = logging.getLogger(__name__)

class ScormServiceError(Exception):
    """Exceção customizada para erros específicos do serviço SCORM."""
    pass

class ScormService:
    def __init__(self, settings_obj: Settings, slack_messenger: callable):
        """
        Inicializa o ScormService com as configurações da aplicação e a função de mensageria Slack.
        """
        self.settings = settings_obj
        self.send_slack_message = slack_messenger
        self.base_url = self.settings.SCORM_BASE_URL
        self.auth_headers = self.settings.SCORM_AUTH_TOKEN # A propriedade computada SCORM_AUTH_TOKEN

    async def configure_postback(self, course_id: str) -> dict:
        """
        Configura o postback de registro para um curso específico no SCORM Cloud.

        Args:
            course_id: O ID do curso a ser configurado.

        Returns:
            Um dicionário contendo os detalhes do sucesso da operação.

        Raises:
            ScormServiceError: Se ocorrer um erro durante o processo de configuração,
                               incluindo problemas de rede ou respostas de erro da API SCORM.
        """
        logger.info(f"Iniciando configuração de postback para o curso: {course_id}")

        scorm_api_url = f"{self.base_url}/courses/{course_id}/configuration"

        headers = {
            "Content-Type": "application/json",
            **self.auth_headers # Desempacota o dicionário de autenticação Base64
        }

        # Constrói o payload de configurações dinamicamente
        # Inclui usuário e senha de autenticação apenas se estiverem definidos
        postback_settings_list = [
            {
                "settingId": "ApiRollupRegistrationPostBackUrl",
                "value": str(self.settings.SCORM_POSTBACK_TARGET_URL)
            },
            {
                "settingId": "ApiRollupRegistrationAuthType",
                "value": self.settings.SCORM_POSTBACK_AUTH_TYPE
            },
            {
                "settingId": "ApiRollupRegistrationFormat",
                "value": "course"
            },
            {
                "settingId": "ApiRollupRegistrationIsJson",
                "value": "true"
            }
        ]

        if self.settings.SCORM_POSTBACK_AUTH_USERNAME:
            postback_settings_list.append({
                "settingId": "ApiRollupRegistrationAuthUser",
                "value": self.settings.SCORM_POSTBACK_AUTH_USERNAME
            })
            
        if self.settings.SCORM_POSTBACK_AUTH_PASSWORD:
            postback_settings_list.append({
                "settingId": "ApiRollupRegistrationAuthPassword",
                "value": self.settings.SCORM_POSTBACK_AUTH_PASSWORD
            })

        payload_to_send = {"settings": postback_settings_list}

        try:
            logger.info(f"Enviando requisição POST de configuração para SCORM Cloud para curso {course_id} em {scorm_api_url}...")
            async with httpx.AsyncClient() as client:
                response = await client.post(scorm_api_url, headers=headers, content=json.dumps(payload_to_send))

            if response.is_success:
                # Mensagem de sucesso detalhada para o Slack
                slack_success_message = (
                    f"✅ SUCESSO: Postback configurado para curso SCORM: `{course_id}`.\n"
                    f"URL de postback configurada: `{self.settings.SCORM_POSTBACK_TARGET_URL}`\n"
                    f"Status da API SCORM: `{response.status_code}`\n"
                    f"**Configurações Enviadas:**\n```json\n{json.dumps(postback_settings_list, indent=2)}\n```" # Inclui as configs
                )
                logger.info(slack_success_message)
                self.send_slack_message(slack_success_message)
                
                return {
                    "status": "success",
                    "message": f"Postback configurado com sucesso para o curso {course_id}.",
                    "scorm_response_status": response.status_code,
                    "scorm_response_detail": response.json() if response.text else "No content"
                }
                
            else:
                # Mensagem de erro para o Slack em caso de falha da API SCORM
                slack_error_message = (
                    f"❌ ERRO: Falha ao configurar postback para curso SCORM: `{course_id}`.\n"
                    f"URL do SCORM: `{scorm_api_url}`\n"
                    f"Status da API SCORM: `{response.status_code}`\n"
                    f"Resposta da API SCORM: ```{response.text}```\n"
                )
                logger.error(slack_error_message)
                self.send_slack_message(slack_error_message)
                raise ScormServiceError(f"Erro da API SCORM: {response.status_code} - {response.text}")

        except httpx.RequestError as exc:
            # Mensagem de erro de rede para o Slack
            slack_network_error_message = (
                f"⚠️ ERRO DE REDE: Impossível conectar ao SCORM Cloud para curso: `{course_id}`.\n"
                f"Erro: `{exc}`\n"
                f"Verifique a conectividade ou a URL da API SCORM: `{scorm_api_url}`"
            )
            logger.error(slack_network_error_message)
            self.send_slack_message(slack_network_error_message)
            raise ScormServiceError(f"Erro de rede ao conectar ao SCORM Cloud: {exc}")
        except Exception as exc:
            # Mensagem de erro inesperado para o Slack (com traceback)
            slack_unexpected_error_message = (
                f"🚨 ERRO INESPERADO: Ocorreu um erro ao configurar postback para curso SCORM: `{course_id}`.\n"
                f"Erro: `{type(exc).__name__}: {exc}`"
            )
            logger.error(slack_unexpected_error_message, exc_info=True)
            self.send_slack_message(slack_unexpected_error_message + f"\nTraceback: ```{traceback.format_exc()}```")
            raise ScormServiceError(f"Erro inesperado no serviço SCORM: {exc}")
