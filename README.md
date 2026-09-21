# Rumo à Aprovação

Plataforma web leve, multi-edital e instalável como PWA para preparação de concursos públicos.

A versão `1.1.0` é entregue com o concurso **Guarda Civil Municipal de Salvador 2026 - Edital nº 002/2026** pré-carregado, incluindo matriz do conteúdo programático, 116 tópicos/aulas e um banco inicial de 224 questões autorais validadas.

> Importante: questões autorais são identificadas como autorais. O projeto não afirma que elas são questões oficiais da FGV. O edital oficial continua sendo a fonte de verdade curricular.

## 1. Objetivos

O projeto foi feito para permitir que o candidato:

- estude dentro do próprio aplicativo;
- acompanhe todo o conteúdo do edital;
- resolva questões filtradas pelo assunto correto;
- revise erros e tópicos no tempo certo;
- faça simulados com a distribuição real do concurso;
- acompanhe cobertura, acertos e evolução;
- registre horários, sessões de estudo e TAF;
- mantenha histórico local;
- exporte e restaure backup;
- instale o site como PWA;
- importe outros editais em PDF futuramente.

## 2. Filosofia do front-end

A interface é intencionalmente simples e focada em texto.

Não há framework visual pesado, imagens decorativas, vídeos de fundo, animações complexas ou grandes dependências. O objetivo é abrir rápido, ler, responder e sair rapidamente de qualquer tela.

O projeto usa:

- HTML semântico;
- CSS modular;
- JavaScript ES Modules;
- IndexedDB;
- Service Worker;
- Web App Manifest;
- PDF.js carregado sob demanda apenas ao importar edital.

## 3. Privacidade e armazenamento

### Não usa `localStorage`

O projeto não usa `localStorage` ou `sessionStorage` como banco de dados.

Dados persistentes ficam no **IndexedDB**:

- concursos;
- disciplinas;
- tópicos;
- aulas;
- questões;
- tentativas;
- progresso;
- revisões;
- sessões de estudo;
- simulados;
- TAF;
- cronograma;
- anotações;
- favoritos;
- estatísticas;
- configurações.

O **Cache Storage** é usado somente pelo Service Worker para arquivos do PWA.

Limpar os dados do site no navegador pode apagar o IndexedDB. Use o backup JSON periodicamente.

## 4. Estrutura do projeto

```text
.
├── index.html                 Shell principal
├── manifest.webmanifest      Metadados do PWA
├── sw.js                     Service Worker
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .nojekyll
│
├── css/
│   ├── base.css              Variáveis, tipografia e normalização
│   ├── layout.css            Sidebar, topbar, grids e estrutura
│   ├── components.css        Cards, formulários, questões e barras
│   └── responsive.css        Adaptação para celular/tablet
│
├── js/
│   ├── app.js                Inicialização e shell
│   ├── config.js             Versão e constantes
│   ├── db.js                 Única camada de IndexedDB
│   ├── router.js             Roteamento por hash para GitHub Pages
│   ├── state.js              Estado temporário da sessão
│   ├── ui.js                 Toast, diálogo e componentes simples
│   ├── utils.js              Utilidades puras
│   ├── services/
│   │   ├── seed.js           Importa o pacote inicial
│   │   ├── questions.js      Motor de seleção de questões
│   │   ├── performance.js    Estatísticas e domínio
│   │   ├── schedule.js       Planejamento de estudo
│   │   ├── calendar.js       Links do Google Calendar
│   │   ├── pdfImport.js      PDF.js + parser híbrido
│   │   └── backup.js         Exportação/restauração
│   └── views/
│       ├── dashboard.js
│       ├── study.js
│       ├── questions.js
│       ├── reviews.js
│       ├── simulator.js
│       ├── performance.js
│       ├── schedule.js
│       ├── taf.js
│       ├── history.js
│       ├── import.js
│       └── settings.js
│
├── data/
│   ├── contests/             Metadados dos concursos embarcados
│   ├── syllabus/             Matriz exata do conteúdo programático
│   ├── lessons/              Resumos didáticos
│   ├── questions/            Banco autoral inicial
│   └── laws/                 Links de fontes oficiais
│
├── docs/
│   ├── edital-gcm-salvador-2026.pdf
│   └── guia-gcm-salvador-2026.pdf
│
├── assets/icons/             Ícones do PWA
├── tools/                    Scripts de geração e validação
└── tests/                    Testes estáticos simples
```

## 5. IndexedDB

Banco: `rumo-aprovacao-db`

Versão inicial: `1`

### Stores

| Store | Finalidade |
|---|---|
| `settings` | preferências e concurso ativo |
| `metadata` | versão dos dados pré-carregados |
| `contests` | concursos cadastrados/importados |
| `subjects` | disciplinas de cada concurso |
| `topics` | tópicos vinculados ao edital |
| `lessons` | conteúdo de estudo |
| `questions` | questões autorais/externas cadastradas |
| `questionAttempts` | histórico de respostas |
| `topicProgress` | situação e acertos por tópico |
| `reviews` | fila de revisão espaçada |
| `studySessions` | tempo de estudo registrado |
| `simulations` | resultados dos simulados |
| `tafSessions` | registros físicos |
| `schedule` | agenda interna |
| `notes` | anotações |
| `favorites` | favoritos |
| `stats` | estatísticas incrementais |
| `imports` | metadados de importações futuras |

