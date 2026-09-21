import { setView, toast } from '../ui.js';
import { buildSimulation, selectQuestions } from '../services/questions.js';
import { recordAttempt } from '../services/performance.js';
import { state } from '../state.js';
import { escapeHtml, shuffle } from '../utils.js';
import { add, get, getByIndex } from '../db.js';

function isCourse(contest) {
  return contest?.kind === 'course';
}

function displayOptions(question) {
  return shuffle(
    question.options.map((text, originalIndex) => ({ text, originalIndex })),
  );
}

export async function renderSimulator(contestId) {
  const [contest, subjects] = await Promise.all([
    get('contests', contestId),
    getByIndex('subjects', 'byContest', contestId, { limit: 100 }),
  ]);

  const course = isCourse(contest);
  const officialTotal = subjects.reduce(
    (sum, subject) => sum + (Number(subject.questions) || 0),
    0,
  );
  const academicTotal = subjects.reduce(
    (sum, subject) => sum + (Number(subject.bankQuestions) || 0),
    0,
  );

  if (course) {
    setView(`
      <section class="view">
        <header class="page-header">
          <h1>Treino misto</h1>
          <p class="muted">
            Sessão aleatória com questões de diferentes módulos do curso. Serve
            para medir retenção global; não representa prova oficial da disciplina.
          </p>
        </header>
        <article class="card">
          <p><strong>Banco disponível:</strong> ${academicTotal || 150} questões autorais baseadas nos PDFs.</p>
          <p><strong>Sessão:</strong> 30 questões · <strong>tempo sugerido:</strong> 60 min.</p>
          <button id="start-sim" class="button button--primary">Gerar treino misto</button>
        </article>
        <div id="sim-area" style="margin-top:14px"></div>
      </section>
    `);
  } else {
    setView(`
      <section class="view">
        <header class="page-header">
          <h1>Simulado</h1>
          <p class="muted">
            A distribuição é lida do edital ativo, não fica presa à Guarda Salvador.
          </p>
        </header>
        <article class="card">
          <p>
            <strong>Distribuição:</strong>
            ${subjects
              .filter(subject => subject.questions)
              .map(subject => `${escapeHtml(subject.name)}: ${subject.questions}`)
              .join(' · ') || 'não configurada'}
          </p>
          <p>
            <strong>Total:</strong> ${officialTotal || '—'} questões.
            <strong>Tempo:</strong>
            ${contest.examDurationMinutes
              ? `${Math.floor(contest.examDurationMinutes / 60)}h${contest.examDurationMinutes % 60 ? String(contest.examDurationMinutes % 60).padStart(2, '0') : ''}`
              : 'não configurado'}.
          </p>
          <button id="start-sim" class="button button--primary" ${officialTotal ? '' : 'disabled'}>
            Gerar simulado aleatório
          </button>
        </article>
        <div id="sim-area" style="margin-top:14px"></div>
      </section>
    `);
  }

  const start = document.querySelector('#start-sim');
  if (!start) return;

  start.addEventListener('click', async () => {
    try {
      const questions = course
        ? await selectQuestions({ contestId, count: 30 })
        : await buildSimulation(contestId);

      if (!questions.length) {
        throw new Error('Não há questões suficientes para iniciar esta sessão.');
      }

      state.currentSimulation = {
        contestId,
        contest,
        subjects,
        course,
        questions,
        index: 0,
        answers: [],
        startedAt: new Date().toISOString(),
        deadline: Date.now() + (course ? 60 : (contest.examDurationMinutes || 270)) * 60000,
      };

      renderSimQuestion();
    } catch (error) {
      toast(error.message, 'danger');
    }
  });
}

