# app/settings.py

import base64
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    
    ADMIN_USER_EMAIL: str
    ADMIN_USER_PASSWORD: str
    
    SCORM_BASE_URL: AnyHttpUrl = "https://cloud.scorm.com/api/v2"
    SCORM_APP_ID: str
    SCORM_APP_SECRET: str
    
    SCORM_POSTBACK_TARGET_URL: AnyHttpUrl 
    SCORM_POSTBACK_AUTH_TYPE: str = "httpbasic" 
    SCORM_POSTBACK_AUTH_USERNAME: str = Field(default="") 
    SCORM_POSTBACK_AUTH_PASSWORD: str = Field(default="") 

    COMUNITIVE_API_KEY: str
    COMUNITIVE_API_URL: AnyHttpUrl = "https://api.comunitive.com"
    
    SLACK_TOKEN: str

    # --- Configurações JWT ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256" # Algoritmo de hashing para o JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Tempo de expiração do token em minutos

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def SCORM_AUTH_TOKEN(self) -> dict:
        credentials = f"{self.SCORM_APP_ID}:{self.SCORM_APP_SECRET}"
        credentials_bytes = credentials.encode("utf-8")
        base64_bytes = base64.b64encode(credentials_bytes)
        base64_credentials = base64_bytes.decode("utf-8")
        
        headers = {
            "Authorization": f"Basic {base64_credentials}"
        }
        
        return headers

    bucket_name: str = Field(default="")
    file_blob_name: str = Field(default="")

    project_id: str = Field(default="")
    private_key_id: str = Field(default="")
    private_key: str = Field(default="")
    client_email: str = Field(default="")
    client_id: str = Field(default="")
    client_x509_cert_url: str = Field(default="")
        
    @property
    def SERVICE_ACCOUNT_DATA(self) -> dict:
        return {
            "type": "service_account",
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key,
            "client_email": self.client_email,
            "client_id": self.client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": self.client_x509_cert_url,
            "universe_domain": "googleapis.com"
        }
    
settings = Settings()
