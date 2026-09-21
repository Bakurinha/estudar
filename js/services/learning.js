/**
 * Motor pedagógico do modo de estudo guiado.
 *
 * Princípios aplicados:
 * - tentativa de recuperação antes da releitura;
 * - leitura segmentada;
 * - recuperação ativa com critério de conferência retirado da própria página;
 * - autoexplicação;
 * - aplicação adequada ao domínio;
 * - intercalação com a página anterior;
 * - revisões espaçadas 1 -> 7 -> 30 dias.
 *
 * O motor NÃO cria conteúdo disciplinar novo. As pistas, critérios e termos são
 * extraídos do texto que já existe na página/aula. Isso é particularmente
 * importante na GCM, em que o edital continua sendo o teto do conteúdo.
 */
import { getByIndex, put } from '../db.js';

const STOPWORDS = new Set(`
a ao aos aonde aquela aquelas aquele aqueles aquilo as até com como contra da das de dela delas dele deles
 desde do dos e ela elas ele eles em entre era essa essas esse esses esta estas este estes eu foi foram há isso isto já
 lhe lhes mais mas me mesmo mesma mesmos mesmas meu minha meus minhas muito na nas nem no nos nós o os ou para pela
 pelas pelo pelos por porque qual quando que quem se sem ser seu seus sua suas também te tem tendo ter teu teus tua
 tuas um uma umas uns você vocês sobre sob onde ainda assim cada outra outras outro outros pode podem deve devem
 página tópico subtópico conteúdo edital material estudo questão questões forma dentro recorte oficial
`.trim().split(/\s+/));

const GENERIC_BODY_PATTERNS = [
  /esta página desenvolve somente/i,
  /o edital exige exatamente/i,
  /todo o capítulo abaixo/i,
  /o limite é o recorte literal/i,
  /reconstrua o conteúdo desta página/i,
  /controle de escopo/i,
  /explique com suas palavras por que esta página/i,
  /para estudar de verdade, não basta decorar/i,
  /ao terminar .* você deve conseguir/i,
  /o objetivo deste capítulo é dominar/i,
  /resolva primeiro questões apenas deste tópico/i,
  /regra de fidelidade/i,
];

const CONTROL_TITLE_PATTERNS = [
  /recorte oficial/i,
  /como usar/i,
  /verificação conceitual/i,
  /controle de escopo/i,
  /regra de fidelidade/i,
  /limite do conteúdo/i,
  /fechamento/i,
];

