from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from app.models import AlignmentQueue, AlignmentStatus, Language, MFAModel, ModelType
from app.schemas import AlignmentQueueCreate, AlignmentQueueUpdate, LanguageCreate, MFAModelCreate, ModelParameter

def create_alignment_task(db: Session, task: AlignmentQueueCreate, audio_path: str, text_path: str) -> AlignmentQueue:
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


# Language CRUD operations
def create_language(db: Session, language: LanguageCreate) -> Language:
    db_language = Language(
        code=language.code,
        name=language.name
    )
    db.add(db_language)
    db.commit()
    db.refresh(db_language)
    return db_language

def get_language_by_code(db: Session, code: str) -> Optional[Language]:
    return db.query(Language).filter(Language.code == code).first()

def get_languages(db: Session, skip: int = 0, limit: int = 100) -> List[Language]:
    return db.query(Language).offset(skip).limit(limit).all()

def get_or_create_language(db: Session, code: str, name: str) -> Language:
    language = get_language_by_code(db, code)
    if not language:
        language_create = LanguageCreate(code=code, name=name)
        language = create_language(db, language_create)
    return language

def bulk_create_languages(db: Session, languages: List[LanguageCreate]) -> List[Language]:
    """Create multiple languages in a single transaction"""
    db_languages = []
    for lang in languages:
        db_language = Language(
            code=lang.code,
            name=lang.name
        )
        db_languages.append(db_language)
    
    db.add_all(db_languages)
    db.commit()
    
    # Refresh to get IDs
    for db_lang in db_languages:
        db.refresh(db_lang)
    
    return db_languages

def get_or_create_languages_bulk(db: Session, language_data: List[dict]) -> dict:
    """Get or create multiple languages efficiently
    Args:
        language_data: List of dicts with 'code' and 'name' keys
    Returns:
        dict: mapping of language_code -> Language object
    """
    # Get all existing languages
    existing_codes = {lang.code for lang in db.query(Language).all()}
    
    # Find languages that need to be created
    languages_to_create = []
    for lang_data in language_data:
        if lang_data['code'] not in existing_codes:
            languages_to_create.append(LanguageCreate(
                code=lang_data['code'],
                name=lang_data['name']
            ))
    
    # Bulk create new languages
    if languages_to_create:
        bulk_create_languages(db, languages_to_create)
    
    # Return mapping of all languages
    all_languages = db.query(Language).all()
    return {lang.code: lang for lang in all_languages}


# MFA Model CRUD operations
def create_mfa_model(db: Session, model: MFAModelCreate) -> MFAModel:
    db_model = MFAModel(
        name=model.name,
        model_type=model.model_type,
        version=model.version,
        variant=model.variant,
        language_id=model.language_id,
        description=model.description
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def bulk_create_mfa_models(db: Session, models: List[MFAModelCreate]) -> int:
    """Create multiple MFA models in a single transaction"""
    db_models = []
    for model in models:
        db_model = MFAModel(
            name=model.name,
            model_type=model.model_type,
            version=model.version,
            variant=model.variant,
            language_id=model.language_id,
            description=model.description
        )
        db_models.append(db_model)
    
    db.add_all(db_models)
    db.commit()
    return len(db_models)

def get_mfa_models(db: Session, skip: int = 0, limit: int = 100, language_code: Optional[str] = None) -> List[MFAModel]:
    query = db.query(MFAModel)
    if language_code:
        query = query.join(Language).filter(Language.code == language_code)
    return query.offset(skip).limit(limit).all()

def count_mfa_models(db: Session) -> int:
    """Count total number of MFA models in database"""
    return db.query(MFAModel).count()

def get_mfa_models_by_type(db: Session, model_type: ModelType, language_code: Optional[str] = None) -> List[MFAModel]:
    query = db.query(MFAModel).filter(MFAModel.model_type == model_type)
    if language_code:
        query = query.join(Language).filter(Language.code == language_code)
    return query.all()

def get_mfa_model_by_name_type_version(db: Session, name: str, model_type: ModelType, version: str, variant: str = None) -> Optional[MFAModel]:
    query = db.query(MFAModel).filter(
        MFAModel.name == name,
        MFAModel.model_type == model_type,
        MFAModel.version == version
    )
    
    if variant is not None:
        query = query.filter(MFAModel.variant == variant)
    else:
        query = query.filter(MFAModel.variant.is_(None))
    
    return query.first()

def delete_all_mfa_models(db: Session) -> int:
    """Delete all MFA models and return count of deleted records"""
    count = db.query(MFAModel).count()
    db.query(MFAModel).delete()
    db.commit()
    return count

def delete_unused_languages(db: Session) -> int:
    """Delete languages that have no associated models"""
    # Get languages that have no models
    unused_languages = db.query(Language).filter(
        ~Language.id.in_(db.query(MFAModel.language_id).distinct())
    ).all()
    
    count = len(unused_languages)
    for language in unused_languages:
        db.delete(language)
    
    db.commit()
    return count


# Model validation functions
def validate_model_exists(db: Session, model_param: ModelParameter, model_type: ModelType) -> Optional[MFAModel]:
    """Validate that a model exists with given name, version and type
    
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
    
    # Try with model type suffix (for backward compatibility)
    type_suffix = model_type.value.lower()  # 'acoustic', 'dictionary', 'g2p'
    name_with_suffix = f"{model_param.name}_{type_suffix}"
    
    return db.query(MFAModel).filter(
        MFAModel.name == name_with_suffix,
        MFAModel.version == model_param.version,
        MFAModel.model_type == model_type
    ).first()

def validate_models_same_language(db: Session, 
                                acoustic_model: ModelParameter,
                                dictionary_model: ModelParameter,
                                g2p_model: Optional[ModelParameter] = None) -> Tuple[bool, Optional[str], Optional[int]]:
    """Validate that all models belong to the same language
    
    Returns:
        Tuple[bool, Optional[str], Optional[int]]: (is_valid, error_message, language_id)
    """
    # Get acoustic model
    acoustic_db = validate_model_exists(db, acoustic_model, ModelType.ACOUSTIC)
    if not acoustic_db:
        return False, f"Acoustic model '{acoustic_model.name}' version '{acoustic_model.version}' not found", None
    
    # Get dictionary model
    dictionary_db = validate_model_exists(db, dictionary_model, ModelType.DICTIONARY)
    if not dictionary_db:
        return False, f"Dictionary '{dictionary_model.name}' version '{dictionary_model.version}' not found", None
    
    # Check if acoustic and dictionary have same language
    if acoustic_db.language_id != dictionary_db.language_id:
        return False, "Acoustic model and dictionary must be for the same language", None
    
    # Check G2P model if provided
    if g2p_model:
        g2p_db = validate_model_exists(db, g2p_model, ModelType.G2P)
        if not g2p_db:
            return False, f"G2P model '{g2p_model.name}' version '{g2p_model.version}' not found", None
        
        if g2p_db.language_id != acoustic_db.language_id:
            return False, "G2P model must be for the same language as acoustic model and dictionary", None
    
    return True, None, acoustic_db.language_id
