import { setView, progressBar } from '../ui.js';
import { get, getByIndex } from '../db.js';
import { getPreparation, getSubjectStats } from '../services/performance.js';
import { daysUntil, escapeHtml, formatMinutes, todayIso } from '../utils.js';

export async function renderDashboard(contestId) {
  const [contest, prep, subjectStats, todayPlan, reviews, sessions] = await Promise.all([
    get('contests', contestId),
    getPreparation(contestId),
    getSubjectStats(contestId),
    getByIndex('schedule', 'byDate', todayIso(), { limit: 50 }),
    getByIndex('reviews', 'byContest', contestId, { limit: 300 }),
    getByIndex('studySessions', 'byContest', contestId, { limit: 100, direction: 'prev' }),
  ]);

  const course = contest?.kind === 'course';
  const due = reviews.filter(review => review.dueDate <= todayIso()).length;
  const todayMinutes = sessions
    .filter(session => session.startedAt?.slice(0, 10) === todayIso())
    .reduce((sum, session) => sum + (session.durationMinutes || 0), 0);
  const days = contest.examDate ? daysUntil(contest.examDate) : null;

  setView(`
    <section class="view">
      <header class="page-header">
        <div class="page-header__row">
          <div>
            <h1>Hoje</h1>
            <p class="muted">${escapeHtml(contest.name)}</p>
          </div>
          <span class="badge badge--primary">
            ${course
              ? `${contest.contentTopicCount || subjectStats.length} módulos/tópicos de estudo`
              : (days === null
                ? 'Data da prova não configurada'
                : (days >= 0 ? `${days} dias até a prova` : 'Prova já realizada'))}
          </span>
        </div>
      </header>

      <div class="grid grid--4">
        <article class="card">
          <div class="metric">${prep.score}%</div>
          <div class="metric-label">Nível atual</div>
          <p class="small">${prep.label}</p>
        </article>
        <article class="card">
          <div class="metric">${prep.accuracy}%</div>
          <div class="metric-label">Acerto geral</div>
          <p class="small">Questões respondidas</p>
        </article>
        <article class="card">
          <div class="metric">${prep.coverage}%</div>
          <div class="metric-label">${course ? 'Conteúdo coberto' : 'Edital coberto'}</div>
          <p class="small">Tópicos estudados</p>
        </article>
        <article class="card">
          <div class="metric">${formatMinutes(todayMinutes)}</div>
          <div class="metric-label">Estudo hoje</div>
          <p class="small">${due} revisão(ões) pendente(s)</p>
        </article>
      </div>

      <article class="card" style="margin-top:14px">
        <div class="row row--between">
          <strong>Evolução geral</strong>
          <span>${prep.score}% → meta 80%</span>
        </div>
        ${progressBar(prep.score, 'Nível de preparação')}
        <p class="small muted" style="margin-top:8px">
          ${course
            ? 'Índice de estudo: combina cobertura, acertos, constância e revisões. Não representa nota acadêmica oficial.'
            : 'Índice de preparação, não probabilidade de aprovação. Combina cobertura, acertos, constância e simulados.'}
        </p>
      </article>

      <nav class="card quick-actions" style="margin-top:14px" aria-label="Ações rápidas">
        <strong class="quick-actions__title">Continuar preparação</strong>
        <div class="quick-actions__grid">
          <a class="button button--primary" href="#/study">Estudar agora</a>
          <a class="button" href="#/questions">Fazer exercícios</a>
          <a class="button" href="#/reviews">Revisões (${due})</a>
          <a class="button" href="#/schedule">Ver agenda</a>
        </div>
      </nav>

      ${contest.studyGuide ? `
        <article class="card" style="margin-top:14px">
          <h2 class="card__title">Guia de preparação</h2>
          <p>${escapeHtml(contest.studyGuide.strategy || '')}</p>
          <div class="row">
            ${(contest.studyGuide.phases || []).map(phase => `
              <span class="badge">${escapeHtml(phase.name)}</span>
            `).join('')}
          </div>
        </article>
      ` : ''}

      <div class="grid grid--2" style="margin-top:14px">
        <article class="card">
          <h2 class="card__title">Plano de hoje</h2>
          ${todayPlan.length
            ? `<div class="stack">${todayPlan.map(item => `
                <div>
                  <strong>${escapeHtml(item.title)}</strong>
                  <div class="small muted">${item.startTime || ''} · ${formatMinutes(item.durationMinutes)}</div>
                </div>
              `).join('')}</div>`
            : '<div class="empty-state">Nenhum bloco planejado para hoje. Gere o cronograma em Agenda.</div>'}
        </article>

        <article class="card">
          <h2 class="card__title">Prioridades por matéria</h2>
          <div class="stack">
            ${subjectStats
              .sort((a, b) => a.domainPct - b.domainPct)
              .slice(0, 5)
              .map(row => `
                <div class="kpi-line">
                  <span>${escapeHtml(row.subject.name)}</span>
                  ${progressBar(row.domainPct, row.subject.name)}
                  <strong>${row.domainPct}%</strong>
                </div>
              `).join('')}
          </div>
        </article>
      </div>
    </section>
  `);
}
