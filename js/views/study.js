import { setView, toast } from '../ui.js';
import { get, getByIndex, put } from '../db.js';
import { escapeHtml } from '../utils.js';
import { navigate } from '../router.js';
import { markTopicStudied } from '../services/performance.js';
import {
  buildLearningPlan,
  loadTopicLearningStates,
  savePageLearningState,
} from '../services/learning.js';

function isCourse(contest) {
  return contest?.kind === 'course';
}

export async function renderStudy(contestId) {
  const [contest, subjects, progress] = await Promise.all([
    get('contests', contestId),
    getByIndex('subjects', 'byContest', contestId, { limit: 100 }),
    getByIndex('topicProgress', 'byContest', contestId, { limit: 1000 }),
  ]);

  const progressMap = new Map(progress.map(item => [item.pk, item]));
  const course = isCourse(contest);

  setView(`
    <section class="view">
      <header class="page-header">
        <h1>Estudar</h1>
        <p class="muted">
          ${course
            ? 'Módulos organizados na ordem do material enviado. Cada tópico possui páginas internas e cada subtópico recebe fundamentos, aplicação, diferenças, armadilhas e revisão ativa.'
            : 'Apostilas organizadas estritamente pela matriz do edital. Cada tópico possui páginas, subtópicos, teoria guiada, aprofundamento, armadilhas e prática.'}
        </p>
      </header>

      <div class="stack">
        ${subjects.map(subject => `
          <article class="card">
            <div class="row row--between">
              <div>
                <h2 class="card__title">${escapeHtml(subject.name)}</h2>
                <span class="small muted">
                  ${course
                    ? `${subject.bankQuestions || 0} questões autorais no banco · Módulo ${subject.module}`
                    : `${subject.questions} questões na prova · Módulo ${subject.module}`}
                </span>
              </div>
              <button class="button" data-open-subject="${subject.id}">
                Abrir tópicos
              </button>
            </div>
            <div id="topics-${subject.id}"></div>
          </article>
        `).join('')}
      </div>
    </section>
  `);

  document.querySelectorAll('[data-open-subject]').forEach(button => {
    button.addEventListener('click', async () => {
      const subject = subjects.find(item => item.id === button.dataset.openSubject);
      const host = document.querySelector(`#topics-${subject.id}`);

      if (host.dataset.loaded) {
        host.innerHTML = '';
        delete host.dataset.loaded;
        button.textContent = 'Abrir tópicos';
        return;
      }

      const topics = await getByIndex('topics', 'bySubject', subject.pk, { limit: 300 });

      host.innerHTML = `
        <div class="topic-list" style="margin-top:12px">
          ${topics.map(topic => {
            const itemProgress = progressMap.get(topic.pk);
            const accuracy = itemProgress?.attempts
              ? Math.round((itemProgress.correct / itemProgress.attempts) * 100)
              : 0;
            const subtopicCount = Array.isArray(topic.subtopics)
              ? topic.subtopics.length
              : 0;

            return `
              <div class="topic-row">
                <div>
                  <div class="topic-row__title">${escapeHtml(topic.label)}</div>
                  <div class="topic-row__meta">${escapeHtml(topic.officialScope)}</div>
                  ${subtopicCount
                    ? `<div class="small muted">${subtopicCount} subtópicos estruturados</div>`
                    : ''}
                  ${itemProgress?.attempts
                    ? `<div class="small">Acertos neste tópico: ${accuracy}%</div>`
                    : ''}
                </div>
                <button class="button button--primary" data-lesson="${topic.id}">
                  Estudar
                </button>
              </div>
            `;
          }).join('')}
        </div>
      `;

      host.dataset.loaded = '1';
      button.textContent = 'Fechar tópicos';

      host.querySelectorAll('[data-lesson]').forEach(lessonButton => {
        lessonButton.addEventListener(
          'click',
          () => navigate('lesson', lessonButton.dataset.lesson),
        );
      });
    });
  });
}

function renderBody(body) {
  if (!body) return '';

  const paragraphs = String(body)
    .split(/\n{1,}/)
    .map(part => part.trim())
    .filter(Boolean);

  return paragraphs
    .map(part => `<p style="line-height:1.78;margin:0 0 12px">${escapeHtml(part)}</p>`)
    .join('');
}

function renderBlock(block) {
  return `
    <section class="lesson-section" style="margin-top:22px">
      <h3>${escapeHtml(block.title || '')}</h3>
      ${renderBody(block.body)}
      ${block.items
        ? `<ul style="line-height:1.75">${block.items.map(item => `
            <li style="margin-bottom:10px">${escapeHtml(item)}</li>
          `).join('')}</ul>`
        : ''}
    </section>
  `;
}

function renderLegacySections(lesson) {
  return (lesson.sections || []).map(section => `
    <section class="lesson-section">
      <h2>${escapeHtml(section.title)}</h2>
      ${renderBody(section.body)}
      ${section.items
        ? `<ul>${section.items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`
        : ''}
    </section>
  `).join('');
}

export async function renderLesson(contestId, topicId, routeQuery = new URLSearchParams()) {
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
  const pageStateId = (page, index) => page?.id || `${topic.id}-page-${String(index + 1).padStart(3, '0')}`;

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
          A conferência usa afirmações já existentes na própria página; em páginas de prática, usa os exercícios e retorna à teoria sem inventar gabarito. O método não adiciona conteúdo novo ao escopo.
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
            const learned = learningStates.get(pageStateId(page, index))?.completedAt;
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
      const pageId = pageStateId(page, activePage);
      const learningState = learningStates.get(pageId) || null;
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
            <div id="learning-reading-material">
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

            </div>

            <section class="card" style="margin-top:24px;border-style:dashed">
              <h3>3. Recuperação ativa — agora pare de olhar o texto</h3>
              <button id="toggle-learning-reading" class="button" style="margin-top:8px">Ocultar leitura enquanto respondo</button>
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
                    <strong>${item.criterionType === 'practice-guidance' ? 'Como conferir sem inventar gabarito' : 'Critério retirado do próprio conteúdo'}</strong>
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
        if (forceRetrieval) {
          const diagnostic = host.querySelector('#learning-diagnostic')?.value?.trim() || '';
          if (diagnostic.length < 10) {
            toast('Escreva primeiro uma tentativa curta de memória antes de abrir o conteúdo.', 'warning');
            return;
          }
        }
        if (contentHost) contentHost.hidden = false;
        contentHost?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });

      const readingMaterial = host.querySelector('#learning-reading-material');
      const readingToggle = host.querySelector('#toggle-learning-reading');
      readingToggle?.addEventListener('click', () => {
        if (!readingMaterial) return;
        readingMaterial.hidden = !readingMaterial.hidden;
        readingToggle.textContent = readingMaterial.hidden
          ? 'Mostrar leitura para conferir'
          : 'Ocultar leitura enquanto respondo';
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
          pageId,
          pageIndex: activePage,
          pageTitle: page.title,
          previousState: learningStates.get(pageId) || null,
          diagnostic,
          recallAnswers: recalls,
          application,
          mastery: Number(masteryValue),
        });

        learningStates.set(pageId, saved);
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
