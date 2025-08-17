from fastapi import FastAPI
from api.domains.alignment.router import router as alignment_router
from api.domains.models.router import router as models_router

app = FastAPI(
    title="Text-Audio Alignment API",
    description="API for forced alignment of text and audio files",
    version="1.0.0",
    swagger_ui_parameters={
        "deepLinking": True,
        "displayRequestDuration": True,
        "defaultModelsExpandDepth": 0,
        "tryItOutEnabled": True
    }
)

# Include routers
app.include_router(alignment_router)
app.include_router(models_router)

@app.get("/")
def read_root():
    return {"message": "Text-Audio Alignment API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
