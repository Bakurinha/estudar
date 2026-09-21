import { setView, toast } from '../ui.js';
import { extractPdfText, analyzeNoticeText, analyzeWithOptionalEndpoint } from '../services/pdfImport.js';
import { get, put, bulkPut } from '../db.js';
import { parseJsonSafe, uid } from '../utils.js';

function normalizeImportedQuestion(contestId, question, index) {
  const id = question.id || `imported-q-${index + 1}`;
  const subjectId = question.subjectId;
  const topicIds = Array.isArray(question.topicIds) ? question.topicIds : [];
  return {
    id,
    pk: `${contestId}|${id}`,
    contestId,
    subjectId,
    subjectPk: `${contestId}|${subjectId}`,
    topicIds,
    topicPks: topicIds.map(t => `${contestId}|${t}`),
    difficulty: question.difficulty || 'medium',
    sourceType: question.sourceType || 'imported-authorial',
    sourceLabel: question.sourceLabel || 'Questão importada - confira a origem antes de usar',
    stem: question.stem || '',
    options: question.options || [],
    answerIndex: Number(question.answerIndex) || 0,
    explanation: question.explanation || '',
    tags: question.tags || [],
  };
}

export async function renderImport(){
  const endpoint=(await get('settings','aiAnalysisEndpoint'))?.value||'';
  setView(`<section class="view"><header class="page-header"><h1>Novo edital</h1><p class="muted">Fluxo híbrido: extração local → análise preliminar → revisão humana → IA opcional → importação.</p></header>
  <div class="notice notice--warning">A importação automática nunca é tratada como verdade absoluta. Confira módulos, questões, pesos, mínimos, TAF e conteúdo antes de confirmar.</div>
  <article class="card" style="margin-top:14px"><h2 class="card__title">1. Selecionar PDF</h2><input id="notice-file" class="input" type="file" accept="application/pdf"><div id="pdf-progress" class="small muted" style="margin-top:8px"></div><button id="analyze-pdf" class="button button--primary" style="margin-top:10px">Extrair e analisar</button></article>
  <article id="analysis-card" class="card" style="margin-top:14px" hidden><h2 class="card__title">2. Conferir análise</h2><p class="small muted">Edite o JSON se necessário. Campos aceitos: name, organizer, examDate, totalQuestions, rules, taf, modules, subjects, lessons e questions.</p><textarea id="analysis-json" class="textarea" style="min-height:420px;font-family:ui-monospace,monospace"></textarea><div class="row" style="margin-top:10px"><button id="ai-refine" class="button" ${endpoint?'':'disabled'}>Refinar com endpoint de IA</button><button id="import-analysis" class="button button--primary">Confirmar e importar estrutura</button></div>${endpoint?'':`<p class="small muted">Configure um endpoint de IA em Configurações se quiser a etapa automática opcional. Nenhuma chave secreta fica no GitHub.</p>`}</article>
  <article class="card" style="margin-top:14px"><h2 class="card__title">Como funciona</h2><ol><li>PDF.js lê o texto no navegador.</li><li>O analisador local procura datas, banca, total de questões e possíveis disciplinas.</li><li>Você confere o JSON.</li><li>Se houver endpoint opcional, ele pode devolver módulos, tópicos, aulas e questões.</li><li>O concurso é criado separado dos demais no IndexedDB.</li><li>Prioridades são calculadas pela distribuição de questões/pesos informados, e o cronograma passa a usar o novo edital.</li></ol></article></section>`);

  let extractedText=''; let localAnalysis=null;
  document.querySelector('#analyze-pdf').addEventListener('click',async()=>{
    const file=document.querySelector('#notice-file').files[0];if(!file){toast('Escolha um PDF.','warning');return;}
    const progress=document.querySelector('#pdf-progress');progress.textContent='Abrindo PDF.js…';
    try{
      extractedText=await extractPdfText(file,(page,total)=>progress.textContent=`Extraindo página ${page}/${total}…`);
      localAnalysis=analyzeNoticeText(extractedText);
      document.querySelector('#analysis-json').value=JSON.stringify(localAnalysis,null,2);
      document.querySelector('#analysis-card').hidden=false;
      progress.textContent=`Extração concluída: ${Math.round(extractedText.length/1000)} mil caracteres.`;
    }catch(err){progress.textContent='Falha na extração.';toast(`Não foi possível ler o PDF: ${err.message}`,'danger');}
  });

  document.querySelector('#ai-refine').addEventListener('click',async()=>{
    try{
      const current=parseJsonSafe(document.querySelector('#analysis-json').value,localAnalysis);
      const refined=await analyzeWithOptionalEndpoint(endpoint,extractedText,current);
      document.querySelector('#analysis-json').value=JSON.stringify(refined,null,2);
      toast('Análise refinada. Confira antes de importar.');
    }catch(err){toast(`Falha no endpoint: ${err.message}`,'danger');}
  });

  document.querySelector('#import-analysis').addEventListener('click',async()=>{
    const data=parseJsonSafe(document.querySelector('#analysis-json').value);
    if(!data?.id||!data?.name){toast('JSON inválido ou incompleto.','danger');return;}
    const totalQuestions=Number(data.totalQuestions)||0;
    const contest={
      id:data.id,
      name:data.name,
      shortName:data.shortName||data.name,
      organizer:data.organizer||'',
      examDate:data.examDate||'',
      examDurationMinutes:Number(data.examDurationMinutes)||0,
      totalQuestions,
      status:'imported',
      rules:{minimumModule1:0,minimumModule2:0,minimumTotal:0,...(data.rules||{})},
      taf:data.taf||null,
      schedule:Array.isArray(data.schedule)?data.schedule:[],
      studyGuide:{
        strategy:'Prioridades iniciais calculadas a partir da distribuição informada no edital importado. Revise a estrutura antes de confiar no plano.',
        targetScore:80,
        phases:[
          {name:'Base',goal:'Entender os fundamentos e diagnosticar fraquezas'},
          {name:'Cobertura',goal:'Passar por todos os tópicos do edital'},
          {name:'Consolidação',goal:'Aumentar acertos e reduzir erros recorrentes'},
          {name:'Reta final',goal:'Simulados, revisões e pontos fracos'}
        ]
      },
      sourceNote:data.sourceNote||'Importado de PDF e confirmado pelo usuário'
    };
    await put('contests',contest);

    const rawSubjects=data.subjects||[];
    const subjectRows=rawSubjects.map((s,i)=>{
      const id=s.id||`subject-${i+1}`;
      const questions=Number(s.questions)||0;
      const weight=Number(s.weight)||1;
      const relative=totalQuestions?questions/totalQuestions:0;
      return {pk:`${contest.id}|${id}`,contestId:contest.id,id,name:s.name||`Disciplina ${i+1}`,module:Number(s.module)||1,questions,weight,priority:Math.max(0.5,1+relative*2+(weight-1)*0.2)};
    });
    await bulkPut('subjects',subjectRows);

    const topicRows=[];
    for(const s of rawSubjects){
      const sid=s.id;
      for(const [idx,t] of (s.topics||[]).entries()){
        const tid=t.id||`${sid}-topic-${idx+1}`;
        topicRows.push({pk:`${contest.id}|${tid}`,contestId:contest.id,id:tid,subjectId:sid,subjectPk:`${contest.id}|${sid}`,label:t.label||t.name||tid,officialScope:t.officialScope||t.text||''});
      }
    }
    await bulkPut('topics',topicRows);

    // Se a análise externa não trouxe aulas, criamos somente um guia inicial honesto:
    // recorte oficial + instrução de estudo. Não inventamos conteúdo técnico ausente.
    const suppliedLessons=Array.isArray(data.lessons)?data.lessons:[];
    const lessonRows=topicRows.map((topic,index)=>{
      const supplied=suppliedLessons.find(l=>l.topicId===topic.id);
      const id=supplied?.id||`lesson-${topic.id}`;
      return {
        pk:`${contest.id}|${id}`,
        id,
        contestId:contest.id,
        subjectId:topic.subjectId,
        topicId:topic.id,
        topicPk:topic.pk,
        title:supplied?.title||topic.label,
        contentType:supplied?.contentType||'guia-inicial-importado',
        officialScope:topic.officialScope,
        summary:supplied?.summary||'Tópico identificado no edital importado. Use o recorte oficial abaixo como fonte de verdade e complemente o conteúdo somente com material conferido.',
        sections:supplied?.sections||[
          {title:'O que o edital pede',body:topic.officialScope||'Recorte ainda não informado.'},
          {title:'Como começar',items:['Entenda os conceitos do recorte oficial.','Resolva questões estritamente vinculadas a este tópico.','Registre dúvidas e erros.','Revise conforme o cronograma.']}
        ],
        source:{type:'imported-notice'}
      };
    });
    await bulkPut('lessons',lessonRows);

    if(Array.isArray(data.questions)&&data.questions.length){
      const valid=data.questions.filter(q=>q.subjectId&&Array.isArray(q.options)&&q.options.length>=2&&Array.isArray(q.topicIds));
      await bulkPut('questions',valid.map((q,i)=>normalizeImportedQuestion(contest.id,q,i)));
    }

    await put('settings',{key:'activeContestId',value:contest.id});
    toast('Concurso importado. Recarregando…');setTimeout(()=>location.reload(),700);
  });
}
