from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from api.domains.alignment.models import AlignmentQueue, AlignmentStatus
from api.domains.alignment.schemas import AlignmentQueueCreate, AlignmentQueueUpdate, ModelParameter
from api.domains.models.models import MFAModel, ModelType


def create_alignment_task(db: Session, task: AlignmentQueueCreate, audio_path: str, text_path: str, user_id: int) -> AlignmentQueue:
    db_task = AlignmentQueue(
        audio_file_path=audio_path,
        text_file_path=text_path,
        original_audio_filename=task.original_audio_filename,
        original_text_filename=task.original_text_filename,
        acoustic_model_name=task.acoustic_model.name,
        acoustic_model_version=task.acoustic_model.version,
        dictionary_model_name=task.dictionary_model.name,
        dictionary_model_version=task.dictionary_model.version,
        g2p_model_name=task.g2p_model.name if task.g2p_model else None,
        g2p_model_version=task.g2p_model.version if task.g2p_model else None,
        user_id=user_id,
        status=AlignmentStatus.PENDING
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_alignment_task(db: Session, task_id: int, user_id: int = None) -> Optional[AlignmentQueue]:
    query = db.query(AlignmentQueue).filter(AlignmentQueue.id == task_id)
    if user_id is not None:
        query = query.filter(AlignmentQueue.user_id == user_id)
    return query.first()


def get_alignment_tasks(db: Session, skip: int = 0, limit: int = 100, user_id: int = None, status: AlignmentStatus = None) -> List[AlignmentQueue]:
    query = db.query(AlignmentQueue)
    if user_id is not None:
        query = query.filter(AlignmentQueue.user_id == user_id)
    if status is not None:
        query = query.filter(AlignmentQueue.status == status)
    return query.offset(skip).limit(limit).all()


def update_alignment_task(db: Session, task_id: int, task_update: AlignmentQueueUpdate, user_id: int = None) -> Optional[AlignmentQueue]:
    query = db.query(AlignmentQueue).filter(AlignmentQueue.id == task_id)
    if user_id is not None:
        query = query.filter(AlignmentQueue.user_id == user_id)
    db_task = query.first()
    if db_task:
        update_data = task_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_task, field, value)
        db.commit()
        db.refresh(db_task)
    return db_task


def delete_alignment_task(db: Session, task_id: int, user_id: int = None) -> bool:
    query = db.query(AlignmentQueue).filter(AlignmentQueue.id == task_id)
    if user_id is not None:
        query = query.filter(AlignmentQueue.user_id == user_id)
    db_task = query.first()
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False




# Model validation functions
def find_model_by_param(db: Session, model_param: ModelParameter, model_type: ModelType) -> Optional[MFAModel]:
    """Find a model by parameter and type, returns the model object or None
    
    First tries exact name match, then tries with model type suffix
    """
    # Try exact name match first
    model = db.query(MFAModel).filter(
        MFAModel.name == model_param.name,
        MFAModel.version == model_param.version,
        MFAModel.model_type == model_type
    ).first()
    
    if model:
        return model
    
    # Try with model type suffix (e.g., "english_us_arpa" + "_acoustic")
    name_with_suffix = f"{model_param.name}_{model_type.value}"
    model = db.query(MFAModel).filter(
        MFAModel.name == name_with_suffix,
        MFAModel.version == model_param.version,
        MFAModel.model_type == model_type
    ).first()
    
    return model




def validate_models_same_language(db: Session, 
                                acoustic_model: ModelParameter,
                                dictionary_model: ModelParameter,
                                g2p_model: Optional[ModelParameter] = None) -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate that all models belong to the same language
    
    Returns:
        Tuple[bool, Optional[str], Optional[int]]: (is_valid, error_message, language_id)
    """
    # Get acoustic model using the helper function
    acoustic = find_model_by_param(db, acoustic_model, ModelType.ACOUSTIC)
    if not acoustic:
        return False, f"Acoustic model '{acoustic_model.name}' not found", None
    
    # Get dictionary model using the helper function
    dictionary = find_model_by_param(db, dictionary_model, ModelType.DICTIONARY)
    if not dictionary:
        return False, f"Dictionary model '{dictionary_model.name}' not found", None
    
    # Check if they have the same language
    if acoustic.language_id != dictionary.language_id:
        return False, "Acoustic and dictionary models must be for the same language", None
    
    # Check G2P model if provided
    if g2p_model:
        g2p = find_model_by_param(db, g2p_model, ModelType.G2P)
        if not g2p:
            return False, f"G2P model '{g2p_model.name}' not found", None
        
        if g2p.language_id != acoustic.language_id:
            return False, "All models must be for the same language", None
    
    return True, None, acoustic.language_id
