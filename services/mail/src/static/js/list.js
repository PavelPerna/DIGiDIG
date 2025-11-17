// List page JavaScript

let currentUserEmail = null;
let currentContextEmailId = null;
let currentContextEmailRead = null;

async function refreshEmails() {
    console.log('[refreshEmails] Starting...');
    try {
        // Use mock user for testing (authentication bypassed)
        currentUserEmail = 'test@example.com';
        console.log('[refreshEmails] User email:', currentUserEmail);

        // Get unread count
        await updateUnreadCount();

        // Get emails from storage service via proxy
        console.log('[refreshEmails] Fetching emails...');
        const response = await window.MailApp.makeRequest(`/api/storage/emails?user_email=${encodeURIComponent(currentUserEmail)}`);
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
                        <div class="email-header">
                            <div class="email-from">From</div>
                            <div class="email-subject">Subject</div>
                            <div class="email-date">Date</div>
                        </div>
                        ${emails.map(email => `
                            <div class="email-row ${!email.read ? 'unread' : ''}" data-email-id="${email._id}" onclick="viewEmail('${email._id}')">
                                <div class="email-from">${email.sender || 'Unknown'}</div>
                                <div class="email-subject">${email.subject || 'No subject'}</div>
                                <div class="email-date">${email.timestamp ? new Date(email.timestamp).toLocaleString() : 'Unknown'}</div>
                                <div class="email-actions">
                                    <span class="context-menu-icon" title="Click for options" onclick="showContextMenu(event, '${email._id}', ${email.read})">⋮</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
                console.log('[refreshEmails] Emails rendered successfully');
            } else {
                console.log('[refreshEmails] No emails, showing empty state');
                emailsList.innerHTML = '<div class="empty-state"><p>No emails found</p><button class="btn btn-primary" onclick="composeEmail()">Compose New Email</button></div>';
            }
        } else {
            console.error('[refreshEmails] .emails-list element not found!');
        }
    } catch (error) {
        console.error('[refreshEmails] Error:', error);
        window.MailApp.showMessage('Error refreshing emails: ' + error.message, 'error');
    }
}

async function updateUnreadCount() {
    try {
        if (!currentUserEmail) return;
        const response = await window.MailApp.makeRequest(`/api/storage/emails/unread/count?user_email=${encodeURIComponent(currentUserEmail)}`);
        const count = response.unread_count || 0;
        
        // Update both menu and page header unread counts
        const menuUnreadSpan = document.getElementById('menu-unread-count');
        const pageUnreadSpan = document.getElementById('unread-count');
        
        const countText = count > 0 ? `(${count})` : '';
        
        if (menuUnreadSpan) {
            menuUnreadSpan.textContent = countText;
        }
        if (pageUnreadSpan) {
            pageUnreadSpan.textContent = countText;
        }
    } catch (error) {
        console.error('Error updating unread count:', error);
    }
}

function viewEmail(emailId) {
    // Navigate to view page instead of showing modal
    window.location.href = `/view/${emailId}`;
}

function showContextMenu(event, emailId, isRead) {
    event.preventDefault();
    event.stopPropagation();

    currentContextEmailId = emailId;
    currentContextEmailRead = isRead;

    const contextMenu = document.getElementById('context-menu');
    const markReadText = document.getElementById('mark-read-text');

    // Update mark as read/unread text
    markReadText.textContent = isRead ? 'Mark as Unread' : 'Mark as Read';

    // Position the context menu near the clicked element (open to the left)
    const rect = event.target.getBoundingClientRect();
    const menuWidth = 200; // Match the CSS width
    contextMenu.style.left = (rect.right + window.scrollX - menuWidth) + 'px';
    contextMenu.style.top = (rect.bottom + window.scrollY) + 'px';
    contextMenu.style.display = 'block';

    // Hide context menu when clicking elsewhere
    document.addEventListener('click', hideContextMenu);
}

function hideContextMenu() {
    const contextMenu = document.getElementById('context-menu');
    contextMenu.style.display = 'none';
    document.removeEventListener('click', hideContextMenu);
}

async function markAsReadFromMenu() {
    hideContextMenu();
    await markAsRead(currentContextEmailId, !currentContextEmailRead);
}

async function replyToEmailFromMenu() {
    hideContextMenu();
    // Navigate to compose page with reply parameters
    window.location.href = `/compose?reply=${currentContextEmailId}`;
}

async function forwardEmailFromMenu() {
    hideContextMenu();
    // Navigate to compose page with forward parameters
    window.location.href = `/compose?forward=${currentContextEmailId}`;
}

async function deleteEmailFromMenu() {
    hideContextMenu();
    if (!confirm('Are you sure you want to delete this email?')) return;

    try {
        await window.MailApp.makeRequest(`/api/storage/emails/${currentContextEmailId}`, {
            method: 'DELETE'
        });

        // Remove from UI
        const emailRow = document.querySelector(`[data-email-id="${currentContextEmailId}"]`);
        if (emailRow) {
            emailRow.remove();
        }

        // Update unread count
        await updateUnreadCount();

        window.MailApp.showMessage('Email deleted successfully', 'success');
    } catch (error) {
        console.error('Error deleting email:', error);
        window.MailApp.showMessage('Error deleting email', 'error');
    }
}

async function markAsRead(emailId, read) {
    try {
        await window.MailApp.makeRequest(`/api/storage/emails/${emailId}/read?read=${read}`, {
            method: 'PUT'
        });

        // Update UI
        const emailRow = document.querySelector(`[data-email-id="${emailId}"]`);
        if (emailRow) {
            if (read) {
                emailRow.classList.remove('unread');
            } else {
                emailRow.classList.add('unread');
            }
        }

        // Update unread count
        await updateUnreadCount();
    } catch (error) {
        console.error('Error marking email as read:', error);
        window.MailApp.showMessage('Error updating email status', 'error');
    }
}

function composeEmail() {
    // Redirect to compose page
    window.location.href = '/compose';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('List page JavaScript loaded');
    // Auto-refresh emails on page load
    refreshEmails();
});