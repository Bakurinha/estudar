/**
 * Ponto de entrada do aplicativo.
 *
 * Responsabilidades: inicializar banco, carregar áreas de estudo, preparar
 * navegação e delegar cada tela ao módulo correspondente.
 */
import { APP_VERSION } from './config.js';
import { ensureSeedData } from './services/seed.js';
import { get, put, getAllSmall, add } from './db.js';
import { currentRoute, updateActiveNav } from './router.js';
import { state } from './state.js';
import { qs, qsa, escapeHtml } from './utils.js';
import { toast, openDialog } from './ui.js';
import { renderDashboard } from './views/dashboard.js';
import { renderStudy, renderLesson } from './views/study.js';
import { renderQuestions } from './views/questions.js';
import { renderReviews } from './views/reviews.js';
import { renderSimulator } from './views/simulator.js';
import { renderPerformance } from './views/performance.js';
import { renderSchedule } from './views/schedule.js';
import { renderTaf } from './views/taf.js';
import { renderHistory } from './views/history.js';
import { renderImport } from './views/import.js';
import { renderSettings, applyTheme } from './views/settings.js';

async function boot() {
  try {
    /*
     * O carregador agora retorna o diagnóstico de cada pacote. Um curso
     * acadêmico opcional com erro não deve mais impedir o restante do app de
     * abrir. Apenas a base principal obrigatória pode interromper o boot.
     */
    const seedResults = await ensureSeedData();

    qs('#app-version').textContent = `v${APP_VERSION}`;
    await loadTheme();
    await loadStudyAreas();
    bindShell();
    registerPwa();
    await renderRoute();

    const failedPackages = seedResults.filter(result => result.status === 'error');
    if (failedPackages.length) {
      const names = failedPackages.map(result => result.id).join(', ');
      toast(
        `Algumas áreas não puderam ser atualizadas (${names}). O restante do aplicativo continua disponível.`,
        'warning',
      );
    }
  } catch (error) {
    console.error('Falha ao inicializar aplicativo:', error);
    qs('#route-view').innerHTML = `
      <div class="notice notice--danger">
        <strong>Não foi possível iniciar o aplicativo.</strong>
        <p>${escapeHtml(error.message)}</p>
        <p>
          Recarregue a página. Se o erro persistir, consulte a seção de solução
          de problemas do README.
        </p>
      </div>
    `;
  }
}

async function loadTheme() {
  const theme = (await get('settings', 'theme'))?.value || 'auto';
  applyTheme(theme);
}

/**
 * Preenche o seletor superior com concursos e cursos acadêmicos. O nome interno
 * activeContestId é mantido por compatibilidade com o banco já existente, mas
 * a interface usa o termo mais correto "Área de estudo".
 */
async function loadStudyAreas() {
  const studyAreas = await getAllSmall('contests', 100);
  const saved = (await get('settings', 'activeContestId'))?.value;

  state.activeContestId = studyAreas.some(area => area.id === saved)
    ? saved
    : studyAreas[0]?.id;

  const selector = qs('#contest-selector');
  selector.innerHTML = studyAreas
    .map(area => `
      <option value="${area.id}">${escapeHtml(area.shortName || area.name)}</option>
    `)
    .join('');
  selector.value = state.activeContestId || '';

  selector.addEventListener('change', async () => {
    state.activeContestId = selector.value;
    await put('settings', {
      key: 'activeContestId',
      value: selector.value,
    });
    await renderRoute();
  });
}

function bindShell() {
  const sidebar = qs('#sidebar');
  const backdrop = qs('#sidebar-backdrop');

  qs('#sidebar-collapse').addEventListener('click', () => {
    qs('#app').classList.toggle('sidebar-collapsed');
  });

  const openMobileMenu = () => {
    sidebar.classList.add('is-open');
    sidebar.setAttribute('aria-hidden', 'false');
    backdrop.hidden = false;
  };

  qs('#mobile-menu').addEventListener('click', openMobileMenu);
  qs('#mobile-menu-bottom')?.addEventListener('click', openMobileMenu);
  qs('#mobile-menu-close')?.addEventListener('click', closeMobileMenu);
  backdrop.addEventListener('click', closeMobileMenu);
  qsa('.nav-list a').forEach(link => link.addEventListener('click', closeMobileMenu));

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') closeMobileMenu();
  });

  window.addEventListener('hashchange', renderRoute);
  qs('#quick-timer').addEventListener('click', openStudyTimer);
  bindConnectionStatus();

  const mobileQuery = window.matchMedia('(max-width: 900px)');
  const syncSidebarAccessibility = event => {
    if (event.matches && !sidebar.classList.contains('is-open')) {
      sidebar.setAttribute('aria-hidden', 'true');
    } else {
      sidebar.setAttribute('aria-hidden', 'false');
    }
  };

  syncSidebarAccessibility(mobileQuery);
  mobileQuery.addEventListener?.('change', syncSidebarAccessibility);
}

function closeMobileMenu() {
  const sidebar = qs('#sidebar');
  sidebar.classList.remove('is-open');
  qs('#sidebar-backdrop').hidden = true;

  if (window.matchMedia('(max-width: 900px)').matches) {
    sidebar.setAttribute('aria-hidden', 'true');
  }
}

/**
 * Mantém um indicador discreto de conectividade. O aplicativo continua usando
 * IndexedDB como fonte do progresso; este estado serve apenas para o usuário
 * saber se links e integrações online estão disponíveis naquele momento.
 */
function bindConnectionStatus() {
  const update = () => {
    const online = navigator.onLine;
    const label = qs('#connection-status');
    const dot = qs('#connection-dot');

    if (label) label.textContent = online ? 'Online' : 'Offline';
    if (dot) dot.classList.toggle('is-offline', !online);
  };

  update();
  window.addEventListener('online', update);
  window.addEventListener('offline', update);
}

