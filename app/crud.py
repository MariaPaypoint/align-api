from sqlalchemy.orm import Session
from typing import List, Optional
from app.models import AlignmentQueue, AlignmentStatus
from app.schemas import AlignmentQueueCreate, AlignmentQueueUpdate

def create_alignment_task(db: Session, task: AlignmentQueueCreate, audio_path: str, text_path: str) -> AlignmentQueue:
    db_task = AlignmentQueue(
        audio_file_path=audio_path,
        text_file_path=text_path,
        original_audio_filename=task.original_audio_filename,
        original_text_filename=task.original_text_filename,
        status=AlignmentStatus.PENDING
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_alignment_task(db: Session, task_id: int) -> Optional[AlignmentQueue]:
    return db.query(AlignmentQueue).filter(AlignmentQueue.id == task_id).first()

def get_alignment_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[AlignmentQueue]:
    return db.query(AlignmentQueue).offset(skip).limit(limit).all()

def update_alignment_task(db: Session, task_id: int, task_update: AlignmentQueueUpdate) -> Optional[AlignmentQueue]:
    db_task = db.query(AlignmentQueue).filter(AlignmentQueue.id == task_id).first()
    if db_task:
        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_alignment_task(db: Session, task_id: int) -> bool:
    db_task = db.query(AlignmentQueue).filter(AlignmentQueue.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False

def get_tasks_by_status(db: Session, status: AlignmentStatus) -> List[AlignmentQueue]:
    return db.query(AlignmentQueue).filter(AlignmentQueue.status == status).all()
