
// Real-time notifications
function checkForNewNotifications() {
    fetch('/notifications/count')
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('.notification-badge');
            if (badge && data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = 'inline';
            } else if (badge) {
                badge.style.display = 'none';
            }
        })
        .catch(error => console.error('Error checking notifications:', error));
}

// Check for notifications every 30 seconds
setInterval(checkForNewNotifications, 30000);

// Initial check
document.addEventListener('DOMContentLoaded', checkForNewNotifications);
