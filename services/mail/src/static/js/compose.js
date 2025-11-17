// Compose page JavaScript

let currentReplyEmailId = null;
let currentForwardEmailId = null;

async function loadReplyOrForward() {
    const urlParams = new URLSearchParams(window.location.search);
    const replyId = urlParams.get('reply');
    const forwardId = urlParams.get('forward');

    if (replyId) {
        currentReplyEmailId = replyId;
        await loadEmailForReply(replyId);
    } else if (forwardId) {
        currentForwardEmailId = forwardId;
        await loadEmailForForward(forwardId);
    }
}

async function loadEmailForReply(emailId) {
    try {
        const response = await window.MailApp.makeRequest(`/api/storage/emails/${emailId}`);
        const email = response;

        document.getElementById('to').value = email.sender;
        document.getElementById('subject').value = email.subject.startsWith('Re: ') ? email.subject : `Re: ${email.subject}`;
        document.getElementById('body').value = `\n\n--- Original message ---\nFrom: ${email.sender}\nSubject: ${email.subject}\n\n${email.body || ''}`;
    } catch (error) {
        console.error('Error loading email for reply:', error);
        window.MailApp.showMessage('Error loading email for reply', 'error');
    }
}

async function loadEmailForForward(emailId) {
    try {
        const response = await window.MailApp.makeRequest(`/api/storage/emails/${emailId}`);
        const email = response;

        document.getElementById('subject').value = email.subject.startsWith('Fwd: ') ? email.subject : `Fwd: ${email.subject}`;
        document.getElementById('body').value = `---------- Forwarded message ----------\nFrom: ${email.sender}\nSubject: ${email.subject}\n\n${email.body || ''}`;
    } catch (error) {
        console.error('Error loading email for forward:', error);
        window.MailApp.showMessage('Error loading email for forward', 'error');
    }
}

function clearForm() {
    document.getElementById('compose-form').reset();
    document.getElementById('message').style.display = 'none';
    // Clear URL parameters
    window.history.replaceState({}, document.title, window.location.pathname);
    currentReplyEmailId = null;
    currentForwardEmailId = null;
}

async function sendEmail(event) {
    event.preventDefault();

    console.log('[sendEmail] Starting...');
    console.log('[sendEmail] User info:', window.DIGIDIG_USER_INFO);

    const formData = new FormData(event.target);
    // Get username from user info and append domain (fallback for testing)
    const username = (window.DIGIDIG_USER_INFO && window.DIGIDIG_USER_INFO.username) ? window.DIGIDIG_USER_INFO.username : 'test';
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
        
        // Redirect to list page after a short delay so user can see the success message
        setTimeout(() => {
            window.location.href = '/list';
        }, 1500);
    } catch (error) {
        console.error('[sendEmail] Error:', error);
        window.MailApp.showMessage('Error sending email: ' + error.message, 'error');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Compose page JavaScript loaded');
    loadReplyOrForward();
});