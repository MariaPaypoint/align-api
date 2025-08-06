from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import AlignmentQueueResponse, AlignmentQueueUpdate, AlignmentQueueCreate, ModelParameter
from app.crud import (
    create_alignment_task, 
    get_alignment_task, 
    get_alignment_tasks,
    update_alignment_task,
    delete_alignment_task,
    get_tasks_by_status,
    validate_models_same_language
)
from app.models import AlignmentStatus
from app.utils import validate_audio_file, validate_text_file, save_uploaded_file

router = APIRouter(prefix="/alignment", tags=["alignment"])

@router.post("/", response_model=AlignmentQueueResponse)
async def create_alignment_request(
    audio_file: UploadFile = File(...),
    text_file: UploadFile = File(...),
    acoustic_model_name: str = Form(..., description="Name of the acoustic model"),
    acoustic_model_version: str = Form(..., description="Version of the acoustic model"),
    dictionary_model_name: str = Form(..., description="Name of the dictionary model"),
    dictionary_model_version: str = Form(..., description="Version of the dictionary model"),
    g2p_model_name: str = Form(None, description="Name of the G2P model (optional)"),
    g2p_model_version: str = Form(None, description="Version of the G2P model (optional)"),
    db: Session = Depends(get_db)
):
    """Create new alignment task with model parameters"""
    
    # Validate files
    if not validate_audio_file(audio_file):
        raise HTTPException(
            status_code=400, 
            detail="Invalid audio file. Only MP3 and WAV files are allowed."
        )
    
    if not validate_text_file(text_file):
        raise HTTPException(
            status_code=400, 
            detail="Invalid text file. Only TXT files are allowed."
        )
    
    try:
        # Create model parameters from form fields
        acoustic_model_param = ModelParameter(
            name=acoustic_model_name,
            version=acoustic_model_version
        )
        
        dictionary_model_param = ModelParameter(
            name=dictionary_model_name,
            version=dictionary_model_version
        )
        
        g2p_model_param = None
        if g2p_model_name and g2p_model_version:
            g2p_model_param = ModelParameter(
                name=g2p_model_name,
                version=g2p_model_version
            )
        
        # Validate models exist and have same language
        is_valid, error_message, language_id = validate_models_same_language(
            db, acoustic_model_param, dictionary_model_param, g2p_model_param
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Save files
        audio_path = save_uploaded_file(audio_file, "audio")
        text_path = save_uploaded_file(text_file, "text")
        
        # Create task
        task_data = AlignmentQueueCreate(
            original_audio_filename=audio_file.filename,
            original_text_filename=text_file.filename,
            acoustic_model=acoustic_model_param,
            dictionary_model=dictionary_model_param,
            g2p_model=g2p_model_param
        )
        
        db_task = create_alignment_task(db, task_data, audio_path, text_path)
        return AlignmentQueueResponse.from_db_model(db_task)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating alignment task: {str(e)}")

@router.get("/", response_model=List[AlignmentQueueResponse])
def get_alignment_requests(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get all alignment tasks"""
    tasks = get_alignment_tasks(db, skip=skip, limit=limit)
    return [AlignmentQueueResponse.from_db_model(task) for task in tasks]

@router.get("/{task_id}", response_model=AlignmentQueueResponse)
def get_alignment_request(task_id: int, db: Session = Depends(get_db)):
    """Get specific alignment task"""
    task = get_alignment_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Alignment task not found")
    return AlignmentQueueResponse.from_db_model(task)

@router.put("/{task_id}", response_model=AlignmentQueueResponse)
def update_alignment_request(
    task_id: int, 
    task_update: AlignmentQueueUpdate, 
    db: Session = Depends(get_db)
):
    """Update alignment task"""
    task = update_alignment_task(db, task_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Alignment task not found")
    return AlignmentQueueResponse.from_db_model(task)

@router.delete("/{task_id}")
def delete_alignment_request(task_id: int, db: Session = Depends(get_db)):
    """Delete alignment task"""
    success = delete_alignment_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alignment task not found")
    return {"message": "Alignment task deleted successfully"}

@router.get("/status/{status}", response_model=List[AlignmentQueueResponse])
def get_tasks_by_status_endpoint(status: AlignmentStatus, db: Session = Depends(get_db)):
    """Get tasks by status"""
    tasks = get_tasks_by_status(db, status)
    return [AlignmentQueueResponse.from_db_model(task) for task in tasks]
