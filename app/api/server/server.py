from fastapi import FastAPI
from app.api.routers.comunitive_webhook_router import router as webhook_router
from app.api.routers.scorm_router import router as scorm_router
from app.api.routers.authentication_router import router as authentication_router

app = FastAPI()

app.include_router(authentication_router)
app.include_router(scorm_router)
app.include_router(webhook_router)

@app.get("/")
async def root():
    return {"message": "Bem-vindo à API de Integrações SCORM!"}