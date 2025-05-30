# app/errors/exceptions.py

class UseCaseError(Exception):
    """Base exception for all use case errors."""
    pass

class MappingNotFoundError(UseCaseError):
    """Raised when no Comunitive webhook URI is found for a given SCORM course ID."""
    def __init__(self, course_id: str, message: str = "Nenhum mapeamento da Comunitive encontrado."):
        self.course_id = course_id
        self.message = message
        super().__init__(f"{self.message} para o curso SCORM ID: {self.course_id}")

class ComunitiveNotificationError(UseCaseError):
    """Raised when the Comunitive notification service fails to send the data."""
    def __init__(self, uri: str, status_code: int, detail: str, message: str = "Falha ao enviar notificação para a Comunitive."):
        self.uri = uri
        self.status_code = status_code
        self.detail = detail
        self.message = message
        super().__init__(f"{self.message} na URI: {self.uri}. Status: {self.status_code}. Detalhe: {self.detail}")

class ScormPostbackProcessingError(UseCaseError):
    """General error during SCORM postback processing within the use case."""
    def __init__(self, message: str = "Erro no processamento do postback SCORM.", original_exception: Exception = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)
