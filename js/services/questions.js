/** Seleção de exercícios: filtra primeiro, só depois aleatoriza. */
import { getByIndex } from '../db.js';
import { shuffle } from '../utils.js';

export async function selectQuestions({ contestId, subjectId, topicId, difficulty, count = 10, onlyWrong = false }) {
  let candidates;
  if (topicId) {
    candidates = await getByIndex('questions', 'byTopic', `${contestId}|${topicId}`, { limit: 1000 });
  } else if (subjectId) {
    candidates = await getByIndex('questions', 'bySubject', `${contestId}|${subjectId}`, { limit: 1000 });
  } else {
    candidates = await getByIndex('questions', 'byContest', contestId, { limit: 2000 });
  }

  if (difficulty) candidates = candidates.filter(q => q.difficulty === difficulty);

  // Questões de simples reconhecimento da matriz ficam em segundo plano quando
  // existem questões substanciais suficientes para a sessão solicitada.
  const substantive = candidates.filter(q => !q.tags?.includes('matriz-edital'));
  if (substantive.length >= count) candidates = substantive;

  if (onlyWrong) {
    const attempts = await getByIndex('questionAttempts', 'byContest', contestId, { limit: 5000, direction: 'prev' });
    const lastByQuestion = new Map();
    attempts.forEach(a => { if (!lastByQuestion.has(a.questionPk)) lastByQuestion.set(a.questionPk, a); });
    candidates = candidates.filter(q => lastByQuestion.get(q.pk)?.correct === false);
  }

  return shuffle(candidates).slice(0, count);
}

/**
 * Monta simulado usando a distribuição cadastrada no edital ativo.
 * Isso é essencial para que a plataforma aceite outros concursos sem manter
 * uma lista hardcoded de matérias da Guarda Salvador.
 */
export async function buildSimulation(contestId) {
  const subjects = await getByIndex('subjects', 'byContest', contestId, { limit: 100 });
  const blocks = [];
  for (const subject of subjects.filter(s => Number(s.questions) > 0)) {
    const amount = Number(subject.questions);
    const qs = await selectQuestions({ contestId, subjectId: subject.id, count: amount });
    if (qs.length < amount) {
      throw new Error(`Banco insuficiente em ${subject.name}: ${qs.length}/${amount}.`);
    }
    blocks.push(...qs);
  }
  if (!blocks.length) throw new Error('Este edital ainda não possui distribuição de questões configurada.');
  return shuffle(blocks);
}
