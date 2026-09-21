/** Exportação e restauração integral dos stores relevantes. */
import { getAllSmall, bulkPut, clearStore } from '../db.js';
import { APP_VERSION, DB_VERSION } from '../config.js';
import { downloadJson } from '../utils.js';

const STORES = [
  'settings','metadata','contests','subjects','topics','lessons','questions','questionAttempts',
  'topicProgress','reviews','studySessions','simulations','tafSessions','schedule','notes',
  'favorites','stats','imports'
];

export async function exportBackup() {
  const data = {};
  for (const store of STORES) data[store] = await getAllSmall(store, 100000);
  const payload = {
    schemaVersion: DB_VERSION,
    appVersion: APP_VERSION,
    exportedAt: new Date().toISOString(),
    data,
  };
  downloadJson(`rumo-aprovacao-backup-${new Date().toISOString().slice(0,10)}.json`, payload);
}

export async function importBackup(payload) {
  if (!payload?.data || !payload.schemaVersion) throw new Error('Arquivo de backup inválido.');
  for (const store of STORES) {
    if (!Array.isArray(payload.data[store])) continue;
    await clearStore(store);
    await bulkPut(store, payload.data[store]);
  }
}
