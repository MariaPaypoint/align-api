from sqlalchemy.orm import Session
from typing import List, Optional
from app.domains.models.models import Language, MFAModel, ModelType
from app.domains.models.schemas import LanguageCreate, MFAModelCreate


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
    for lang in unused_languages:
        db.delete(lang)
    
    db.commit()
    return count
