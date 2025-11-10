// List page JavaScript

async function refreshEmails() {
    try {
        // Get current user from session via proxy
        const sessionResponse = await window.MailApp.makeRequest('/api/identity/session/verify');
        const userEmail = sessionResponse.username + '@example.com'; // Add domain for email address

        // Get emails from storage service via proxy
        const response = await window.MailApp.makeRequest(`/api/storage/emails?user_email=${encodeURIComponent(userEmail)}`);
        const emails = response.emails || [];

        // Update the emails list
        const emailsList = document.querySelector('.emails-list');
        if (emailsList) {
            if (emails.length > 0) {
                emailsList.innerHTML = `
                    <div class="emails-table">
                        ${emails.map(email => `
                            <div class="email-row" onclick="viewEmail('${email._id}')">
                                <div class="email-from">${email.sender || 'Unknown'}</div>
                                <div class="email-subject">${email.subject || 'No subject'}</div>
                                <div class="email-date">${new Date(email.timestamp).toLocaleString()}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                emailsList.innerHTML = '<p class="no-emails">No emails found</p>';
            }
        }
    } catch (error) {
        console.error('Error refreshing emails:', error);
        window.MailApp.showMessage('Error refreshing emails: ' + error.message, 'error');
    }
}

async function viewEmail(emailId) {
    try {
        // For now, just show a placeholder since storage doesn't have individual email endpoint
        // TODO: Implement proper email viewing when storage service supports it
        alert('Email viewing not yet implemented. Email ID: ' + emailId);
    } catch (error) {
        console.error('Error viewing email:', error);
        alert('Error loading email: ' + error.message);
    }
}

function closeEmailModal() {
    window.MailApp.hideModal('email-modal');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('List page JavaScript loaded');
    // Auto-refresh emails on page load
    refreshEmails();
});