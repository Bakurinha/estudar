# Rumo à Aprovação

Plataforma web leve de estudos, instalável como PWA e hospedável diretamente no GitHub Pages.

A versão **1.5.1** é multiárea: concursos e conteúdos acadêmicos convivem no mesmo aplicativo sem misturar progresso, exercícios ou histórico.

Áreas embarcadas atualmente:

- **Guarda Civil Municipal de Salvador 2026** — preparação por edital, TAF, simulados e banco expandido de questões;
- **Paradigmas de Linguagens de Programação em Python** — conteúdo derivado dos 4 PDFs fornecidos, organizado em 15 módulos/tópicos, 150 questões autorais baseadas no material e 46 exercícios/atividades localizados nos PDFs;
- **Matemática e Lógica** — conteúdo derivado dos 7 PDFs fornecidos, organizado em 24 módulos/tópicos, 150 questões autorais baseadas no material e 122 exercícios/atividades localizados nos PDFs.

> Questões criadas pelo projeto são identificadas como autorais. Nos cursos acadêmicos, a interface informa o PDF, módulo e páginas usados como fonte-base quando esses metadados estão disponíveis.

## 1. Objetivo

O aplicativo foi construído para ser uma ferramenta diária de estudo, não apenas uma checklist. Ele permite:

- estudar teoria dentro do navegador;
- navegar por módulos, tópicos, subtópicos e páginas internas;
- resolver questões aleatórias filtradas pelo assunto correto;
- revisar erros e conteúdos vencidos;
- acompanhar percentual de acerto, cobertura e evolução;
- registrar sessões e histórico;
- gerar cronograma e eventos para o Google Calendar;
- fazer simulados oficiais quando o edital possui distribuição de questões;
- fazer treino misto nos cursos acadêmicos;
- acompanhar TAF quando a área de estudo possui teste físico;
- exportar e restaurar backup;
- instalar o site como PWA no celular e no computador;
- importar novos editais em PDF futuramente.

## 2. Filosofia do front-end

A interface é propositalmente leve e orientada a texto.

Não há framework visual pesado, vídeos de fundo ou animações desnecessárias. A prioridade é:

1. abrir rápido;
2. encontrar o assunto rapidamente;
3. ler com conforto;
4. responder exercícios sem recarregar a página;
5. consultar histórico e desempenho sem travamentos.

Tecnologias principais:

- HTML semântico;
- CSS modular e responsivo;
- JavaScript ES Modules;
- IndexedDB;
- Service Worker;
- Web App Manifest;
- PDF.js carregado sob demanda para importação de editais.

## 3. Persistência: IndexedDB

O projeto **não utiliza `localStorage` ou `sessionStorage` como banco persistente**.

Dados do usuário permanecem no IndexedDB, incluindo:

- área de estudo ativa;
- progresso;
- respostas e tentativas;
- revisões;
- simulados;
- sessões de estudo;
- TAF;
- cronograma;
- anotações;
- favoritos;
- estatísticas;
- configurações.

O Cache Storage é usado pelo Service Worker apenas para o PWA e recursos da aplicação.

> Limpar os dados do site pelo navegador pode apagar o IndexedDB. Exporte um backup antes de limpar os dados do domínio.

## 4. Estrutura multiárea

Internamente, todas as áreas usam a mesma estrutura:

```text
Área de estudo
└── disciplinas / unidades
    └── tópicos
        ├── subtópicos
        ├── páginas de estudo
        ├── exercícios
        └── progresso
```

O nome interno `contestId` ainda aparece em algumas estruturas do código por compatibilidade com versões antigas, mas agora representa a **área de estudo ativa**, que pode ser um concurso ou um curso acadêmico.

Cada área mantém seus próprios IDs, portanto responder questões de Matemática e Lógica não altera estatísticas da GCM ou de Python.

## 5. Pacotes acadêmicos compactados

Python e Matemática/Lógica são distribuídos como pacotes `gzip` codificados em Base64 e divididos em pequenos chunks dentro de:

```text
data/packages/
```

Quantidade atual:

```text
paradigmas-python.part-01.b64 ... part-10.b64
matematica-logica.part-01.b64 ... part-07.b64
```

O navegador baixa as partes na primeira importação da versão do pacote, descompacta o JSON e persiste o conteúdo no IndexedDB.

Isso evita manter grandes bancos textuais permanentemente carregados na memória em cada navegação.

Cada pacote possui versão própria em `js/config.js`. Dessa forma uma atualização de Matemática não exige reimportar todo o banco da GCM.

## 6. Falhas de pacote não derrubam o aplicativo

