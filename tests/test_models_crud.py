import pytest
from sqlalchemy.orm import Session
from app.models import Language, MFAModel, ModelType
from app.schemas import LanguageCreate, MFAModelCreate
from app.crud import (
    create_language,
    get_language_by_code,
    get_or_create_language,
    create_mfa_model,
    get_mfa_models,
    get_mfa_models_by_type,
    get_mfa_model_by_name_type_version,
    delete_all_mfa_models,
    delete_unused_languages
)


class TestLanguageCRUD:
    """Test cases for Language CRUD operations"""
    
    def test_create_language(self, db_session: Session):
        """Test creating a new language"""
        language_data = LanguageCreate(code="en", name="English")
        language = create_language(db_session, language_data)
        
        assert language.id is not None
        assert language.code == "en"
        assert language.name == "English"
        assert language.created_at is not None
        assert language.updated_at is not None
    
    def test_get_language_by_code(self, db_session: Session):
        """Test getting language by code"""
        # Create a language first
        language_data = LanguageCreate(code="ru", name="Russian")
        created_language = create_language(db_session, language_data)
        
        # Retrieve it
        retrieved_language = get_language_by_code(db_session, "ru")
        
        assert retrieved_language is not None
        assert retrieved_language.id == created_language.id
        assert retrieved_language.code == "ru"
        assert retrieved_language.name == "Russian"
    
    def test_get_language_by_code_not_found(self, db_session: Session):
        """Test getting non-existent language"""
        language = get_language_by_code(db_session, "nonexistent")
        assert language is None
    
    def test_get_or_create_language_existing(self, db_session: Session):
        """Test get_or_create with existing language"""
        # Create a language first
        language_data = LanguageCreate(code="es", name="Spanish")
        created_language = create_language(db_session, language_data)
        
        # Try to get or create the same language
        retrieved_language = get_or_create_language(db_session, "es", "Spanish")
        
        assert retrieved_language.id == created_language.id
        assert retrieved_language.code == "es"
        assert retrieved_language.name == "Spanish"
    
    def test_get_or_create_language_new(self, db_session: Session):
        """Test get_or_create with new language"""
        language = get_or_create_language(db_session, "fr", "French")
        
        assert language.id is not None
        assert language.code == "fr"
        assert language.name == "French"
        
        # Verify it was actually created in the database
        retrieved = get_language_by_code(db_session, "fr")
        assert retrieved is not None
        assert retrieved.id == language.id


