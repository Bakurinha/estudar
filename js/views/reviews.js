import { setView } from '../ui.js';
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
