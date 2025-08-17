from fastapi import FastAPI
from api.domains.alignment.router import router as alignment_router
from api.domains.models.router import router as models_router
from api.domains.auth.routes import router as auth_router
from api.domains.users.routes import router as users_router

app = FastAPI(
    title="Text-Audio Alignment API",
    description="Распределенная система для принудительного выравнивания текста и аудио с использованием MFA",
    version="2.0.0",
    swagger_ui_parameters={
        "deepLinking": True,
        "displayRequestDuration": True,
        "defaultModelsExpandDepth": 0,
        "tryItOutEnabled": True
    }
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(alignment_router)
app.include_router(models_router)

@app.get("/")
def read_root():
    return {"message": "Text-Audio Alignment API", "version": "2.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
