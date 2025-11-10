// Compose page JavaScript

function clearForm() {
    document.getElementById('compose-form').reset();
    document.getElementById('message').style.display = 'none';
}

async function sendEmail(event) {
    event.preventDefault();
    
    console.log('[sendEmail] Starting...');
    console.log('[sendEmail] User info:', window.DIGIDIG_USER_INFO);

    const formData = new FormData(event.target);
    // Get username from user info and append domain
    const username = window.DIGIDIG_USER_INFO ? window.DIGIDIG_USER_INFO.username : 'anonymous';
    const userEmail = username + '@example.com';
    
    const emailData = {
        sender: userEmail,
        recipient: formData.get('to'),
        subject: formData.get('subject'),
        body: formData.get('body')
    };
    
    console.log('[sendEmail] Email data:', emailData);

    try {
        // Send email via SMTP service through proxy
        console.log('[sendEmail] Sending via /api/smtp/send...');
        const response = await window.MailApp.makeRequest('/api/smtp/send', {
            method: 'POST',
            body: JSON.stringify(emailData)
        });
        
        console.log('[sendEmail] Response:', response);
        
        // Show notification (removed alert)
        window.MailApp.showMessage('Email sent successfully!', 'success');
        clearForm();
    } catch (error) {
        console.error('[sendEmail] Error:', error);
        window.MailApp.showMessage('Error sending email: ' + error.message, 'error');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Compose page JavaScript loaded');
});