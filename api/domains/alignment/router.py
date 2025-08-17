from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from api.database import get_db
from api.domains.alignment.schemas import AlignmentQueueResponse, AlignmentQueueUpdate, AlignmentQueueCreate, ModelParameter
from api.domains.alignment.crud import (
    create_alignment_task, 
    get_alignment_task, 
    get_alignment_tasks,
    update_alignment_task,
    delete_alignment_task,
    get_tasks_by_status,
    validate_models_same_language
)
from api.domains.alignment.models import AlignmentStatus
from api.utils import validate_audio_file, validate_text_file, save_uploaded_file

router = APIRouter(prefix="/alignment", tags=["alignment"])

@router.post("/", 
    response_model=AlignmentQueueResponse,
    summary="Create alignment task",
    description="Upload audio and text files to create a new alignment task. The task will be queued for processing.",
    responses={
        201: {"description": "Alignment task created successfully"},
        400: {"description": "Invalid file format or model validation error"},
        500: {"description": "Internal server error"}
    }
)
async def create_alignment_request(
    audio_file: UploadFile = File(..., description="Audio file (MP3 or WAV format)"),
    text_file: UploadFile = File(..., description="Text file (TXT format)"),
    acoustic_model_name: str = Form(..., description="Name of the acoustic model (e.g., 'russian_mfa')"),
    acoustic_model_version: str = Form(..., description="Version of the acoustic model (e.g., '3.1.0')"),
    dictionary_model_name: str = Form(..., description="Name of the dictionary model (e.g., 'russian_mfa')"),
    dictionary_model_version: str = Form(..., description="Version of the dictionary model (e.g., '3.1.0')"),
    g2p_model_name: str = Form(None, description="Name of the G2P model (optional, e.g., 'russian_mfa_g2p')"),
    g2p_model_version: str = Form(None, description="Version of the G2P model (optional, e.g., '3.1.0')"),
    db: Session = Depends(get_db)
):
    """
    Create a new text-audio alignment task.
    
    This endpoint accepts audio and text files along with model parameters to create
    an alignment task. The task will be validated and queued for processing.
    
    **Requirements:**
    - Audio file: MP3 or WAV format
    - Text file: TXT format  
    - All models must exist and belong to the same language
    """
    
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
        
        # Validate that all models belong to the same language
        is_valid, error_message, language_id = validate_models_same_language(
            db, acoustic_model_param, dictionary_model_param, g2p_model_param
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Save uploaded files
        audio_path = save_uploaded_file(audio_file, "audio")
        text_path = save_uploaded_file(text_file, "text")
        
        # Create alignment request object
        alignment_request = AlignmentQueueCreate(
            original_audio_filename=audio_file.filename,
            original_text_filename=text_file.filename,
            acoustic_model=acoustic_model_param,
            dictionary_model=dictionary_model_param,
            g2p_model=g2p_model_param
        )
        
        # Create task in database
        db_task = create_alignment_task(db, alignment_request, audio_path, text_path)
        
        # Return response using the from_db_model method
        return AlignmentQueueResponse.from_db_model(db_task)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any other exceptions and return 500 with detailed error message
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/", 
    response_model=List[AlignmentQueueResponse],
    summary="List alignment tasks",
    description="Retrieve all alignment tasks with optional status filtering and pagination support."
)
def get_alignment_requests(
    skip: int = 0, 
    limit: int = 100,
    status: AlignmentStatus = None,
    db: Session = Depends(get_db)
):
    """Get all alignment tasks with optional status filter and pagination."""
    if status:
        tasks = get_tasks_by_status(db, status=status)
        # Apply pagination to filtered results
        tasks = tasks[skip:skip + limit]
    else:
        tasks = get_alignment_tasks(db, skip=skip, limit=limit)
    return [AlignmentQueueResponse.from_db_model(task) for task in tasks]


@router.get("/{task_id}", 
    response_model=AlignmentQueueResponse,
    summary="Get alignment task",
    description="Retrieve a specific alignment task by ID.",
    responses={
        200: {"description": "Alignment task found"},
        404: {"description": "Alignment task not found"}
    }
)
def get_alignment_request(task_id: int, db: Session = Depends(get_db)):
    """Get a specific alignment task by its ID."""
    task = get_alignment_task(db, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Alignment task not found")
    return AlignmentQueueResponse.from_db_model(task)


@router.put("/{task_id}", 
    response_model=AlignmentQueueResponse,
    summary="Update alignment task",
    description="Update an existing alignment task (status, error message, result, etc.).",
    responses={
        200: {"description": "Alignment task updated successfully"},
        404: {"description": "Alignment task not found"}
    }
)
def update_alignment_request(
    task_id: int, 
    task_update: AlignmentQueueUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing alignment task."""
    task = update_alignment_task(db, task_id=task_id, task_update=task_update)
    if task is None:
        raise HTTPException(status_code=404, detail="Alignment task not found")
    return AlignmentQueueResponse.from_db_model(task)


@router.delete("/{task_id}",
    summary="Delete alignment task",
    description="Delete an alignment task from the queue.",
    responses={
        200: {"description": "Task deleted successfully"},
        404: {"description": "Alignment task not found"}
    }
)
def delete_alignment_request(task_id: int, db: Session = Depends(get_db)):
    """Delete an alignment task from the queue."""
    success = delete_alignment_task(db, task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alignment task not found")
    return {"message": "Task deleted successfully"}
