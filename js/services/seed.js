/**
 * Importa os pacotes acadêmicos/concursos para o IndexedDB.
 *
 * Regra de robustez importante:
 * - o pacote principal da GCM é obrigatório;
 * - cursos acadêmicos são independentes e opcionais durante o boot;
 * - falha de rede, chunk ausente ou pacote corrompido de um curso NÃO pode
 *   derrubar o restante do aplicativo.
 */
import {
  SEED_CONTEST_ID,
  SEED_DATA_VERSION,
  SEED_PACKAGES,
} from '../config.js';
import { get, put, bulkPut } from '../db.js';

/**
 * Faz fetch sem usar uma cópia antiga do arquivo. O parâmetro de versão muda a
 * URL quando o conteúdo é atualizado e evita que um Service Worker antigo
 * devolva um pacote incompatível com o config atual.
 */
async function fetchVersioned(path, version = '') {
  const separator = path.includes('?') ? '&' : '?';
  const versionedPath = version
    ? `${path}${separator}v=${encodeURIComponent(version)}`
    : path;

  let response;

  try {
    response = await fetch(versionedPath, { cache: 'no-store' });
  } catch (error) {
    throw new Error(`Falha de rede ao carregar ${path}: ${error.message}`);
  }

  if (!response.ok) {
    throw new Error(`Falha ao carregar ${path}: HTTP ${response.status}`);
  }

  return response;
}

async function loadJson(path, version = '') {
  const response = await fetchVersioned(path, version);
  return response.json();
}

/**
 * Converte gzip codificado em base64 novamente para JSON.
 */
async function decodeGzipBase64(base64Text) {
  if (typeof DecompressionStream === 'undefined') {
    throw new Error(
      'Este navegador não oferece suporte à descompressão dos pacotes acadêmicos. Atualize o navegador e tente novamente.',
    );
  }

  const normalized = base64Text.replace(/\s+/g, '');
  const binary = atob(normalized);
  const bytes = new Uint8Array(binary.length);

  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  try {
    const decompressedStream = new Blob([bytes])
      .stream()
      .pipeThrough(new DecompressionStream('gzip'));

    const jsonText = await new Response(decompressedStream).text();
    return JSON.parse(jsonText);
  } catch (error) {
    throw new Error(`Pacote compactado inválido ou incompleto: ${error.message}`);
  }
}

/**
 * Carrega os chunks em sequência. Além de reduzir o pico de conexões e memória
 * em celulares, isso deixa a mensagem de erro indicar exatamente qual parte
 * está ausente.
 */
async function loadCompressedPackage(packageConfig) {
  const parts = [];

  for (let index = 0; index < packageConfig.chunkCount; index += 1) {
    const partNumber = String(index + 1).padStart(2, '0');
    const path = `./data/packages/${packageConfig.id}.part-${partNumber}.b64`;
    const response = await fetchVersioned(path, packageConfig.version);
    parts.push(await response.text());
  }

  return decodeGzipBase64(parts.join(''));
}

async function loadPackage(packageConfig) {
  if (packageConfig.format === 'gzip-base64-chunks') {
    return loadCompressedPackage(packageConfig);
  }

  const [contest, syllabus, lessons, questions] = await Promise.all([
    loadJson(`./data/contests/${packageConfig.id}.json`, packageConfig.version),
    loadJson(`./data/syllabus/${packageConfig.id}.json`, packageConfig.version),
    loadJson(`./data/lessons/${packageConfig.id}.json`, packageConfig.version),
    loadJson(`./data/questions/${packageConfig.id}.json`, packageConfig.version),
  ]);

  return { contest, syllabus, lessons, questions };
}

function validatePackageData(data, packageConfig) {
  if (!data?.contest?.id || data.contest.id !== packageConfig.id) {
    throw new Error(`Pacote ${packageConfig.id} não possui identificação válida.`);
  }

  if (!Array.isArray(data?.syllabus?.subjects)) {
    throw new Error(`Pacote ${packageConfig.id} não possui matriz de estudo válida.`);
  }

  if (!Array.isArray(data.lessons) || !Array.isArray(data.questions)) {
    throw new Error(`Pacote ${packageConfig.id} está incompleto.`);
  }
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

  if (current?.value === packageConfig.version) {
    return { id: packageConfig.id, status: 'current' };
  }

  /*
   * Migração sem custo para quem já usava a GCM na versão anterior.
   */
  if (
    packageConfig.id === SEED_CONTEST_ID &&
    legacySeedVersion?.value === packageConfig.version
  ) {
    await put('metadata', { key: metadataKey, value: packageConfig.version });
    return { id: packageConfig.id, status: 'current' };
  }

  const data = await loadPackage(packageConfig);
  validatePackageData(data, packageConfig);
  await persistPackage(data);

  await put('metadata', {
    key: metadataKey,
    value: packageConfig.version,
  });

  await put('metadata', {
    key: `seedError:${packageConfig.id}`,
    value: null,
  });

  return { id: packageConfig.id, status: 'loaded' };
}

/**
 * Garante os pacotes disponíveis sem transformar uma falha opcional em tela
 * branca. Retornamos o diagnóstico para a interface poder avisar discretamente
 * caso algum curso não tenha sido carregado.
 */
export async function ensureSeedData() {
  const legacySeedVersion = await get('metadata', 'seedVersion');
  const results = [];

  for (const packageConfig of SEED_PACKAGES) {
    try {
      results.push(await ensurePackage(packageConfig, legacySeedVersion));
    } catch (error) {
      console.error(`Falha no pacote ${packageConfig.id}:`, error);

      await put('metadata', {
        key: `seedError:${packageConfig.id}`,
        value: {
          message: error.message,
          at: new Date().toISOString(),
        },
      });

      results.push({
        id: packageConfig.id,
        status: 'error',
        message: error.message,
      });

      // Somente um pacote explicitamente obrigatório pode interromper o boot.
      if (packageConfig.required) {
        throw error;
      }
    }
  }

  await put('metadata', { key: 'seedVersion', value: SEED_DATA_VERSION });

  const active = await get('settings', 'activeContestId');
  if (!active) {
    await put('settings', {
      key: 'activeContestId',
      value: SEED_CONTEST_ID,
    });
  }

  return results;
}
