import { setView, toast } from '../ui.js';
import { buildSimulation } from '../services/questions.js';
import { recordAttempt } from '../services/performance.js';
import { state } from '../state.js';
import { escapeHtml } from '../utils.js';
import { add, get, getByIndex } from '../db.js';

export async function renderSimulator(contestId){
  const [contest, subjects] = await Promise.all([
    get('contests', contestId),
    getByIndex('subjects','byContest',contestId,{limit:100})
  ]);
  const total=subjects.reduce((sum,s)=>sum+(Number(s.questions)||0),0);
  setView(`<section class="view"><header class="page-header"><h1>Simulado</h1><p class="muted">A distribuição é lida do edital ativo, não fica presa à Guarda Salvador.</p></header><article class="card"><p><strong>Distribuição:</strong> ${subjects.filter(s=>s.questions).map(s=>`${escapeHtml(s.name)}: ${s.questions}`).join(' · ') || 'não configurada'}</p><p><strong>Total:</strong> ${total || '—'} questões. <strong>Tempo:</strong> ${contest.examDurationMinutes ? `${Math.floor(contest.examDurationMinutes/60)}h${contest.examDurationMinutes%60?String(contest.examDurationMinutes%60).padStart(2,'0'):''}` : 'não configurado'}.</p><button id="start-sim" class="button button--primary" ${total?'':'disabled'}>Gerar simulado aleatório</button></article><div id="sim-area" style="margin-top:14px"></div></section>`);
  const start=document.querySelector('#start-sim'); if(!start)return;
  start.addEventListener('click',async()=>{
    try{const qs=await buildSimulation(contestId);state.currentSimulation={contestId,contest,subjects,questions:qs,index:0,answers:[],startedAt:new Date().toISOString(),deadline:Date.now()+(contest.examDurationMinutes||270)*60000};renderSimQuestion();}catch(err){toast(err.message,'danger');}
  });
}

function renderSimQuestion(){
  const sim=state.currentSimulation;const host=document.querySelector('#sim-area');if(!sim||!host)return;
  if(sim.index>=sim.questions.length){finishSimulation();return;}
  const q=sim.questions[sim.index];
  host.innerHTML=`<article class="card question-card"><div class="row row--between"><span class="badge">${sim.index+1}/${sim.questions.length}</span><span id="sim-timer" class="badge"></span></div><div class="question-stem" style="margin-top:14px">${escapeHtml(q.stem)}</div><div class="options">${q.options.map((o,i)=>`<button class="option-button" data-sim-option="${i}"><strong>${String.fromCharCode(65+i)}.</strong> ${escapeHtml(o)}</button>`).join('')}</div></article>`;
  const update=()=>{const left=Math.max(0,sim.deadline-Date.now());const min=Math.floor(left/60000),sec=Math.floor((left%60000)/1000);const el=document.querySelector('#sim-timer');if(el)el.textContent=`${Math.floor(min/60)}:${String(min%60).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;if(left<=0)finishSimulation();};update();sim.timer&&clearInterval(sim.timer);sim.timer=setInterval(update,1000);
  host.querySelectorAll('[data-sim-option]').forEach(btn=>btn.addEventListener('click',async()=>{const selected=Number(btn.dataset.simOption);sim.answers.push({questionPk:q.pk,subjectId:q.subjectId,selected,correct:selected===q.answerIndex});await recordAttempt(q,selected);sim.index+=1;renderSimQuestion();}));
}

async function finishSimulation(){
  const sim=state.currentSimulation;if(!sim)return;clearInterval(sim.timer);
  const bySubject={};for(const a of sim.answers){bySubject[a.subjectId]??={correct:0,total:0};bySubject[a.subjectId].total+=1;bySubject[a.subjectId].correct+=a.correct?1:0;}
  let m1=0,m2=0; for(const subject of sim.subjects){const correct=bySubject[subject.id]?.correct||0;if(Number(subject.module)===1)m1+=correct;else if(Number(subject.module)===2)m2+=correct;}
  const total=m1+m2;const max=sim.questions.length;const scorePct=max?Math.round(total/max*100):0;const rules=sim.contest.rules||{};
  const m1Max=sim.subjects.filter(s=>Number(s.module)===1).reduce((n,s)=>n+(Number(s.questions)||0),0);const m2Max=sim.subjects.filter(s=>Number(s.module)===2).reduce((n,s)=>n+(Number(s.questions)||0),0);
  const passM1=!rules.minimumModule1||m1>=rules.minimumModule1;const passM2=!rules.minimumModule2||m2>=rules.minimumModule2;const passTotal=!rules.minimumTotal||total>=rules.minimumTotal;
  await add('simulations',{contestId:sim.contestId,startedAt:sim.startedAt,finishedAt:new Date().toISOString(),m1,m2,total,max,scorePct,questionPks:sim.questions.map(q=>q.pk)});
  const host=document.querySelector('#sim-area');host.innerHTML=`<article class="card"><h2>Resultado</h2><div class="grid grid--3"><div><div class="metric">${m1}/${m1Max}</div><div class="metric-label">Módulo I ${passM1?'✓':'✗'}</div></div><div><div class="metric">${m2}/${m2Max}</div><div class="metric-label">Módulo II ${passM2?'✓':'✗'}</div></div><div><div class="metric">${total}/${max}</div><div class="metric-label">Total ${passTotal?'✓':'✗'}</div></div></div><p style="margin-top:14px"><strong>${passM1&&passM2&&passTotal?'Você atingiria os mínimos objetivos configurados neste simulado.':'Você não atingiria todos os mínimos objetivos configurados neste simulado.'}</strong></p><p class="muted">Isso não é previsão de aprovação; use o resultado para direcionar o estudo.</p></article>`;state.currentSimulation=null;
}
