from pydantic import BaseSettings, AnyHttpUrl

class Settings(BaseSettings):
    STATIC_TOKEN: str
    SCORM_BASE_URL: AnyHttpUrl = "https://cloud.scorm.com/api/v2"
    SCORM_APP_ID: str
    SCORM_APP_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()