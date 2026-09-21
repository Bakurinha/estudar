from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace(path, old, new):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'Pattern not found in {path}: {old[:80]}')
    p.write_text(text.replace(old, new), encoding='utf-8')


# app.js: repassa query string para a aula sem alterar as demais rotas.
replace(
    'js/app.js',
    "  const { route, parts } = currentRoute();",
    "  const { route, parts, query } = currentRoute();",
)
replace(
    'js/app.js',
    "    case 'lesson': return renderLesson(state.activeContestId, parts[0]);",
    "    case 'lesson': return renderLesson(state.activeContestId, parts[0], query);",
)

# learning.js: guarde o título da página para a fila de revisão.
replace(
    'js/services/learning.js',
    "  pageId,\n  pageIndex,\n  previousState = null,",
    "  pageId,\n  pageIndex,\n  pageTitle = '',\n  previousState = null,",
)
replace(
    'js/services/learning.js',
    "    pageId,\n    pageIndex,\n    type: 'page-learning',",
    "    pageId,\n    pageIndex,\n    pageTitle: normalizeWhitespace(pageTitle),\n    type: 'page-learning',",
)

# performance.js: a revisão passa a respeitar progressão 1 -> 7 -> 30.
perf = ROOT / 'js/services/performance.js'
text = perf.read_text(encoding='utf-8')
pattern = re.compile(r"export async function completeReview\(review, scorePct\) \{.*?\n\}", re.S)
new_func = '''export async function completeReview(review, scorePct) {
  const current = Number(review.intervalDays || 1);
  let next = 1;

  if (scorePct >= 80) {
    if (current < 7) next = 7;
    else next = 30;
  } else if (scorePct >= 60) {
    // Acerto intermediário mantém uma recuperação relativamente próxima.
    next = current < 7 ? 7 : Math.min(current, 30);
  } else {
    // Dificuldade real: volta ao ciclo curto em vez de empurrar o erro adiante.
    next = 1;
  }

  const date = new Date();
  date.setDate(date.getDate() + next);
  review.intervalDays = next;
  review.dueDate = date.toISOString().slice(0, 10);
  review.completedCount = (review.completedCount || 0) + 1;
  review.lastScore = scorePct;
  await put('reviews', review);
}'''
text, count = pattern.subn(new_func, text, count=1)
if count != 1:
    raise SystemExit('Could not replace completeReview')
perf.write_text(text, encoding='utf-8')

# reviews.js: mantém questões e acrescenta revisões de página baseadas em recuperação.
(ROOT / 'js/views/reviews.js').write_text(r'''import { setView } from '../ui.js';
import { getByIndex, get } from '../db.js';
import { todayIso, escapeHtml } from '../utils.js';

export async function renderReviews(contestId) {
  const today = todayIso();
  const [reviews, learningRows] = await Promise.all([
    getByIndex('reviews', 'byContest', contestId, { limit: 500 }),
    getByIndex('notes', 'byContest', contestId, { limit: 6000 }),
  ]);

  const dueTopics = reviews
    .filter(review => review.dueDate <= today)
    .sort((a, b) => a.dueDate.localeCompare(b.dueDate));

  const duePages = learningRows
    .filter(row => row.type === 'page-learning' && row.nextReviewDate && row.nextReviewDate <= today)
    .sort((a, b) => a.nextReviewDate.localeCompare(b.nextReviewDate))
    .slice(0, 40);

  const topicRows = [];
  for (const review of dueTopics) {
    const topic = await get('topics', review.topicPk);
    if (topic) topicRows.push({ review, topic });
  }

  const pageRows = [];
  for (const state of duePages) {
    const topic = await get('topics', state.topicPk);
    if (topic) pageRows.push({ state, topic });
  }

  setView(`
    <section class="view">
      <header class="page-header">
        <h1>Revisões</h1>
        <p class="muted">
          A revisão combina recuperação ativa de páginas e questões do tópico.
          O ciclo-base é 1 → 7 → 30 dias e encurta quando o desempenho cai.
        </p>
      </header>

      <article class="card" style="margin-bottom:16px">
        <h2 class="card__title">Recuperação ativa de páginas</h2>
        <p class="small muted" style="margin-top:6px">
          Entre sem reler. Tente reconstruir a página primeiro; só depois abra o conteúdo e confira.
        </p>
        ${pageRows.length ? `
          <div class="topic-list" style="margin-top:12px">
            ${pageRows.map(({ state, topic }) => `
              <div class="topic-row">
                <div>
                  <strong>${escapeHtml(topic.label)}</strong>
                  <div class="small muted">
                    ${escapeHtml(state.pageTitle || `Página ${Number(state.pageIndex || 0) + 1}`)}
                    · revisão desde ${escapeHtml(state.nextReviewDate)}
                    · intervalo ${Number(state.intervalDays || 1)} dia(s)
                  </div>
                </div>
                <a class="button button--primary"
                   href="#/lesson/${encodeURIComponent(topic.id)}?page=${Number(state.pageIndex || 0)}&review=1">
                  Recuperar sem olhar
                </a>
              </div>
            `).join('')}
          </div>
        ` : '<div class="empty-state" style="margin-top:12px">Nenhuma página vencida hoje.</div>'}
      </article>

      <article class="card">
        <h2 class="card__title">Revisão com questões</h2>
        <p class="small muted" style="margin-top:6px">
          Depois da recuperação livre, use questões para testar reconhecimento, aplicação e discriminação de alternativas.
        </p>
        ${topicRows.length ? `
          <div class="topic-list" style="margin-top:12px">
            ${topicRows.map(({ review, topic }) => `
              <div class="topic-row">
                <div>
                  <strong>${escapeHtml(topic.label)}</strong>
                  <div class="small muted">
                    Vencimento: ${escapeHtml(review.dueDate)} · intervalo atual ${Number(review.intervalDays || 1)} dia(s)
                  </div>
                </div>
                <a class="button button--primary"
                   href="#/questions?topic=${encodeURIComponent(topic.id)}&review=1&count=5">
                  Revisar com questões
                </a>
              </div>
            `).join('')}
          </div>
        ` : '<div class="empty-state" style="margin-top:12px">Nenhuma revisão por questões vencida hoje.</div>'}
      </article>
    </section>
  `);
}
''', encoding='utf-8')

