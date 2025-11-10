// List page JavaScript

async function refreshEmails() {
    try {
        // Get current user from session via proxy
        const sessionResponse = await window.MailApp.makeRequest('/api/identity/session/verify');
        const userEmail = sessionResponse.username || 'admin@example.com'; // Fallback

        // TODO: Storage service doesn't have GET /emails endpoint yet
        // For now, use empty array until storage implements it
        const emails = [];
        // const emails = await window.MailApp.makeRequest(`/api/storage/emails?user_id=${encodeURIComponent(userEmail)}`);

        // Update the emails list
        const emailsList = document.querySelector('.emails-list');
        if (emailsList && emails.length > 0) {
            const emailsTable = emailsList.querySelector('.emails-table');
            if (emailsTable) {
                const tbody = emailsTable.querySelector('tbody') || emailsTable;
                tbody.innerHTML = emails.map(email => `
                    <div class="email-row" onclick="viewEmail('${email._id || email.id || email.timestamp}')">
                        <div class="email-from">${email.sender || 'Unknown'}</div>
                        <div class="email-subject">${email.subject || 'No subject'}</div>
                        <div class="email-date">${email.timestamp || 'Unknown'}</div>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error refreshing emails:', error);
        alert('Error refreshing emails: ' + error.message);
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
});