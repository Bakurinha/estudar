/**
 * Camada única de acesso ao IndexedDB.
 *
 * Por que existe: views não devem conhecer detalhes de transações, stores ou
 * cursores. Isso permite otimizar consultas e migrar o schema no futuro sem
 * reescrever cada tela do aplicativo.
 */
import { DB_NAME, DB_VERSION } from './config.js';

let dbPromise;

export function openDatabase() {
  if (dbPromise) return dbPromise;

  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;
      createSchema(db, request.transaction);
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => console.warn('IndexedDB bloqueado por outra aba antiga.');
  });

  return dbPromise;
}

function createSchema(db, upgradeTransaction) {
  const ensure = (name, options, indexes = []) => {
    const store = db.objectStoreNames.contains(name)
      ? upgradeTransaction.objectStore(name)
      : db.createObjectStore(name, options);
    indexes.forEach(({ name: indexName, keyPath, options: indexOptions = {} }) => {
      if (!store.indexNames.contains(indexName)) {
        store.createIndex(indexName, keyPath, indexOptions);
      }
    });
    return store;
  };

  ensure('settings', { keyPath: 'key' });
  ensure('metadata', { keyPath: 'key' });
  ensure('contests', { keyPath: 'id' }, [
    { name: 'byStatus', keyPath: 'status' },
  ]);
  ensure('subjects', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
  ]);
  ensure('topics', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'bySubject', keyPath: 'subjectPk' },
  ]);
  ensure('lessons', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'bySubject', keyPath: 'subjectId' },
    { name: 'byTopic', keyPath: 'topicPk', unique: true },
  ]);
  ensure('questions', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'bySubject', keyPath: 'subjectPk' },
    { name: 'byTopic', keyPath: 'topicPks', options: { multiEntry: true } },
    { name: 'byDifficulty', keyPath: 'difficulty' },
  ]);
  ensure('questionAttempts', { keyPath: 'id', autoIncrement: true }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'byQuestion', keyPath: 'questionPk' },
    { name: 'bySubject', keyPath: 'subjectPk' },
    { name: 'byTopic', keyPath: 'topicPks', options: { multiEntry: true } },
    { name: 'byDate', keyPath: 'answeredAt' },
    { name: 'byCorrect', keyPath: 'correct' },
  ]);
  ensure('topicProgress', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'bySubject', keyPath: 'subjectPk' },
    { name: 'byStatus', keyPath: 'status' },
  ]);
  ensure('reviews', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'byDueDate', keyPath: 'dueDate' },
    { name: 'byTopic', keyPath: 'topicPk' },
  ]);
  ensure('studySessions', { keyPath: 'id', autoIncrement: true }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'byDate', keyPath: 'startedAt' },
    { name: 'bySubject', keyPath: 'subjectPk' },
  ]);
  ensure('simulations', { keyPath: 'id', autoIncrement: true }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'byDate', keyPath: 'finishedAt' },
  ]);
  ensure('tafSessions', { keyPath: 'id', autoIncrement: true }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'byDate', keyPath: 'date' },
  ]);
  ensure('schedule', { keyPath: 'id' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'byDate', keyPath: 'date' },
    { name: 'byType', keyPath: 'type' },
  ]);
  ensure('notes', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'byTopic', keyPath: 'topicPk' },
  ]);
  ensure('favorites', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'byType', keyPath: 'type' },
  ]);
  ensure('stats', { keyPath: 'pk' }, [
    { name: 'byContest', keyPath: 'contestId' },
    { name: 'bySubject', keyPath: 'subjectPk' },
  ]);
  ensure('imports', { keyPath: 'id' }, [
    { name: 'byCreatedAt', keyPath: 'createdAt' },
  ]);
}

function requestToPromise(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function get(storeName, key) {
  const db = await openDatabase();
  return requestToPromise(db.transaction(storeName, 'readonly').objectStore(storeName).get(key));
}

export async function put(storeName, value) {
  const db = await openDatabase();
  return requestToPromise(db.transaction(storeName, 'readwrite').objectStore(storeName).put(value));
}

export async function add(storeName, value) {
  const db = await openDatabase();
  return requestToPromise(db.transaction(storeName, 'readwrite').objectStore(storeName).add(value));
}

export async function remove(storeName, key) {
  const db = await openDatabase();
  return requestToPromise(db.transaction(storeName, 'readwrite').objectStore(storeName).delete(key));
}

export async function clearStore(storeName) {
  const db = await openDatabase();
  return requestToPromise(db.transaction(storeName, 'readwrite').objectStore(storeName).clear());
}

export async function count(storeName, indexName = null, value = undefined) {
  const db = await openDatabase();
  const tx = db.transaction(storeName, 'readonly');
  const source = indexName ? tx.objectStore(storeName).index(indexName) : tx.objectStore(storeName);
  const request = value === undefined ? source.count() : source.count(IDBKeyRange.only(value));
  return requestToPromise(request);
}

/**
 * Consulta indexada com limite real de registros.
 *
 * Evitamos getAll() irrestrito em tabelas que podem crescer muito. O cursor é
 * encerrado assim que alcança o limite, o que mantém histórico e banco de
 * questões rápidos mesmo depois de meses de uso.
 */
export async function getByIndex(storeName, indexName, value, { limit = 100, direction = 'next' } = {}) {
  const db = await openDatabase();
  const tx = db.transaction(storeName, 'readonly');
  const index = tx.objectStore(storeName).index(indexName);
  const results = [];

  return new Promise((resolve, reject) => {
    const request = index.openCursor(IDBKeyRange.only(value), direction);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const cursor = request.result;
      if (!cursor || results.length >= limit) {
        resolve(results);
        return;
      }
      results.push(cursor.value);
      cursor.continue();
    };
  });
}

export async function getRangeByIndex(storeName, indexName, lower, upper, { limit = 100, direction = 'next' } = {}) {
  const db = await openDatabase();
  const tx = db.transaction(storeName, 'readonly');
  const index = tx.objectStore(storeName).index(indexName);
  const results = [];
  const range = IDBKeyRange.bound(lower, upper);
  return new Promise((resolve, reject) => {
    const request = index.openCursor(range, direction);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const cursor = request.result;
      if (!cursor || results.length >= limit) return resolve(results);
      results.push(cursor.value);
      cursor.continue();
    };
  });
}

export async function getAllSmall(storeName, limit = 1000) {
  const db = await openDatabase();
  const store = db.transaction(storeName, 'readonly').objectStore(storeName);
  const results = [];
  return new Promise((resolve, reject) => {
    const request = store.openCursor();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const cursor = request.result;
      if (!cursor || results.length >= limit) return resolve(results);
      results.push(cursor.value);
      cursor.continue();
    };
  });
}

/** Executa vários puts na mesma transação para reduzir overhead. */
export async function bulkPut(storeName, values) {
  if (!values.length) return;
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    const store = tx.objectStore(storeName);
    values.forEach(value => store.put(value));
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

export async function deleteDatabase() {
  if (dbPromise) {
    const db = await dbPromise;
    db.close();
    dbPromise = null;
  }
  return new Promise((resolve, reject) => {
    const request = indexedDB.deleteDatabase(DB_NAME);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error('Feche outras abas deste aplicativo antes de apagar os dados.'));
  });
}
