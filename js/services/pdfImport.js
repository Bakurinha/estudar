/**
 * Importação híbrida de edital.
 *
 * 1) PDF.js extrai o texto no próprio navegador.
 * 2) Heurísticas locais montam uma primeira estrutura.
 * 3) O usuário revisa o JSON antes de importar.
 * 4) Opcionalmente, um endpoint de IA configurado pelo usuário pode melhorar a análise.
 *    Nenhuma chave secreta é colocada no repositório público.
 */
import { PDFJS_VERSION } from '../config.js';
import { uid } from '../utils.js';

export async function extractPdfText(file, onProgress = () => {}) {
  const pdfjs = await import(`https://cdn.jsdelivr.net/npm/pdfjs-dist@${PDFJS_VERSION}/build/pdf.mjs`);
  pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${PDFJS_VERSION}/build/pdf.worker.mjs`;
  const bytes = new Uint8Array(await file.arrayBuffer());
  const pdf = await pdfjs.getDocument({ data: bytes }).promise;
  const pages = [];
  for (let pageNo = 1; pageNo <= pdf.numPages; pageNo += 1) {
    const page = await pdf.getPage(pageNo);
    const content = await page.getTextContent();
    pages.push(content.items.map(item => item.str).join(' '));
    onProgress(pageNo, pdf.numPages);
  }
  return pages.join('\n\n');
}

export function analyzeNoticeText(text) {
  const normalized = text.replace(/\s+/g, ' ').trim();
  const dateMatches = [...normalized.matchAll(/\b\d{2}\/\d{2}\/\d{4}\b/g)].map(m => m[0]);
  const questionMatch = normalized.match(/(\d{1,3})\s*\(?[^)]*\)?\s*questões/i);
  const organizer = /FGV|Fundação Getulio Vargas/i.test(normalized) ? 'FGV' : '';

  const contentStart = normalized.search(/CONTE[ÚU]DO PROGRAM[ÁA]TICO/i);
  const contentText = contentStart >= 0 ? normalized.slice(contentStart) : normalized;
  const subjectCandidates = [...contentText.matchAll(/(?:^|[.;])\s*([A-ZÁÉÍÓÚÃÕÇ][A-ZÁÉÍÓÚÃÕÇ\s\-/]{5,60})(?=\s*[:\-])/g)]
    .map(m => m[1].trim())
    .filter((value, index, arr) => arr.indexOf(value) === index)
    .slice(0, 30);

  return {
    id: uid('contest'),
    name: 'Novo concurso importado',
    organizer,
    examDate: '',
    detectedDates: dateMatches.slice(0, 30),
    totalQuestions: questionMatch ? Number(questionMatch[1]) : null,
    modules: [],
    subjects: subjectCandidates.map((name, index) => ({
      id: `subject-${index + 1}`,
      name: name.replace(/\s+/g, ' '),
      module: 1,
      questions: 0,
      topics: [],
    })),
    analysisStatus: 'needs-review',
    sourceNote: 'Estrutura preliminar gerada por heurísticas locais. Confira o PDF antes de confirmar.',
  };
}

export async function analyzeWithOptionalEndpoint(endpoint, text, localAnalysis) {
  if (!endpoint) return localAnalysis;
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      task: 'analyze-public-exam-notice',
      instruction: 'Retorne JSON. Preserve somente o que está explicitamente no edital e marque incertezas.',
      text,
      localAnalysis,
    }),
  });
  if (!response.ok) throw new Error(`Endpoint de IA respondeu ${response.status}.`);
  return response.json();
}
