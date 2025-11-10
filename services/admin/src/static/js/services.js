// Services page JavaScript

async function refreshServices() {
    location.reload(); // Simple refresh for now
}

async function viewServiceLogs(serviceName) {
    try {
        const logs = await window.AdminApp.makeRequest(`${window.DIGIDIG_SERVICE_URLS.smtp}/logs`);
        showServiceModal(`Logs for ${serviceName}`, `<pre>${JSON.stringify(logs, null, 2)}</pre>`);
    } catch (error) {
        console.error('Error fetching logs:', error);
        showServiceModal(`Error`, `<p>Could not fetch logs: ${error.message}</p>`);
    }
}

async function viewServiceStats(serviceName) {
    try {
        const stats = await window.AdminApp.makeRequest(`${window.DIGIDIG_SERVICE_URLS.smtp}/stats`);
        showServiceModal(`Stats for ${serviceName}`, `<pre>${JSON.stringify(stats, null, 2)}</pre>`);
    } catch (error) {
        console.error('Error fetching stats:', error);
        showServiceModal(`Error`, `<p>Could not fetch stats: ${error.message}</p>`);
    }
}

function showServiceModal(title, content) {
    document.getElementById('service-modal-title').textContent = title;
    document.getElementById('service-details-content').innerHTML = content;
    window.AdminApp.showModal('service-modal');
}

function closeServiceModal() {
    window.AdminApp.hideModal('service-modal');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Services page JavaScript loaded');
});