function normalizeWhitespace(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function normalizeForCompare(value) {
  return normalizeWhitespace(value)
    .toLocaleLowerCase('pt-BR')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

function isGenericBody(text) {
  return GENERIC_BODY_PATTERNS.some(pattern => pattern.test(text));
}

function isControlTitle(title) {
  return CONTROL_TITLE_PATTERNS.some(pattern => pattern.test(title || ''));
}

function splitSentences(text) {
  const clean = normalizeWhitespace(text);
  if (!clean) return [];

  return clean
    .split(/(?<=[.!?])\s+|\s*;\s*/)
    .map(sentence => sentence.trim())
    .filter(sentence => sentence.length >= 45 && sentence.length <= 520);
}

function substantiveBlocks(page) {
  const blocks = Array.isArray(page?.blocks) ? page.blocks : [];
  const preferred = blocks.filter(block => {
    const body = normalizeWhitespace(block?.body);
    return body.length >= 120 && !isControlTitle(block?.title) && !isGenericBody(body);
  });

  if (preferred.length) return preferred;

  return blocks.filter(block => normalizeWhitespace(block?.body).length >= 80);
}

function scoreSentence(sentence, blockIndex) {
  let score = 0;
  const length = sentence.length;

  if (length >= 80 && length <= 280) score += 8;
  else if (length <= 400) score += 5;
  else score += 2;

  if (/\d|%|=|\+|−|-|\/|\b(?:lei|art|artigo|função|classe|objeto|proposição|regra|princípio|requisito|efeito|causa|consequência)\b/i.test(sentence)) {
    score += 3;
  }

  score += Math.max(0, 4 - blockIndex);
  if (isGenericBody(sentence)) score -= 20;
  return score;
}

/**
 * Extrai afirmações que já existem na página. Nenhuma resposta de conferência
 * é inventada: o critério exibido ao aluno é uma frase do próprio material.
 */
export function extractGroundedClaims(page, lesson = {}) {
  const candidates = [];

  substantiveBlocks(page).forEach((block, blockIndex) => {
    splitSentences(block.body).forEach(sentence => {
      if (isGenericBody(sentence)) return;
      candidates.push({
        sentence,
        blockTitle: normalizeWhitespace(block.title),
        score: scoreSentence(sentence, blockIndex),
      });
    });
  });

  const fallbackTexts = [
    page?.editalBasis,
    page?.sourceScope,
    lesson?.officialScope,
  ];

  if (candidates.length < 3) {
    fallbackTexts.forEach(text => {
      splitSentences(text).forEach(sentence => {
        candidates.push({ sentence, blockTitle: 'Escopo da página', score: 1 });
      });
    });
  }

  const seen = new Set();
  return candidates
    .sort((a, b) => b.score - a.score)
    .filter(item => {
      const key = normalizeForCompare(item.sentence);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 3);
}

function tokenize(text) {
  return normalizeWhitespace(text)
    .toLocaleLowerCase('pt-BR')
    .match(/[\p{L}\p{N}][\p{L}\p{N}./_-]*/gu) || [];
}

export function extractKeyTerms(claims, pageTitle = '') {
  const counts = new Map();
  const order = new Map();
  let position = 0;
  const source = `${pageTitle} ${claims.map(item => item.sentence).join(' ')}`;

  tokenize(source).forEach(token => {
    const normalized = token.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}./_-]+$/gu, '');
    if (normalized.length < 4 || STOPWORDS.has(normalized)) return;
    if (!order.has(normalized)) order.set(normalized, position++);
    counts.set(normalized, (counts.get(normalized) || 0) + 1);
  });

  return [...counts.entries()]
    .sort((a, b) => {
      const frequency = b[1] - a[1];
      if (frequency) return frequency;
      return (order.get(a[0]) || 0) - (order.get(b[0]) || 0);
    })
    .slice(0, 7)
    .map(([term]) => term);
}

function inferDomain({ contestId, subjectId = '', topicLabel = '' }) {
  const haystack = `${contestId} ${subjectId} ${topicLabel}`.toLocaleLowerCase('pt-BR');

  if (haystack.includes('paradigmas-python') || /python|programa|orientad.*objeto/.test(haystack)) {
    return 'programming';
  }
  if (haystack.includes('matematica-logica') || /racioc|matem|lógic|algebr|geometr|probabil|porcent|juros|plano-cartesiano/.test(haystack)) {
    return 'math';
  }
  if (/portugu|textual|ortograf|sintax|pontua|vocab|lingu/.test(haystack)) {
    return 'language';
  }
  if (/penal|processual|constitucional|civil|legisla|lei|direito/.test(haystack)) {
    return 'law';
  }
  if (/informática|informatica|windows|word|excel|internet|arquivo/.test(haystack)) {
    return 'computing';
  }
  if (/administra|política|politica|gestão|gestao|governança|governanca/.test(haystack)) {
    return 'conceptual';
  }
  if (/atuação|atuacao|incêndio|incendio|socorrista|inteligência|inteligencia|proteção|protecao|segurança|seguranca/.test(haystack)) {
    return 'operational';
  }
  return 'general';
}

