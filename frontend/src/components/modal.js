/**
 * Reusable Modal System.
 */

export function showModal({ title, contentHtml, onConfirm, confirmText = 'Confirm', confirmClass = 'btn-primary' }) {
  const container = document.getElementById('modal-container');
  if (!container) return;

  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';

  overlay.innerHTML = `
    <div class="modal">
      <div class="modal-header">
        <h2>${title}</h2>
        <button class="btn btn-ghost btn-icon modal-close-btn" style="font-size: var(--text-xl); line-height: 1;">&times;</button>
      </div>
      <form id="modal-form">
        <div class="modal-body">
          ${contentHtml}
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary modal-cancel-btn">Cancel</button>
          <button type="submit" class="btn ${confirmClass}">${confirmText}</button>
        </div>
      </form>
    </div>
  `;

  container.appendChild(overlay);

  const form = overlay.querySelector('#modal-form');
  const closeBtn = overlay.querySelector('.modal-close-btn');
  const cancelBtn = overlay.querySelector('.modal-cancel-btn');

  const close = () => {
    overlay.remove();
  };

  closeBtn.addEventListener('click', close);
  cancelBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>';

    try {
      const formData = new FormData(form);
      const data = {};
      formData.forEach((value, key) => {
        // Handle skills (split by comma)
        if (key === 'required_skills' || key === 'tech_stack') {
          data[key] = value.split(',').map(s => s.trim()).filter(Boolean);
        } else if (key === 'max_members') {
          data[key] = parseInt(value, 10) || 5;
        } else {
          data[key] = value;
        }
      });

      const success = await onConfirm(data);
      if (success !== false) {
        close();
      }
    } catch (err) {
      console.error(err);
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = confirmText;
    }
  });

  return { close };
}