# study.js: substitui apenas a experiência da aula; listagem de matérias/tópicos é preservada.
study = ROOT / 'js/views/study.js'
text = study.read_text(encoding='utf-8')
import_old = "import { markTopicStudied } from '../services/performance.js';"
import_new = """import { markTopicStudied } from '../services/performance.js';
import {
  buildLearningPlan,
  loadTopicLearningStates,
  savePageLearningState,
} from '../services/learning.js';"""
if import_old not in text:
    raise SystemExit('study import anchor missing')
text = text.replace(import_old, import_new, 1)

start = text.index('export async function renderLesson(')
prefix = text[:start]
new_render = r'''export async function renderLesson(contestId, topicId, routeQuery = new URLSearchParams()) {
  const [contest, topic] = await Promise.all([
    get('contests', contestId),
    get('topics', `${contestId}|${topicId}`),
  ]);

  if (!topic) {
    setView('<div class="empty-state">Tópico não encontrado.</div>');
    return;
  }

  const lessonRows = await getByIndex('lessons', 'byTopic', topic.pk, { limit: 1 });
  const lesson = lessonRows[0];

  if (!lesson) {
    setView('<div class="empty-state">Aula não encontrada para este tópico.</div>');
    return;
  }

  const course = isCourse(contest);
  const totalMinutes = Number(lesson.estimatedMinutes || 0);
  const theoryMinutes = Number(lesson.theoryMinutes || 0);
  const practiceMinutes = Number(lesson.practiceMinutes || 0);
  const pages = Array.isArray(lesson.studyPages) ? lesson.studyPages : [];
  const totalChars = Number(lesson.contentCharacters || 0);
  const subtopics = Array.isArray(topic.subtopics) ? topic.subtopics : [];
  const practiceCount = course ? 10 : 30;
  const learningStates = await loadTopicLearningStates(topic.pk);
  const reviewMode = routeQuery?.get?.('review') === '1';
  const requestedPage = Number(routeQuery?.get?.('page') || 0);

  const completedPages = () => [...learningStates.values()].filter(item => item.completedAt).length;

  const timeBlock = totalMinutes
    ? `
      <div class="notice" style="margin-top:14px">
        <strong>Tempo planejado para estudar o tópico</strong>
        <p style="margin-top:6px">
          ≈ ${totalMinutes} min no total
          ${theoryMinutes ? ` · ${theoryMinutes} min de teoria` : ''}
          ${practiceMinutes ? ` · ${practiceMinutes} min de prática` : ''}.
          É uma referência de carga, não um cronômetro. Divida o capítulo em sessões quando necessário.
        </p>
      </div>
    `
    : '';

  const sourceBlock = course
    ? `
      <div class="notice" style="margin-top:14px">
        <strong>Módulo de origem</strong>
        <p style="margin-top:6px">
          ${escapeHtml(lesson.sourceModuleName || lesson.sourceModule || 'Material de estudo')}.
          ${lesson.originalExerciseCount
            ? ` Foram localizados ${lesson.originalExerciseCount} exercício(s)/atividade(s) do material-base neste tópico.`
            : ''}
        </p>
      </div>
    `
    : '';

  const methodologyBlock = pages.length
    ? `
      <div class="notice" style="margin-top:14px">
        <strong>Modo Aprender — não é só leitura</strong>
        <p style="margin-top:6px">
          Cada página segue: <strong>tentativa inicial → leitura → recuperação sem olhar → conferência → aplicação → revisão espaçada</strong>.
          A conferência usa afirmações já existentes na própria página; o método não adiciona conteúdo novo ao escopo.
        </p>
        <div class="small muted" id="learning-progress" style="margin-top:8px">
          Páginas concluídas pelo método: ${completedPages()}/${pages.length}.
        </div>
      </div>
    `
    : '';

  const subtopicIndex = subtopics.length
    ? `
      <aside class="card" style="margin-top:18px">
        <strong>Subtópicos estruturados</strong>
        <p class="small muted" style="margin-top:4px">
          A numeração preserva a ordem do módulo e desdobra seus conceitos para facilitar a revisão.
        </p>
        <ol style="line-height:1.7;margin-top:10px">
          ${subtopics.map(item => `
            <li style="margin-bottom:8px">
              <strong>${escapeHtml(item.number)}</strong> — ${escapeHtml(item.label)}
              <div class="small muted">${escapeHtml(item.description || '')}</div>
            </li>
          `).join('')}
        </ol>
      </aside>
    `
    : '';

  const pageIndex = pages.length
    ? `
      <aside class="card" style="margin-top:18px">
        <div class="row row--between">
          <div>
            <strong>Índice da apostila</strong>
            <div class="small muted">
              ${pages.length} páginas internas
              ${totalChars ? ` · cerca de ${Math.round(totalChars / 1000)} mil caracteres de conteúdo` : ''}
            </div>
          </div>
        </div>
        <div id="lesson-page-index" style="display:grid;gap:8px;margin-top:12px">
          ${pages.map((page, index) => {
            const learned = learningStates.get(page.id)?.completedAt;
            return `
              <button
                class="button"
                style="text-align:left;justify-content:flex-start"
                data-page-index="${index}"
              >
                <span data-page-label="${index}">${learned ? '✓ ' : ''}${index + 1}. ${escapeHtml(page.title)}</span>
              </button>
            `;
          }).join('')}
        </div>
      </aside>
    `
    : '';

  setView(`
    <article class="reading-view">
      <header class="page-header">
        <p class="small muted"><a href="#/study">Estudar</a> › ${escapeHtml(topic.label)}</p>
        <h1>${escapeHtml(lesson.title)}</h1>
        ${lesson.summary ? `<p class="muted">${escapeHtml(lesson.summary)}</p>` : ''}
      </header>

      <div class="official-scope">
        <strong>${course ? 'Escopo do módulo no material-fonte' : 'O que o edital pede — recorte literal'}</strong>
        <div>${escapeHtml(lesson.officialScope)}</div>
      </div>

      ${sourceBlock}
      ${timeBlock}
      ${methodologyBlock}
      ${subtopicIndex}
      ${pageIndex}
      ${pages.length
        ? '<div id="lesson-page-host" style="margin-top:22px"></div>'
        : renderLegacySections(lesson)}

      <div class="row" style="margin-top:28px;flex-wrap:wrap">
        <button id="mark-studied" class="button button--primary">
          Marcar tópico como estudado
        </button>
        <a
          class="button"
          href="#/questions?topic=${encodeURIComponent(topic.id)}&count=${practiceCount}"
        >
          Fazer ${practiceCount} exercícios deste tópico
        </a>
      </div>

      <section class="lesson-section" style="margin-top:24px">
        <h2>Anotações</h2>
        <p class="small muted">
          Registre regras, diferenças e erros que você realmente confundiu. Evite copiar a apostila inteira.
        </p>
        <textarea
          id="lesson-note"
          class="textarea"
          placeholder="Escreva sua anotação deste tópico..."
        ></textarea>
        <button id="save-note" class="button" style="margin-top:8px">
          Salvar anotação
        </button>
      </section>
    </article>
  `);

  if (pages.length) {
    let activePage = Math.max(0, Math.min(Number.isFinite(requestedPage) ? requestedPage : 0, pages.length - 1));
    const host = document.querySelector('#lesson-page-host');
    const indexButtons = [...document.querySelectorAll('[data-page-index]')];

    const updateProgressUi = () => {
      const progress = document.querySelector('#learning-progress');
      if (progress) progress.textContent = `Páginas concluídas pelo método: ${completedPages()}/${pages.length}.`;

      pages.forEach((page, index) => {
        const label = document.querySelector(`[data-page-label="${index}"]`);
        if (!label) return;
        label.textContent = `${learningStates.get(page.id)?.completedAt ? '✓ ' : ''}${index + 1}. ${page.title}`;
      });
    };

    const drawPage = index => {
      activePage = Math.max(0, Math.min(index, pages.length - 1));
      const page = pages[activePage];
      const learningState = learningStates.get(page.id) || null;
      const today = new Date().toISOString().slice(0, 10);
      const due = Boolean(learningState?.nextReviewDate && learningState.nextReviewDate <= today);
      const forceRetrieval = reviewMode || due || !learningState?.completedAt;
      const plan = buildLearningPlan({
        contestId,
        subjectId: topic.subjectId,
        topicLabel: topic.label,
        page,
        lesson,
        previousPage: activePage > 0 ? pages[activePage - 1] : null,
      });

      indexButtons.forEach((button, buttonIndex) => {
        button.style.fontWeight = buttonIndex === activePage ? '700' : '400';
        button.setAttribute('aria-current', buttonIndex === activePage ? 'page' : 'false');
      });

      host.innerHTML = `
        <article class="card" style="padding:clamp(16px,3vw,30px)">
          <div class="row row--between" style="gap:12px;align-items:flex-start">
            <div>
              <div class="small muted">
                Página ${activePage + 1} de ${pages.length} · ${escapeHtml(page.kind || 'teoria')}
              </div>
              <h2 style="margin-top:6px">${escapeHtml(page.title)}</h2>
              ${learningState?.completedAt ? `
                <div class="small" style="margin-top:6px">
                  ✓ estudada pelo método · próxima recuperação: ${escapeHtml(learningState.nextReviewDate || '—')}
                </div>
              ` : ''}
            </div>
          </div>

          <section class="notice" style="margin-top:16px">
            <strong>1. Tentativa inicial — antes de reler</strong>
            <p style="margin-top:6px">${escapeHtml(plan.diagnosticPrompt)}</p>
            <textarea id="learning-diagnostic" class="textarea" style="margin-top:8px"
              placeholder="Escreva de memória. Não precisa estar bonito; precisa revelar o que você realmente lembra.">${forceRetrieval ? '' : escapeHtml(learningState?.diagnostic || '')}</textarea>
            <button id="open-learning-content" class="button button--primary" style="margin-top:8px">
              ${forceRetrieval ? 'Registrar tentativa e abrir conteúdo' : 'Abrir conteúdo'}
            </button>
            ${forceRetrieval ? '<div class="small muted" style="margin-top:6px">O texto fica oculto inicialmente para evitar a ilusão de familiaridade da releitura.</div>' : ''}
          </section>

          <div id="learning-content" ${forceRetrieval ? 'hidden' : ''}>
            <div class="official-scope" style="margin-top:14px">
              <strong>${course ? 'Origem desta página no material' : 'Por que esta página está no edital'}</strong>
              <div>${escapeHtml(page.editalBasis || page.sourceScope || lesson.officialScope)}</div>
            </div>

            ${page.scopeBoundary
              ? `
                <div class="notice" style="margin-top:12px">
                  <strong>${course ? 'Regra de fidelidade ao material' : 'Limite do conteúdo'}</strong>
                  <p style="margin-top:6px">${escapeHtml(page.scopeBoundary)}</p>
                </div>
              `
              : ''}

            <div style="margin-top:18px">
              <div class="small muted">2. Leitura segmentada — procure responder mentalmente “o que?”, “como?”, “quando?” e “qual a diferença?” enquanto lê.</div>
              ${(page.blocks || []).map(renderBlock).join('')}
            </div>

            <section class="card" style="margin-top:24px;border-style:dashed">
              <h3>3. Recuperação ativa — agora pare de olhar o texto</h3>
              <p class="small muted" style="margin-top:6px">
                Responda primeiro. O botão de conferência revela uma afirmação que já existe nesta página.
              </p>
              ${plan.recallPrompts.map((item, promptIndex) => `
                <div style="margin-top:18px">
                  <strong>Pergunta ${promptIndex + 1}</strong>
                  <p style="margin-top:6px">${escapeHtml(item.prompt)}</p>
                  <textarea class="textarea" data-learning-recall="${promptIndex}"
                    placeholder="Responda sem consultar o texto."></textarea>
                  <button class="button" data-reveal-criterion="${promptIndex}" style="margin-top:6px">
                    Conferir com a página
                  </button>
                  <div class="notice" data-criterion="${promptIndex}" hidden style="margin-top:8px">
                    <strong>Critério retirado do próprio conteúdo</strong>
                    <p style="margin-top:6px">${escapeHtml(item.criterion)}</p>
                    ${item.sourceBlock ? `<div class="small muted">Bloco: ${escapeHtml(item.sourceBlock)}</div>` : ''}
                  </div>
                </div>
              `).join('')}
            </section>

            <section class="card" style="margin-top:18px">
              <h3>4. Autoexplicação, aplicação e intercalação</h3>
              <p style="margin-top:10px"><strong>Autoexplicação:</strong> ${escapeHtml(plan.selfExplanationPrompt)}</p>
              <p style="margin-top:10px"><strong>Aplicação:</strong> ${escapeHtml(plan.applicationPrompt)}</p>
              <textarea id="learning-application" class="textarea" style="margin-top:8px"
                placeholder="Registre sua aplicação, exemplo, cálculo, trecho ou justificativa."></textarea>
              <p style="margin-top:14px"><strong>Intercalação:</strong> ${escapeHtml(plan.interleavePrompt)}</p>
            </section>

            <section class="notice" style="margin-top:18px">
              <strong>5. Julgamento de domínio</strong>
              <p class="small muted" style="margin-top:6px">
                Avalie pelo que conseguiu recuperar e aplicar, não pela sensação de que o texto “parece familiar”.
              </p>
              <label class="field" style="margin-top:10px">
                <span>Como você ficou nesta página?</span>
                <select id="learning-mastery" class="select">
                  <option value="">Selecione</option>
                  <option value="0">0 — não consigo reconstruir ainda</option>
                  <option value="1">1 — lembro partes, mas dependo do texto</option>
                  <option value="2">2 — consigo explicar sem olhar</option>
                  <option value="3">3 — consigo explicar e aplicar/diferenciar</option>
                </select>
              </label>
              <button id="complete-learning-page" class="button button--primary" style="margin-top:10px">
                ${learningState?.completedAt ? 'Registrar esta revisão' : 'Concluir aprendizagem desta página'}
              </button>
              <div class="small muted" style="margin-top:7px">
                A primeira conclusão agenda 1 dia. Revisões bem recuperadas avançam para 7 e depois 30 dias.
              </div>
            </section>
          </div>

          <div class="row row--between" style="margin-top:24px;gap:10px;flex-wrap:wrap">
            <button class="button" id="lesson-prev-page" ${activePage === 0 ? 'disabled' : ''}>← Página anterior</button>
            <span class="small muted">${activePage + 1}/${pages.length}</span>
            <button class="button button--primary" id="lesson-next-page" ${activePage === pages.length - 1 ? 'disabled' : ''}>Próxima página →</button>
          </div>
        </article>
      `;

      const contentHost = host.querySelector('#learning-content');
      host.querySelector('#open-learning-content')?.addEventListener('click', () => {
        if (contentHost) contentHost.hidden = false;
        contentHost?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });

      host.querySelectorAll('[data-reveal-criterion]').forEach(button => {
        button.addEventListener('click', () => {
          const criterion = host.querySelector(`[data-criterion="${button.dataset.revealCriterion}"]`);
          if (criterion) criterion.hidden = false;
        });
      });

      host.querySelector('#complete-learning-page')?.addEventListener('click', async () => {
        const diagnostic = host.querySelector('#learning-diagnostic')?.value?.trim() || '';
        const recalls = [...host.querySelectorAll('[data-learning-recall]')].map(input => input.value.trim());
        const application = host.querySelector('#learning-application')?.value?.trim() || '';
        const masteryValue = host.querySelector('#learning-mastery')?.value;

        if (diagnostic.length < 10) {
          toast('Faça primeiro uma tentativa de recuperação de memória antes de concluir.', 'warning');
          return;
        }
        if (recalls.some(answer => answer.length < 10)) {
          toast('Responda às perguntas de recuperação antes de concluir a página.', 'warning');
          return;
        }
        if (masteryValue === '') {
          toast('Selecione seu nível de domínio com base no que conseguiu recuperar.', 'warning');
          return;
        }

        const saved = await savePageLearningState({
          contestId,
          topicId: topic.id,
          topicPk: topic.pk,
          pageId: page.id,
          pageIndex: activePage,
          pageTitle: page.title,
          previousState: learningStates.get(page.id) || null,
          diagnostic,
          recallAnswers: recalls,
          application,
          mastery: Number(masteryValue),
        });

        learningStates.set(page.id, saved);
        updateProgressUi();
        toast(`Página registrada. Próxima recuperação: ${saved.nextReviewDate}.`);
      });

      const previous = host.querySelector('#lesson-prev-page');
      const next = host.querySelector('#lesson-next-page');

      previous?.addEventListener('click', () => {
        drawPage(activePage - 1);
        host.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });

      next?.addEventListener('click', () => {
        drawPage(activePage + 1);
        host.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    };

    indexButtons.forEach(button => {
      button.addEventListener('click', () => {
        drawPage(Number(button.dataset.pageIndex));
        host.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });

    drawPage(activePage);
  }

  const notePk = `${contestId}|note|${topic.id}`;
  const note = await get('notes', notePk);
  if (note) document.querySelector('#lesson-note').value = note.text;

  document.querySelector('#mark-studied').addEventListener('click', async () => {
    await markTopicStudied(contestId, topic.subjectPk, topic.pk);
    const learned = completedPages();
    if (pages.length && learned < pages.length) {
      toast(`Tópico marcado, mas o modo Aprender foi concluído em ${learned}/${pages.length} páginas. Revisão de 1 dia agendada.`, 'warning');
    } else {
      toast('Tópico marcado como estudado e revisão de 1 dia agendada.');
    }
  });

  document.querySelector('#save-note').addEventListener('click', async () => {
    await put('notes', {
      pk: notePk,
      contestId,
      topicPk: topic.pk,
      text: document.querySelector('#lesson-note').value,
      updatedAt: new Date().toISOString(),
    });
    toast('Anotação salva.');
  });
}
'''
study.write_text(prefix + new_render, encoding='utf-8')