### Índices e performance

O aplicativo evita ler tabelas grandes inteiras sem necessidade.

Exemplos de índices:

- questões por concurso, matéria e tópico;
- tentativas por concurso, questão, matéria, tópico e data;
- tópicos por matéria;
- revisões por vencimento;
- sessões e TAF por data.

`db.js` implementa consultas por cursor com limite. O histórico inicial, por exemplo, traz somente uma janela de registros e não tenta renderizar milhares de itens de uma vez.

As estatísticas principais são incrementais. Ao responder uma questão, o total de acertos/erros é atualizado no store `stats`, evitando recalcular todo o histórico a cada abertura do dashboard.

## 6. Banco de questões

A versão atual contém **224 questões autorais validadas**.

Cada questão guarda:

```json
{
  "id": "...",
  "contestId": "gcm-salvador-2026",
  "subjectId": "rlm",
  "topicIds": ["porcentagem-proporcao"],
  "difficulty": "medium",
  "sourceType": "authorial",
  "stem": "...",
  "options": ["..."],
  "answerIndex": 0,
  "explanation": "..."
}
```

### Regra de seleção

O motor de exercícios faz nesta ordem:

1. filtra o concurso;
2. filtra matéria;
3. filtra tópico, quando escolhido;
4. filtra dificuldade, quando escolhida;
5. reduz questões de metaconteúdo da matriz quando há questões substanciais suficientes;
6. embaralha;
7. seleciona a quantidade pedida.

Isso evita que uma sessão de “Porcentagem” receba uma questão de PA apenas porque ambas pertencem a RLM.

### Como adicionar uma questão

Para o pacote embarcado, adicione a questão ao gerador em `tools/generate_seed_data.py` e rode:

```bash
python tools/generate_seed_data.py
```

Depois rode o validador:

```bash
python tools/validate_project.py
```

Para conteúdo importado dinamicamente, a arquitetura aceita inserção via IndexedDB.

## 7. Conteúdo e fonte de verdade

O arquivo:

```text
data/syllabus/gcm-salvador-2026.json
```

é a matriz curricular da versão inicial.

Cada tópico contém `officialScope`, que preserva o recorte do Anexo I do edital. O nome curto usado na interface é apenas organização didática.

Os resumos do aplicativo são **resumos didáticos**, não reprodução do texto legal.

O edital original foi incluído em:

```text
docs/edital-gcm-salvador-2026.pdf
```

## 8. Simulado da Guarda Salvador 2026

A distribuição implementada é:

- Português: 10;
- RLM: 10;
- Informática: 8;
- Constitucional/Civil: 10;
- Penal/Processual: 7;
- Administração/Políticas Públicas: 5;
- Área de Atuação: 10;
- Legislação: 10.

Total: 70.

O relatório confere simultaneamente:

- Módulo I >= 14/28;
- Módulo II >= 21/42;
- total >= 35/70.

Atingir esses mínimos no aplicativo não é garantia de classificação real.

## 9. PWA

O PWA usa:

- `manifest.webmanifest`;
- `sw.js`;
- ícones 192x192 e 512x512;
- `start_url` relativo;
- `scope` relativo.

Isso permite publicar o aplicativo em subdiretórios do tipo:

```text
https://usuario.github.io/nome-do-repositorio/
```

### Atualização

Altere `APP_VERSION` em `js/config.js`, atualize `CACHE_VERSION` em `sw.js` e registre a mudança no `CHANGELOG.md`.

### Registro robusto no GitHub Pages

O `app.js` localiza o Service Worker a partir de `import.meta.url`, em vez de assumir que o site está publicado na raiz do domínio. Isso evita o erro clássico em URLs como `https://usuario.github.io/repositorio/`.

O `sw.js` também monta suas URLs a partir do próprio escopo e faz o pré-cache arquivo por arquivo. Se um recurso opcional falhar, a instalação inteira do PWA não é cancelada.

Na próxima visita, o navegador buscará os assets atualizados. Em desenvolvimento, se parecer que uma versão antiga ficou presa, use DevTools → Application → Service Workers → Unregister e recarregue.

## 10. Importação híbrida de novos editais

A tela **Novo edital** foi projetada para futuros PDFs.

Fluxo:

```text
PDF
↓
PDF.js extrai texto no navegador
↓
parser local identifica estrutura provável
↓
usuário confere o JSON
↓
endpoint de IA opcional pode refinar
↓
usuário confirma
↓
novo concurso é criado separadamente no IndexedDB
```

### Por que existe revisão humana?

Editais variam muito. Um parser pode interpretar incorretamente uma tabela, peso ou mínimo eliminatório. Por isso a aplicação nunca afirma que a importação automática é infalível.

### PDF.js

