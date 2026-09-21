/**
 * Motor de seleção de exercícios.
 *
 * Regras importantes:
 * 1. Filtra matéria/tópico/dificuldade ANTES de qualquer aleatoriedade.
 * 2. Evita repetir questões vistas há pouco quando há alternativas disponíveis.
 * 3. Prioriza questões inéditas e questões que o aluno errou anteriormente.
 * 4. Nunca altera o gabarito da questão; a ordem visual das alternativas é
 *    embaralhada somente na camada de interface (views/questions.js).
 */
import { getByIndex } from '../db.js';
import { shuffle } from '../utils.js';

const DAY_MS = 86_400_000;

/**
 * Resume o histórico recente por questão.
 * Percorremos as tentativas da mais nova para a mais antiga; assim a primeira
 * ocorrência encontrada é sempre a resposta mais recente daquela questão.
 */
async function getAttemptHistory(contestId) {
  const attempts = await getByIndex(
    'questionAttempts',
    'byContest',
    contestId,
    { limit: 10_000, direction: 'prev' },
  );

  const history = new Map();

  for (const attempt of attempts) {
    const current = history.get(attempt.questionPk);

    if (!current) {
      history.set(attempt.questionPk, {
        lastAnsweredAt: attempt.answeredAt,
        lastCorrect: attempt.correct,
        timesSeen: 1,
        wrongCount: attempt.correct ? 0 : 1,
      });
      continue;
    }

    current.timesSeen += 1;
    if (!attempt.correct) current.wrongCount += 1;
  }

  return history;
}

/**
 * Calcula uma prioridade de exibição.
 *
 * Quanto MAIOR o valor, mais cedo a questão tende a aparecer. A pequena
 * parcela aleatória impede que duas sessões com os mesmos filtros tenham a
 * mesma ordem, mas não deixa a aleatoriedade atropelar o histórico do aluno.
 */
function questionPriority(question, history, now = Date.now()) {
  const info = history.get(question.pk);

  // Questões nunca vistas recebem prioridade máxima.
  if (!info) return 1_000 + Math.random() * 50;

  const lastTime = new Date(info.lastAnsweredAt).getTime();
  const ageDays = Number.isFinite(lastTime)
    ? Math.max(0, (now - lastTime) / DAY_MS)
    : 30;

  let score = Math.min(ageDays, 60) * 4;

  // Erros merecem reaparecer, mas não imediatamente depois de o usuário ter
  // acabado de responder a mesma questão.
  if (!info.lastCorrect) score += 180;
  score += Math.min(info.wrongCount, 5) * 15;

  // Quanto mais vezes a questão já apareceu, menor sua prioridade normal.
  score -= Math.min(info.timesSeen, 20) * 10;

  // Evita repetição irritante no mesmo dia quando existem outras questões.
  if (ageDays < 1) score -= 300;
  else if (ageDays < 3) score -= 120;
  else if (ageDays < 7) score -= 40;

  // Desempate aleatório controlado.
  score += Math.random() * 30;

  return score;
}

/**
 * Seleciona exercícios compatíveis com os filtros escolhidos pelo usuário.
 */
export async function selectQuestions({
  contestId,
  subjectId,
  topicId,
  difficulty,
  count = 10,
  onlyWrong = false,
}) {
  let candidates;

  if (topicId) {
    candidates = await getByIndex(
      'questions',
      'byTopic',
      `${contestId}|${topicId}`,
      { limit: 5_000 },
    );
  } else if (subjectId) {
    candidates = await getByIndex(
      'questions',
      'bySubject',
      `${contestId}|${subjectId}`,
      { limit: 10_000 },
    );
  } else {
    candidates = await getByIndex(
      'questions',
      'byContest',
      contestId,
      { limit: 20_000 },
    );
  }

  if (difficulty) {
    candidates = candidates.filter(
      question => question.difficulty === difficulty,
    );
  }

  // Questões que só ensinam a posição do tópico na matriz do edital são úteis
  // como reforço, mas não devem dominar uma sessão quando há questões de
  // conteúdo suficientes.
  const substantive = candidates.filter(
    question => !question.tags?.includes('matriz-edital'),
  );

  if (substantive.length >= count) {
    candidates = substantive;
  }

  const history = await getAttemptHistory(contestId);

  if (onlyWrong) {
    candidates = candidates.filter(
      question => history.get(question.pk)?.lastCorrect === false,
    );
  }

  if (!candidates.length) return [];

  // Antes de ordenar por prioridade, embaralhamos. Isso impede que a ordem do
  // arquivo JSON ou do IndexedDB influencie empates de pontuação.
  const randomized = shuffle(candidates);
  const now = Date.now();

  randomized.sort(
    (a, b) => questionPriority(b, history, now) - questionPriority(a, history, now),
  );

  return randomized.slice(0, count);
}

/**
 * Monta simulado usando a distribuição cadastrada no edital ativo.
 * Isso permite que futuros concursos usem quantidades diferentes sem manter
 * uma lista fixa de matérias da Guarda Salvador dentro do código.
 */
export async function buildSimulation(contestId) {
  const subjects = await getByIndex(
    'subjects',
    'byContest',
    contestId,
    { limit: 100 },
  );

  const blocks = [];

  for (const subject of subjects.filter(item => Number(item.questions) > 0)) {
    const amount = Number(subject.questions);
    const questions = await selectQuestions({
      contestId,
      subjectId: subject.id,
      count: amount,
    });

    if (questions.length < amount) {
      throw new Error(
        `Banco insuficiente em ${subject.name}: ${questions.length}/${amount}.`,
      );
    }

    blocks.push(...questions);
  }

  if (!blocks.length) {
    throw new Error(
      'Este edital ainda não possui distribuição de questões configurada.',
    );
  }

  return shuffle(blocks);
}
