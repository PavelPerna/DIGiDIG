// List page JavaScript

async function refreshEmails() {
    console.log('[refreshEmails] Starting...');
    try {
        // Get current user from session via proxy
        console.log('[refreshEmails] Fetching session info...');
        const sessionResponse = await window.MailApp.makeRequest('/api/identity/session/verify');
        console.log('[refreshEmails] Session response:', sessionResponse);
        const userEmail = sessionResponse.username + '@example.com'; // Add domain for email address
        console.log('[refreshEmails] User email:', userEmail);

        // Get emails from storage service via proxy
        console.log('[refreshEmails] Fetching emails...');
        const response = await window.MailApp.makeRequest(`/api/storage/emails?user_email=${encodeURIComponent(userEmail)}`);
        console.log('[refreshEmails] Emails response:', response);
        const emails = response.emails || [];
        console.log('[refreshEmails] Found', emails.length, 'emails');

        // Update the emails list
        const emailsList = document.querySelector('.emails-list');
        console.log('[refreshEmails] emails-list element:', emailsList);
        if (emailsList) {
            if (emails.length > 0) {
                console.log('[refreshEmails] Rendering emails...');
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
                console.log('[refreshEmails] Emails rendered successfully');
            } else {
                console.log('[refreshEmails] No emails, showing empty state');
                emailsList.innerHTML = '<p class="no-emails">No emails found</p>';
            }
        } else {
            console.error('[refreshEmails] .emails-list element not found!');
        }
    } catch (error) {
        console.error('[refreshEmails] Error:', error);
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