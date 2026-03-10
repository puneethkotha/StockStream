/**
 * StockStream landing page — interactive enhancements
 */

document.addEventListener('DOMContentLoaded', () => {
  // Update GitHub links with actual repo URL if available
  const repoUrl = getRepoUrl();
  if (repoUrl) {
    document.querySelectorAll('a[href="https://github.com"]').forEach((a) => {
      a.href = repoUrl;
    });
  }

  // Smooth scroll for anchor links (enhance native scroll-behavior)
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const href = anchor.getAttribute('href');
      if (href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Intersection observer for subtle scroll animations
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
  );

  document.querySelectorAll('.feature, .step, .arch-diagram, .dashboard-wrap').forEach((el) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(12px)';
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    observer.observe(el);
  });

  // Add visible class handler
  const style = document.createElement('style');
  style.textContent = `
    .visible {
      opacity: 1 !important;
      transform: translateY(0) !important;
    }
  `;
  document.head.appendChild(style);
});

function getRepoUrl() {
  return 'https://github.com/puneethkotha/StockStream';
}