PDF.js é carregado **somente quando a tela de importação precisa dele**. Isso mantém o carregamento comum leve.

### IA opcional

Em `Configurações` existe um campo de endpoint proxy.

O navegador envia JSON parecido com:

```json
{
  "task": "analyze-public-exam-notice",
  "instruction": "Retorne JSON...",
  "text": "texto extraído...",
  "localAnalysis": {}
}
```

Não coloque uma API key secreta no código do GitHub Pages.

Se você desejar OpenAI, Gemini ou outro provedor, use um pequeno proxy/serverless que mantenha a credencial no servidor e devolva apenas o JSON analisado.

Sem endpoint, a importação local continua funcionando e o usuário pode editar manualmente o JSON.

## 11. Google Calendar

O modo básico não exige OAuth.

O aplicativo gera URLs de criação de evento do Google Calendar com:

- título;
- início;
- fim;
- descrição.

O usuário confirma o evento no próprio Google Calendar.

Uma integração bidirecional futura exigiria OAuth/backend adequado. Não exponha `client_secret` em um repositório público.

## 12. Hospedar no GitHub Pages

### Opção A - interface do GitHub

1. Crie uma conta em `github.com`.
2. Clique em **New repository**.
3. Escolha um nome, por exemplo `rumo-aprovacao`.
4. Crie o repositório.
5. Envie **o conteúdo desta pasta**, mantendo `index.html` na raiz.
6. Faça o commit.
7. Abra **Settings** do repositório.
8. Abra **Pages**.
9. Em **Build and deployment**, escolha **Deploy from a branch**.
10. Selecione a branch `main` e a pasta `/ (root)`.
11. Salve.
12. Aguarde o endereço aparecer na própria tela do GitHub Pages.

A aplicação usa roteamento por hash (`#/study`, `#/questions` etc.) exatamente para não depender de rewrites de servidor.

### Opção B - Git

```bash
git init
git add .
git commit -m "feat: versão inicial da plataforma"
git branch -M main
git remote add origin https://github.com/SEU-USUARIO/rumo-aprovacao.git
git push -u origin main
```

Depois ative Pages em Settings.

## 13. Instalar como PWA no Android

No Chrome/Edge Android:

1. abra a URL do GitHub Pages;
2. aguarde carregar;
3. toque no menu do navegador;
4. escolha **Instalar app** ou **Adicionar à tela inicial**;
5. confirme.

Em navegadores compatíveis, o próprio aplicativo também mostra o botão **Instalar** quando o evento de instalação estiver disponível.

## 14. Desenvolvimento local

Service Worker, módulos ES e PDF.js funcionam melhor servidos por HTTP em vez de abrir `file://`.

Com Python:

```bash
python -m http.server 8080
```

Abra:

```text
http://localhost:8080
```

Não é necessário Node.js em produção.

## 15. Backup

Em **Configurações**:

- **Exportar JSON** cria cópia de todos os stores;
- **Importar JSON** restaura o conteúdo do arquivo;
- o backup carrega `schemaVersion` e `appVersion`.

Antes de apagar dados do navegador ou trocar de aparelho, exporte o backup.

## 16. TAF

A versão inicial inclui parâmetros do Edital 002/2026 para masculino e feminino e permite registrar:

- corrida;
- barra;
- abdominal remador;
- flexão;
- observação.

O aplicativo mostra se os mínimos cadastrados foram atingidos, mas não prescreve treinamento médico/individualizado.

## 17. Solução de problemas

### GitHub Pages mostra 404

Confirme que `index.html` está na raiz da origem configurada em Pages.

### O PWA não oferece instalação

Verifique:

- acesso por HTTPS ou localhost;
- `manifest.webmanifest` carregando sem 404;
- `sw.js` registrado;
- ícones existentes;
- DevTools → Application → Manifest.

### Estou vendo uma versão antiga

O Service Worker pode ter uma versão em cache. Recarregue; se necessário, desregistre o SW em DevTools e limpe apenas o cache, preservando IndexedDB se não quiser perder progresso.

### IndexedDB não abre

Veja o console do navegador. Navegação privada/restrições corporativas podem impedir armazenamento persistente.

### Meu progresso desapareceu

Possíveis causas:

- limpeza dos dados do site;
- outro navegador/perfil;
- outro domínio/origem;
- restauração incompleta.

Restaure o backup JSON quando disponível.

### Banco grande ficou lento

O código já utiliza índices, limites e cursores. Ao criar novas funcionalidades, evite `getAll()` sem limite e evite renderizar milhares de elementos de uma vez.

## 18. Acessibilidade

O projeto usa:

- HTML semântico;
- `label` em formulários;
- `aria-current` na navegação;
- `aria-live` para avisos;
- link “Pular para o conteúdo”;
- foco visível;
- navegação por teclado;
- contraste claro/escuro;
- informação textual além de cor.

## 19. Licença

Código do aplicativo: MIT, conforme `LICENSE`.

O edital e legislação mantêm seus respectivos regimes jurídicos e fontes originais. Questões autorais do pacote são material criado para esta plataforma.
