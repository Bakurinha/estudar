import { setView } from '../ui.js';
import { getByIndex } from '../db.js';
import { escapeHtml, formatDate, formatMinutes } from '../utils.js';

export async function renderHistory(contestId){
  const [sessions, attempts, sims, taf] = await Promise.all([
    getByIndex('studySessions','byContest',contestId,{limit:100,direction:'prev'}),
    getByIndex('questionAttempts','byContest',contestId,{limit:100,direction:'prev'}),
    getByIndex('simulations','byContest',contestId,{limit:30,direction:'prev'}),
    getByIndex('tafSessions','byContest',contestId,{limit:30,direction:'prev'}),
  ]);
  const events=[
    ...sessions.map(s=>({date:s.startedAt,type:'Estudo',detail:`${formatMinutes(s.durationMinutes)} ${s.label||''}`})),
    ...attempts.map(a=>({date:a.answeredAt,type:'Questão',detail:a.correct?'Acerto':'Erro'})),
    ...sims.map(s=>({date:s.finishedAt,type:'Simulado',detail:`${s.total}/70`})),
    ...taf.map(t=>({date:`${t.date}T12:00:00`,type:'TAF',detail:`Corrida ${t.runM||0} m · Barra ${t.bar||0}`})),
  ].sort((a,b)=>new Date(b.date)-new Date(a.date)).slice(0,200);
  setView(`<section class="view"><header class="page-header"><h1>Histórico</h1><p class="muted">Carregamento limitado e progressivo para manter a tela rápida.</p></header>${events.length?`<div class="table-wrap"><table><thead><tr><th>Data</th><th>Tipo</th><th>Registro</th></tr></thead><tbody>${events.map(e=>`<tr><td>${formatDate(e.date,{dateStyle:'short',timeStyle:e.date.includes('T')?'short':undefined})}</td><td>${e.type}</td><td>${escapeHtml(e.detail)}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty-state">Seu histórico aparecerá aqui quando você começar a usar o aplicativo.</div>'}</section>`);
}