async function renderRoute() {
  if (!state.activeContestId) return;

  const { route, parts } = currentRoute();
  updateActiveNav(route);

  switch (route) {
    case 'study': return renderStudy(state.activeContestId);
    case 'lesson': return renderLesson(state.activeContestId, parts[0]);
    case 'questions': return renderQuestions(state.activeContestId);
    case 'reviews': return renderReviews(state.activeContestId);
    case 'simulator': return renderSimulator(state.activeContestId);
    case 'performance': return renderPerformance(state.activeContestId);
    case 'schedule': return renderSchedule(state.activeContestId);
    case 'taf': return renderTaf(state.activeContestId);
    case 'history': return renderHistory(state.activeContestId);
    case 'import': return renderImport();
    case 'settings': return renderSettings();
    default: return renderDashboard(state.activeContestId);
  }
}

function openStudyTimer() {
  const dialog = openDialog(`
    <div class="dialog__content">
      <h2>Iniciar sessão de estudo</h2>
      <div class="grid grid--2">
        <label class="field">
          <span>Duração</span>
          <select id="timer-minutes" class="select">
            <option>25</option>
            <option selected>50</option>
            <option>90</option>
            <option value="0">Livre</option>
          </select>
        </label>
        <label class="field">
          <span>Descrição</span>
          <input id="timer-label" class="input" placeholder="ex.: funções - domínio e imagem">
        </label>
      </div>
      <div id="timer-display" class="metric" style="margin-top:18px">50:00</div>
    </div>
    <div class="dialog__footer">
      <button class="button" data-close-dialog>Cancelar</button>
      <button id="timer-start" class="button button--primary">Iniciar</button>
    </div>
  `);

  let timerId;
  let startedAt;

  qs('#timer-minutes', dialog).addEventListener('change', event => {
    qs('#timer-display', dialog).textContent = `${String(event.target.value || 0).padStart(2, '0')}:00`;
  });

  qs('#timer-start', dialog).addEventListener('click', () => {
    if (timerId) return;

    const minutes = Number(qs('#timer-minutes', dialog).value);
    startedAt = new Date();
    const deadline = minutes ? Date.now() + minutes * 60000 : null;

    qs('#timer-start', dialog).textContent = 'Finalizar sessão';
    qs('#timer-start', dialog).onclick = async () => {
      clearInterval(timerId);
      const durationMinutes = Math.max(
        1,
        Math.round((Date.now() - startedAt.getTime()) / 60000),
      );

      await add('studySessions', {
        contestId: state.activeContestId,
        startedAt: startedAt.toISOString(),
        finishedAt: new Date().toISOString(),
        durationMinutes,
        label: qs('#timer-label', dialog).value,
      });

      dialog.close();
      toast(`Sessão registrada: ${durationMinutes} min.`);
    };

    timerId = setInterval(() => {
      if (!deadline) {
        const elapsed = Date.now() - startedAt.getTime();
        const total = Math.floor(elapsed / 1000);
        qs('#timer-display', dialog).textContent = `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
        return;
      }

      const left = Math.max(0, deadline - Date.now());
      const total = Math.ceil(left / 1000);
      qs('#timer-display', dialog).textContent = `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;

      if (left <= 0) {
        toast('Tempo planejado concluído. Finalize a sessão para registrar.');
      }
    }, 1000);
  }, { once: true });
}

function registerPwa() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
      try {
        /*
         * import.meta.url aponta para /js/app.js. Partimos dele para chegar ao
         * sw.js na raiz real do projeto. Isso continua correto tanto em domínio
         * próprio quanto em GitHub Pages publicado em /nome-do-repositorio/.
         */
        const serviceWorkerUrl = new URL('../sw.js', import.meta.url);
        const registration = await navigator.serviceWorker.register(
          serviceWorkerUrl.href,
          { updateViaCache: 'none' },
        );

        registration.update().catch(() => {});

        registration.addEventListener('updatefound', () => {
          const installingWorker = registration.installing;
          if (!installingWorker) return;

          installingWorker.addEventListener('statechange', () => {
            if (
              installingWorker.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              showUpdateAvailable(registration);
            }
          });
        });
      } catch (error) {
        console.warn('Não foi possível registrar o Service Worker:', error);
        toast(
          'PWA indisponível nesta abertura. O site continua funcionando online.',
          'warning',
        );
      }
    });
  }

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    state.installPrompt = event;
    const button = qs('#install-app');
    button.hidden = false;

    button.onclick = async () => {
      await state.installPrompt.prompt();
      state.installPrompt = null;
      button.hidden = true;
    };
  });
}

/**
 * Exibe uma confirmação simples quando uma versão nova do PWA foi baixada.
 * O usuário decide quando recarregar para não perder uma resposta em andamento.
 */
function showUpdateAvailable(registration) {
  const dialog = openDialog(`
    <div class="dialog__content">
      <h2>Atualização disponível</h2>
      <p>
        Uma nova versão do aplicativo já foi baixada. Você pode atualizar agora
        ou continuar estudando e atualizar depois.
      </p>
    </div>
    <div class="dialog__footer">
      <button class="button" data-close-dialog>Depois</button>
      <button id="apply-app-update" class="button button--primary">Atualizar agora</button>
    </div>
  `);

  qs('#apply-app-update', dialog)?.addEventListener('click', () => {
    registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
  });

  navigator.serviceWorker.addEventListener('controllerchange', () => {
    window.location.reload();
  }, { once: true });
}

boot();
