/** Funções visuais compartilhadas. */
import { qs } from './utils.js';

export function toast(message, type = 'info') {
  const region = qs('#toast-region');
  const node = document.createElement('div');
  node.className = `toast toast--${type}`;
  node.textContent = message;
  region.appendChild(node);
  setTimeout(() => node.remove(), 3800);
}

export function setView(html) {
  const view = qs('#route-view');
  view.innerHTML = html;
  qs('#main-content')?.focus({preventScroll:true});
}

export function openDialog(html) {
  const dialog = qs('#global-dialog');
  dialog.innerHTML = html;
  dialog.showModal();
  dialog.querySelectorAll('[data-close-dialog]').forEach(btn => btn.addEventListener('click',()=>dialog.close()));
  return dialog;
}

export function progressBar(value, label = '') {
  const safe = Math.max(0,Math.min(100,Number(value)||0));
  return `<div class="progress" role="progressbar" aria-label="${label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${safe}"><span style="width:${safe}%"></span></div>`;
}
