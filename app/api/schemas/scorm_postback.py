# app/schemas/scorm_postback.py (ou um local similar para seus schemas)

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List

# Modelos aninhados (do mais interno para o mais externo, geralmente)

class CourseModel(BaseModel):
    id: str
    title: str
    version: Optional[int] = None

class LearnerModel(BaseModel):
    id: str  # Geralmente o e-mail do aluno
    firstName: Optional[str] = None
    lastName: Optional[str] = None

class ScoreModel(BaseModel):
    raw: Optional[float] = None
    scaled: Optional[float] = None

class ActivityProgressModel(BaseModel):
    score: Optional[ScoreModel] = None

class ActivityDetailsModel(BaseModel):
    id: str
    title: Optional[str] = None
    attempts: Optional[int] = None
    activityCompletion: Optional[str] = None # Ex: "COMPLETED", "INCOMPLETE"
    activitySuccess: Optional[str] = None # Ex: "UNKNOWN", "PASSED", "FAILED"
    timeTracked: Optional[str] = None # Ex: "0000:00:00" - pode ser convertido para timedelta se necessário
    completionAmount: Optional[dict] = None # Se precisar de mais detalhes, crie um modelo para isso
    suspended: Optional[bool] = None
    staticProperties: Optional[dict] = None # Se precisar de mais detalhes, crie um modelo para isso
    activityProgress: Optional[ActivityProgressModel] = None # Adicionado para a estrutura do score

# Modelo principal para o postback
class ScormRegistrationPostback(BaseModel):
    id: str
    instance: int
    xapiRegistrationId: Optional[str] = None
    updated: Optional[str] = None
    registrationCompletion: Optional[str] = None # Ex: "COMPLETED", "INCOMPLETE"
    registrationSuccess: Optional[str] = None # Ex: "UNKNOWN", "PASSED", "FAILED"
    totalSecondsTracked: Optional[float] = None
    firstAccessDate: Optional[str] = None
    lastAccessDate: Optional[str] = None
    completedDate: Optional[str] = None
    createdDate: Optional[str] = None
    
    course: CourseModel
    learner: LearnerModel
    activityDetails: ActivityDetailsModel
    
    registrationCompletionAmount: Optional[float] = None
    tags: Optional[List[str]] = Field(default_factory=list) # Define como uma lista vazia por padrão

    # Você pode adicionar propriedades computadas aqui para extrair valores complexos
    @property
    def processed_pontuacao(self) -> int:
        score = None
        if self.activityDetails and self.activityDetails.activityProgress and self.activityDetails.activityProgress.score:
            score = self.activityDetails.activityProgress.score

        if score:
            if score.raw is not None:
                return int(score.raw)
            
            elif score.scaled is not None:
                return int(score.scaled * 100) # Converte de 0.0 a 1.0 para 0 a 100
        
        return 0

    @property
    def learner_full_name(self) -> str:
        first = self.learner.firstName or ''
        last = self.learner.lastName or ''
        return f"{first} {last}".strip()
