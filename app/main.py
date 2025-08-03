from fastapi import FastAPI
from app.routers import alignment

app = FastAPI(
    title="Text-Audio Alignment API",
    description="API for forced alignment of text and audio files",
    version="1.0.0"
)

# Include routers
app.include_router(alignment.router)

@app.get("/")
def read_root():
    return {"message": "Text-Audio Alignment API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