class TestMFAModelCRUD:
    """Test cases for MFA Model CRUD operations"""
    
    @pytest.fixture
    def sample_language(self, db_session: Session):
        """Create a sample language for testing"""
        language_data = LanguageCreate(code="en", name="English")
        return create_language(db_session, language_data)
    
    def test_create_mfa_model(self, db_session: Session, sample_language: Language):
        """Test creating a new MFA model"""
        model_data = MFAModelCreate(
            name="english_us_arpa",
            model_type=ModelType.G2P,
            version="2.2.1",
            variant="us_arpa",
            language_id=sample_language.id,
            description="English G2P model for US pronunciation"
        )
        
        model = create_mfa_model(db_session, model_data)
        
        assert model.id is not None
        assert model.name == "english_us_arpa"
        assert model.model_type == ModelType.G2P
        assert model.version == "2.2.1"
        assert model.variant == "us_arpa"
        assert model.language_id == sample_language.id
        assert model.description == "English G2P model for US pronunciation"
        assert model.created_at is not None
        assert model.updated_at is not None
    
    def test_create_mfa_model_without_variant(self, db_session: Session, sample_language: Language):
        """Test creating MFA model without variant"""
        model_data = MFAModelCreate(
            name="english_mfa",
            model_type=ModelType.DICTIONARY,
            version="3.1.0",
            language_id=sample_language.id
        )
        
        model = create_mfa_model(db_session, model_data)
        
        assert model.variant is None
        assert model.description is None
    
    def test_get_mfa_models(self, db_session: Session, sample_language: Language):
        """Test getting all MFA models"""
        # Create multiple models
        for i in range(3):
            model_data = MFAModelCreate(
                name=f"model_{i}",
                model_type=ModelType.ACOUSTIC,
                version="1.0.0",
                language_id=sample_language.id
            )
            create_mfa_model(db_session, model_data)
        
        models = get_mfa_models(db_session)
        assert len(models) >= 3
    
    def test_get_mfa_models_by_type(self, db_session: Session, sample_language: Language):
        """Test getting models by type"""
        # Create models of different types
        g2p_model = MFAModelCreate(
            name="g2p_model",
            model_type=ModelType.G2P,
            version="1.0.0",
            language_id=sample_language.id
        )
        create_mfa_model(db_session, g2p_model)
        
        acoustic_model = MFAModelCreate(
            name="acoustic_model",
            model_type=ModelType.ACOUSTIC,
            version="1.0.0",
            language_id=sample_language.id
        )
        create_mfa_model(db_session, acoustic_model)
        
        # Get only G2P models
        g2p_models = get_mfa_models_by_type(db_session, ModelType.G2P)
        
        assert len(g2p_models) >= 1
        for model in g2p_models:
            assert model.model_type == ModelType.G2P
    
    def test_get_mfa_model_by_name_type_version(self, db_session: Session, sample_language: Language):
        """Test getting model by name, type, and version"""
        model_data = MFAModelCreate(
            name="test_model",
            model_type=ModelType.DICTIONARY,
            version="2.0.0",
            variant="test_variant",
            language_id=sample_language.id
        )
        created_model = create_mfa_model(db_session, model_data)
        
        # Find the model
        found_model = get_mfa_model_by_name_type_version(
            db_session, "test_model", ModelType.DICTIONARY, "2.0.0", "test_variant"
        )
        
        assert found_model is not None
        assert found_model.id == created_model.id
        assert found_model.name == "test_model"
        assert found_model.variant == "test_variant"
    
    def test_get_mfa_model_by_name_type_version_no_variant(self, db_session: Session, sample_language: Language):
        """Test getting model without variant"""
        model_data = MFAModelCreate(
            name="no_variant_model",
            model_type=ModelType.ACOUSTIC,
            version="1.5.0",
            language_id=sample_language.id
        )
        created_model = create_mfa_model(db_session, model_data)
        
        # Find the model without variant
        found_model = get_mfa_model_by_name_type_version(
            db_session, "no_variant_model", ModelType.ACOUSTIC, "1.5.0"
        )
        
        assert found_model is not None
        assert found_model.id == created_model.id
        assert found_model.variant is None
    
    def test_get_mfa_model_not_found(self, db_session: Session):
        """Test getting non-existent model"""
        model = get_mfa_model_by_name_type_version(
            db_session, "nonexistent", ModelType.G2P, "1.0.0"
        )
        assert model is None
    
    def test_delete_all_mfa_models(self, db_session: Session, sample_language: Language):
        """Test deleting all MFA models"""
        # Create some models
        for i in range(3):
            model_data = MFAModelCreate(
                name=f"delete_test_{i}",
                model_type=ModelType.G2P,
                version="1.0.0",
                language_id=sample_language.id
            )
            create_mfa_model(db_session, model_data)
        
        # Delete all models
        deleted_count = delete_all_mfa_models(db_session)
        
        assert deleted_count >= 3
        
        # Verify no models remain
        remaining_models = get_mfa_models(db_session)
        assert len(remaining_models) == 0
    
    def test_delete_unused_languages(self, db_session: Session):
        """Test deleting languages with no associated models"""
        # Create languages
        lang1 = get_or_create_language(db_session, "unused1", "Unused Language 1")
        lang2 = get_or_create_language(db_session, "used", "Used Language")
        lang3 = get_or_create_language(db_session, "unused2", "Unused Language 2")
        
        # Create a model for lang2 only
        model_data = MFAModelCreate(
            name="test_model",
            model_type=ModelType.ACOUSTIC,
            version="1.0.0",
            language_id=lang2.id
        )
        create_mfa_model(db_session, model_data)
        
        # Delete unused languages
        deleted_count = delete_unused_languages(db_session)
        
        assert deleted_count >= 2  # At least unused1 and unused2
        
        # Verify used language still exists
        remaining_lang = get_language_by_code(db_session, "used")
        assert remaining_lang is not None
        
        # Verify unused languages are gone
        unused1 = get_language_by_code(db_session, "unused1")
        unused2 = get_language_by_code(db_session, "unused2")
        assert unused1 is None
        assert unused2 is None
