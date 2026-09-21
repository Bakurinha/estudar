/**
 * Service Worker da plataforma Rumo à Aprovação.
 *
 * Estratégia:
 * - navegação HTML: rede primeiro, cache como fallback;
 * - JS/JSON/pacotes acadêmicos: rede primeiro para evitar código/config antigo;
 * - CSS/ícones: cache rápido com atualização em segundo plano;
 * - falha de um arquivo opcional nunca invalida a instalação inteira.
 */

const CACHE_VERSION = 'v1.5.1';
const STATIC_CACHE = `rumo-aprovacao-static-${CACHE_VERSION}`;
const RUNTIME_CACHE = `rumo-aprovacao-runtime-${CACHE_VERSION}`;

const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './css/base.css',
  './css/layout.css',
  './css/components.css',
  './css/responsive.css',
  './js/app.js',
  './js/config.js',
  './js/db.js',
  './js/router.js',
  './js/state.js',
  './js/ui.js',
  './js/utils.js',
  './assets/icons/icon-192.png',
  './assets/icons/icon-512.png'
];

function scopedUrl(relativePath) {
  return new URL(relativePath, self.registration.scope).href;
}

async function putIfUsable(cacheName, request, response) {
  if (!response?.ok) return;
  const cache = await caches.open(cacheName);
  await cache.put(request, response.clone());
}

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(STATIC_CACHE);

    await Promise.allSettled(
      APP_SHELL.map(async path => {
        const request = new Request(scopedUrl(path), { cache: 'reload' });
        const response = await fetch(request);

        if (!response.ok) {
          throw new Error(`Falha ao pré-cachear ${path}: HTTP ${response.status}`);
        }

        await cache.put(request, response);
      })
    );

    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const validCaches = new Set([STATIC_CACHE, RUNTIME_CACHE]);
    const cacheNames = await caches.keys();

    await Promise.all(
      cacheNames
        .filter(name => name.startsWith('rumo-aprovacao-') && !validCaches.has(name))
        .map(name => caches.delete(name))
    );

    await self.clients.claim();
  })());
});

/**
 * Rede primeiro é importante para JS, JSON e os arquivos .b64 dos cursos.
 * Esses recursos definem estrutura e conteúdo; usar uma cópia velha com um
 * config novo foi justamente uma das causas da quebra na migração v1.5.
 */
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    await putIfUsable(RUNTIME_CACHE, request, response);
    return response;
  } catch {
    return (
      await caches.match(request) ||
      Response.error()
    );
  }
}

async function staleWhileRevalidate(request, event) {
  const cachedResponse = await caches.match(request);
  const networkPromise = fetch(request)
    .then(async response => {
      await putIfUsable(RUNTIME_CACHE, request, response);
      return response;
    })
    .catch(() => null);

  if (cachedResponse) {
    event.waitUntil(networkPromise);
    return cachedResponse;
  }

  return (await networkPromise) || Response.error();
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const response = await fetch(request);
        await putIfUsable(RUNTIME_CACHE, request, response);
        return response;
      } catch {
        return (
          await caches.match(request) ||
          await caches.match(scopedUrl('./index.html')) ||
          Response.error()
        );
      }
    })());
    return;
  }

  const pathname = url.pathname.toLowerCase();
  const mustBeFresh =
    pathname.endsWith('.js') ||
    pathname.endsWith('.json') ||
    pathname.endsWith('.b64') ||
    pathname.endsWith('.webmanifest');

  if (mustBeFresh) {
    event.respondWith(networkFirst(request));
    return;
  }

  event.respondWith(staleWhileRevalidate(request, event));
});

self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
