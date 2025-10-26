"""
Internationalization (i18n) module for DIGiDIG project.

Provides translation support for multiple languages with fallback to English.
Thread-safe for async applications.

Supported languages:
- cs: Czech (čeština)
- en: English (default)

Usage:
    from lib.common.i18n import I18n

    # Initialize
    i18n = I18n(default_language='cs')
    
    # Get translation
    text = i18n.get('login.title')  # Returns translated text
    
    # Change language
    i18n.set_language('en')
    
    # Get with parameters
    text = i18n.get('welcome.message', username='John')
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class I18n:
    """Internationalization handler with JSON-based translations."""
    
    # Supported languages
    SUPPORTED_LANGUAGES = ['cs', 'en']
    DEFAULT_LANGUAGE = 'en'
    
    def __init__(self, default_language: str = 'en', service_name: Optional[str] = None):
        """
        Initialize i18n handler.
        
        Args:
            default_language: Default language code (cs, en)
            service_name: Service name for loading service-specific translations
        """
        self._current_language = default_language if default_language in self.SUPPORTED_LANGUAGES else self.DEFAULT_LANGUAGE
        self._service_name = service_name
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        
        # Load translations
        self._load_translations()
    
    def _get_locales_dir(self) -> Path:
        """Get path to locales directory."""
        # Locales are in project root
        project_root = Path(__file__).parent.parent.parent
        return project_root / 'locales'
    
    def _load_translations(self):
        """Load translation files for all supported languages."""
        locales_dir = self._get_locales_dir()
        
        if not locales_dir.exists():
            logger.warning(f"Locales directory not found: {locales_dir}")
            return
        
        for lang in self.SUPPORTED_LANGUAGES:
            lang_dir = locales_dir / lang
            if not lang_dir.exists():
                logger.warning(f"Language directory not found: {lang_dir}")
                continue
            
            # Load common translations
            self._load_language_file(lang, 'common')
            
            # Load service-specific translations if service_name is provided
            if self._service_name:
                self._load_language_file(lang, self._service_name)
    
    def _load_language_file(self, lang: str, module: str):
        """
        Load a specific translation file.
        
        Args:
            lang: Language code (cs, en)
            module: Module name (common, admin, client, etc.)
        """
        locales_dir = self._get_locales_dir()
        file_path = locales_dir / lang / f"{module}.json"
        
        if not file_path.exists():
            logger.debug(f"Translation file not found: {file_path}")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Initialize language dict if not exists
                if lang not in self._translations:
                    self._translations[lang] = {}
                
                # Merge translations (flatten nested structure)
                self._flatten_dict(data, self._translations[lang])
                
                logger.info(f"Loaded translations from {file_path}")
        except Exception as e:
            logger.error(f"Error loading translation file {file_path}: {e}")
    
    def _flatten_dict(self, nested_dict: Dict, flat_dict: Dict, prefix: str = ''):
        """
        Flatten nested dictionary to dot-notation keys.
        
        Example:
            {'login': {'title': 'Login'}} -> {'login.title': 'Login'}
        """
        for key, value in nested_dict.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._flatten_dict(value, flat_dict, full_key)
            else:
                flat_dict[full_key] = value
    
    def set_language(self, language: str):
        """
        Set current language.
        
        Args:
            language: Language code (cs, en)
        """
        with self._lock:
            if language in self.SUPPORTED_LANGUAGES:
                self._current_language = language
                logger.info(f"Language changed to: {language}")
            else:
                logger.warning(f"Unsupported language: {language}, using {self._current_language}")
    
    def get_language(self) -> str:
        """Get current language code."""
        return self._current_language
    
    def get(self, key: str, **kwargs) -> str:
        """
        Get translated text for given key.
        
        Args:
            key: Translation key in dot notation (e.g., 'login.title')
            **kwargs: Parameters for string formatting
        
        Returns:
            Translated text or key if translation not found
        """
        with self._lock:
            current_lang = self._current_language
            
            # Try current language
            if current_lang in self._translations:
                text = self._translations[current_lang].get(key)
                if text:
                    return self._format_text(text, kwargs)
            
            # Fallback to English
            if current_lang != self.DEFAULT_LANGUAGE and self.DEFAULT_LANGUAGE in self._translations:
                text = self._translations[self.DEFAULT_LANGUAGE].get(key)
                if text:
                    logger.debug(f"Using fallback translation for key: {key}")
                    return self._format_text(text, kwargs)
            
            # Return key if no translation found
            logger.warning(f"Translation not found for key: {key} (lang: {current_lang})")
            return key
    
    def _format_text(self, text: str, params: Dict[str, Any]) -> str:
        """
        Format text with parameters.
        
        Args:
            text: Text template (e.g., "Hello {username}")
            params: Parameters for formatting
        
        Returns:
            Formatted text
        """
        if not params:
            return text
        
        try:
            return text.format(**params)
        except KeyError as e:
            logger.error(f"Missing parameter in translation: {e}")
            return text
    
    def get_all(self, prefix: str = '') -> Dict[str, str]:
        """
        Get all translations for current language with optional prefix filter.
        
        Args:
            prefix: Optional key prefix filter (e.g., 'login' for all login.* keys)
        
        Returns:
            Dictionary of all matching translations
        """
        with self._lock:
            current_lang = self._current_language
            
            if current_lang not in self._translations:
                return {}
            
            translations = self._translations[current_lang]
            
            if prefix:
                return {k: v for k, v in translations.items() if k.startswith(prefix)}
            
            return translations.copy()


# Global instance for simple usage
_global_i18n: Optional[I18n] = None


def init_i18n(default_language: str = 'en', service_name: Optional[str] = None) -> I18n:
    """
    Initialize global i18n instance.
    
    Args:
        default_language: Default language code
        service_name: Service name for service-specific translations
    
    Returns:
        I18n instance
    """
    global _global_i18n
    _global_i18n = I18n(default_language=default_language, service_name=service_name)
    return _global_i18n


def get_i18n() -> I18n:
    """
    Get global i18n instance.
    
    Returns:
        I18n instance
    
    Raises:
        RuntimeError: If i18n not initialized
    """
    global _global_i18n
    if _global_i18n is None:
        raise RuntimeError("i18n not initialized. Call init_i18n() first.")
    return _global_i18n


def t(key: str, **kwargs) -> str:
    """
    Shorthand function for translation.
    
    Args:
        key: Translation key
        **kwargs: Parameters for formatting
    
    Returns:
        Translated text
    """
    return get_i18n().get(key, **kwargs)
