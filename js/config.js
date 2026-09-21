/**
 * Configuração central do aplicativo.
 *
 * O aplicativo é multiárea: concursos e disciplinas acadêmicas podem coexistir
 * no mesmo IndexedDB sem misturar progresso. Cada pacote de conteúdo possui
 * sua própria versão para evitar recarregar conteúdos que não mudaram.
 */
export const APP_NAME = 'Rumo à Aprovação';
export const APP_VERSION = '1.5.1';
export const DB_NAME = 'rumo-aprovacao-db';
export const DB_VERSION = 1;

// Mantido por compatibilidade com módulos antigos que ainda esperam um concurso
// inicial. A interface exibe todos os pacotes disponíveis como áreas de estudo.
export const SEED_CONTEST_ID = 'gcm-salvador-2026';

export const SEED_PACKAGES = [
  {
    id: 'gcm-salvador-2026',
    version: '2026.09.21.4',
    format: 'json',
    required: true,
  },
  {
    id: 'paradigmas-python',
    version: '2026.09.21.1',
    format: 'gzip-base64-chunks',
    chunkCount: 10,
    required: false,
  },
  {
    id: 'matematica-logica',
    version: '2026.09.21.1',
    format: 'gzip-base64-chunks',
    chunkCount: 7,
    required: false,
  },
];

// Versão global apenas para diagnóstico/compatibilidade. O controle efetivo de
// atualização é feito individualmente em seedVersion:<id-do-pacote>.
export const SEED_DATA_VERSION = '2026.09.21.6';
export const PDFJS_VERSION = '6.3.289';

export const ROUTES = [
  'dashboard',
  'study',
  'questions',
  'reviews',
  'simulator',
  'performance',
  'schedule',
  'taf',
  'history',
  'import',
  'settings',
  'lesson'
];
