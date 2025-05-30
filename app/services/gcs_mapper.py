# app/services/gcs_mapper.py

import json
import logging
import time
from typing import Dict, Optional, Any

# Importe o BucketManager do seu caminho correto
from app.google_cloud_storage.bucket_manager import BucketManager
from app.settings import settings

logger = logging.getLogger(__name__)

class GCSMapperError(Exception):
    """Exceção customizada para erros no GCSMapper."""
    pass

class GCSMapper:
    def __init__(self, bucket_manager: BucketManager, file_name: str):
        """
        Inicializa o GCSMapper com uma instância de BucketManager e o nome do arquivo.
        """
        self.bucket_manager = bucket_manager
        self.file_name = file_name # O nome específico do arquivo JSON de mapeamentos
        
        self._cache: Dict[str, str] = {}
        self._last_loaded_timestamp: float = 0
        self._cache_refresh_interval_seconds: int = 60 # Recarrega o cache a cada 60 segundos

    async def _load_from_gcs(self) -> Dict[str, str]:
        """Carrega os mapeamentos do arquivo JSON no GCS usando BucketManager."""
        try:
            logger.info(f"Tentando carregar mapeamentos do arquivo '{self.file_name}' no bucket '{self.bucket_manager.bucket_name}'.")
            
            # --- CORREÇÃO AQUI: Usa o novo método read_blob_as_text do BucketManager ---
            contents = self.bucket_manager.read_blob_as_text(self.file_name)
            
            if contents is None: # Arquivo não encontrado no GCS
                logger.warning(f"Arquivo de mapeamento '{self.file_name}' não encontrado. Iniciando com mapeamento vazio.")
                return {}
            
            return json.loads(contents)
        
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON do arquivo de mapeamento '{self.file_name}': {e}")
            raise GCSMapperError(f"Falha ao decodificar JSON do GCS: {e}")
        
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar mapeamentos do GCS via BucketManager: {e}")
            raise GCSMapperError(f"Falha ao carregar mapeamentos do GCS: {e}")

    async def load_mappings(self, force_reload: bool = False) -> Dict[str, str]:
        """
        Retorna os mapeamentos, utilizando cache. Recarrega do GCS se o cache for antigo
        ou se force_reload for True.
        """
        current_time = time.time()
        if force_reload or (current_time - self._last_loaded_timestamp > self._cache_refresh_interval_seconds):
            try:
                self._cache = await self._load_from_gcs() 
                self._last_loaded_timestamp = current_time
            
            except GCSMapperError as e:
                logger.warning(f"Falha ao recarregar o cache de mapeamentos: {e}. Usando cache existente ou vazio.")
                if not self._cache: # Garante que o cache não é None se a carga inicial falhar
                    self._cache = {}
        
        return self._cache

    async def update_mapping(self, new_mappings: Dict[str, Any]):
        """
        Substitui o mapeamento completo no arquivo JSON do GCS usando BucketManager.
        """
        logger.info(f"Iniciando atualização completa do mapeamento para '{self.file_name}' no GCS.")
        
        try:
            # --- JÁ ESTÁ CORRETO: Usa o novo método upload_string_to_blob do BucketManager ---
            self.bucket_manager.upload_string_to_blob(
                content=json.dumps(new_mappings, indent=4), 
                destination_blob_name=self.file_name,
                content_type="application/json" # Definir content type para JSON
            )
            logger.info(f"Mapeamento salvo com sucesso em '{self.file_name}' no bucket '{self.bucket_manager.bucket_name}'.")
            
            # Atualiza o cache local imediatamente após uma escrita bem-sucedida
            self._cache = new_mappings
            self._last_loaded_timestamp = time.time()

        except Exception as e:
            logger.error(f"Erro ao salvar mapeamento no GCS via BucketManager: {e}")
            raise GCSMapperError(f"Falha ao salvar mapeamento no GCS: {e}")

# --- ATUALIZAÇÃO DA INSTANCIAÇÃO GLOBAL DO GCSMapper ---
bucket_manager_instance = BucketManager(bucket_name=settings.bucket_name)

# Inicializa o GCSMapper com a instância do BucketManager e o nome do arquivo
gcs_mapper = GCSMapper(
    bucket_manager=bucket_manager_instance,
    file_name=settings.file_blob_name
)