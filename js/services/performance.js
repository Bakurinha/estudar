/** Atualiza estatísticas incrementais e calcula o nível de preparação. */
import { get, put, getByIndex, count } from '../db.js';
import { clamp, preparationLabel, todayIso } from '../utils.js';

export async function recordAttempt(question, selectedIndex) {
  const correct = selectedIndex === question.answerIndex;
  const now = new Date().toISOString();
  const attempt = {
    contestId: question.contestId,
    questionPk: question.pk,
    subjectPk: question.subjectPk,
    topicPks: question.topicPks,
    selectedIndex,
    correct,
    answeredAt: now,
  };

  const { add } = await import('../db.js');
  await add('questionAttempts', attempt);

  await updateStat(`${question.contestId}|global`, question.contestId, null, correct);
  await updateStat(`${question.contestId}|${question.subjectId}`, question.contestId, question.subjectPk, correct);

  for (const topicPk of question.topicPks) {
    await updateTopicProgress(question.contestId, question.subjectPk, topicPk, correct);
  }
  return correct;
}

async function updateStat(pk, contestId, subjectPk, correct) {
  const stat = await get('stats', pk) || {
    pk, contestId, subjectPk, answered: 0, correct: 0, wrong: 0, updatedAt: null,
  };
  stat.answered += 1;
  stat.correct += correct ? 1 : 0;
  stat.wrong += correct ? 0 : 1;
  stat.updatedAt = new Date().toISOString();
  await put('stats', stat);
}

async function updateTopicProgress(contestId, subjectPk, topicPk, correct) {
  const progress = await get('topicProgress', topicPk) || {
    pk: topicPk,
    contestId,
    subjectPk,
    status: 'studying',
    studied: false,
    attempts: 0,
    correct: 0,
    lastStudiedAt: null,
  };
  progress.attempts += 1;
  progress.correct += correct ? 1 : 0;
  progress.lastStudiedAt = new Date().toISOString();
  const accuracy = progress.attempts ? progress.correct / progress.attempts : 0;
  if (progress.studied && progress.attempts >= 5 && accuracy >= 0.8) progress.status = 'dominated';
  else if (progress.attempts >= 3 && accuracy >= 0.6) progress.status = 'reviewing';
  else progress.status = 'studying';
  await put('topicProgress', progress);
}

export async function markTopicStudied(contestId, subjectPk, topicPk) {
  const progress = await get('topicProgress', topicPk) || {
    pk: topicPk, contestId, subjectPk, attempts: 0, correct: 0,
  };
  progress.studied = true;
  progress.status = progress.status === 'dominated' ? 'dominated' : 'studied';
  progress.lastStudiedAt = new Date().toISOString();
  await put('topicProgress', progress);

  const due = new Date();
  due.setDate(due.getDate() + 1);
  await put('reviews', {
    pk: `${contestId}|${topicPk.split('|').pop()}`,
    contestId,
    topicPk,
    dueDate: due.toISOString().slice(0, 10),
    intervalDays: 1,
    completedCount: 0,
  });
}

export async function completeReview(review, scorePct) {
  let next = 30;
  if (scorePct < 60) next = 1;
  else if (scorePct < 80) next = 7;
  const date = new Date();
  date.setDate(date.getDate() + next);
  review.intervalDays = next;
  review.dueDate = date.toISOString().slice(0, 10);
  review.completedCount = (review.completedCount || 0) + 1;
  review.lastScore = scorePct;
  await put('reviews', review);
}

export async function getPreparation(contestId) {
  const [topicTotal, progressRows, globalStat, sessions, simulations] = await Promise.all([
    count('topics', 'byContest', contestId),
    getByIndex('topicProgress', 'byContest', contestId, { limit: 1000 }),
    get('stats', `${contestId}|global`),
    getByIndex('studySessions', 'byContest', contestId, { limit: 200, direction: 'prev' }),
    getByIndex('simulations', 'byContest', contestId, { limit: 20, direction: 'prev' }),
  ]);

  const studied = progressRows.filter(p => p.studied).length;
  const coverage = topicTotal ? Math.round((studied / topicTotal) * 100) : 0;
  const accuracy = globalStat?.answered ? Math.round((globalStat.correct / globalStat.answered) * 100) : 0;

  const last14 = Date.now() - 14 * 86400000;
  const activeDays = new Set(
    sessions.filter(s => new Date(s.startedAt).getTime() >= last14)
      .map(s => s.startedAt.slice(0, 10))
  ).size;
  const consistency = Math.round((activeDays / 12) * 100);
  const sim = simulations[0]?.scorePct ?? 0;

  const score = clamp(Math.round(coverage * 0.4 + accuracy * 0.35 + consistency * 0.15 + sim * 0.10));
  return { score, label: preparationLabel(score), coverage, accuracy, consistency: clamp(consistency), simulation: sim };
}

export async function getSubjectStats(contestId) {
  const subjects = await getByIndex('subjects', 'byContest', contestId, { limit: 100 });
  const progress = await getByIndex('topicProgress', 'byContest', contestId, { limit: 1000 });
  const rows = [];
  for (const subject of subjects) {
    const topics = await getByIndex('topics', 'bySubject', subject.pk, { limit: 200 });
    const subjectProgress = progress.filter(p => p.subjectPk === subject.pk);
    const studied = subjectProgress.filter(p => p.studied).length;
    const stat = await get('stats', `${contestId}|${subject.id}`);
    const contentPct = topics.length ? Math.round((studied / topics.length) * 100) : 0;
    const accuracyPct = stat?.answered ? Math.round((stat.correct / stat.answered) * 100) : 0;
    const domainPct = Math.round(contentPct * 0.45 + accuracyPct * 0.55);
    rows.push({ subject, contentPct, accuracyPct, domainPct, answered: stat?.answered || 0 });
  }
  return rows;
}
