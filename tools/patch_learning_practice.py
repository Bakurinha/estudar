from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
learning = ROOT / 'js/services/learning.js'
text = learning.read_text(encoding='utf-8')

pattern = re.compile(r"function substantiveBlocks\(page\) \{.*?\n\}\n\nfunction scoreSentence", re.S)
replacement = r'''function blockCombinedText(block) {
  const body = normalizeWhitespace(block?.body);
  const items = Array.isArray(block?.items)
    ? block.items.map(normalizeWhitespace).filter(Boolean)
    : [];
  return [body, ...items].filter(Boolean).join(' ');
}

function isPracticePage(page) {
  const label = `${page?.title || ''} ${page?.kind || ''}`.toLocaleLowerCase('pt-BR');
  return /treino|quest[oõ]es|exerc[ií]cios|pr[aá]tica|atividade|desafio/.test(label);
}

function extractExercisePrompts(page) {
  const prompts = [];
  const blocks = Array.isArray(page?.blocks) ? page.blocks : [];

  blocks.forEach(block => {
    const title = normalizeWhitespace(block?.title);
    const practiceBlock = /treino|quest[oõ]es|exerc[ií]cios|pr[aá]tica|atividade|desafio/i.test(title);

    if (Array.isArray(block?.items)) {
      block.items.forEach(item => {
        const clean = normalizeWhitespace(item);
        if (clean.length >= 12) prompts.push(clean);
      });
    }

    if (practiceBlock) {
      const body = normalizeWhitespace(block?.body);
      splitSentences(body).forEach(sentence => prompts.push(sentence));
    }
  });

  const seen = new Set();
  return prompts.filter(prompt => {
    const key = normalizeForCompare(prompt);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 3);
}

function substantiveBlocks(page) {
  const blocks = Array.isArray(page?.blocks) ? page.blocks : [];
  const preferred = blocks.filter(block => {
    const body = blockCombinedText(block);
    return body.length >= 120 && !isControlTitle(block?.title) && !isGenericBody(body);
  });

  if (preferred.length) return preferred;

  return blocks.filter(block => blockCombinedText(block).length >= 80);
}

function scoreSentence'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit('Could not patch substantiveBlocks')

text = text.replace('splitSentences(block.body).forEach(sentence => {', 'splitSentences(blockCombinedText(block)).forEach(sentence => {', 1)

pattern = re.compile(r"export function buildLearningPlan\(\{ contestId, subjectId, topicLabel, page, lesson, previousPage = null \}\) \{.*?\n\}\n\nexport function learningStatePk", re.S)
replacement = r'''export function buildLearningPlan({ contestId, subjectId, topicLabel, page, lesson, previousPage = null }) {
  const practicePage = isPracticePage(page);
  const exercisePrompts = extractExercisePrompts(page);
  const claims = extractGroundedClaims(page, lesson);
  const terms = extractKeyTerms(claims, page?.title || topicLabel);
  const domain = inferDomain({ contestId, subjectId, topicLabel });
  let recallPrompts = claims.map((claim, index) => ({
    prompt: cueForClaim(domain, terms, index),
    criterion: claim.sentence,
    sourceBlock: claim.blockTitle,
    criterionType: 'source-claim',
  }));

  if (!recallPrompts.length && practicePage && exercisePrompts.length) {
    recallPrompts = exercisePrompts.map((exercise, index) => ({
      prompt: `Tentativa independente ${index + 1}: ${exercise}`,
      criterion: 'Esta página é de prática e não contém, por si só, uma resposta teórica completa. Resolva primeiro e depois volte ao conceito correspondente nas páginas anteriores ou ao comentário/gabarito quando o próprio material o fornecer. O modo Aprender não inventa um gabarito ausente.',
      sourceBlock: 'Exercício/atividade do material',
      criterionType: 'practice-guidance',
    }));
  }

  if (!recallPrompts.length) {
    recallPrompts.push({
      prompt: `Sem consultar, explique o que esta página ensina sobre “${page?.title || topicLabel}”.`,
      criterion: normalizeWhitespace(page?.editalBasis || page?.sourceScope || lesson?.officialScope),
      sourceBlock: 'Escopo da página',
      criterionType: 'source-claim',
    });
  }

  const priorTitle = previousPage?.title ? normalizeWhitespace(previousPage.title) : '';
  const interleavePrompt = priorTitle
    ? `Intercalação: sem voltar à página anterior, explique uma relação ou uma diferença entre “${page?.title || topicLabel}” e “${priorTitle}”. Depois confira as duas páginas e corrija qualquer mistura de conceitos.`
    : `Intercalação: ao terminar esta página, relacione-a com outro conceito já estudado no mesmo tópico. Se não houver relação direta, explique justamente por que não devem ser confundidos.`;

  const diagnosticPrompt = practicePage
    ? `Antes de reler explicações anteriores, identifique de memória quais conceitos e procedimentos deste tópico você espera usar em “${page?.title || topicLabel}”. Depois abra a página e tente os exercícios antes de consultar teoria ou comentário.`
    : `Antes de ler, escreva de memória o que você já sabe sobre “${page?.title || topicLabel}”. Tente usar corretamente pelo menos dois destes termos, se já os conhecer: ${terms.slice(0, 5).join(', ') || 'os termos centrais da página'}. Não consulte o texto ainda.`;

  const application = practicePage
    ? `Depois de resolver, escolha um dos exercícios desta página e explique por que cada passo da sua solução é sustentado por um conceito já estudado. Se o material não trouxer gabarito, não presuma uma resposta: marque a dúvida e confronte-a com a teoria correspondente.`
    : applicationPrompt(domain, terms, page?.title || topicLabel);

  return {
    domain,
    terms,
    claims,
    practicePage,
    exercisePrompts,
    diagnosticPrompt,
    recallPrompts,
    selfExplanationPrompt: selfExplanationPrompt(domain, terms),
    applicationPrompt: application,
    interleavePrompt,
  };
}

export function learningStatePk'''
text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit('Could not patch buildLearningPlan')

learning.write_text(text, encoding='utf-8')

study = ROOT / 'js/views/study.js'
study_text = study.read_text(encoding='utf-8')
study_text = study_text.replace(
    'A conferência usa afirmações já existentes na própria página; o método não adiciona conteúdo novo ao escopo.',
    'A conferência usa afirmações já existentes na própria página; em páginas de prática, usa os exercícios e retorna à teoria sem inventar gabarito. O método não adiciona conteúdo novo ao escopo.',
)
study_text = study_text.replace(
    '<strong>Critério retirado do próprio conteúdo</strong>',
    "<strong>${item.criterionType === 'practice-guidance' ? 'Como conferir sem inventar gabarito' : 'Critério retirado do próprio conteúdo'}</strong>",
)
study.write_text(study_text, encoding='utf-8')

print('practice-page learning patch applied')
