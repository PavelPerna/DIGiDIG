// View page JavaScript

let currentEmailId = null;
let currentUserEmail = null;
let currentEmailData = null;

async function loadEmail() {
    // Get email ID from URL path: /view/{email_id}
    const pathParts = window.location.pathname.split('/');
    const emailId = pathParts[pathParts.length - 1]; // Last part of path

    if (!emailId || emailId === 'view') {
        window.MailApp.showMessage('No email ID provided', 'error');
        goBack();
        return;
    }

    currentEmailId = emailId;

    try {
        // Use mock user for testing (authentication bypassed)
        currentUserEmail = 'test@example.com';

        // Get email details
        const response = await window.MailApp.makeRequest(`/api/storage/emails/${currentEmailId}`);
        currentEmailData = response;

        // Update UI
        document.getElementById('email-subject').textContent = currentEmailData.subject || 'No subject';
        document.getElementById('email-from').textContent = currentEmailData.sender || 'Unknown';
        document.getElementById('email-to').textContent = currentEmailData.recipient || 'Unknown';
        document.getElementById('email-date').textContent = currentEmailData.timestamp ?
            new Date(currentEmailData.timestamp).toLocaleString() : 'Unknown';
        document.getElementById('email-body').innerHTML = (currentEmailData.body || 'No content')
            .replace(/\n/g, '<br>');

        // Update mark as read button
        const markReadBtn = document.getElementById('mark-read-btn');
        if (currentEmailData.read) {
            markReadBtn.textContent = 'Mark as Unread';
            markReadBtn.onclick = () => markAsRead(false);
        } else {
            markReadBtn.textContent = 'Mark as Read';
            markReadBtn.onclick = () => markAsRead(true);
        }

        // Mark as read if not already read
        if (!currentEmailData.read) {
            await markAsRead(true);
        }

        // Update unread count initially
        await updateUnreadCount();

    } catch (error) {
        console.error('Error loading email:', error);
        window.MailApp.showMessage('Error loading email: ' + error.message, 'error');
        goBack();
    }
}

async function markAsRead(read) {
    // If no parameter provided, toggle current state
    if (read === undefined) {
        read = !currentEmailData.read;
    }
    
    try {
        await window.MailApp.makeRequest(`/api/storage/emails/${currentEmailId}/read?read=${read}`, {
            method: 'PUT'
        });

        // Update button
        const markReadBtn = document.getElementById('mark-read-btn');
        if (read) {
            markReadBtn.textContent = 'Mark as Unread';
            markReadBtn.onclick = () => markAsRead(false);
        } else {
            markReadBtn.textContent = 'Mark as Read';
            markReadBtn.onclick = () => markAsRead(true);
        }

        currentEmailData.read = read;
        
        // Update unread count in menu
        await updateUnreadCount();
    } catch (error) {
        console.error('Error updating email status:', error);
        window.MailApp.showMessage('Error updating email status', 'error');
    }
}

function replyToEmail() {
    if (!currentEmailData) return;

    // Setup reply form
    document.getElementById('compose-modal-title').textContent = 'Reply';
    document.getElementById('reply-to').value = currentEmailData.sender;
    document.getElementById('reply-subject').value = currentEmailData.subject.startsWith('Re: ') ?
        currentEmailData.subject : `Re: ${currentEmailData.subject}`;
    document.getElementById('reply-body').value = `\n\n--- Original message ---\nFrom: ${currentEmailData.sender}\nSubject: ${currentEmailData.subject}\n\n`;

    // Show modal
    window.MailApp.showModal('compose-modal');
}

function forwardEmail() {
    if (!currentEmailData) return;

    // Setup forward form
    document.getElementById('compose-modal-title').textContent = 'Forward';
    document.getElementById('reply-to').value = '';
    document.getElementById('reply-subject').value = currentEmailData.subject.startsWith('Fwd: ') ?
        currentEmailData.subject : `Fwd: ${currentEmailData.subject}`;
    document.getElementById('reply-body').value = `---------- Forwarded message ----------\nFrom: ${currentEmailData.sender}\nSubject: ${currentEmailData.subject}\n\n${currentEmailData.body || ''}`;

    // Show modal
    window.MailApp.showModal('compose-modal');
}

async function deleteEmail() {
    if (!confirm('Are you sure you want to delete this email?')) return;

    try {
        await window.MailApp.makeRequest(`/api/storage/emails/${currentEmailId}`, {
            method: 'DELETE'
        });

        window.MailApp.showMessage('Email deleted successfully', 'success');
        goBack();
    } catch (error) {
        console.error('Error deleting email:', error);
        window.MailApp.showMessage('Error deleting email', 'error');
    }
}

async function sendReply(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const replyData = {
        from: currentUserEmail,
        to: formData.get('to'),
        subject: formData.get('subject'),
        body: formData.get('body')
    };

    try {
        // Determine if this is a reply or forward based on modal title
        const isReply = document.getElementById('compose-modal-title').textContent === 'Reply';

        if (isReply) {
            await window.MailApp.makeRequest(`/api/storage/emails/${currentEmailId}/reply`, {
                method: 'POST',
                body: JSON.stringify(replyData)
            });
        } else {
            await window.MailApp.makeRequest(`/api/storage/emails/${currentEmailId}/forward`, {
                method: 'POST',
                body: JSON.stringify(replyData)
            });
        }

        closeComposeModal();
        window.MailApp.showMessage('Email sent successfully', 'success');
    } catch (error) {
        console.error('Error sending email:', error);
        window.MailApp.showMessage('Error sending email', 'error');
    }
}

function goBack() {
    window.location.href = '/list';
}

function closeComposeModal() {
    window.MailApp.hideModal('compose-modal');
    document.getElementById('reply-form').reset();
}

async function updateUnreadCount() {
    try {
        if (!currentUserEmail) return;
        const response = await window.MailApp.makeRequest(`/api/storage/emails/unread/count?user_email=${encodeURIComponent(currentUserEmail)}`);
        const count = response.unread_count || 0;
        
        // Update menu unread count
        const menuUnreadSpan = document.getElementById('menu-unread-count');
        const countText = count > 0 ? `(${count})` : '';
        
        if (menuUnreadSpan) {
            menuUnreadSpan.textContent = countText;
        }
    } catch (error) {
        console.error('Error updating unread count:', error);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('View page JavaScript loaded');
    loadEmail();
});