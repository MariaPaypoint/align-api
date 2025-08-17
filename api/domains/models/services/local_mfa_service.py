import os
import re
import subprocess
from typing import List, Dict, Optional
from pathlib import Path
from api.domains.models.models import ModelType
import logging

logger = logging.getLogger(__name__)

class LocalMFAService:
    """Service for working with local MFA models repository"""
    
    def __init__(self, repo_path: str = None):
        if repo_path is None:
            # Default to mfa-models directory in project root
            self.repo_path = Path("/app/mfa-models")
        else:
            self.repo_path = Path(repo_path)
        
        logger.info(f"LocalMFAService initialized with repo_path: {self.repo_path}")
    
    async def update_repository(self) -> bool:
        """Update the local MFA models repository"""
        try:
            if not self.repo_path.exists():
                logger.info("Repository doesn't exist, cloning...")
                result = subprocess.run([
                    "git", "clone", 
                    "https://github.com/MontrealCorpusTools/mfa-models.git",
                    str(self.repo_path)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    logger.error(f"Failed to clone repository: {result.stderr}")
                    return False
                logger.info("Repository cloned successfully")
            else:
                logger.info("Repository exists, updating...")
                result = subprocess.run([
                    "git", "pull", "--rebase", "origin", "main"
                ], cwd=self.repo_path, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    logger.error(f"Failed to update repository: {result.stderr}")
                    return False
                logger.info("Repository updated successfully")
            
            return True
        except subprocess.TimeoutExpired:
            logger.error("Git operation timed out")
            return False
        except Exception as e:
            logger.error(f"Error updating repository: {e}")
            return False
    
    async def fetch_models(self) -> List[Dict]:
        """
        Fetch all models from local repository
        Always updates repository first to get latest models
        Returns list of model dictionaries
        """
        logger.info("=== Starting fetch_models from local repository ===")
        
        # Always update repository to get latest models
        logger.info("Updating repository...")
        if not await self.update_repository():
            logger.warning("Failed to update repository, using existing data")
        
        models = []
        
        # Process each model type
        for model_type_str in ["g2p", "dictionary", "acoustic"]:
            try:
                logger.info(f"=== Processing model type: {model_type_str} ===")
                type_models = await self._fetch_type_models(model_type_str)
                models.extend(type_models)
                logger.info(f"=== Completed {model_type_str}: found {len(type_models)} models ===")
            except Exception as e:
                logger.error(f"=== ERROR in {model_type_str}: {e} ===")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        logger.info(f"=== FINAL RESULT: {len(models)} total models ===")
        return models
    
    async def _fetch_type_models(self, model_type_str: str) -> List[Dict]:
        """Fetch models for one type from local repository"""
        logger.info(f"--- Starting _fetch_type_models for {model_type_str} ---")
        models = []
        
        # Convert string to ModelType enum
        model_type = getattr(ModelType, model_type_str.upper())
        
        type_path = self.repo_path / model_type_str
        if not type_path.exists():
            logger.warning(f"Path doesn't exist: {type_path}")
            return models
        
        # Get all language directories
        language_dirs = [d for d in type_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        logger.info(f"Found {len(language_dirs)} language directories for {model_type_str}")
        
        for language_dir in language_dirs:
            try:
                language_code = language_dir.name
                logger.info(f"Processing language: {language_code}")
                
                language_models = await self._fetch_language_models(
                    model_type, model_type_str, language_code, language_dir
                )
                models.extend(language_models)
                logger.info(f"Got {len(language_models)} models for {language_code}")
                
            except Exception as e:
                logger.error(f"Error processing language {language_dir.name}: {e}")
                continue
        
        return models
    
    async def _fetch_language_models(self, model_type: ModelType, model_type_str: str, 
                                   language_code: str, language_dir: Path) -> List[Dict]:
        """Fetch models for a specific language"""
        models = []
        
        # Language name mapping (basic implementation)
        language_name = self._get_language_name(language_code)
        
        # Look for variant directories or version directories
        subdirs = [d for d in language_dir.iterdir() if d.is_dir()]
        
        if not subdirs:
            # No subdirectories, this might be a direct model
            model = {
                "name": language_code,
                "model_type": model_type,
                "version": "latest",
                "variant": None,
                "language_code": language_code,
                "language_name": language_name
            }
            models.append(model)
            logger.debug(f"Added direct model: {model['name']}")
        else:
            # Process subdirectories (variants or versions)
            for subdir in subdirs:
                variant = None
                version = "latest"
                
                # Try to determine if this is a variant or version
                if re.match(r'^v?\d+\.\d+', subdir.name):
                    # Looks like a version
                    version = subdir.name.lstrip('v')
                else:
                    # Treat as variant
                    variant = subdir.name
                
                # Check for version subdirectories within variant
                version_dirs = [d for d in subdir.iterdir() if d.is_dir() and re.match(r'^v?\d+\.\d+', d.name)]
                
                if version_dirs:
                    # Has version subdirectories
                    for version_dir in version_dirs:
                        version = version_dir.name.lstrip('v')
                        model_name = f"{language_code}_{variant}" if variant else language_code
                        
                        model = {
                            "name": model_name,
                            "model_type": model_type,
                            "version": version,
                            "variant": variant,
                            "language_code": language_code,
                            "language_name": language_name
                        }
                        models.append(model)
                        logger.debug(f"Added versioned model: {model['name']} v{version}")
                else:
                    # No version subdirectories
                    model_name = f"{language_code}_{variant}" if variant else language_code
                    
                    model = {
                        "name": model_name,
                        "model_type": model_type,
                        "version": version,
                        "variant": variant,
                        "language_code": language_code,
                        "language_name": language_name
                    }
                    models.append(model)
                    logger.debug(f"Added variant model: {model['name']}")
        
        return models
    
    def _get_language_name(self, language_code: str) -> str:
        """Convert language code to human-readable name"""
        language_names = {
            'english': 'English',
            'spanish': 'Spanish',
            'french': 'French',
            'german': 'German',
            'russian': 'Russian',
            'chinese': 'Chinese',
            'mandarin': 'Mandarin Chinese',
            'japanese': 'Japanese',
            'korean': 'Korean',
            'portuguese': 'Portuguese',
            'italian': 'Italian',
            'dutch': 'Dutch',
            'polish': 'Polish',
            'czech': 'Czech',
            'hungarian': 'Hungarian',
            'romanian': 'Romanian',
            'bulgarian': 'Bulgarian',
            'croatian': 'Croatian',
            'serbian': 'Serbian',
            'slovenian': 'Slovenian',
            'slovak': 'Slovak',
            'ukrainian': 'Ukrainian',
            'belarusian': 'Belarusian',
            'lithuanian': 'Lithuanian',
            'latvian': 'Latvian',
            'estonian': 'Estonian',
            'finnish': 'Finnish',
            'swedish': 'Swedish',
            'norwegian': 'Norwegian',
            'danish': 'Danish',
            'icelandic': 'Icelandic',
            'greek': 'Greek',
            'turkish': 'Turkish',
            'arabic': 'Arabic',
            'hebrew': 'Hebrew',
            'persian': 'Persian',
            'hindi': 'Hindi',
            'urdu': 'Urdu',
            'bengali': 'Bengali',
            'tamil': 'Tamil',
            'telugu': 'Telugu',
            'malayalam': 'Malayalam',
            'kannada': 'Kannada',
            'gujarati': 'Gujarati',
            'marathi': 'Marathi',
            'punjabi': 'Punjabi',
            'thai': 'Thai',
            'vietnamese': 'Vietnamese',
            'indonesian': 'Indonesian',
            'malay': 'Malay',
            'tagalog': 'Tagalog',
            'swahili': 'Swahili',
            'hausa': 'Hausa',
            'yoruba': 'Yoruba',
            'amharic': 'Amharic',
            'armenian': 'Armenian',
            'georgian': 'Georgian',
            'kazakh': 'Kazakh',
            'uzbek': 'Uzbek',
            'kyrgyz': 'Kyrgyz',
            'tajik': 'Tajik',
            'turkmen': 'Turkmen',
            'mongolian': 'Mongolian',
            'tibetan': 'Tibetan',
            'burmese': 'Burmese',
            'khmer': 'Khmer',
            'lao': 'Lao',
            'basque': 'Basque',
            'catalan': 'Catalan',
            'galician': 'Galician',
            'welsh': 'Welsh',
            'irish': 'Irish',
            'scottish': 'Scottish Gaelic',
            'maltese': 'Maltese',
            'albanian': 'Albanian',
            'macedonian': 'Macedonian',
            'montenegrin': 'Montenegrin',
            'bosnian': 'Bosnian',
            'wu': 'Wu Chinese',
            'abkhaz': 'Abkhaz',
            'bashkir': 'Bashkir',
            'chuvash': 'Chuvash'
        }
        
        return language_names.get(language_code.lower(), language_code.title())
