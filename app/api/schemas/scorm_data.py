# app/schemas/scorm_data.py

from pydantic import BaseModel, HttpUrl
from typing import List

class ScormCourseConfiguration(BaseModel):
    """
    Representa a configuração de um curso SCORM, incluindo o ID do curso e a URI do webhook da Comunitive.
    """
    course_id: str

class ScormCourseLink(BaseModel):
    """
    Representa o mapeamento de um ID de curso SCORM para uma URI de webhook da Comunitive.
    """
    course_id: str
    comunitive_webhook_uri: HttpUrl # HttpUrl garante que a URI seja uma URL válida

class ScormCourseLinkList(BaseModel):
    """
    Representa uma lista de ScormCourseLink, usada para o corpo da requisição POST
    que atualiza múltiplos vínculos de uma vez.
    """
    links: List[ScormCourseLink]
