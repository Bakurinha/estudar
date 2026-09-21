/**
 * Configuração central do aplicativo.
 *
 * O aplicativo é multiárea: concursos e disciplinas acadêmicas podem coexistir
 * no mesmo IndexedDB sem misturar progresso. Cada pacote de conteúdo possui
 * sua própria versão para evitar recarregar milhões de caracteres quando só um
 * curso novo é adicionado.
 */
export const APP_NAME = 'Rumo à Aprovação';
export const APP_VERSION = '1.5.0';
export const DB_NAME = 'rumo-aprovacao-db';
export const DB_VERSION = 1;

// Mantido por compatibilidade com módulos antigos que ainda esperam um concurso
// inicial. O seletor da interface passa a exibir todos os pacotes abaixo.
export const SEED_CONTEST_ID = 'gcm-salvador-2026';

export const SEED_PACKAGES = [
  {
    id: 'gcm-salvador-2026',
    version: '2026.09.21.4',
    format: 'json',
  },
  {
    id: 'paradigmas-python',
    version: '2026.09.21.1',
    format: 'gzip-base64-chunks',
    chunkCount: 8,
  },
  {
    id: 'matematica-logica',
    version: '2026.09.21.1',
    format: 'gzip-base64-chunks',
    chunkCount: 12,
  },
];

// Versão global apenas para diagnóstico/compatibilidade. O controle efetivo de
// atualização é feito individualmente em seedVersion:<id-do-pacote>.
export const SEED_DATA_VERSION = '2026.09.21.5';
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
