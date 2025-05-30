# app/google_cloud_storage/conn_cloud_storage.py

import logging
from typing import Any, Optional
from google.cloud import storage
import os
from app.settings import settings

# Configuração básica do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleCloudStorage:
    """
    Singleton para gerenciar a conexão com o Google Cloud Storage.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GoogleCloudStorage, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        """
        Inicializa o cliente do Google Cloud Storage.
        """
        if not hasattr(self, 'client'):
            self.client = self.__get_cloud_storage_client()

    def __get_cloud_storage_client(self):
        """
        Cria e retorna o cliente do Google Cloud Storage com base no ambiente de execução.

        :return: Instância do cliente do Google Cloud Storage.
        :raises Exception: Se ocorrer um erro ao criar o cliente.
        """
        try:
            logger.info("Criando cliente do Google Cloud Storage.")
            if os.getenv("GAE_ENV", "").startswith("standard") or os.getenv("K_SERVICE"):
                logger.info("Executando no ambiente Google Cloud.")
        
                return storage.Client()
        
            else:
                logger.info("Executando localmente, usando conta de serviço.")
        
                return storage.Client.from_service_account_info(settings.SERVICE_ACCOUNT_DATA)
        
        except Exception as e:
            logger.error(f"Erro ao criar o cliente do Google Cloud Storage: {e}")
            raise
        
storage = GoogleCloudStorage()
        