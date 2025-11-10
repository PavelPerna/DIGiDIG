// Compose page JavaScript

function clearForm() {
    document.getElementById('compose-form').reset();
    document.getElementById('message').style.display = 'none';
}

async function sendEmail(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const userEmail = window.DIGIDIG_USER_INFO ? window.DIGIDIG_USER_INFO.email : 'anonymous@example.com';
    const emailData = {
        sender: userEmail,
        recipient: formData.get('to'),
        subject: formData.get('subject'),
        body: formData.get('body')
    };

    try {
        // Send email via SMTP service through proxy
        await window.MailApp.makeRequest('/api/smtp/send', {
            method: 'POST',
            body: JSON.stringify(emailData)
        });

        window.MailApp.showMessage('Email sent successfully!', 'success');
        clearForm();
    } catch (error) {
        console.error('Error sending email:', error);
        window.MailApp.showMessage('Error sending email: ' + error.message, 'error');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Compose page JavaScript loaded');
});