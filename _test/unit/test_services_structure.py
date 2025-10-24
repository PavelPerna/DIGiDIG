"""
Structural tests for DIGiDIG services
Tests service files existence and basic structure without importing
"""
import pytest
from pathlib import Path
import ast
import os


class TestServiceStructure:
    """Test service file structure and content"""
    
    def test_identity_service_exists(self):
        """Test that identity service file exists"""
        identity_file = Path(__file__).parent.parent.parent / 'identity' / 'src' / 'identity.py'
        assert identity_file.exists()
        
        # Read and parse the file
        with open(identity_file, 'r') as f:
            content = f.read()
        
        # Check for key components
        assert 'FastAPI' in content
        assert 'def ' in content or 'async def ' in content
        assert 'app = FastAPI' in content or 'app=' in content
    
    def test_smtp_service_exists(self):
        """Test that SMTP service file exists"""
        smtp_file = Path(__file__).parent.parent.parent / 'smtp' / 'src' / 'smtp.py'
        assert smtp_file.exists()
        
        with open(smtp_file, 'r') as f:
            content = f.read()
        
        assert 'FastAPI' in content or 'app' in content
    
    def test_storage_service_exists(self):
        """Test that storage service file exists"""
        storage_file = Path(__file__).parent.parent.parent / 'storage' / 'src' / 'storage.py'
        assert storage_file.exists()
        
        with open(storage_file, 'r') as f:
            content = f.read()
        
        assert 'FastAPI' in content or 'app' in content
    
    def test_imap_service_exists(self):
        """Test that IMAP service file exists"""
        imap_file = Path(__file__).parent.parent.parent / 'imap' / 'src' / 'imap.py'
        assert imap_file.exists()
        
        with open(imap_file, 'r') as f:
            content = f.read()
        
        assert 'FastAPI' in content or 'app' in content
    
    def test_client_service_exists(self):
        """Test that client service file exists"""
        client_file = Path(__file__).parent.parent.parent / 'client' / 'src' / 'client.py'
        assert client_file.exists()
        
        with open(client_file, 'r') as f:
            content = f.read()
        
        assert 'FastAPI' in content or 'app' in content
    
    def test_admin_service_exists(self):
        """Test that admin service file exists"""
        admin_file = Path(__file__).parent.parent.parent / 'admin' / 'src' / 'admin.py'
        assert admin_file.exists()
        
        with open(admin_file, 'r') as f:
            content = f.read()
        
        assert 'FastAPI' in content or 'app' in content
    
    def test_apidocs_service_exists(self):
        """Test that API docs service file exists"""
        apidocs_file = Path(__file__).parent.parent.parent / 'apidocs' / 'src' / 'apidocs.py'
        assert apidocs_file.exists()
        
        with open(apidocs_file, 'r') as f:
            content = f.read()
        
        assert 'FastAPI' in content or 'app' in content


class TestServiceParsing:
    """Test that service files can be parsed as valid Python"""
    
    def test_identity_service_syntax(self):
        """Test identity service has valid Python syntax"""
        identity_file = Path(__file__).parent.parent.parent / 'identity' / 'src' / 'identity.py'
        
        with open(identity_file, 'r') as f:
            content = f.read()
        
        # Should parse without syntax errors
        try:
            ast.parse(content)
            assert True
        except SyntaxError:
            pytest.fail("identity.py has syntax errors")
    
    def test_smtp_service_syntax(self):
        """Test SMTP service has valid Python syntax"""
        smtp_file = Path(__file__).parent.parent.parent / 'smtp' / 'src' / 'smtp.py'
        
        with open(smtp_file, 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            assert True
        except SyntaxError:
            pytest.fail("smtp.py has syntax errors")
    
    def test_storage_service_syntax(self):
        """Test storage service has valid Python syntax"""
        storage_file = Path(__file__).parent.parent.parent / 'storage' / 'src' / 'storage.py'
        
        with open(storage_file, 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            assert True
        except SyntaxError:
            pytest.fail("storage.py has syntax errors")
    
    def test_imap_service_syntax(self):
        """Test IMAP service has valid Python syntax"""
        imap_file = Path(__file__).parent.parent.parent / 'imap' / 'src' / 'imap.py'
        
        with open(imap_file, 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            assert True
        except SyntaxError:
            pytest.fail("imap.py has syntax errors")
    
    def test_client_service_syntax(self):
        """Test client service has valid Python syntax"""
        client_file = Path(__file__).parent.parent.parent / 'client' / 'src' / 'client.py'
        
        with open(client_file, 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            assert True
        except SyntaxError:
            pytest.fail("client.py has syntax errors")
    
    def test_admin_service_syntax(self):
        """Test admin service has valid Python syntax"""
        admin_file = Path(__file__).parent.parent.parent / 'admin' / 'src' / 'admin.py'
        
        with open(admin_file, 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            assert True
        except SyntaxError:
            pytest.fail("admin.py has syntax errors")
    
    def test_apidocs_service_syntax(self):
        """Test API docs service has valid Python syntax"""
        apidocs_file = Path(__file__).parent.parent.parent / 'apidocs' / 'src' / 'apidocs.py'
        
        with open(apidocs_file, 'r') as f:
            content = f.read()
        
        try:
            ast.parse(content)
            assert True
        except SyntaxError:
            pytest.fail("apidocs.py has syntax errors")


class TestServiceFunctions:
    """Test that services contain expected function definitions"""
    
    def test_identity_service_functions(self):
        """Test identity service contains expected functions"""
        identity_file = Path(__file__).parent.parent.parent / 'identity' / 'src' / 'identity.py'
        
        with open(identity_file, 'r') as f:
            content = f.read()
        
        # Parse and find function definitions
        tree = ast.parse(content)
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
        
        # Should have some functions
        assert len(functions) > 0
        
        # Check for common patterns
        function_content = ' '.join(functions)
        has_auth_functions = any(word in function_content.lower() for word in ['create', 'verify', 'login', 'auth'])
        assert has_auth_functions, f"Identity service should have auth-related functions. Found: {functions[:5]}"
    
    def test_smtp_service_functions(self):
        """Test SMTP service contains expected functions"""
        smtp_file = Path(__file__).parent.parent.parent / 'smtp' / 'src' / 'smtp.py'
        
        with open(smtp_file, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
        
        assert len(functions) > 0
        
        # Check for email-related functions
        function_content = ' '.join(functions)
        has_email_functions = any(word in function_content.lower() for word in ['send', 'email', 'mail', 'smtp'])
        assert has_email_functions, f"SMTP service should have email-related functions. Found: {functions[:5]}"
    
    def test_storage_service_functions(self):
        """Test storage service contains expected functions"""
        storage_file = Path(__file__).parent.parent.parent / 'storage' / 'src' / 'storage.py'
        
        with open(storage_file, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
        
        assert len(functions) > 0
        
        # Check for storage-related functions
        function_content = ' '.join(functions)
        has_storage_functions = any(word in function_content.lower() for word in ['store', 'save', 'retrieve', 'get', 'delete'])
        assert has_storage_functions, f"Storage service should have storage-related functions. Found: {functions[:5]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])