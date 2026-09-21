# Changelog

Todas as alterações relevantes deste projeto serão documentadas neste arquivo.

O formato segue a ideia do [Keep a Changelog](https://keepachangelog.com/pt-BR/) e o projeto usa versionamento semântico.


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

- registro do `sw.js` agora é resolvido a partir de `import.meta.url`, compatível com GitHub Pages em subdiretórios;
- instalação do Service Worker não depende mais de `cache.addAll()`, que podia cancelar todo o PWA quando um único arquivo falhava;
- URLs do cache agora são montadas a partir do escopo real do Service Worker;
- navegação HTML offline possui fallback para o `index.html`;
- documentação corrigida para refletir o banco atual de 224 questões validadas.

### Performance

- cache separado entre shell estático e recursos de runtime;
- estratégia network-first para navegação e stale-while-revalidate para assets locais;
- interface móvel mantém apenas navegação essencial sempre visível.

## [1.0.0] - 2026-09-21

### Adicionado

- arquitetura multi-edital;
- concurso Guarda Civil Municipal de Salvador 2026 pré-carregado;
- matriz curricular baseada no Anexo I do Edital nº 002/2026;
- 116 tópicos/aulas;
- 224 questões autorais validadas pré-carregadas;
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
- PDFs do edital e guia incluídos em `docs/`;
- README completo;
- gerador de dados e validador de projeto.

### Performance

- PDF.js carregado somente quando necessário;
- consultas IndexedDB por índices;
- cursores com limite em tabelas de crescimento contínuo;
- dashboard usa estatísticas incrementais em vez de recalcular todo o histórico;
- histórico limitado a janela recente;
- questões filtradas antes do embaralhamento;
- assets visuais reduzidos ao essencial.

### Segurança e privacidade

- nenhuma utilização de `localStorage` como persistência;
- nenhuma API key incluída no código;
- integração Google Calendar básica sem OAuth;
- aviso explícito antes de apagar o banco local.