# Versão do app/PWA. Não mudamos versões dos pacotes: conteúdo disciplinar ficou intacto.
replace('js/config.js', "export const APP_VERSION = '1.8.0';", "export const APP_VERSION = '1.9.0';")
replace('sw.js', "const CACHE_VERSION = 'v1.8.0';", "const CACHE_VERSION = 'v1.9.0';")
replace(
    'sw.js',
    "  './js/utils.js',\n  './assets/icons/icon-192.png',",
    "  './js/utils.js',\n  './js/services/learning.js',\n  './assets/icons/icon-192.png',",
)

# README/CHANGELOG: registro curto da metodologia sem alterar o escopo disciplinar.
changelog = ROOT / 'CHANGELOG.md'
if changelog.exists():
    old = changelog.read_text(encoding='utf-8')
    entry = '''# Changelog\n\n## 1.9.0 — Aprendizagem guiada baseada em evidências\n\n- Modo Aprender por página: tentativa inicial, leitura segmentada, recuperação ativa, conferência, autoexplicação, aplicação e intercalação.\n- Pistas e critérios de conferência são derivados do conteúdo já existente; nenhum novo assunto disciplinar é criado pelo motor pedagógico.\n- Progresso de aprendizagem por página salvo localmente no IndexedDB.\n- Revisões de página em ciclo 1 → 7 → 30 dias e revisão de tópicos ajustada ao desempenho.\n- Área Revisões agora separa recuperação livre de páginas e prática com questões.\n- Aplicado a GCM, Paradigmas/Python e Matemática e Lógica sem mudar seus escopos.\n\n'''
    if old.startswith('# Changelog'):
        old = old[len('# Changelog'):].lstrip('\n')
        changelog.write_text(entry + old, encoding='utf-8')
    elif '## 1.9.0' not in old:
        changelog.write_text(entry + old, encoding='utf-8')

print('learning-science v1.9.0 migration applied')
