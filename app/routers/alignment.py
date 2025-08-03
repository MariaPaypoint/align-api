from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import AlignmentQueueResponse, AlignmentQueueUpdate
from app.crud import (
    create_alignment_task, 
    get_alignment_task, 
    get_alignment_tasks,
    update_alignment_task,
    delete_alignment_task,
    get_tasks_by_status
)
from app.models import AlignmentStatus
from app.utils import validate_audio_file, validate_text_file, save_uploaded_file
from app.schemas import AlignmentQueueCreate

router = APIRouter(prefix="/alignment", tags=["alignment"])

@router.post("/", response_model=AlignmentQueueResponse)
async def create_alignment_request(
    audio_file: UploadFile = File(...),
    text_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Create new alignment task"""
    
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
        # Save files
        audio_path = save_uploaded_file(audio_file, "audio")
        text_path = save_uploaded_file(text_file, "text")
        
        # Create task
        task_data = AlignmentQueueCreate(
            original_audio_filename=audio_file.filename,
            original_text_filename=text_file.filename
        )
        
        db_task = create_alignment_task(db, task_data, audio_path, text_path)
        return db_task
        
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
    return tasks

@router.get("/{task_id}", response_model=AlignmentQueueResponse)
def get_alignment_request(task_id: int, db: Session = Depends(get_db)):
    """Get specific alignment task"""
    task = get_alignment_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Alignment task not found")
    return task

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
    return task

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
    return tasks
