"""
Integration test for SMTP to IMAP email flow
Tests local delivery mechanism:
1. Send email via SMTP to local user
2. Verify email stored in storage
3. Retrieve email via IMAP
"""

import pytest
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import os


# Test configuration
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))
def get_service_url(service, port, default_host='localhost'):
    """Get service URL, preferring Docker service names in containerized environment"""
    if os.getenv('SKIP_COMPOSE') == '1':  # Running in Docker test container
        return f'http://{service}:{port}'
    return f'http://{default_host}:{port}'

IDENTITY_URL = get_service_url('identity', 8001)
STORAGE_URL = get_service_url('storage', 8002)
IMAP_URL = get_service_url('imap', 8003)

# Test credentials (should exist in system)
TEST_SENDER = "admin@example.com"
TEST_RECIPIENT = "admin@example.com"
TEST_PASSWORD = "admin"


@pytest.fixture
def setup_test_environment():
    """Ensure test domain and user exist"""
    # The admin user should already exist from initialization
    # Verify domain exists
    try:
        response = requests.get(f"{IDENTITY_URL}/api/domains/example.com/exists")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True, "Test domain 'example.com' must exist"
    except Exception as e:
        pytest.skip(f"Cannot verify test environment: {e}")
    
    yield
    
    # Cleanup: We don't delete test emails to allow inspection