function cueForClaim(domain, terms, index) {
  const visible = terms.slice(index, index + 3);
  const cue = visible.length ? visible.join(', ') : 'os conceitos centrais desta página';

  const prompts = {
    programming: `Sem consultar o texto, explique como ${cue} se relacionam nesta página. Se houver comportamento de código, descreva também entrada, processamento e resultado esperado.`,
    math: `Sem consultar o texto, reconstrua a regra, relação ou procedimento envolvendo ${cue}. Se houver cálculo, explique a sequência e o motivo de cada passo, não apenas o resultado.`,
    language: `Sem consultar o texto, explique a relação linguística ou textual envolvendo ${cue} e diga como você a reconheceria em um enunciado diferente.`,
    law: `Sem consultar o texto, reconstrua a regra associada a ${cue}. Separe, quando existirem na página, sujeito, requisito, condição, consequência e diferença relevante.`,
    computing: `Sem consultar o texto, explique a função de ${cue}, em que situação aparece e qual diferença a página estabelece em relação aos conceitos próximos.`,
    conceptual: `Sem consultar o texto, defina e relacione ${cue}. Em seguida, diga qual característica impediria confundir esses conceitos numa questão.`,
    operational: `Sem consultar o texto, explique a finalidade e os critérios associados a ${cue}, mantendo-se no nível conceitual apresentado no material.`,
    general: `Sem consultar o texto, reconstrua a ideia central envolvendo ${cue}. Explique definição, relação e consequência quando existirem.`,
  };

  return prompts[domain] || prompts.general;
}

function applicationPrompt(domain, terms, pageTitle) {
  const cue = terms.slice(0, 4).join(', ') || pageTitle;

  const prompts = {
    programming: `Aplicação: escreva de memória um exemplo mínimo que use corretamente ${cue}. Depois compare cada linha com as regras da página; não acrescente recurso que a página não ensinou.`,
    math: `Aplicação: crie ou resolva um exemplo pequeno usando ${cue}. Mostre os passos e, ao final, explique qual regra desta página justificou cada transformação.`,
    language: `Aplicação: crie uma frase ou um pequeno trecho em que ${cue} possa ser identificado. Depois indique exatamente quais pistas permitem reconhecer o fenômeno estudado.`,
    law: `Aplicação: formule uma situação hipotética curta que contenha somente os elementos tratados nesta página. Depois identifique quais fatos ativam a regra e quais detalhes seriam insuficientes para aplicá-la.`,
    computing: `Aplicação: imagine uma tarefa de usuário envolvendo ${cue}. Descreva o procedimento ou a decisão correta e justifique cada etapa com o conteúdo desta página.`,
    conceptual: `Aplicação: produza um exemplo e um contraexemplo para ${cue}. Explique qual característica da página separa os dois casos.`,
    operational: `Aplicação conceitual: descreva um cenário simples relacionado a ${cue} e identifique o princípio, finalidade ou critério estudado, sem improvisar procedimento operacional fora do material.`,
    general: `Aplicação: crie um exemplo e um contraexemplo envolvendo ${cue}. Justifique ambos usando somente o que esta página apresentou.`,
  };

  return prompts[domain] || prompts.general;
}

function selfExplanationPrompt(domain, terms) {
  const cue = terms.slice(0, 3).join(', ') || 'os conceitos centrais';
  if (domain === 'math' || domain === 'programming') {
    return `Autoexplicação: por que o procedimento envolvendo ${cue} funciona? Explique a lógica de cada etapa como se estivesse ensinando alguém que nunca viu o assunto.`;
  }
  if (domain === 'law') {
    return `Autoexplicação: por que a distinção envolvendo ${cue} muda a resposta de uma questão? Identifique qual palavra, requisito ou consequência é decisiva.`;
  }
  return `Autoexplicação: por que ${cue} são importantes nesta página e como se conectam? Explique sem repetir literalmente o texto.`;
}

