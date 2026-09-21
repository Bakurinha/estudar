from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rep(path, old, new, count=1):
    p = ROOT / path
    text = p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'anchor missing in {path}: {old[:100]}')
    p.write_text(text.replace(old, new, count), encoding='utf-8')

# Páginas práticas devem usar exercícios como prática, não tratar enunciado longo como teoria.
rep(
    'js/services/learning.js',
    '  let recallPrompts = claims.map((claim, index) => ({',
    '  let recallPrompts = practicePage ? [] : claims.map((claim, index) => ({',
)

# IDs estáveis em páginas acadêmicas legadas sem page.id.
rep(
    'js/views/study.js',
    "  const requestedPage = Number(routeQuery?.get?.('page') || 0);\n\n  const completedPages",
    "  const requestedPage = Number(routeQuery?.get?.('page') || 0);\n  const pageStateId = (page, index) => page?.id || `${topic.id}-page-${String(index + 1).padStart(3, '0')}`;\n\n  const completedPages",
)
rep(
    'js/views/study.js',
    "          ${pages.map((page, index) => {\n            const learned = learningStates.get(page.id)?.completedAt;",
    "          ${pages.map((page, index) => {\n            const learned = learningStates.get(pageStateId(page, index))?.completedAt;",
)
rep(
    'js/views/study.js',
    "      const page = pages[activePage];\n      const learningState = learningStates.get(page.id) || null;",
    "      const page = pages[activePage];\n      const pageId = pageStateId(page, activePage);\n      const learningState = learningStates.get(pageId) || null;",
)
rep('js/views/study.js', '          pageId: page.id,', '          pageId,')
rep(
    'js/views/study.js',
    '          previousState: learningStates.get(page.id) || null,',
    '          previousState: learningStates.get(pageId) || null,',
)
rep('js/views/study.js', '        learningStates.set(page.id, saved);', '        learningStates.set(pageId, saved);')

# Separe leitura do bloco de recuperação para poder ocultar o texto enquanto responde.
rep(
    'js/views/study.js',
    '          <div id="learning-content" ${forceRetrieval ? \'hidden\' : \'\'}>\n            <div class="official-scope"',
    '          <div id="learning-content" ${forceRetrieval ? \'hidden\' : \'\'}>\n            <div id="learning-reading-material">\n            <div class="official-scope"',
)
rep(
    'js/views/study.js',
    '            <section class="card" style="margin-top:24px;border-style:dashed">\n              <h3>3. Recuperação ativa — agora pare de olhar o texto</h3>',
    '            </div>\n\n            <section class="card" style="margin-top:24px;border-style:dashed">\n              <h3>3. Recuperação ativa — agora pare de olhar o texto</h3>\n              <button id="toggle-learning-reading" class="button" style="margin-top:8px">Ocultar leitura enquanto respondo</button>',
)

# O diagnóstico realmente precisa existir antes de revelar o conteúdo em primeira leitura/revisão.
rep(
    'js/views/study.js',
    "      host.querySelector('#open-learning-content')?.addEventListener('click', () => {\n        if (contentHost) contentHost.hidden = false;\n        contentHost?.scrollIntoView({ behavior: 'smooth', block: 'start' });\n      });",
    "      host.querySelector('#open-learning-content')?.addEventListener('click', () => {\n        if (forceRetrieval) {\n          const diagnostic = host.querySelector('#learning-diagnostic')?.value?.trim() || '';\n          if (diagnostic.length < 10) {\n            toast('Escreva primeiro uma tentativa curta de memória antes de abrir o conteúdo.', 'warning');\n            return;\n          }\n        }\n        if (contentHost) contentHost.hidden = false;\n        contentHost?.scrollIntoView({ behavior: 'smooth', block: 'start' });\n      });",
)

rep(
    'js/views/study.js',
    "      host.querySelectorAll('[data-reveal-criterion]').forEach(button => {",
    "      const readingMaterial = host.querySelector('#learning-reading-material');\n      const readingToggle = host.querySelector('#toggle-learning-reading');\n      readingToggle?.addEventListener('click', () => {\n        if (!readingMaterial) return;\n        readingMaterial.hidden = !readingMaterial.hidden;\n        readingToggle.textContent = readingMaterial.hidden\n          ? 'Mostrar leitura para conferir'\n          : 'Ocultar leitura enquanto respondo';\n      });\n\n      host.querySelectorAll('[data-reveal-criterion]').forEach(button => {",
)

# Atualiza versões do shell; dados disciplinares continuam nas mesmas versões.
rep('js/config.js', "export const APP_VERSION = '1.9.0';", "export const APP_VERSION = '1.9.1';")
rep('sw.js', "const CACHE_VERSION = 'v1.9.0';", "const CACHE_VERSION = 'v1.9.1';")

# Registra hotfix no changelog, se existir.
changelog = ROOT / 'CHANGELOG.md'
if changelog.exists():
    text = changelog.read_text(encoding='utf-8')
    marker = '## 1.9.0'
    entry = "## 1.9.1 — Recuperação sem olhar e IDs estáveis\n\n- Páginas acadêmicas sem ID passam a usar identificador estável por tópico e posição.\n- Páginas práticas sempre usam tentativa independente, sem transformar enunciado em resposta teórica.\n- Em primeira leitura/revisão, a tentativa inicial é exigida antes de abrir o texto.\n- A leitura pode ser ocultada durante as respostas de recuperação.\n\n"
    if '## 1.9.1' not in text and marker in text:
        changelog.write_text(text.replace(marker, entry + marker, 1), encoding='utf-8')

print('learning v1.9.1 hotfix applied')
