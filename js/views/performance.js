import { setView, progressBar } from '../ui.js';
import { getPreparation, getSubjectStats } from '../services/performance.js';
import { escapeHtml } from '../utils.js';

export async function renderPerformance(contestId){
  const [prep,rows]=await Promise.all([getPreparation(contestId),getSubjectStats(contestId)]);
  setView(`<section class="view"><header class="page-header"><h1>Desempenho</h1><p class="muted">Acompanhamento de cobertura, questões e domínio estimado.</p></header>
  <article class="card"><div class="row row--between"><div><strong>${prep.label}</strong><div class="small muted">Índice geral de preparação</div></div><div class="metric">${prep.score}%</div></div>${progressBar(prep.score,'Preparação geral')}<div class="grid grid--3" style="margin-top:14px"><div><strong>${prep.coverage}%</strong><div class="small muted">Cobertura</div></div><div><strong>${prep.accuracy}%</strong><div class="small muted">Acerto</div></div><div><strong>${prep.consistency}%</strong><div class="small muted">Constância recente</div></div></div></article>
  <div class="table-wrap" style="margin-top:14px"><table><thead><tr><th>Matéria</th><th>Conteúdo</th><th>Questões</th><th>Domínio</th><th>Respondidas</th></tr></thead><tbody>${rows.map(r=>`<tr><td>${escapeHtml(r.subject.name)}</td><td>${r.contentPct}%</td><td>${r.accuracyPct}%</td><td><strong>${r.domainPct}%</strong></td><td>${r.answered}</td></tr>`).join('')}</tbody></table></div>
  <div class="notice" style="margin-top:14px">O nível exibido mede preparação dentro do aplicativo; não representa chance estatística de aprovação nem nota de corte.</div></section>`);
}