export function buildLearningPlan({ contestId, subjectId, topicLabel, page, lesson, previousPage = null }) {
  const claims = extractGroundedClaims(page, lesson);
  const terms = extractKeyTerms(claims, page?.title || topicLabel);
  const domain = inferDomain({ contestId, subjectId, topicLabel });
  const recallPrompts = claims.map((claim, index) => ({
    prompt: cueForClaim(domain, terms, index),
    criterion: claim.sentence,
    sourceBlock: claim.blockTitle,
  }));

  if (!recallPrompts.length) {
    recallPrompts.push({
      prompt: `Sem consultar, explique o que esta página ensina sobre “${page?.title || topicLabel}”.`,
      criterion: normalizeWhitespace(page?.editalBasis || page?.sourceScope || lesson?.officialScope),
      sourceBlock: 'Escopo da página',
    });
  }

  const priorTitle = previousPage?.title ? normalizeWhitespace(previousPage.title) : '';
  const interleavePrompt = priorTitle
    ? `Intercalação: sem voltar à página anterior, explique uma relação ou uma diferença entre “${page?.title || topicLabel}” e “${priorTitle}”. Depois confira as duas páginas e corrija qualquer mistura de conceitos.`
    : `Intercalação: ao terminar esta página, relacione-a com outro conceito já estudado no mesmo tópico. Se não houver relação direta, explique justamente por que não devem ser confundidos.`;

  return {
    domain,
    terms,
    claims,
    diagnosticPrompt: `Antes de ler, escreva de memória o que você já sabe sobre “${page?.title || topicLabel}”. Tente usar corretamente pelo menos dois destes termos, se já os conhecer: ${terms.slice(0, 5).join(', ') || 'os termos centrais da página'}. Não consulte o texto ainda.`,
    recallPrompts,
    selfExplanationPrompt: selfExplanationPrompt(domain, terms),
    applicationPrompt: applicationPrompt(domain, terms, page?.title || topicLabel),
    interleavePrompt,
  };
}

export function learningStatePk(contestId, topicId, pageId) {
  return `${contestId}|learning|${topicId}|${pageId}`;
}

export async function loadTopicLearningStates(topicPk) {
  const rows = await getByIndex('notes', 'byTopic', topicPk, { limit: 5000 });
  return new Map(
    rows
      .filter(row => row.type === 'page-learning' && row.pageId)
      .map(row => [row.pageId, row]),
  );
}

function addDaysIso(days) {
  const date = new Date();
  date.setHours(12, 0, 0, 0);
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

/**
 * A primeira conclusão sempre agenda recuperação em 1 dia. Nas revisões,
 * domínio suficiente avança 1 -> 7 -> 30; dificuldade reinicia em 1 dia.
 */
export async function savePageLearningState({
  contestId,
  topicId,
  topicPk,
  pageId,
  pageIndex,
  previousState = null,
  diagnostic = '',
  recallAnswers = [],
  application = '',
  mastery = 0,
}) {
  const now = new Date().toISOString();
  const wasCompleted = Boolean(previousState?.completedAt);
  let stage = Number(previousState?.reviewStage || 0);

  if (wasCompleted) {
    if (mastery >= 2) stage = Math.min(stage + 1, 2);
    else stage = 0;
  } else {
    stage = 0;
  }

  const intervals = [1, 7, 30];
  const intervalDays = mastery === 0 ? 1 : intervals[stage];
  const record = {
    ...(previousState || {}),
    pk: learningStatePk(contestId, topicId, pageId),
    contestId,
    topicPk,
    topicId,
    pageId,
    pageIndex,
    type: 'page-learning',
    methodVersion: 'learning-science-v1.9.0',
    diagnostic: normalizeWhitespace(diagnostic),
    recallAnswers: recallAnswers.map(normalizeWhitespace),
    application: normalizeWhitespace(application),
    mastery: Number(mastery),
    reviewStage: stage,
    intervalDays,
    nextReviewDate: addDaysIso(intervalDays),
    completedAt: previousState?.completedAt || now,
    lastReviewedAt: wasCompleted ? now : null,
    updatedAt: now,
  };

  await put('notes', record);
  return record;
}
