import { setView, toast } from '../ui.js';
import { getByIndex } from '../db.js';
import { escapeHtml } from '../utils.js';
import { selectQuestions } from '../services/questions.js';
import { recordAttempt, completeReview } from '../services/performance.js';
import { get } from '../db.js';
import { state } from '../state.js';

function queryParams() {
  const hash = location.hash;
  const idx = hash.indexOf('?');
  return new URLSearchParams(idx >= 0 ? hash.slice(idx + 1) : '');
}

export async function renderQuestions(contestId) {
  const subjects = await getByIndex('subjects','byContest',contestId,{limit:100});
  const params = queryParams();
  const preTopic = params.get('topic') || '';
  const isReview = params.get('review') === '1';
  const requestedCount = params.get('count') || '10';

  setView(`<section class="view"><header class="page-header"><h1>Exercícios</h1><p class="muted">Questões autorais, filtradas primeiro pelo assunto e só depois embaralhadas.</p></header>
    <article class="card"><div class="grid grid--4">
      <label class="field"><span>Matéria</span><select id="q-subject" class="select"><option value="">Todas</option>${subjects.map(s=>`<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('')}</select></label>
      <label class="field"><span>Tópico</span><select id="q-topic" class="select"><option value="">Todos</option></select></label>
      <label class="field"><span>Quantidade</span><select id="q-count" class="select"><option ${requestedCount==='5'?'selected':''}>5</option><option ${requestedCount==='10'?'selected':''}>10</option><option ${requestedCount==='20'?'selected':''}>20</option><option ${requestedCount==='30'?'selected':''}>30</option></select></label>
      <label class="field"><span>Dificuldade</span><select id="q-difficulty" class="select"><option value="">Todas</option><option value="easy">Fácil</option><option value="medium">Média</option><option value="hard">Difícil</option></select></label>
    </div><div class="row" style="margin-top:12px"><button id="start-questions" class="button button--primary">Começar</button><button id="wrong-questions" class="button">Somente erradas</button></div></article>
    <div id="question-area" style="margin-top:14px"></div></section>`);

  const subjectSelect=document.querySelector('#q-subject');
  const topicSelect=document.querySelector('#q-topic');
  async function loadTopics(){
    const sid=subjectSelect.value;
    topicSelect.innerHTML='<option value="">Todos</option>';
    if(!sid)return;
    const subject=subjects.find(s=>s.id===sid);
    const topics=await getByIndex('topics','bySubject',subject.pk,{limit:300});
    topicSelect.insertAdjacentHTML('beforeend',topics.map(t=>`<option value="${t.id}">${escapeHtml(t.label)}</option>`).join(''));
    if(preTopic && topics.some(t=>t.id===preTopic))topicSelect.value=preTopic;
  }
  subjectSelect.addEventListener('change',loadTopics);
  if(preTopic){
    for(const s of subjects){const topics=await getByIndex('topics','bySubject',s.pk,{limit:300});if(topics.some(t=>t.id===preTopic)){subjectSelect.value=s.id;await loadTopics();break;}}
  }

  async function start(onlyWrong=false){
    const selected=await selectQuestions({contestId,subjectId:subjectSelect.value||null,topicId:topicSelect.value||null,difficulty:document.querySelector('#q-difficulty').value||null,count:Number(document.querySelector('#q-count').value),onlyWrong});
    if(!selected.length){toast('Nenhuma questão encontrada com esses filtros.','warning');return;}
    state.currentQuestionSession={questions:selected,index:0,correct:0,answered:0,reviewTopicId:isReview?topicSelect.value:null,contestId};
    renderCurrentQuestion();
  }
  document.querySelector('#start-questions').addEventListener('click',()=>start(false));
  document.querySelector('#wrong-questions').addEventListener('click',()=>start(true));
}

async function renderCurrentQuestion(){
  const session=state.currentQuestionSession;
  const host=document.querySelector('#question-area');
  if(!session||!host)return;
  if(session.index>=session.questions.length){
    const pct=session.answered?Math.round(session.correct/session.answered*100):0;
    host.innerHTML=`<article class="card question-card"><h2>Sessão concluída</h2><div class="metric">${session.correct}/${session.answered}</div><p>${pct}% de acertos.</p><button class="button button--primary" onclick="location.hash='#/questions'">Nova sessão</button></article>`;
    if(session.reviewTopicId){
      const review=await get('reviews',`${session.contestId}|${session.reviewTopicId}`);
      if(review){await completeReview(review,pct);toast(`Revisão concluída. Próximo intervalo: ${review.intervalDays} dia(s).`);}
    }
    return;
  }
  const q=session.questions[session.index];
  host.innerHTML=`<article class="card question-card"><div class="row row--between"><span class="badge">${session.index+1}/${session.questions.length}</span><span class="badge badge--primary">Questão autoral</span></div><div class="question-stem" style="margin-top:14px">${escapeHtml(q.stem)}</div><div class="options">${q.options.map((o,i)=>`<button class="option-button" data-option="${i}"><strong>${String.fromCharCode(65+i)}.</strong> ${escapeHtml(o)}</button>`).join('')}</div><div id="q-feedback"></div><div class="question-footer"><span class="small muted">${escapeHtml(q.topicIds.join(', '))}</span><button id="next-question" class="button button--primary" disabled>Próxima</button></div></article>`;
  let answered=false;
  host.querySelectorAll('[data-option]').forEach(btn=>btn.addEventListener('click',async()=>{
    if(answered)return;answered=true;
    const selected=Number(btn.dataset.option);const correct=await recordAttempt(q,selected);session.answered+=1;if(correct)session.correct+=1;
    host.querySelectorAll('[data-option]').forEach((b,i)=>{b.disabled=true;if(i===q.answerIndex)b.classList.add('is-correct');else if(i===selected)b.classList.add('is-wrong');});
    document.querySelector('#q-feedback').innerHTML=`<div class="notice ${correct?'notice--success':'notice--danger'}" style="margin-top:14px"><strong>${correct?'Correto.':'Incorreto.'}</strong><p style="margin-top:6px">${escapeHtml(q.explanation)}</p></div>`;
    document.querySelector('#next-question').disabled=false;
  }));
  document.querySelector('#next-question').addEventListener('click',()=>{session.index+=1;renderCurrentQuestion();});
}
