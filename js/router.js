/** Roteador por hash: funciona no GitHub Pages sem configuração de rewrite. */
import { ROUTES } from './config.js';
import { qsa } from './utils.js';

export function currentRoute() {
  const rawHash = location.hash.replace(/^#\/?/, '');
  const [path = 'dashboard', queryString = ''] = rawHash.split('?');
  const [route = 'dashboard', ...parts] = path.split('/');
  return {
    route: ROUTES.includes(route) ? route : 'dashboard',
    parts,
    query: new URLSearchParams(queryString),
  };
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
