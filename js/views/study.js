import { setView, toast } from '../ui.js';
import { get, getByIndex, put } from '../db.js';
import { escapeHtml } from '../utils.js';
import { navigate } from '../router.js';
import { markTopicStudied } from '../services/performance.js';

export async function renderStudy(contestId) {
  const subjects = await getByIndex('subjects','byContest',contestId,{limit:100});
  const progress = await getByIndex('topicProgress','byContest',contestId,{limit:1000});
  const progressMap = new Map(progress.map(p=>[p.pk,p]));
  setView(`<section class="view"><header class="page-header"><h1>Estudar</h1><p class="muted">Apostilas organizadas estritamente pela matriz do edital. Cada tópico possui páginas, subtópicos, teoria guiada, aprofundamento, armadilhas e prática.</p></header>
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

function renderBlock(block) {
  return `<section class="lesson-section" style="margin-top:22px">
    <h3>${escapeHtml(block.title || '')}</h3>
    ${block.body?`<p style="line-height:1.75">${escapeHtml(block.body)}</p>`:''}
    ${block.items?`<ul style="line-height:1.75">${block.items.map(i=>`<li style="margin-bottom:10px">${escapeHtml(i)}</li>`).join('')}</ul>`:''}
  </section>`;
}

function renderLegacySections(lesson) {
  return (lesson.sections||[]).map(section=>`<section class="lesson-section"><h2>${escapeHtml(section.title)}</h2>${section.body?`<p>${escapeHtml(section.body)}</p>`:''}${section.items?`<ul>${section.items.map(i=>`<li>${escapeHtml(i)}</li>`).join('')}</ul>`:''}</section>`).join('');
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
  const pages=Array.isArray(lesson.studyPages)?lesson.studyPages:[];
  const totalChars=Number(lesson.contentCharacters||0);
  const timeBlock=totalMinutes?`<div class="notice" style="margin-top:14px"><strong>Tempo planejado para dominar o tópico</strong><p style="margin-top:6px">≈ ${totalMinutes} min no total${theoryMinutes?` · ${theoryMinutes} min de teoria`:''}${practiceMinutes?` · ${practiceMinutes} min de prática`:''}. É uma referência de carga, não um cronômetro. Divida o capítulo em sessões se necessário.</p></div>`:'';

  const pageIndex=pages.length?`<aside class="card" style="margin-top:18px"><div class="row row--between"><div><strong>Índice da apostila</strong><div class="small muted">${pages.length} páginas internas${totalChars?` · cerca de ${Math.round(totalChars/1000)} mil caracteres de conteúdo`:''}</div></div></div><div id="lesson-page-index" style="display:grid;gap:8px;margin-top:12px">${pages.map((page,index)=>`<button class="button" style="text-align:left;justify-content:flex-start" data-page-index="${index}">${index+1}. ${escapeHtml(page.title)}</button>`).join('')}</div></aside>`:'';

  setView(`<article class="reading-view">
    <header class="page-header"><p class="small muted"><a href="#/study">Estudar</a> › ${escapeHtml(topic.label)}</p><h1>${escapeHtml(lesson.title)}</h1>${lesson.summary?`<p class="muted">${escapeHtml(lesson.summary)}</p>`:''}</header>
    <div class="official-scope"><strong>O que o edital pede — recorte literal</strong><div>${escapeHtml(lesson.officialScope)}</div></div>
    ${timeBlock}
    ${pageIndex}
    ${pages.length?'<div id="lesson-page-host" style="margin-top:22px"></div>':renderLegacySections(lesson)}
    <div class="row" style="margin-top:28px"><button id="mark-studied" class="button button--primary">Marcar tópico como estudado</button><a class="button" href="#/questions?topic=${encodeURIComponent(topic.id)}&count=30">Fazer 30 exercícios deste tópico</a></div>
    <section class="lesson-section" style="margin-top:24px"><h2>Anotações</h2><p class="small muted">Registre regras, diferenças e erros que você realmente confundiu. Evite copiar a apostila inteira.</p><textarea id="lesson-note" class="textarea" placeholder="Escreva sua anotação deste tópico..."></textarea><button id="save-note" class="button" style="margin-top:8px">Salvar anotação</button></section>
  </article>`);

  if(pages.length){
    let activePage=0;
    const host=document.querySelector('#lesson-page-host');
    const indexButtons=[...document.querySelectorAll('[data-page-index]')];
    const drawPage=(index)=>{
      activePage=Math.max(0,Math.min(index,pages.length-1));
      const page=pages[activePage];
      indexButtons.forEach((button,i)=>{
        button.style.fontWeight=i===activePage?'700':'400';
        button.setAttribute('aria-current',i===activePage?'page':'false');
      });
      host.innerHTML=`<article class="card" style="padding:clamp(16px,3vw,30px)">
        <div class="row row--between" style="gap:12px;align-items:flex-start"><div><div class="small muted">Página ${activePage+1} de ${pages.length} · ${escapeHtml(page.kind||'teoria')}</div><h2 style="margin-top:6px">${escapeHtml(page.title)}</h2></div></div>
        <div class="official-scope" style="margin-top:14px"><strong>Por que esta página está no edital</strong><div>${escapeHtml(page.editalBasis||page.sourceScope||lesson.officialScope)}</div></div>
        ${page.scopeBoundary?`<div class="notice" style="margin-top:12px"><strong>Limite do conteúdo</strong><p style="margin-top:6px">${escapeHtml(page.scopeBoundary)}</p></div>`:''}
        ${(page.blocks||[]).map(renderBlock).join('')}
        <div class="row row--between" style="margin-top:24px;gap:10px;flex-wrap:wrap"><button class="button" id="lesson-prev-page" ${activePage===0?'disabled':''}>← Página anterior</button><span class="small muted">${activePage+1}/${pages.length}</span><button class="button button--primary" id="lesson-next-page" ${activePage===pages.length-1?'disabled':''}>Próxima página →</button></div>
      </article>`;
      const prev=host.querySelector('#lesson-prev-page');
      const next=host.querySelector('#lesson-next-page');
      if(prev)prev.addEventListener('click',()=>{drawPage(activePage-1);host.scrollIntoView({behavior:'smooth',block:'start'});});
      if(next)next.addEventListener('click',()=>{drawPage(activePage+1);host.scrollIntoView({behavior:'smooth',block:'start'});});
    };
    indexButtons.forEach(button=>button.addEventListener('click',()=>{drawPage(Number(button.dataset.pageIndex));host.scrollIntoView({behavior:'smooth',block:'start'});}));
    drawPage(0);
  }

  const notePk=`${contestId}|note|${topic.id}`;
  const note=await get('notes',notePk);
  if(note)document.querySelector('#lesson-note').value=note.text;
  document.querySelector('#mark-studied').addEventListener('click',async()=>{await markTopicStudied(contestId,topic.subjectPk,topic.pk);toast('Tópico marcado como estudado e revisão de 1 dia agendada.');});
  document.querySelector('#save-note').addEventListener('click',async()=>{await put('notes',{pk:notePk,contestId,topicPk:topic.pk,text:document.querySelector('#lesson-note').value,updatedAt:new Date().toISOString()});toast('Anotação salva.');});
}
