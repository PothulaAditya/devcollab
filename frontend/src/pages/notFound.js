export default async function renderNotFound(app) {
  app.innerHTML = `
    <main style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80vh; text-align: center; padding: var(--space-8);" class="animate-in">
      <div style="font-size: 6rem; margin-bottom: var(--space-4); background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800; line-height: 1;">404</div>
      <h2 style="font-size: var(--text-2xl); font-weight: 700; margin-bottom: var(--space-2);">Lost in space?</h2>
      <p style="color: var(--text-secondary); max-width: 400px; margin-bottom: var(--space-8);">The page you are looking for does not exist or has been relocated to another galaxy.</p>
      <a href="#/" class="btn btn-primary">Return Dashboard</a>
    </main>
  `;
}
