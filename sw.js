/**
 * Service Worker da plataforma Rumo à Aprovação.
 *
 * Objetivos:
 * 1. permitir que o shell principal continue abrindo quando a rede oscilar;
 * 2. funcionar corretamente quando o projeto estiver em um subdiretório do
 *    GitHub Pages, por exemplo /meu-usuario/rumo-aprovacao/;
 * 3. nunca impedir a instalação inteira porque apenas um arquivo opcional
 *    falhou durante o pré-cache.
 */

const CACHE_VERSION = 'v1.1.0';
const STATIC_CACHE = `rumo-aprovacao-static-${CACHE_VERSION}`;
const RUNTIME_CACHE = `rumo-aprovacao-runtime-${CACHE_VERSION}`;

/*
 * Caminhos relativos à pasta onde o sw.js está hospedado.
 * O GitHub Pages pode publicar o projeto em um subdiretório; por isso não
 * usamos caminhos iniciados por "/".
 */
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

/**
 * Converte um caminho relativo em URL absoluta dentro do escopo atual do
 * service worker. Isto evita erros quando o repositório está em /repo/.
 */
function scopedUrl(relativePath) {
  return new URL(relativePath, self.registration.scope).href;
}

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(STATIC_CACHE);

    /*
     * cache.addAll() cancela toda a instalação se um único recurso falhar.
     * Aqui adicionamos item a item. Os arquivos essenciais continuam sendo
     * guardados mesmo se algum asset opcional estiver temporariamente ausente.
     */
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

self.addEventListener('fetch', event => {
  const request = event.request;

  if (request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);

  /*
   * Não interceptamos recursos de outros domínios. Isso mantém integrações
   * online e bibliotecas remotas funcionando normalmente.
   */
  if (url.origin !== self.location.origin) {
    return;
  }

  /*
   * Para navegação HTML, preferimos a rede para receber atualizações novas.
   * Se a rede falhar, voltamos para o index.html em cache. Como o roteamento
   * usa hash, o index.html consegue reconstruir qualquer tela interna.
   */
  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const networkResponse = await fetch(request);
        const cache = await caches.open(RUNTIME_CACHE);
        await cache.put(request, networkResponse.clone());
        return networkResponse;
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

  /*
   * Para CSS, JS, JSON, ícones e demais arquivos locais usamos
   * stale-while-revalidate: responde rápido do cache e atualiza em paralelo.
   */
  event.respondWith((async () => {
    const cachedResponse = await caches.match(request);

    const networkPromise = fetch(request)
      .then(async response => {
        if (response.ok) {
          const cache = await caches.open(RUNTIME_CACHE);
          await cache.put(request, response.clone());
        }
        return response;
      })
      .catch(() => null);

    if (cachedResponse) {
      event.waitUntil(networkPromise);
      return cachedResponse;
    }

    const networkResponse = await networkPromise;
    return networkResponse || Response.error();
  })());
});

/*
 * Permite que a interface solicite ativação imediata de uma nova versão do
 * service worker após o usuário clicar em "Atualizar".
 */
self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
