import { setView } from '../ui.js';
import { getByIndex, get } from '../db.js';
import { todayIso, escapeHtml } from '../utils.js';

export async function renderReviews(contestId){
  const reviews=await getByIndex('reviews','byContest',contestId,{limit:500});
  const due=reviews.filter(r=>r.dueDate<=todayIso()).sort((a,b)=>a.dueDate.localeCompare(b.dueDate));
  const rows=[];
  for(const r of due){const t=await get('topics',r.topicPk);if(t)rows.push({review:r,topic:t});}
  setView(`<section class="view"><header class="page-header"><h1>Revisões</h1><p class="muted">Faça 5 questões do tópico; o próximo intervalo será ajustado pelo resultado.</p></header>${rows.length?`<div class="topic-list">${rows.map(({review,topic})=>`<div class="topic-row"><div><strong>${escapeHtml(topic.label)}</strong><div class="small muted">Vencimento: ${review.dueDate} · intervalo atual ${review.intervalDays} dia(s)</div></div><a class="button button--primary" href="#/questions?topic=${encodeURIComponent(topic.id)}&review=1&count=5">Revisar com questões</a></div>`).join('')}</div>`:'<div class="empty-state">Nenhuma revisão vencida hoje.</div>'}</section>`);
}
