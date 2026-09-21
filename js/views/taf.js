import { setView, toast } from '../ui.js';
import { get, getByIndex, add, put } from '../db.js';

export async function renderTaf(contestId) {
  const contest = await get('contests', contestId);

  if (!contest.taf) {
    const message = contest?.kind === 'course'
      ? 'Esta área acadêmica não possui TAF. O acompanhamento físico continua disponível somente nas áreas de concurso que tenham teste de aptidão física configurado.'
      : 'Este edital não possui parâmetros de TAF cadastrados. Se o PDF importado tiver teste físico, confirme os índices na análise do edital antes de adicioná-los.';

    setView(`
      <section class="view">
        <header class="page-header">
          <h1>TAF</h1>
        </header>
        <div class="notice notice--warning">${message}</div>
      </section>
    `);
    return;
  }

  const pref = (await get('settings', 'tafProfile'))?.value || 'male';
  const rules = contest.taf?.[pref];
  const history = await getByIndex(
    'tafSessions',
    'byContest',
    contestId,
    { limit: 50, direction: 'prev' },
  );

  setView(`
    <section class="view">
      <header class="page-header">
        <h1>TAF</h1>
        <p class="muted">
          Registro de evolução física. O aplicativo não substitui avaliação médica ou profissional.
        </p>
      </header>

      <article class="card">
        <div class="row">
          <label class="field">
            <span>Perfil do edital</span>
            <select id="taf-profile" class="select">
              <option value="male" ${pref === 'male' ? 'selected' : ''}>Masculino</option>
              <option value="female" ${pref === 'female' ? 'selected' : ''}>Feminino</option>
            </select>
          </label>
        </div>

        <div class="grid grid--4" style="margin-top:12px">
          <div><strong>Corrida</strong><div>${rules.run.distanceM} m / ${rules.run.timeMinutes} min</div></div>
          <div><strong>Barra</strong><div>${rules.bar.type === 'dynamic' ? `${rules.bar.minimum} repetições` : `${rules.bar.minimumSeconds} s estática`}</div></div>
          <div><strong>Abdominal</strong><div>${rules.abdominal.minimum} repetições</div></div>
          <div><strong>Flexão</strong><div>${rules.pushup.minimum} repetições</div></div>
        </div>
      </article>

      <article class="card" style="margin-top:14px">
        <h2 class="card__title">Registrar treino/teste</h2>
        <div class="grid grid--4">
          <label class="field"><span>Data</span><input id="taf-date" class="input" type="date" value="${new Date().toISOString().slice(0, 10)}"></label>
          <label class="field"><span>Corrida (m)</span><input id="taf-run" class="input" type="number" min="0"></label>
          <label class="field"><span>Barra (rep/s)</span><input id="taf-bar" class="input" type="number" min="0"></label>
          <label class="field"><span>Abdominal</span><input id="taf-abd" class="input" type="number" min="0"></label>
          <label class="field"><span>Flexão</span><input id="taf-push" class="input" type="number" min="0"></label>
          <label class="field"><span>Observação</span><input id="taf-note" class="input" placeholder="ex.: treino leve"></label>
        </div>
        <button id="save-taf" class="button button--primary" style="margin-top:10px">Salvar</button>
      </article>

      <article class="card" style="margin-top:14px">
        <h2 class="card__title">Histórico recente</h2>
        ${history.length
          ? `<div class="table-wrap"><table><thead><tr><th>Data</th><th>Corrida</th><th>Barra</th><th>Abdominal</th><th>Flexão</th><th>Situação</th></tr></thead><tbody>${history.map(item => {
              const okRun = (item.runM || 0) >= rules.run.distanceM;
              const okBar = rules.bar.type === 'dynamic'
                ? (item.bar || 0) >= rules.bar.minimum
                : (item.bar || 0) >= rules.bar.minimumSeconds;
              const okAbdominal = (item.abdominal || 0) >= rules.abdominal.minimum;
              const okPushup = (item.pushup || 0) >= rules.pushup.minimum;
              const all = okRun && okBar && okAbdominal && okPushup;
              return `<tr><td>${item.date}</td><td>${item.runM || 0} m</td><td>${item.bar || 0}</td><td>${item.abdominal || 0}</td><td>${item.pushup || 0}</td><td><span class="badge ${all ? 'badge--success' : 'badge--warning'}">${all ? 'Mínimos atingidos' : 'Em evolução'}</span></td></tr>`;
            }).join('')}</tbody></table></div>`
          : '<div class="empty-state">Nenhum treino registrado.</div>'}
      </article>
    </section>
  `);

  document.querySelector('#taf-profile').addEventListener('change', async event => {
    await put('settings', { key: 'tafProfile', value: event.target.value });
    renderTaf(contestId);
  });

  document.querySelector('#save-taf').addEventListener('click', async () => {
    await add('tafSessions', {
      contestId,
      date: document.querySelector('#taf-date').value,
      runM: Number(document.querySelector('#taf-run').value) || 0,
      bar: Number(document.querySelector('#taf-bar').value) || 0,
      abdominal: Number(document.querySelector('#taf-abd').value) || 0,
      pushup: Number(document.querySelector('#taf-push').value) || 0,
      note: document.querySelector('#taf-note').value,
    });
    toast('Treino salvo.');
    renderTaf(contestId);
  });
}