Desde a versão 1.5.1, cursos acadêmicos são pacotes opcionais durante a inicialização.

Se um chunk estiver temporariamente ausente, houver erro de rede ou o pacote estiver corrompido:

- o erro é registrado em `metadata`;
- a área defeituosa não é atualizada;
- o restante da aplicação continua abrindo;
- a GCM e áreas já importadas continuam acessíveis.

Somente um pacote explicitamente marcado como obrigatório pode interromper o boot.

Essa mudança corrige o problema em que o Pages mostrava:

```text
Não foi possível iniciar o aplicativo.
Failed to fetch
```

quando um pacote acadêmico incompleto estava sendo publicado.

## 7. Service Worker e atualização

O Service Worker usa a versão de cache `v1.5.1`.

Estratégia atual:

- navegação HTML: **network-first**, com cache como fallback;
- JavaScript, JSON, `.b64` e manifesto: **network-first**;
- CSS e ícones: cache rápido com atualização em segundo plano.

Arquivos que definem código ou conteúdo precisam priorizar a rede para impedir combinações incompatíveis do tipo:

```text
config.js novo + seed.js antigo
```

Caches antigos `rumo-aprovacao-*` são removidos quando o novo Service Worker é ativado.

O usuário não precisa limpar o IndexedDB para atualizar o aplicativo.

## 8. Conteúdo acadêmico e rastreabilidade

### Paradigmas de Linguagens de Programação em Python

Os módulos seguem a ordem dos PDFs enviados:

1. classificação, critérios, paradigmas e implementação de linguagens;
2. fundamentos de Python;
3. decisão, repetição, funções, bibliotecas, exceções e eventos;
4. programação orientada a objetos em Python.

Os 4 documentos foram desdobrados em **15 tópicos principais**, cada um podendo conter subtópicos e várias páginas internas.

O banco acadêmico possui **150 questões autorais baseadas nos PDFs**, com distribuição balanceada do gabarito. Além disso, **46 exercícios/atividades do próprio material** foram identificados para referência e desenvolvimento das aulas.

### Matemática e Lógica

A progressão segue os PDFs enviados:

1. teoria dos conjuntos e princípios de contagem;
2. gráficos e interpretação gráfica;
3. funções reais;
4. cálculo proposicional;
5. cálculo de predicados;
6. métodos de demonstração e indução;
7. material Praticando, com estudos de caso e desafios.

Os 7 documentos foram desdobrados em **24 tópicos principais**.

O banco possui **150 questões autorais baseadas nos PDFs**, também com gabaritos balanceados. **122 exercícios/atividades do próprio material** foram identificados.

### Conteúdo complementar

Quando a aula acrescenta explicação didática externa ou uma reformulação para facilitar entendimento, esse conteúdo deve servir para explicar o tópico-fonte e não deve ser apresentado como reprodução literal do PDF.

## 9. Exercícios

O motor segue esta ordem:

1. identifica a área ativa;
2. filtra a disciplina/unidade;
3. filtra o tópico;
4. aplica dificuldade, quando selecionada;
5. consulta histórico;
6. prioriza questões inéditas e erros antigos;
7. reduz repetição de questões vistas recentemente;
8. embaralha a seleção;
9. embaralha visualmente as alternativas sem alterar o gabarito real.

Nos cursos acadêmicos, cada questão pode mostrar:

```text
Fonte-base: nome-do-pdf · módulo X · páginas Y-Z
```

Isso permite conferir de onde veio o tema cobrado.

## 10. GCM Salvador 2026

A área da GCM continua separada dos cursos acadêmicos e mantém recursos específicos de concurso:

- edital estruturado;
- aulas extensas e paginadas;
- banco expandido de questões;
- revisão;
- simulado oficial de 70 questões;
- verificação dos mínimos por módulo;
- agenda do concurso;
- TAF masculino e feminino;
- acompanhamento de desempenho.

O simulado respeita a distribuição cadastrada para o edital ativo.

## 11. Simulados acadêmicos

Cursos sem uma prova oficial configurada não fingem possuir um simulado oficial.

Neles, a tela **Simulados** vira **Treino misto**:

- 30 questões aleatórias;
- 60 minutos sugeridos;
- mistura de diferentes módulos;
- relatório de acertos total e por unidade;
- histórico salvo separadamente.

O resultado é indicador de retenção e não nota acadêmica oficial.

## 12. TAF

A tela de TAF só apresenta métricas físicas para áreas que possuem regras de TAF cadastradas.

Em Python e Matemática/Lógica a interface informa explicitamente que o recurso não se aplica àquela área acadêmica.

## 13. Estrutura resumida do projeto

