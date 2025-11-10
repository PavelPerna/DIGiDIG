// Domains page JavaScript

function showAddDomainModal() {
    document.getElementById('modal-title').textContent = 'Add Domain';
    document.getElementById('domain-form').reset();
    document.getElementById('original-name').value = '';
    window.AdminApp.showModal('domain-modal');
}

function editDomain(domainName) {
    document.getElementById('modal-title').textContent = 'Edit Domain';
    document.getElementById('domain-name').value = domainName;
    document.getElementById('original-name').value = domainName;
    window.AdminApp.showModal('domain-modal');
}

function closeDomainModal() {
    window.AdminApp.hideModal('domain-modal');
}

async function saveDomain(event) {
    event.preventDefault();

    const formData = new FormData(event.target);
    const data = {
        name: formData.get('name'),
        originalName: formData.get('originalName')
    };

    try {
        const isEdit = data.originalName;
        const url = isEdit ? 'http://10.1.1.26:8001/domains' : 'http://10.1.1.26:8001/domains';
        const method = isEdit ? 'POST' : 'POST'; // Identity service uses POST for both

        if (isEdit) {
            data.old_name = data.originalName;
        }

        await window.AdminApp.makeRequest(url, {
            method: method,
            body: JSON.stringify(data)
        });

        closeDomainModal();
        location.reload(); // Simple refresh for now
    } catch (error) {
        console.error('Error saving domain:', error);
        alert('Error saving domain: ' + error.message);
    }
}

async function deleteDomain(domainName) {
    if (!confirm(`Are you sure you want to delete domain "${domainName}"?`)) {
        return;
    }

    try {
        await window.AdminApp.makeRequest(`http://10.1.1.26:8001/domains/${domainName}`, {
            method: 'DELETE'
        });

        location.reload(); // Simple refresh for now
    } catch (error) {
        console.error('Error deleting domain:', error);
        alert('Error deleting domain: ' + error.message);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Domains page JavaScript loaded');
});