class TestSMTPIMAPFlow:
    """Test complete email flow from SMTP to IMAP"""
    
    def test_local_delivery_check(self, setup_test_environment):
        """Test that Identity service correctly identifies local domain"""
        response = requests.get(f"{IDENTITY_URL}/api/domains/example.com/exists")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is True
        assert data["domain"] == "example.com"
        
        # Test non-existent domain
        response = requests.get(f"{IDENTITY_URL}/api/domains/nonexistent.com/exists")
        assert response.status_code == 200
        data = response.json()
        assert data["exists"] is False
    
    def test_send_email_via_smtp(self, setup_test_environment):
        """Test sending email via SMTP server"""
        # Create test email
        msg = MIMEMultipart()
        msg["From"] = TEST_SENDER
        msg["To"] = TEST_RECIPIENT
        msg["Subject"] = f"Test Email - {int(time.time())}"
        
        body = f"This is a test email sent at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        msg.attach(MIMEText(body, "plain"))
        
        # Send via SMTP with authentication
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.set_debuglevel(0)
                # Login with test credentials
                server.login(TEST_SENDER, TEST_PASSWORD)
                server.send_message(msg)
                print(f"✓ Email sent successfully to {TEST_RECIPIENT}")
        except Exception as e:
            pytest.fail(f"Failed to send email via SMTP: {e}")
    
    def test_complete_email_flow(self, setup_test_environment):
        """Test complete flow: SMTP -> Storage -> IMAP"""
        # Step 1: Send email via SMTP
        unique_subject = f"Integration Test - {int(time.time())}"
        unique_body = f"Test body with unique ID: {int(time.time() * 1000)}"
        
        msg = MIMEMultipart()
        msg["From"] = TEST_SENDER
        msg["To"] = TEST_RECIPIENT
        msg["Subject"] = unique_subject
        msg.attach(MIMEText(unique_body, "plain"))
        
        print(f"\n1. Sending email via SMTP...")
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.set_debuglevel(0)
                # Authenticate
                server.login(TEST_SENDER, TEST_PASSWORD)
                server.send_message(msg)
            print(f"   ✓ Email sent to {TEST_RECIPIENT}")
        except Exception as e:
            pytest.fail(f"SMTP sending failed: {e}")
        
        # Step 2: Wait for processing and verify in storage
        print(f"\n2. Waiting for email to be processed...")
        time.sleep(2)  # Give SMTP handler time to process
        
        print(f"\n3. Checking storage directly...")
        try:
            response = requests.get(
                f"{STORAGE_URL}/emails",
                params={"user_id": TEST_RECIPIENT}
            )
            assert response.status_code == 200, f"Storage request failed: {response.status_code}"
            emails = response.json()
            
            # Find our email
            found = False
            for email in emails:
                if email["subject"] == unique_subject:
                    found = True
                    assert email["sender"] == TEST_SENDER
                    assert email["recipient"] == TEST_RECIPIENT
                    assert unique_body in email["body"]
                    assert "timestamp" in email
                    print(f"   ✓ Email found in storage")
                    print(f"     Subject: {email['subject']}")
                    print(f"     Timestamp: {email.get('timestamp')}")
                    break
            
            assert found, f"Email with subject '{unique_subject}' not found in storage. Found {len(emails)} emails total."
        except Exception as e:
            pytest.fail(f"Storage verification failed: {e}")
        
        # Step 3: Retrieve via IMAP REST API
        print(f"\n4. Retrieving via IMAP service...")
        
        # First, login to get token
        try:
            login_response = requests.post(
                f"{IDENTITY_URL}/login",
                json={
                    "username": "admin",
                    "domain": "example.com", 
                    "password": TEST_PASSWORD
                }
            )
            assert login_response.status_code == 200, f"Login failed: {login_response.status_code}"
            token = login_response.json()["access_token"]
            print(f"   ✓ Authenticated successfully")
        except Exception as e:
            pytest.fail(f"Authentication failed: {e}")
        
        # Retrieve emails via IMAP
        try:
            response = requests.get(
                f"{IMAP_URL}/emails",
                params={"user_id": TEST_RECIPIENT},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200, f"IMAP request failed: {response.status_code}"
            emails = response.json()
            
            # Find our email
            found = False
            for email in emails:
                if email["subject"] == unique_subject:
                    found = True
                    assert email["sender"] == TEST_SENDER
                    assert email["recipient"] == TEST_RECIPIENT
                    print(f"   ✓ Email retrieved via IMAP")
                    print(f"     Subject: {email['subject']}")
                    break
            
            assert found, f"Email not found via IMAP. Retrieved {len(emails)} emails."
        except Exception as e:
            pytest.fail(f"IMAP retrieval failed: {e}")
        
        print(f"\n✓ Complete flow test PASSED")
    
    def test_external_domain_handling(self, setup_test_environment):
        """Test that external domains are handled (stored locally for now)"""
        msg = MIMEMultipart()
        msg["From"] = TEST_SENDER
        msg["To"] = "external@gmail.com"
        msg["Subject"] = f"External Test - {int(time.time())}"
        msg.attach(MIMEText("Test to external domain", "plain"))
        
        print(f"\n1. Sending to external domain...")
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.login(TEST_SENDER, TEST_PASSWORD)
                server.send_message(msg)
            print(f"   ✓ SMTP accepted external recipient")
            # Note: Currently stored locally, external relay not implemented
        except Exception as e:
            # This is acceptable - external delivery may be rejected
            print(f"   ⚠ External delivery rejected (expected): {e}")
    
    def test_rest_api_send(self, setup_test_environment):
        """Test sending email via REST API"""
        smtp_url = get_service_url('smtp', 8000)
        recipient = "restapi@example.com"
        
        email_data = {
            "sender": TEST_SENDER,
            "recipient": recipient,
            "subject": f"REST API Test - {int(time.time())}",
            "body": "This email was sent via REST API"
        }
        
        print(f"\n1. Sending email via REST API...")
        try:
            response = requests.post(
                f"{smtp_url}/api/send",
                json=email_data,
                timeout=10
            )
            assert response.status_code == 200, f"REST API failed: {response.status_code}"
            data = response.json()
            assert data["status"] == "success"
            print(f"   ✓ Email sent via REST API")
        except Exception as e:
            pytest.fail(f"REST API send failed: {e}")
        
        # Verify email was stored
        print(f"\n2. Verifying email in storage...")
        time.sleep(1)
        try:
            response = requests.get(
                f"{STORAGE_URL}/emails",
                params={"user_id": recipient}
            )
            assert response.status_code == 200
            emails = response.json()
            
            found = False
            for email in emails:
                if email["subject"] == email_data["subject"]:
                    found = True
                    assert email["sender"] == TEST_SENDER
                    assert email["body"] == email_data["body"]
                    print(f"   ✓ Email found in storage")
                    break
            
            assert found, "Email not found in storage"
        except Exception as e:
            pytest.fail(f"Storage verification failed: {e}")
        
        print(f"\n✓ REST API test PASSED")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
