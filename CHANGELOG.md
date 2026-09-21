# Changelog

Todas as alterações relevantes deste projeto são registradas aqui.

O formato segue a ideia do [Keep a Changelog](https://keepachangelog.com/pt-BR/) e o projeto utiliza versionamento semântico.


## [1.6.0] - 2026-09-21

### Alterado

- aprofundamento intensivo dos subtópicos dos dois cursos acadêmicos sem mudar módulos, tópicos, IDs ou questões;
- cada subtópico agora possui páginas próprias de fundamentos, aplicação, diferenças/armadilhas e revisão ativa;
- nomes dos arquivos-fonte foram removidos da interface; somente os nomes dos módulos são exibidos;
- Paradigmas/Python passou a 510 páginas internas e aproximadamente 904.614 caracteres didáticos;
- Matemática e Lógica passou a 816 páginas internas e aproximadamente 1.397.882 caracteres didáticos.

### Mantido

- escopo original do projeto e dos cursos;
- 150 questões de Python e 150 de Matemática/Lógica;
- IDs de módulos, tópicos e questões para preservar o progresso no IndexedDB.

## [1.5.1] - 2026-09-21

### Corrigido

- corrigido o erro de inicialização `Failed to fetch` no GitHub Pages;
- corrigida a quantidade de chunks do pacote **Paradigmas de Linguagens de Programação em Python** de 8 para 10;
- corrigida a quantidade de chunks do pacote **Matemática e Lógica** de 12 para 7;
- cursos acadêmicos deixaram de ser dependências obrigatórias do boot: falha em um pacote opcional não derruba mais todo o aplicativo;
- erros de pacote agora são registrados individualmente em `metadata`;
- mensagens de erro de rede, HTTP e descompressão ficaram mais específicas;
- Service Worker atualizado para evitar mistura entre `config.js` novo e JavaScript/dados antigos em cache.

### Adicionado

- publicação dos 7 chunks completos de Matemática e Lógica;
- carregamento versionado dos pacotes usando query string de versão;
- validação básica da estrutura interna de cada pacote antes da gravação no IndexedDB;
- diagnóstico do carregamento de cada área de estudo;
- aviso não bloqueante quando somente um curso opcional não pode ser atualizado.

### Alterado

- Service Worker elevado para cache `v1.5.1`;
- JavaScript, JSON, manifesto e arquivos `.b64` agora usam estratégia **network-first**;
- CSS e ícones continuam usando cache rápido com atualização em segundo plano;
- seletor superior passou de “Concurso ativo” para **“Área de estudo”**;
- branding alterado para “Plataforma de estudos”;
- Dashboard passou a distinguir concurso de curso acadêmico;
- tela Estudar passou a exibir rastreabilidade do PDF, subtópicos e quantidade de atividades do material;
- tela Exercícios exibe PDF/módulo/páginas utilizados como fonte-base nas questões acadêmicas;
- cursos acadêmicos receberam **Treino misto** no lugar de um falso simulado oficial;
- TAF informa explicitamente quando não se aplica a uma área acadêmica.

### Performance

- chunks acadêmicos são baixados sequencialmente para reduzir pico de memória/conexões em celulares;
- pacotes já importados não são recarregados quando sua versão não mudou;
- um pacote atualizado pode ser reimportado sem exigir reconstrução de todas as outras áreas.

## [1.5.0] - 2026-09-21

### Adicionado

- arquitetura multiárea para concursos e disciplinas acadêmicas no mesmo IndexedDB;
- área **Paradigmas de Linguagens de Programação em Python**;
- 4 PDFs de Python organizados na sequência do material-fonte;
- 15 tópicos principais de Python com subtópicos e páginas internas;
- 150 questões autorais baseadas nos PDFs de Python;
- 46 exercícios/atividades do material de Python identificados para uso nas aulas;
- área **Matemática e Lógica**;
- 7 PDFs de Matemática/Lógica organizados na sequência do material-fonte;
- 24 tópicos principais de Matemática/Lógica com subtópicos e páginas internas;
- 150 questões autorais baseadas nos PDFs de Matemática/Lógica;
- 122 exercícios/atividades do material de Matemática/Lógica identificados;
- metadados de rastreabilidade por documento, módulo e páginas;
- pacotes acadêmicos compactados em gzip + Base64 e divididos em chunks;
- versão própria para cada pacote de conteúdo.

### Validação

- os 11 PDFs utilizados foram comparados e não apresentaram duplicação de arquivo por hash;
- banco de Python validado com 150 IDs e enunciados únicos;
- banco de Matemática/Lógica validado com 150 IDs e enunciados únicos;
- todas as questões acadêmicas possuem cinco alternativas, gabarito válido, explicação e vínculo a tópico existente;
- distribuição original do gabarito de cada banco foi balanceada em 30 respostas por posição A–E;
- questões continuam tendo alternativas embaralhadas na camada visual sem mudar o gabarito real.

## [1.4.0] - 2026-09-21

### Adicionado

- aulas da GCM transformadas em apostilas paginadas;
- índice interno de páginas;
- navegação anterior/próxima;
- indicação explícita do recorte do edital que fundamenta cada página;
- validações mínimas de volume e densidade por tópico.

### Conteúdo

- 116 tópicos da GCM convertidos em 116 apostilas;
- 928 páginas internas de estudo;
- aproximadamente 3,7 milhões de caracteres no banco de aulas expandido.

## [1.3.0] - 2026-09-21

### Adicionado

- aprofundamento específico em todos os 116 tópicos da GCM;
- validação de pontos específicos por tópico.

### Banco de questões

- banco da GCM expandido para 2.650 questões autorais;
- verificação de alternativas duplicadas, gabaritos, explicações e vínculo matéria/tópico.

## [1.2.0] - 2026-09-21

### Alterado

- seleção de exercícios passou a considerar histórico de respostas;
- questões inéditas e erros anteriores receberam prioridade;
- questões vistas recentemente receberam menor prioridade;
- alternativas passaram a ser embaralhadas a cada exibição preservando o gabarito original.

## [1.1.0] - 2026-09-21

### Alterado

- front-end remodelado para leitura rápida e menor densidade visual;
- menu lateral desktop reorganizado por grupos;
- menu lateral móvel transformado em drawer com fechamento explícito;
- adicionada barra de navegação rápida inferior no celular;
- botões de exercícios e questões receberam áreas de toque maiores;
- layout de cards, formulários, diálogos e leitura ajustado para telas pequenas;
- dashboard ganhou atalhos diretos para estudo, exercícios, revisões e agenda;
- indicador discreto de conectividade adicionado ao menu.

### Corrigido

- registro do `sw.js` passou a ser resolvido a partir de `import.meta.url`, compatível com GitHub Pages em subdiretórios;
- instalação do Service Worker deixou de depender de `cache.addAll()`, que podia cancelar todo o PWA quando um único arquivo falhava;
- URLs do cache passaram a ser montadas a partir do escopo real do Service Worker;
- navegação HTML offline recebeu fallback para o `index.html`.

### Performance

- cache separado entre shell estático e recursos de runtime;
- estratégia network-first para navegação e stale-while-revalidate para assets locais;
- interface móvel mantém apenas navegação essencial sempre visível.

## [1.0.0] - 2026-09-21

### Adicionado

- arquitetura multi-edital;
- concurso Guarda Civil Municipal de Salvador 2026 pré-carregado;
- matriz curricular baseada no Anexo I do Edital nº 002/2026;
- 116 tópicos/aulas iniciais;
- banco inicial autoral;
- filtro de exercícios por matéria, tópico, dificuldade e erros;
- seleção aleatória após filtragem curricular;
- simulado de 70 questões com distribuição oficial;
- validação dos mínimos do Módulo I, Módulo II e total;
- IndexedDB como armazenamento persistente;
- estatísticas incrementais;
- acompanhamento de cobertura, acerto, constância e domínio;
- barra de nível de preparação;
- revisão espaçada inicial de 1, 7 e 30 dias;
- caderno de anotações por tópico;
- cronômetro de estudo;
- registro de sessões;
- agenda interna e gerador de blocos de estudo;
- links de criação de eventos no Google Calendar;
- módulo de TAF masculino/feminino;
- histórico de estudo, questões, simulados e TAF;
- exportação e importação de backup JSON;
- modo claro, escuro e automático;
- PWA e Service Worker;
- menu lateral adaptativo;
- roteamento por hash compatível com GitHub Pages;
- importação local de edital com PDF.js;
- parser preliminar de novos editais;
- revisão manual da estrutura antes da importação;
- endpoint de IA opcional sem credencial embutida no repositório;
- README completo;
- geradores de dados e validadores do projeto.

### Segurança e privacidade

- nenhuma utilização de `localStorage` como persistência;
- nenhuma API key incluída no código;
- integração Google Calendar básica sem OAuth;
- aviso explícito antes de apagar o banco local.
