/** Importa o pacote inicial da Guarda Salvador para o IndexedDB uma única vez. */
import { SEED_CONTEST_ID, SEED_DATA_VERSION } from '../config.js';
import { get, put, bulkPut } from '../db.js';

async function loadJson(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Falha ao carregar ${path}`);
  return response.json();
}

export async function ensureSeedData() {
  const seeded = await get('metadata', 'seedVersion');
  if (seeded?.value === SEED_DATA_VERSION) return;

  const [contest, syllabus, lessons, questions] = await Promise.all([
    loadJson(`./data/contests/${SEED_CONTEST_ID}.json`),
    loadJson(`./data/syllabus/${SEED_CONTEST_ID}.json`),
    loadJson(`./data/lessons/${SEED_CONTEST_ID}.json`),
    loadJson(`./data/questions/${SEED_CONTEST_ID}.json`),
  ]);

  await put('contests', contest);
  const subjectRows = syllabus.subjects.map(subject => ({
    pk: `${contest.id}|${subject.id}`,
    contestId: contest.id,
    ...subject,
  }));
  await bulkPut('subjects', subjectRows);

  const topicRows = syllabus.subjects.flatMap(subject => subject.topics.map(topic => ({
    pk: `${contest.id}|${topic.id}`,
    contestId: contest.id,
    subjectId: subject.id,
    subjectPk: `${contest.id}|${subject.id}`,
    ...topic,
  })));
  await bulkPut('topics', topicRows);

  await bulkPut('lessons', lessons.map(lesson => ({
    ...lesson,
    pk: `${contest.id}|${lesson.id}`,
    topicPk: `${contest.id}|${lesson.topicId}`,
  })));

  await bulkPut('questions', questions.map(question => ({
    ...question,
    pk: `${contest.id}|${question.id}`,
    subjectPk: `${contest.id}|${question.subjectId}`,
    topicPks: question.topicIds.map(id => `${contest.id}|${id}`),
  })));

  await put('metadata', { key: 'seedVersion', value: SEED_DATA_VERSION });
  const active = await get('settings', 'activeContestId');
  if (!active) await put('settings', { key: 'activeContestId', value: contest.id });
}
