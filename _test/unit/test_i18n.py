"""
Unit tests for i18n (internationalization) module
"""
import pytest
import tempfile
import json
import os
from pathlib import Path

# Add common to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib'))

from lib.common.i18n import I18n


@pytest.fixture
def temp_locales_dir():
    """Create temporary locales directory with test translations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        locales_dir = Path(tmpdir) / "locales"
        locales_dir.mkdir()
        
        # Create English translations
        en_dir = locales_dir / "en"
        en_dir.mkdir()
        en_translations = {
            "login": {
                "title": "Login",
                "button": "Sign In",
                "username": "Username",
                "password": "Password"
            },
            "welcome": {
                "message": "Welcome {username}!",
                "title": "Welcome"
            },
            "errors": {
                "invalid_credentials": "Invalid username or password",
                "server_error": "Server error occurred"
            }
        }
        
        with open(en_dir / "common.json", "w") as f:
            json.dump(en_translations, f, indent=2)
        
        # Create Czech translations
        cs_dir = locales_dir / "cs"
        cs_dir.mkdir()
        cs_translations = {
            "login": {
                "title": "Přihlášení",
                "button": "Přihlásit se",
                "username": "Uživatelské jméno",
                "password": "Heslo"
            },
            "welcome": {
                "message": "Vítejte {username}!",
                "title": "Vítejte"
            },
            "errors": {
                "invalid_credentials": "Neplatné uživatelské jméno nebo heslo"
                # Missing server_error to test fallback
            }
        }
        
        with open(cs_dir / "common.json", "w") as f:
            json.dump(cs_translations, f, indent=2)
        
        # Create service-specific translations
        smtp_translations = {
            "email": {
                "sent": "Email sent successfully",
                "failed": "Failed to send email"
            }
        }
        
        with open(en_dir / "smtp.json", "w") as f:
            json.dump(smtp_translations, f, indent=2)
        
        yield locales_dir


@pytest.mark.unit
def test_i18n_basic_initialization():
    """Test basic I18n initialization"""
    i18n = I18n()
    
    assert i18n._current_language == 'en'  # Default language
    assert 'en' in I18n.SUPPORTED_LANGUAGES
    assert 'cs' in I18n.SUPPORTED_LANGUAGES


@pytest.mark.unit
def test_i18n_custom_language():
    """Test initialization with custom language"""
    i18n = I18n(default_language='cs')
    assert i18n._current_language == 'cs'
    
    # Test unsupported language fallback
    i18n = I18n(default_language='fr')
    assert i18n._current_language == 'en'  # Should fallback to default


@pytest.mark.unit
def test_i18n_set_language():
    """Test changing language"""
    i18n = I18n()
    
    # Change to supported language
    i18n.set_language('cs')
    assert i18n._current_language == 'cs'
    
    # Try unsupported language
    i18n.set_language('fr')
    assert i18n._current_language == 'cs'  # Should not change


@pytest.mark.unit
def test_i18n_missing_translation():
    """Test behavior with completely missing translation"""
    i18n = I18n()
    
    # Should return the key itself when translation not found
    missing_key = 'completely.missing.key'
    assert i18n.get(missing_key) == missing_key


@pytest.mark.unit
def test_i18n_parameter_substitution():
    """Test parameter substitution in translations"""
    i18n = I18n()
    
    # Mock a simple translation for testing
    i18n._translations = {
        'en': {
            'greeting': 'Hello {name}, you have {count} messages'
        }
    }
    
    result = i18n.get('greeting', name='Alice', count=5)
    assert result == 'Hello Alice, you have 5 messages'


@pytest.mark.unit 
def test_i18n_thread_safety():
    """Test thread safety of I18n"""
    i18n = I18n()
    
    # Basic test - real thread safety would need threading test
    assert hasattr(i18n, '_lock')
    assert i18n._lock is not None


@pytest.mark.unit
def test_i18n_get_available_languages():
    """Test getting available languages"""
    assert 'en' in I18n.SUPPORTED_LANGUAGES
    assert 'cs' in I18n.SUPPORTED_LANGUAGES
    assert len(I18n.SUPPORTED_LANGUAGES) >= 2


@pytest.mark.unit
def test_i18n_invalid_parameters():
    """Test handling invalid parameters in translations"""
    i18n = I18n()
    
    # Mock translation with parameters
    i18n._translations = {
        'en': {
            'test': 'Hello {name}'
        }
    }
    
    # Missing parameter - should not crash
    result = i18n.get('test')
    assert 'Hello' in result  # Should still contain base text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])