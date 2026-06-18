/**
 * Toast notifications.
 */

export function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';
  if (type === 'warning') icon = '⚠️';

  toast.innerHTML = `
    <span>${icon}</span>
    <div style="flex: 1;">${message}</div>
    <button class="toast-close">&times;</button>
  `;

  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => {
    toast.style.animation = 'fadeOut var(--transition-fast) forwards';
    toast.addEventListener('animationend', () => toast.remove());
  });

  container.appendChild(toast);

  // Auto-remove
  setTimeout(() => {
    if (toast.parentElement) {
      toast.style.animation = 'fadeOut var(--transition-fast) forwards';
      toast.addEventListener('animationend', () => toast.remove());
    }
  }, 4000);
}
