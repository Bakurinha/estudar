import { setView, toast } from '../ui.js';
import { get, put, getByIndex } from '../db.js';
import { defaultAvailability, generatePlan } from '../services/schedule.js';
import { googleCalendarUrl } from '../services/calendar.js';
import { escapeHtml, todayIso } from '../utils.js';

const dayNames=['Domingo','Segunda','Terça','Quarta','Quinta','Sexta','Sábado'];

export async function renderSchedule(contestId){
  const pref=(await get('settings','studyAvailability'))?.value||defaultAvailability();
  const tafPref=(await get('settings','tafAvailability'))?.value||{days:['2','4','6'],start:'07:00',durationMinutes:45};
  const upcoming=await getByIndex('schedule','byContest',contestId,{limit:200});
  const future=upcoming.filter(i=>i.date>=todayIso()).sort((a,b)=>a.date.localeCompare(b.date)).slice(0,30);
  setView(`<section class="view"><header class="page-header"><h1>Agenda e cronograma</h1><p class="muted">Defina seus horários; o aplicativo distribui os tópicos pendentes por prioridade.</p></header>
    <article class="card"><h2 class="card__title">Horário de estudo</h2><div class="table-wrap"><table><thead><tr><th>Dia</th><th>Estudar</th><th>Início</th><th>Minutos</th></tr></thead><tbody>${dayNames.map((name,i)=>{const s=pref[String(i)]||{};return `<tr><td>${name}</td><td><input type="checkbox" data-day-enabled="${i}" ${s.enabled?'checked':''}></td><td><input class="input" type="time" data-day-start="${i}" value="${s.start||'19:00'}"></td><td><input class="input" type="number" min="30" step="10" data-day-minutes="${i}" value="${s.durationMinutes||120}"></td></tr>`}).join('')}</tbody></table></div><div class="row" style="margin-top:12px"><button id="save-availability" class="button">Salvar horários</button><button id="generate-plan" class="button button--primary">Gerar/Reorganizar 14 dias</button></div></article>
    <article class="card" style="margin-top:14px"><h2 class="card__title">Horário do TAF</h2><div class="grid grid--3"><label class="field"><span>Dias (0=dom, 6=sáb)</span><input id="taf-days" class="input" value="${tafPref.days.join(',')}"></label><label class="field"><span>Início</span><input id="taf-start" class="input" type="time" value="${tafPref.start}"></label><label class="field"><span>Duração (min)</span><input id="taf-duration" class="input" type="number" value="${tafPref.durationMinutes}"></label></div><button id="save-taf-time" class="button" style="margin-top:10px">Salvar horário do TAF</button></article>
    <article class="card" style="margin-top:14px"><h2 class="card__title">Próximos blocos</h2>${future.length?`<div class="stack">${future.map(item=>`<div class="row row--between"><div><strong>${escapeHtml(item.title)}</strong><div class="small muted">${item.date} ${item.startTime||''}</div></div><a class="button" target="_blank" rel="noopener" href="${googleCalendarUrl({title:item.title,start:`${item.date}T${item.startTime||'19:00'}:00-03:00`,end:new Date(new Date(`${item.date}T${item.startTime||'19:00'}:00-03:00`).getTime()+(item.durationMinutes||50)*60000).toISOString(),details:'Bloco de estudo gerado pelo Rumo à Aprovação.'})}">Google Agenda</a></div>`).join('')}</div>`:'<div class="empty-state">Nenhum bloco gerado ainda.</div>'}</article>
  </section>`);

  document.querySelector('#save-availability').addEventListener('click',async()=>{const value={};for(let i=0;i<7;i+=1)value[String(i)]={enabled:document.querySelector(`[data-day-enabled="${i}"]`).checked,start:document.querySelector(`[data-day-start="${i}"]`).value,durationMinutes:Number(document.querySelector(`[data-day-minutes="${i}"]`).value)||120};await put('settings',{key:'studyAvailability',value});toast('Horários de estudo salvos.');});
  document.querySelector('#generate-plan').addEventListener('click',async()=>{await document.querySelector('#save-availability').click();const created=await generatePlan(contestId,14);toast(`${created.length} bloco(s) distribuído(s).`);setTimeout(()=>renderSchedule(contestId),400);});
  document.querySelector('#save-taf-time').addEventListener('click',async()=>{const value={days:document.querySelector('#taf-days').value.split(',').map(x=>x.trim()).filter(Boolean),start:document.querySelector('#taf-start').value,durationMinutes:Number(document.querySelector('#taf-duration').value)||45};await put('settings',{key:'tafAvailability',value});toast('Horário do TAF salvo.');});
}
