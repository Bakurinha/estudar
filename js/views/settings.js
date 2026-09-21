import { setView, toast } from '../ui.js';
import { get, put, deleteDatabase } from '../db.js';
import { exportBackup, importBackup } from '../services/backup.js';
import { APP_VERSION } from '../config.js';
import { parseJsonSafe } from '../utils.js';

export async function renderSettings(){
  const theme=(await get('settings','theme'))?.value||'auto';
  const endpoint=(await get('settings','aiAnalysisEndpoint'))?.value||'';
  setView(`<section class="view"><header class="page-header"><h1>Configurações</h1><p class="muted">Versão ${APP_VERSION}</p></header>
  <div class="grid grid--2"><article class="card"><h2 class="card__title">Aparência</h2><label class="field"><span>Tema</span><select id="theme" class="select"><option value="auto" ${theme==='auto'?'selected':''}>Automático</option><option value="light" ${theme==='light'?'selected':''}>Claro</option><option value="dark" ${theme==='dark'?'selected':''}>Escuro</option></select></label><button id="save-theme" class="button" style="margin-top:10px">Salvar</button></article>
  <article class="card"><h2 class="card__title">IA opcional para editais</h2><label class="field"><span>Endpoint proxy</span><input id="ai-endpoint" class="input" placeholder="https://seu-endpoint.exemplo/analisar" value="${endpoint}"></label><p class="small muted">Não coloque client secret no repositório. O endpoint deve cuidar da autenticação no servidor.</p><button id="save-endpoint" class="button">Salvar</button></article></div>
  <article class="card" style="margin-top:14px"><h2 class="card__title">Backup</h2><div class="row"><button id="export-backup" class="button">Exportar JSON</button><label class="button" for="import-file">Importar JSON</label><input id="import-file" class="visually-hidden" type="file" accept="application/json"></div><p class="small muted">Como o progresso fica no IndexedDB, limpar dados do navegador pode apagá-lo. Faça backup periódico.</p></article>
  <article class="card" style="margin-top:14px"><h2 class="card__title">Privacidade e dados</h2><p>O progresso, histórico, respostas, cronograma e TAF são armazenados no IndexedDB deste navegador. O GitHub Pages hospeda os arquivos públicos do aplicativo; não coloque informações sensíveis no repositório.</p><button id="delete-data" class="button button--danger">Apagar todos os dados locais</button></article></section>`);
  document.querySelector('#save-theme').addEventListener('click',async()=>{const value=document.querySelector('#theme').value;await put('settings',{key:'theme',value});applyTheme(value);toast('Tema salvo.');});
  document.querySelector('#save-endpoint').addEventListener('click',async()=>{await put('settings',{key:'aiAnalysisEndpoint',value:document.querySelector('#ai-endpoint').value.trim()});toast('Endpoint salvo.');});
  document.querySelector('#export-backup').addEventListener('click',exportBackup);
  document.querySelector('#import-file').addEventListener('change',async e=>{const file=e.target.files[0];if(!file)return;const payload=parseJsonSafe(await file.text());try{await importBackup(payload);toast('Backup importado. Recarregando…');setTimeout(()=>location.reload(),700);}catch(err){toast(err.message,'danger');}});
  document.querySelector('#delete-data').addEventListener('click',async()=>{if(!confirm('Apagar TODO o progresso local deste aplicativo? Faça backup antes.'))return;try{await deleteDatabase();location.reload();}catch(err){toast(err.message,'danger');}});
}

export function applyTheme(theme){
  const dark=theme==='dark'||(theme==='auto'&&matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.dataset.theme=dark?'dark':'light';
}
