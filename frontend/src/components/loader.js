/**
 * Loading Skeletons.
 */

export function renderProjectsSkeleton() {
  return `
    <div class="projects-grid">
      ${Array(6).fill(0).map(() => `
        <div class="card project-card">
          <div class="project-card-header">
            <div class="skeleton skeleton-title" style="width: 50%;"></div>
            <div class="skeleton" style="width: 60px; height: 20px; border-radius: var(--radius-full);"></div>
          </div>
          <div class="skeleton-text skeleton" style="width: 90%;"></div>
          <div class="skeleton-text skeleton" style="width: 80%;"></div>
          <div class="skeleton-text skeleton" style="width: 40%; margin-bottom: var(--space-5);"></div>
          <div class="project-card-pills">
            <div class="skeleton" style="width: 50px; height: 22px; border-radius: var(--radius-full);"></div>
            <div class="skeleton" style="width: 70px; height: 22px; border-radius: var(--radius-full);"></div>
            <div class="skeleton" style="width: 60px; height: 22px; border-radius: var(--radius-full);"></div>
          </div>
          <div class="project-card-footer" style="margin-top: auto;">
            <div class="skeleton" style="width: 80px; height: 12px;"></div>
            <div class="skeleton" style="width: 50px; height: 12px;"></div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

export function renderProjectDetailSkeleton() {
  return `
    <div class="project-header">
      <div class="project-header-top">
        <div class="project-title-area" style="flex-grow: 1;">
          <div class="skeleton skeleton-title" style="width: 40%; height: 36px; margin-bottom: var(--space-4);"></div>
          <div class="project-meta-pills">
            <div class="skeleton" style="width: 80px; height: 24px; border-radius: var(--radius-full);"></div>
            <div class="skeleton" style="width: 100px; height: 24px; border-radius: var(--radius-full);"></div>
            <div class="skeleton" style="width: 90px; height: 24px; border-radius: var(--radius-full);"></div>
          </div>
        </div>
        <div class="skeleton" style="width: 120px; height: 40px; border-radius: var(--radius-md);"></div>
      </div>
    </div>
    <div class="skeleton" style="width: 100%; height: 42px; margin-bottom: var(--space-6); border-radius: 0;"></div>
    <div class="overview-grid">
      <div class="overview-main">
        <div class="card">
          <div class="skeleton skeleton-title" style="width: 30%;"></div>
          <div class="skeleton-text skeleton" style="width: 100%;"></div>
          <div class="skeleton-text skeleton" style="width: 95%;"></div>
          <div class="skeleton-text skeleton" style="width: 80%;"></div>
        </div>
      </div>
      <div class="overview-sidebar">
        <div class="card">
          <div class="skeleton skeleton-title" style="width: 50%;"></div>
          <div class="skeleton-text skeleton" style="width: 90%;"></div>
          <div class="skeleton-text skeleton" style="width: 60%;"></div>
        </div>
      </div>
    </div>
  `;
}

export function renderTableSkeleton(rows = 5, cols = 4) {
  return `
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            ${Array(cols).fill(0).map(() => `<th><div class="skeleton" style="height: 12px; width: 60px;"></div></th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${Array(rows).fill(0).map(() => `
            <tr>
              ${Array(cols).fill(0).map(() => `<td><div class="skeleton" style="height: 14px; width: 80%;"></div></td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}
