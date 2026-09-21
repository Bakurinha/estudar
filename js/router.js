/** Roteador por hash: funciona no GitHub Pages sem configuração de rewrite. */
import { ROUTES } from './config.js';
import { qsa } from './utils.js';

export function currentRoute() {
  const hash = location.hash.replace(/^#\/?/, '');
  const [route = 'dashboard', ...parts] = hash.split('/');
  return { route: ROUTES.includes(route) ? route : 'dashboard', parts };
}

export function navigate(route, ...parts) {
  location.hash = `#/${[route, ...parts].join('/')}`;
}

export function updateActiveNav(route) {
  qsa('[data-route-link]').forEach(link => {
    if (link.dataset.routeLink === route) link.setAttribute('aria-current','page');
    else link.removeAttribute('aria-current');
  });
}