function renderSimQuestion() {
  const sim = state.currentSimulation;
  const host = document.querySelector('#sim-area');
  if (!sim || !host) return;

  if (sim.index >= sim.questions.length) {
    finishSimulation();
    return;
  }

  const question = sim.questions[sim.index];
  const options = displayOptions(question);

  host.innerHTML = `
    <article class="card question-card">
      <div class="row row--between">
        <span class="badge">${sim.index + 1}/${sim.questions.length}</span>
        <span id="sim-timer" class="badge"></span>
      </div>

      ${question.sourceDocument
        ? `<div class="small muted" style="margin-top:10px">Fonte-base: ${escapeHtml(question.sourceDocument)}${question.sourceModule ? ` · módulo ${escapeHtml(String(question.sourceModule))}` : ''}</div>`
        : ''}

      <div class="question-stem" style="margin-top:14px">
        ${escapeHtml(question.stem)}
      </div>

      <div class="options">
        ${options.map((option, displayIndex) => `
          <button class="option-button" data-sim-option="${option.originalIndex}">
            <strong>${String.fromCharCode(65 + displayIndex)}.</strong>
            ${escapeHtml(option.text)}
          </button>
        `).join('')}
      </div>
    </article>
  `;

  const updateTimer = () => {
    const left = Math.max(0, sim.deadline - Date.now());
    const minutes = Math.floor(left / 60000);
    const seconds = Math.floor((left % 60000) / 1000);
    const element = document.querySelector('#sim-timer');

    if (element) {
      element.textContent = `${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    if (left <= 0) finishSimulation();
  };

  updateTimer();
  if (sim.timer) clearInterval(sim.timer);
  sim.timer = setInterval(updateTimer, 1000);

  host.querySelectorAll('[data-sim-option]').forEach(button => {
    button.addEventListener('click', async () => {
      const selected = Number(button.dataset.simOption);
      const correct = selected === question.answerIndex;

      sim.answers.push({
        questionPk: question.pk,
        subjectId: question.subjectId,
        selected,
        correct,
      });

      await recordAttempt(question, selected);
      sim.index += 1;
      renderSimQuestion();
    });
  });
}

async function finishSimulation() {
  const sim = state.currentSimulation;
  if (!sim) return;

  clearInterval(sim.timer);

  const bySubject = {};
  for (const answer of sim.answers) {
    bySubject[answer.subjectId] ??= { correct: 0, total: 0 };
    bySubject[answer.subjectId].total += 1;
    bySubject[answer.subjectId].correct += answer.correct ? 1 : 0;
  }

  const totalCorrect = sim.answers.filter(answer => answer.correct).length;
  const max = sim.questions.length;
  const scorePct = max ? Math.round((totalCorrect / max) * 100) : 0;

  await add('simulations', {
    contestId: sim.contestId,
    startedAt: sim.startedAt,
    finishedAt: new Date().toISOString(),
    mode: sim.course ? 'academic-mixed' : 'official',
    total: totalCorrect,
    max,
    scorePct,
    questionPks: sim.questions.map(question => question.pk),
  });

  const host = document.querySelector('#sim-area');

  if (sim.course) {
    const subjectRows = sim.subjects
      .map(subject => {
        const result = bySubject[subject.id] || { correct: 0, total: 0 };
        if (!result.total) return '';
        const pct = Math.round((result.correct / result.total) * 100);
        return `
          <tr>
            <td>${escapeHtml(subject.name)}</td>
            <td>${result.correct}/${result.total}</td>
            <td>${pct}%</td>
          </tr>
        `;
      })
      .join('');

    host.innerHTML = `
      <article class="card">
        <h2>Resultado do treino misto</h2>
        <div class="metric">${totalCorrect}/${max}</div>
        <p><strong>${scorePct}% de acertos.</strong></p>
        <p class="muted">
          Use este resultado para localizar módulos que precisam de revisão; ele
          não é uma nota oficial da disciplina.
        </p>
        <div class="table-wrap" style="margin-top:14px">
          <table>
            <thead><tr><th>Módulo</th><th>Acertos</th><th>%</th></tr></thead>
            <tbody>${subjectRows}</tbody>
          </table>
        </div>
      </article>
    `;

    state.currentSimulation = null;
    return;
  }

  let module1 = 0;
  let module2 = 0;

  for (const subject of sim.subjects) {
    const correct = bySubject[subject.id]?.correct || 0;
    if (Number(subject.module) === 1) module1 += correct;
    else if (Number(subject.module) === 2) module2 += correct;
  }

  const rules = sim.contest.rules || {};
  const module1Max = sim.subjects
    .filter(subject => Number(subject.module) === 1)
    .reduce((sum, subject) => sum + (Number(subject.questions) || 0), 0);
  const module2Max = sim.subjects
    .filter(subject => Number(subject.module) === 2)
    .reduce((sum, subject) => sum + (Number(subject.questions) || 0), 0);

  const passModule1 = !rules.minimumModule1 || module1 >= rules.minimumModule1;
  const passModule2 = !rules.minimumModule2 || module2 >= rules.minimumModule2;
  const passTotal = !rules.minimumTotal || totalCorrect >= rules.minimumTotal;

  host.innerHTML = `
    <article class="card">
      <h2>Resultado</h2>
      <div class="grid grid--3">
        <div><div class="metric">${module1}/${module1Max}</div><div class="metric-label">Módulo I ${passModule1 ? '✓' : '✗'}</div></div>
        <div><div class="metric">${module2}/${module2Max}</div><div class="metric-label">Módulo II ${passModule2 ? '✓' : '✗'}</div></div>
        <div><div class="metric">${totalCorrect}/${max}</div><div class="metric-label">Total ${passTotal ? '✓' : '✗'}</div></div>
      </div>
      <p style="margin-top:14px">
        <strong>
          ${passModule1 && passModule2 && passTotal
            ? 'Você atingiria os mínimos objetivos configurados neste simulado.'
            : 'Você não atingiria todos os mínimos objetivos configurados neste simulado.'}
        </strong>
      </p>
      <p class="muted">Isso não é previsão de aprovação; use o resultado para direcionar o estudo.</p>
    </article>
  `;

  state.currentSimulation = null;
}
