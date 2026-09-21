/** Planejador por prioridades do edital e pendências reais do aluno. */
import { getByIndex, get, put, remove } from '../db.js';
import { uid, todayIso } from '../utils.js';

function addMinutesToTime(hhmm, minutes) {
  const [h, m] = hhmm.split(':').map(Number);
  const total = h * 60 + m + minutes;
  return `${String(Math.floor(total / 60) % 24).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
}

export async function generatePlan(contestId, days = 14) {
  const [subjects, topics, progress, preferences, existing] = await Promise.all([
    getByIndex('subjects','byContest',contestId,{limit:100}),
    getByIndex('topics','byContest',contestId,{limit:2000}),
    getByIndex('topicProgress','byContest',contestId,{limit:2000}),
    get('settings','studyAvailability'),
    getByIndex('schedule','byContest',contestId,{limit:3000}),
  ]);

  // "Reorganizar" substitui somente blocos futuros de estudo gerados pelo app.
  // Eventos oficiais, TAF ou registros passados permanecem intactos.
  for (const item of existing.filter(i => i.type === 'study' && i.date >= todayIso())) {
    await remove('schedule', item.id);
  }

  const done = new Set(progress.filter(p => p.studied).map(p => p.pk));
  const pending = topics.filter(t => !done.has(t.pk));
  const subjectMap = new Map(subjects.map(s => [s.id,s]));

  // Prioridade principal: peso curricular. Em empate, mantemos a ordem da matriz.
  pending.sort((a,b) => (subjectMap.get(b.subjectId)?.priority || 1) - (subjectMap.get(a.subjectId)?.priority || 1));

  const availability = preferences?.value || defaultAvailability();
  let cursor = 0;
  const base = new Date(`${todayIso()}T12:00:00`);
  const created = [];

  for (let offset = 0; offset < days; offset += 1) {
    const date = new Date(base);
    date.setDate(base.getDate()+offset);
    const weekday = String(date.getDay());
    const slot = availability[weekday];
    if (!slot?.enabled || cursor >= pending.length) continue;
    const dateIso = date.toISOString().slice(0,10);
    const blockLength = 50;
    const blocks = Math.max(1, Math.floor(slot.durationMinutes / blockLength));

    for (let i=0;i<blocks && cursor<pending.length;i+=1) {
      const topic = pending[cursor++];
      const subject = subjectMap.get(topic.subjectId);
      const item = {
        id: uid('schedule'),
        contestId,
        type:'study',
        date:dateIso,
        startTime:addMinutesToTime(slot.start, i * blockLength),
        durationMinutes:blockLength,
        subjectPk:subject.pk,
        topicPk:topic.pk,
        title:`${subject.name}: ${topic.label}`,
        completed:false,
        generated:true,
      };
      await put('schedule', item);
      created.push(item);
    }
  }
  return created;
}

export function defaultAvailability() {
  return {
    '0': {enabled:false,start:'09:00',durationMinutes:0},
    '1': {enabled:true,start:'19:00',durationMinutes:180},
    '2': {enabled:true,start:'19:00',durationMinutes:180},
    '3': {enabled:true,start:'19:00',durationMinutes:180},
    '4': {enabled:true,start:'19:00',durationMinutes:180},
    '5': {enabled:true,start:'19:00',durationMinutes:180},
    '6': {enabled:true,start:'14:00',durationMinutes:240},
  };
}
