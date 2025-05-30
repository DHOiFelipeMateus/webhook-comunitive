# app/google_cloud_storage/bucket_manager.py

import logging
from io import BytesIO
from typing import Optional
import os
from tempfile import mkdtemp

from .conn_cloud_storage import GoogleCloudStorage, storage as storage_client
from google.cloud import storage
from google.cloud.storage import Bucket

# Configuração básica do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BucketManager:
    """
    Gerencia operações de upload, download e listagem de arquivos em um bucket do Google Cloud Storage.
    """
    
    def __init__(self, bucket_name: str, google_cloud_storage: GoogleCloudStorage = storage_client) -> None:
        self.__gcs_client = google_cloud_storage.client
        self.bucket_name = bucket_name
        logger.info(f"Inicializando GCSBucketManager para o bucket: {bucket_name}")
        
    def __get_bucket(self) -> storage.Bucket: # Tipo de retorno Storage.Bucket
        logger.info(f"Obtendo bucket: {self.bucket_name}")
        return self.__gcs_client.bucket(bucket_name=self.bucket_name)
    
    def download_blob(self, blob_name: str, file_name: Optional[str] = None) -> str:
        logger.info(f"Fazendo download do blob: {blob_name}")
        bucket = self.__get_bucket()
        blob = bucket.blob(blob_name=blob_name)
        
        # Cria um diretório temporário para o arquivo baixado
        temp_dir = mkdtemp()
        file_path = os.path.join(temp_dir, file_name if file_name is not None else blob_name)
        
        try:
            blob.download_to_filename(file_path) # Usa download_to_filename para garantir o arquivo local
            logger.info(f"Blob {blob_name} baixado para {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erro ao baixar o blob {blob_name} para {file_path}: {e}")
            raise
    
    def upload_blob(self, source_file_name: str, destination_blob_name: str) -> None:
        logger.info(f"Fazendo upload do arquivo: {source_file_name} para blob: {destination_blob_name}")
        bucket = self.__get_bucket()
        blob = bucket.blob(destination_blob_name)

        try:
            blob.upload_from_filename(source_file_name)
            logger.info(f"Arquivo {source_file_name} enviado para {destination_blob_name}")
        
        except Exception as e:
            logger.error(f"Erro ao fazer upload de arquivo {source_file_name} para {destination_blob_name}: {e}")
            raise
        
    def get_latest_file_content(self) -> Optional[BytesIO]:
        logger.info("Recuperando conteúdo do arquivo mais recente no bucket")
        bucket = self.__get_bucket()
        blobs = list(bucket.list_blobs())

        if not blobs:
            logger.info("Nenhum blob encontrado no bucket")
            return None

        # Ordena os blobs pela data de criação, do mais recente ao mais antigo
        blobs.sort(key=lambda blob: blob.updated, reverse=True)

        # Pega o blob mais recente
        latest_blob = blobs[0]
        logger.info(f"Blob mais recente encontrado: {latest_blob.name}")

        # Baixa o conteúdo do blob para um BytesIO
        file_content = BytesIO()
        try:
            latest_blob.download_to_file(file_content)
            file_content.seek(0)  # Reseta o ponteiro do BytesIO para o início
            return file_content
        except Exception as e:
            logger.error(f"Erro ao baixar o conteúdo do blob mais recente {latest_blob.name}: {e}")
            return None

    # --- NOVOS MÉTODOS PARA GCSMapper ---
    def read_blob_as_text(self, blob_name: str) -> Optional[str]:
        """
        Lê o conteúdo de um blob específico como uma string (decodificada em UTF-8).

        :param blob_name: Nome do blob no GCS.
        :return: String contendo o conteúdo do blob, ou None se o blob não for encontrado/erro.
        """
        logger.info(f"Lendo blob '{blob_name}' como texto.")
        bucket = self.__get_bucket()
        blob = bucket.blob(blob_name)

        if not blob.exists():
            logger.warning(f"Blob '{blob_name}' não encontrado no bucket '{self.bucket_name}'.")
            return None
        
        try:
            content = blob.download_as_string().decode('utf-8')
            logger.info(f"Blob '{blob_name}' lido com sucesso.")
            return content
        
        except Exception as e:
            logger.error(f"Erro ao ler blob '{blob_name}' como texto: {e}")
            return None

    def upload_string_to_blob(self, content: str, destination_blob_name: str, content_type: Optional[str] = None) -> None:
        """
        Faz upload de uma string diretamente para um blob no GCS.

        :param content: A string a ser enviada.
        :param destination_blob_name: Nome do blob no GCS.
        :param content_type: Tipo de conteúdo (ex: "application/json").
        :raises Exception: Se ocorrer um erro durante o upload.
        """
        logger.info(f"Fazendo upload de string para blob: {destination_blob_name}")
        bucket = self.__get_bucket()
        blob = bucket.blob(destination_blob_name)

        try:
            blob.upload_from_string(content, content_type=content_type)
            logger.info(f"String enviada para {destination_blob_name} com sucesso.")
        
        except Exception as e:
            logger.error(f"Erro ao fazer upload de string para {destination_blob_name}: {e}")
            raise