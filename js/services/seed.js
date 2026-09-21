/**
 * Importa os pacotes acadêmicos/concursos para o IndexedDB.
 *
 * A partir da v1.5 cada pacote possui uma versão própria. Isso evita recarregar
 * o banco gigante da GCM quando somente um novo curso é adicionado.
 */
import {
  SEED_CONTEST_ID,
  SEED_DATA_VERSION,
  SEED_PACKAGES,
} from '../config.js';
import { get, put, bulkPut } from '../db.js';

async function loadJson(path) {
  const response = await fetch(path, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Falha ao carregar ${path}`);
  return response.json();
}

/**
 * Converte um pacote gzip codificado em base64 de volta para JSON.
 *
 * Os cursos acadêmicos possuem centenas de páginas internas. Guardá-los
 * compactados reduz bastante o tamanho transferido e acelera a primeira
 * importação no celular. DecompressionStream existe nos navegadores modernos
 * usados para PWA; se não existir, mostramos uma mensagem clara em vez de
 * gravar dados incompletos.
 */
async function decodeGzipBase64(base64Text) {
  if (typeof DecompressionStream === 'undefined') {
    throw new Error(
      'Este navegador não oferece suporte à descompressão necessária para os pacotes acadêmicos. Atualize o navegador e tente novamente.',
    );
  }

  const normalized = base64Text.replace(/\s+/g, '');
  const binary = atob(normalized);
  const bytes = new Uint8Array(binary.length);

  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  const decompressedStream = new Blob([bytes])
    .stream()
    .pipeThrough(new DecompressionStream('gzip'));

  const jsonText = await new Response(decompressedStream).text();
  return JSON.parse(jsonText);
}

async function loadCompressedPackage(packageConfig) {
  const parts = await Promise.all(
    Array.from({ length: packageConfig.chunkCount }, async (_, index) => {
      const partNumber = String(index + 1).padStart(2, '0');
      const path = `./data/packages/${packageConfig.id}.part-${partNumber}.b64`;
      const response = await fetch(path, { cache: 'no-store' });
      if (!response.ok) throw new Error(`Falha ao carregar ${path}`);
      return response.text();
    }),
  );

  return decodeGzipBase64(parts.join(''));
}

async function loadPackage(packageConfig) {
  if (packageConfig.format === 'gzip-base64-chunks') {
    return loadCompressedPackage(packageConfig);
  }

  const [contest, syllabus, lessons, questions] = await Promise.all([
    loadJson(`./data/contests/${packageConfig.id}.json`),
    loadJson(`./data/syllabus/${packageConfig.id}.json`),
    loadJson(`./data/lessons/${packageConfig.id}.json`),
    loadJson(`./data/questions/${packageConfig.id}.json`),
  ]);

  return { contest, syllabus, lessons, questions };
}

async function persistPackage({ contest, syllabus, lessons, questions }) {
  await put('contests', contest);

  const subjectRows = syllabus.subjects.map(subject => ({
    pk: `${contest.id}|${subject.id}`,
    contestId: contest.id,
    ...subject,
  }));
  await bulkPut('subjects', subjectRows);

  const topicRows = syllabus.subjects.flatMap(subject =>
    subject.topics.map(topic => ({
      pk: `${contest.id}|${topic.id}`,
      contestId: contest.id,
      subjectId: subject.id,
      subjectPk: `${contest.id}|${subject.id}`,
      ...topic,
    })),
  );
  await bulkPut('topics', topicRows);

  await bulkPut(
    'lessons',
    lessons.map(lesson => ({
      ...lesson,
      pk: `${contest.id}|${lesson.id}`,
      topicPk: `${contest.id}|${lesson.topicId}`,
    })),
  );

  await bulkPut(
    'questions',
    questions.map(question => ({
      ...question,
      pk: `${contest.id}|${question.id}`,
      contestId: contest.id,
      subjectPk: `${contest.id}|${question.subjectId}`,
      topicPks: question.topicIds.map(id => `${contest.id}|${id}`),
    })),
  );
}

async function ensurePackage(packageConfig, legacySeedVersion) {
  const metadataKey = `seedVersion:${packageConfig.id}`;
  const current = await get('metadata', metadataKey);
  if (current?.value === packageConfig.version) return;

  /*
   * Migração sem custo para quem já usa a GCM desde a v1.4: o pacote está no
   * IndexedDB e a versão global antiga confirma que ele já foi importado.
   * Assim não recarregamos todo o material da GCM apenas para criar a nova
   * chave de metadados individual.
   */
  if (
    packageConfig.id === SEED_CONTEST_ID &&
    legacySeedVersion?.value === packageConfig.version
  ) {
    await put('metadata', { key: metadataKey, value: packageConfig.version });
    return;
  }

  const data = await loadPackage(packageConfig);
  await persistPackage(data);
  await put('metadata', { key: metadataKey, value: packageConfig.version });
}

export async function ensureSeedData() {
  const legacySeedVersion = await get('metadata', 'seedVersion');

  // Importação sequencial reduz pico de memória em celulares modestos.
  for (const packageConfig of SEED_PACKAGES) {
    await ensurePackage(packageConfig, legacySeedVersion);
  }

  await put('metadata', { key: 'seedVersion', value: SEED_DATA_VERSION });

  const active = await get('settings', 'activeContestId');
  if (!active) {
    await put('settings', {
      key: 'activeContestId',
      value: SEED_CONTEST_ID,
    });
  }
}
