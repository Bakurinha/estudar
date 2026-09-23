# Quality Gate Pedagógico V2

## Objetivo

Impedir que o projeto volte a confundir **mais caracteres/páginas** com **mais aprendizagem**. A unidade de qualidade passa a ser o ganho cognitivo: o que o aluno consegue compreender, recuperar, aplicar e transferir.

A regra permanente é:

> **Repetir conhecimento para revisão é permitido. Repetir a mesma experiência cognitiva sem ganho novo é proibido.**

O escopo disciplinar continua sendo o `officialScope` já existente. Esta política não autoriza adicionar conteúdo fora do edital ou dos módulos acadêmicos.

## Catraca de dívida legada

O banco atual possui padrões repetitivos já conhecidos. Bloqueá-los retroativamente de uma só vez impediria a correção gradual. Por isso o gate trabalha com uma catraca:

- dívida já existente é registrada na linha de base;
- ela pode diminuir;
- ela **não pode aumentar**;
- qualquer questão/página nova ou alterada recebe regras mais rígidas do que o legado intacto.

Isso significa que uma família antiga como `student-note-concept` não pode receber novas questões. Ao tocar numa questão antiga, ela precisa ser promovida ao padrão V2.

## Regras para questões novas ou alteradas

1. Enunciado normalizado não pode ser duplicado.
2. Similaridade de 90% ou mais com questão do mesmo tópico/família é bloqueada.
3. É proibido criar questão metalinguística cuja habilidade seja apenas reconhecer o "recorte do edital".
4. É proibido usar alternativas-placeholder como "Afirmação incompatível...".
5. Toda questão nova/alterada declara `pedagogy.templateFamily`, `cognitiveLevel`, `cognitiveOps`, `skillTarget` e `errorTarget`.
6. `hard` só é aceito quando exige aplicação/transferência e pelo menos duas operações cognitivas.
7. A família de template deve variar; famílias legadas repetitivas não podem crescer.
8. Uma questão oficial usada para validação externa não pode ser reaproveitada como treino autoral disfarçado.

## Regras para páginas e blocos novos ou alterados

1. Página nova declara `pedagogicalRole`.
2. Bloco novo/alterado declara `learningGain`: qual capacidade concreta ele acrescenta.
3. Texto metodológico genérico não pode ultrapassar 15% do texto novo/alterado.
4. Bloco literalmente repetido é bloqueado, exceto revisão intencional marcada com `revisitOf`.
5. A estrutura pedagógica pode se repetir; o texto e a operação cognitiva não.
6. Aumento de caracteres não conta como métrica de qualidade.

## Escada do piloto

Nos quatro tópicos-piloto, a sequência-alvo é:

`explicação simples → explicação técnica → exemplo resolvido → exemplo comentado → prática guiada → prática independente → transferência → FGV-like → revisão espaçada`

O aluno só avança em domínio quando produz evidência: recuperar, aplicar, transferir e repetir o desempenho depois.

## Tópicos-piloto

- `interpretacao-argumentativa`
- `porcentagem-proporcao`
- `penal-ilicitude`
- `leg-guardas`

Esses quatro cobrem linguagem, matemática, raciocínio jurídico e legislação literal/aplicada.

## O que o CI verifica

O `tools/pedagogical_quality_gate.py` compara o estado atual com a versão Git anterior e bloqueia regressões de:

- duplicação literal de enunciados;
- flags de dívida legada;
- crescimento das quatro famílias repetitivas identificadas;
- duplicação literal de blocos;
- proporção de metodologia genérica.

Além da catraca, conteúdo novo/alterado passa pelas regras estritas de metadados, similaridade e ganho pedagógico.

## Limitação técnica atual

A branch `main` não possui proteção de branch no GitHub. Portanto, o gate bloqueia o **pipeline oficial de geração** e sinaliza regressões em pushes/PRs, mas um push direto feito deliberadamente na `main` ainda pode contornar um status de CI. A política do projeto passa a proibir alterações de conteúdo que não atravessem o gate; proteção de branch pode ser habilitada depois para transformar essa regra em bloqueio de repositório.
