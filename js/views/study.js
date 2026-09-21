import { setView, toast } from '../ui.js';
import { get, getByIndex, put } from '../db.js';
import { escapeHtml } from '../utils.js';
import { navigate } from '../router.js';
import { markTopicStudied } from '../services/performance.js';

export async function renderStudy(contestId) {
  const subjects = await getByIndex('subjects','byContest',contestId,{limit:100});
  const progress = await getByIndex('topicProgress','byContest',contestId,{limit:1000});
  const progressMap = new Map(progress.map(p=>[p.pk,p]));
  setView(`<section class="view"><header class="page-header"><h1>Estudar</h1><p class="muted">Aulas organizadas estritamente pela matriz do edital. Cada tópico combina teoria guiada, aprofundamento, exemplos e prática.</p></header>
    <div class="stack">${subjects.map(subject=>{
      return `<article class="card"><div class="row row--between"><div><h2 class="card__title">${escapeHtml(subject.name)}</h2><span class="small muted">${subject.questions} questões na prova · Módulo ${subject.module}</span></div><button class="button" data-open-subject="${subject.id}">Abrir tópicos</button></div><div id="topics-${subject.id}"></div></article>`;
    }).join('')}</div></section>`);

  document.querySelectorAll('[data-open-subject]').forEach(btn=>btn.addEventListener('click',async()=>{
    const subject = subjects.find(s=>s.id===btn.dataset.openSubject);
    const host=document.querySelector(`#topics-${subject.id}`);
    if(host.dataset.loaded){host.innerHTML='';delete host.dataset.loaded;btn.textContent='Abrir tópicos';return;}
    const topics=await getByIndex('topics','bySubject',subject.pk,{limit:300});
    host.innerHTML=`<div class="topic-list" style="margin-top:12px">${topics.map(topic=>{
      const p=progressMap.get(topic.pk); const acc=p?.attempts?Math.round(p.correct/p.attempts*100):0;
      return `<div class="topic-row"><div><div class="topic-row__title">${escapeHtml(topic.label)}</div><div class="topic-row__meta">${escapeHtml(topic.officialScope)}</div>${p?.attempts?`<div class="small">Acertos neste tópico: ${acc}%</div>`:''}</div><button class="button button--primary" data-lesson="${topic.id}">Estudar</button></div>`;
    }).join('')}</div>`;
    host.dataset.loaded='1';btn.textContent='Fechar tópicos';
    host.querySelectorAll('[data-lesson]').forEach(b=>b.addEventListener('click',()=>navigate('lesson',b.dataset.lesson)));
  }));
}

export async function renderLesson(contestId, topicId) {
  const topic = await get('topics',`${contestId}|${topicId}`);
  if(!topic){setView('<div class="empty-state">Tópico não encontrado.</div>');return;}
  const lessonRows=await getByIndex('lessons','byTopic',topic.pk,{limit:1});
  const lesson=lessonRows[0];
  if(!lesson){setView('<div class="empty-state">Aula não encontrada para este tópico.</div>');return;}

  const totalMinutes=Number(lesson.estimatedMinutes||0);
  const theoryMinutes=Number(lesson.theoryMinutes||0);
  const practiceMinutes=Number(lesson.practiceMinutes||0);
  const timeBlock=totalMinutes?`<div class="notice" style="margin-top:14px"><strong>Tempo planejado</strong><p style="margin-top:6px">≈ ${totalMinutes} min no total${theoryMinutes?` · ${theoryMinutes} min de teoria`:''}${practiceMinutes?` · ${practiceMinutes} min de prática`:''}. Não é para correr: avance somente quando conseguir explicar o ponto com suas próprias palavras.</p></div>`:'';

  setView(`<article class="reading-view">
    <header class="page-header"><p class="small muted"><a href="#/study">Estudar</a> › ${escapeHtml(topic.label)}</p><h1>${escapeHtml(lesson.title)}</h1>${lesson.summary?`<p class="muted">${escapeHtml(lesson.summary)}</p>`:''}</header>
    <div class="official-scope"><strong>O que o edital pede</strong><div>${escapeHtml(lesson.officialScope)}</div></div>
    ${timeBlock}
    ${lesson.sections.map(section=>`<section class="lesson-section"><h2>${escapeHtml(section.title)}</h2>${section.body?`<p>${escapeHtml(section.body)}</p>`:''}${section.items?`<ul>${section.items.map(i=>`<li>${escapeHtml(i)}</li>`).join('')}</ul>`:''}</section>`).join('')}
    <div class="row"><button id="mark-studied" class="button button--primary">Marcar como estudado</button><a class="button" href="#/questions?topic=${encodeURIComponent(topic.id)}&count=30">Fazer exercícios deste tópico</a></div>
    <section class="lesson-section" style="margin-top:24px"><h2>Anotações</h2><p class="small muted">Tente registrar regras, diferenças e erros que você realmente confundiu. Evite copiar a aula inteira.</p><textarea id="lesson-note" class="textarea" placeholder="Escreva sua anotação deste tópico..."></textarea><button id="save-note" class="button" style="margin-top:8px">Salvar anotação</button></section>
  </article>`);
  const notePk=`${contestId}|note|${topic.id}`; const note=await get('notes',notePk); if(note)document.querySelector('#lesson-note').value=note.text;
  document.querySelector('#mark-studied').addEventListener('click',async()=>{await markTopicStudied(contestId,topic.subjectPk,topic.pk);toast('Tópico marcado como estudado e revisão de 1 dia agendada.');});
  document.querySelector('#save-note').addEventListener('click',async()=>{await put('notes',{pk:notePk,contestId,topicPk:topic.pk,text:document.querySelector('#lesson-note').value,updatedAt:new Date().toISOString()});toast('Anotação salva.');});
}