```text
.
├── index.html
├── manifest.webmanifest
├── sw.js
├── README.md
├── CHANGELOG.md
├── css/
├── js/
│   ├── app.js
│   ├── config.js
│   ├── db.js
│   ├── services/
│   └── views/
├── data/
│   ├── contests/
│   ├── syllabus/
│   ├── lessons/
│   ├── questions/
│   ├── packages/
│   └── laws/
├── docs/
├── assets/
└── tools/
```

## 14. GitHub Pages

O projeto foi pensado para URLs em subdiretório, por exemplo:

```text
https://bakurinha.github.io/estudar/
```

Para publicar em outro repositório:

1. coloque `index.html`, `sw.js` e `manifest.webmanifest` na raiz;
2. envie todas as pastas mantendo os caminhos relativos;
3. abra **Settings → Pages**;
4. escolha **Deploy from a branch**;
5. selecione `main` e `/ (root)`;
6. aguarde o deploy terminar.

O roteamento usa hash (`#/study`, `#/questions` etc.), portanto não necessita configuração de rewrite no servidor.

## 15. Instalação como PWA

No Android com Chrome/Edge:

1. abra a URL do Pages;
2. aguarde a versão atual carregar;
3. use **Instalar app** ou **Adicionar à tela inicial**;
4. confirme.

Quando uma versão nova do Service Worker é detectada, o aplicativo pode mostrar **Atualização disponível**. Prefira usar **Atualizar agora** em vez de limpar os dados do site.

## 16. Se aparecer uma versão antiga

Faça nesta ordem:

1. feche totalmente a aba/PWA e abra novamente;
2. aguarde alguns segundos com internet;
3. aceite **Atualizar agora**, se aparecer;
4. recarregue a página uma vez.

Evite apagar dados do site, pois isso pode remover seu IndexedDB.

Se for indispensável limpar dados, exporte o backup primeiro.

## 17. Importação híbrida de editais

A tela **Novo edital** usa um fluxo híbrido:

```text
PDF
↓
PDF.js extrai o texto no navegador
↓
parser local identifica uma estrutura provável
↓
usuário confere
↓
IA opcional pode refinar a análise
↓
usuário confirma
↓
nova área é salva no IndexedDB
```

O parser nunca deve ser considerado infalível para pesos, mínimos eliminatórios ou cronogramas; a revisão humana continua obrigatória.

Não coloque API keys secretas em um repositório GitHub Pages público.

## 18. Google Calendar

O modo básico gera um link para criação de evento contendo título, início, fim e descrição. O usuário confirma o evento no Google Calendar.

Uma sincronização bidirecional completa exigiria OAuth e um backend adequado.

## 19. Backup

Em **Configurações**:

- exporte o banco para JSON;
- restaure um backup JSON;
- mantenha uma cópia antes de trocar de aparelho ou limpar dados do navegador.

O backup deve preservar progresso, histórico, anotações, cronograma e configurações do IndexedDB.

## 20. Desenvolvimento local

Não abra o projeto diretamente por `file://`.

Use um servidor HTTP simples, por exemplo:

```bash
python -m http.server 8080
```

Depois acesse:

```text
http://localhost:8080
```

## 21. Versionamento

A versão da aplicação fica em:

```text
js/config.js
```

O cache do PWA fica em:

```text
sw.js
```

Ao alterar comportamento ou conteúdo relevante:

1. atualize a versão adequada;
2. registre a mudança no `CHANGELOG.md`;
3. valide os pacotes;
4. confirme o deploy do Pages.

## 22. Privacidade

O GitHub Pages hospeda os arquivos públicos da aplicação. Progresso e histórico do usuário permanecem no IndexedDB do navegador, salvo quando algum recurso externo for explicitamente acionado.

Nenhuma credencial privada deve ser inserida diretamente no repositório público.


## Conteúdo acadêmico aprofundado (v1.6.0)

A versão 1.6.0 preserva integralmente a arquitetura multiárea e os IDs existentes. A mudança é de profundidade, não de escopo.

- Paradigmas/Python: 90 subtópicos, 510 páginas internas, cerca de 904.614 caracteres didáticos e 150 questões.
- Matemática e Lógica: 144 subtópicos, 816 páginas internas, cerca de 1.397.882 caracteres didáticos e 150 questões.
- Cada subtópico possui fundamentos, aplicação, comparações, armadilhas e revisão ativa.
- Nomes de arquivos-fonte não são exibidos; a interface apresenta somente módulos, tópicos e subtópicos.
- O conteúdo complementar permanece preso aos conceitos já previstos nos materiais-base.
