#!/usr/bin/env python3
"""Gera os dados iniciais da plataforma.

Este script transforma a matriz oficial do Edital 002/2026 em arquivos JSON usados
pelo aplicativo. Ele também cria um banco autoral de questões. As questões não são
questões oficiais da FGV; cada item recebe essa identificação no próprio JSON.

O arquivo foi deixado no projeto de propósito: facilita auditoria, manutenção e
expansão para futuros editais sem esconder a origem dos dados pré-carregados.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONTEST_ID = "gcm-salvador-2026"
random.seed(20260921)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def slug(text: str) -> str:
    table = str.maketrans(
        "áàãâéêíóôõúüçÁÀÃÂÉÊÍÓÔÕÚÜÇ",
        "aaaaeeiooouucAAAAEEIOOOUUC",
    )
    clean = text.translate(table).lower()
    return "-".join("".join(ch if ch.isalnum() else " " for ch in clean).split())


contest = {
    "id": CONTEST_ID,
    "name": "Guarda Civil Municipal de Salvador 2026",
    "shortName": "GCM Salvador 2026",
    "organization": "Prefeitura Municipal do Salvador",
    "organizer": "FGV",
    "notice": "Edital nº 002/2026",
    "noticeDate": "2026-09-24",
    "examDate": "2027-01-17T08:00:00-03:00",
    "examDurationMinutes": 270,
    "totalQuestions": 70,
    "status": "open",
    "officialPage": "https://conhecimento.fgv.br/concursos/pmsguarda2026",
    "localNoticePath": "./docs/edital-gcm-salvador-2026.pdf",
    "localGuidePath": "./docs/guia-gcm-salvador-2026.pdf",
    "rules": {
        "minimumModule1": 14,
        "minimumModule2": 21,
        "minimumTotal": 35,
        "questionValue": 1,
    },
    "taf": {
        "male": {
            "run": {"distanceM": 2200, "timeMinutes": 12},
            "bar": {"type": "dynamic", "minimum": 3},
            "abdominal": {"minimum": 25},
            "pushup": {"minimum": 20},
        },
        "female": {
            "run": {"distanceM": 2200, "timeMinutes": 14},
            "bar": {"type": "static", "minimumSeconds": 10},
            "abdominal": {"minimum": 20},
            "pushup": {"minimum": 15},
        },
    },
    "studyGuide": {
        "strategy": "Priorizar Português e RLM sem abandonar matérias de 10 questões e os mínimos dos dois módulos.",
        "dailyMethod": "Teoria curta -> questões -> correção -> revisão ativa -> registro do erro.",
        "targetScore": 80,
        "phases": [
            {"name": "Base", "goal": "Aprender fundamentos e mapear fraquezas"},
            {"name": "Cobertura", "goal": "Passar por todo o edital ao menos uma vez"},
            {"name": "Consolidação", "goal": "Questões, revisões e simulados"},
            {"name": "Reta final", "goal": "Simulados cronometrados, leis e pontos fracos"}
        ]
    },
    "schedule": [
        {"title": "Inscrições", "start": "2026-09-21", "end": "2026-10-30", "type": "official"},
        {"title": "Isenção da taxa", "start": "2026-09-21", "end": "2026-09-22", "type": "official"},
        {"title": "Prazo limite para pagamento", "start": "2026-11-06", "end": "2026-11-06", "type": "official"},
        {"title": "Locais de prova", "start": "2027-01-11", "end": "2027-01-11", "type": "official"},
        {"title": "Prova objetiva", "start": "2027-01-17T08:00:00-03:00", "end": "2027-01-17T12:30:00-03:00", "type": "official"},
        {"title": "Convocação para o TAF", "start": "2027-03-17", "end": "2027-03-17", "type": "official"},
        {"title": "TAF", "start": "2027-04-05", "end": "2027-04-07", "type": "official"},
        {"title": "Avaliação psicológica", "start": "2027-05-30", "end": "2027-05-30", "type": "official"},
        {"title": "Resultado final previsto", "start": "2027-09-02", "end": "2027-09-02", "type": "official"},
    ],
}
write_json(DATA / "contests" / f"{CONTEST_ID}.json", contest)


# Cada tópico abaixo preserva o recorte do Anexo I. "label" é um nome curto para UI;
# "official" mantém a redação ou o recorte literal usado como referência curricular.
subjects: list[dict[str, Any]] = [
    {
        "id": "portugues",
        "module": 1,
        "name": "Língua Portuguesa",
        "questions": 10,
        "priority": 1.25,
        "topics": [
            ("interpretacao-argumentativa", "Interpretação de textos argumentativos", "Interpretação de textos argumentativos, com destaque para métodos de raciocínio e tipologia argumentativa"),
            ("construcao-textual", "Processos de construção textual", "Processos de construção textual"),
            ("progressao-textual", "Progressão textual", "A progressão textual"),
            ("coesao-coerencia-intertextualidade", "Coesão, coerência e intertextualidade", "As marcas de textualidade: a coesão, a coerência e a intertextualidade"),
            ("reescritura", "Reescritura de frases", "Reescritura de frases em busca da melhor expressão escrita"),
            ("vocabulario", "Domínio vocabular", "Domínio vocabular e sua importância na construção do sentido do texto"),
            ("estrangeirismos", "Estrangeirismos", "A presença dos estrangeirismos em nosso léxico"),
            ("classes-palavras", "Classes de palavras", "Os diversos usos das várias classes de palavras"),
            ("sintaxe-pontuacao", "Sintaxe e pontuação", "A organização sintática e o emprego dos sinais de pontuação"),
            ("variacao-linguistica", "Variação linguística e adequação", "A variação linguística e sua adequação às diversas situações comunicativas"),
            ("denotacao-conotacao", "Denotação e conotação", "A linguagem denotativa e a conotativa"),
            ("nova-ortografia", "Nova ortografia", "A nova ortografia"),
        ],
    },
    {
        "id": "rlm",
        "module": 1,
        "name": "Raciocínio Lógico-Matemático",
        "questions": 10,
        "priority": 1.25,
        "topics": [
            ("proposicoes", "Proposições e conectivos", "Proposições, valor-verdade, negação, conjunção, disjunção, implicação, equivalência, proposições compostas"),
            ("equivalencias", "Equivalências lógicas", "Equivalências lógicas"),
            ("problemas-raciocinio", "Problemas de raciocínio", "Problemas de raciocínio: deduzir informações de relações arbitrárias entre objetos, lugares, pessoas e/ou eventos fictícios dados"),
            ("diagramas-graficos", "Diagramas, tabelas e gráficos", "Diagramas lógicos, tabelas e gráficos"),
            ("conjuntos", "Conjuntos e operações", "Conjuntos e suas operações"),
            ("numeros-operacoes", "Números e operações", "Números naturais, inteiros, racionais, reais e suas operações"),
            ("reta-numerica", "Representação na reta", "Representação na reta"),
            ("unidades-medida", "Unidades de medida", "Unidades de medida: distância, massa e tempo"),
            ("plano-cartesiano", "Plano cartesiano", "Representação de pontos no plano cartesiano"),
            ("algebra", "Álgebra básica", "Álgebra básica: equações, sistemas e problemas do primeiro grau"),
            ("porcentagem-proporcao", "Porcentagem e proporcionalidade", "Porcentagem e proporcionalidade direta e inversa"),
            ("sequencias-pa-pg", "Sequências, PA e PG", "Sequências, reconhecimento de padrões, progressões aritmética e geométrica"),
            ("juros", "Juros", "Juros"),
            ("geometria-basica", "Geometria básica", "Geometria básica: distâncias e ângulos, polígonos, circunferência, perímetro e área"),
            ("semelhanca-triangulo", "Semelhança e triângulo retângulo", "Semelhança e relações métricas no triângulo retângulo"),
            ("medidas-area-volume", "Comprimento, área e volume", "Medidas de comprimento, área e volume"),
            ("contagem-probabilidade", "Contagem e probabilidade", "Princípios de contagem e noção de probabilidade"),
        ],
    },
    {
        "id": "informatica",
        "module": 1,
        "name": "Informática",
        "questions": 8,
        "priority": 0.9,
        "topics": [
            ("arquivos-digitais", "Arquivos digitais", "Arquivos digitais: documentos, planilhas, imagens, sons, vídeos; principais padrões e características"),
            ("pdf", "Arquivos PDF", "Arquivos PDF"),
            ("windows", "Windows XP, 7 e 8", "Sistema operacional Windows XP, 7 e 8: manipulação de janelas, programas e arquivos; telas de controle e menus típicos; mecanismos de ajuda; mecanismos de busca"),
            ("editores-texto", "Editores de texto", "Editores de texto: formatação, configuração de páginas, impressão, títulos, fontes, tabelas, corretores ortográficos, manipulação de figuras, cabeçalhos, rodapés, anotações e outras funcionalidades de formatação"),
            ("localizar-substituir", "Localização e substituição", "Comandos de localização e substituição"),
            ("word-arquivos", "Word 2010+ e manipulação de arquivos", "Manipulação de arquivos: leitura e gravação; controle de alterações; uso de senhas para proteção; formatos para gravação; inserção de objetos; macros; impressão; criação e manipulação de formulários; integração com planilhas; MS Word 2010 BR ou superior"),
            ("excel", "Excel 2010+", "Planilhas: criação, manipulação de dados, fórmulas, cópia e recorte de dados, formatação de dados e outras funcionalidades para operação; manipulação de arquivos: leitura e gravação; integração com outras planilhas; filtros; ordenação; macros; controle de exibição; recursos para impressão; importação e exportação de dados; controle de alterações; proteção de dados e planilhas; MS Excel 2010 BR ou superior"),
            ("internet-seguranca", "Internet e segurança", "Internet: conceitos gerais e funcionamento; endereçamento de recursos; navegação segura: cuidados no uso da Internet; ameaças; uso de senhas e criptografia; tokens e outros dispositivos de segurança; senhas fracas e fortes; navegadores e suas principais funções; sites e links; buscas; transferência de arquivos e dados: upload, download, banda, velocidades de transmissão"),
        ],
    },
    {
        "id": "constitucional-civil",
        "module": 2,
        "name": "Direito Constitucional e Direito Civil",
        "questions": 10,
        "priority": 1.05,
        "topics": [
            ("const-conceito-principios", "Constituição: conceito, classificações e princípios", "Constituição: conceito, classificações e princípios fundamentais"),
            ("const-direitos", "Direitos e garantias fundamentais", "Direitos e garantias fundamentais: direitos e deveres individuais e coletivos, direitos sociais, nacionalidade, cidadania, direitos políticos e partidos políticos"),
            ("const-organizacao", "Organização político-administrativa", "Organização político-administrativa: União, Estados, Distrito Federal, Municípios e Territórios"),
            ("const-administracao", "Administração pública e servidores", "Administração pública: disposições gerais e servidores públicos"),
            ("const-judiciario", "Poder Judiciário", "Poder Judiciário: disposições gerais e órgãos do Poder Judiciário, competências e estrutura"),
            ("const-cnj", "Conselho Nacional de Justiça", "Conselho Nacional de Justiça (CNJ): composição e competência"),
            ("const-funcoes-justica", "Funções essenciais à Justiça", "Funções essenciais à Justiça: Ministério Público, advocacia e defensoria pública"),
            ("civil-lindb", "Aplicação da lei e LINDB", "Aplicação da Lei no Tempo e no Espaço; interpretação da Lei; analogia; princípios gerais do Direito e equidade; Lei de Introdução às Normas do Direito Brasileiro"),
            ("civil-pessoas", "Pessoas, domicílio e capacidade", "Pessoas naturais; pessoas jurídicas; domicílio; capacidade civil e direitos inerentes à personalidade; emancipação"),
            ("civil-bens", "Bens", "Bens considerados em si mesmos; bens reciprocamente considerados; bens públicos"),
            ("civil-fatos", "Fatos jurídicos", "Negócio jurídico; atos jurídicos lícitos; atos ilícitos; prescrição e decadência; prova"),
            ("civil-obrigacoes", "Obrigações", "Modalidades das obrigações; transmissão; adimplemento e extinção; inadimplemento"),
            ("civil-responsabilidade", "Responsabilidade civil", "Responsabilidade civil; preferências e privilégios creditórios; indenização por dano moral; perda de uma chance; desconsideração da personalidade jurídica; preservação e reparação de danos; decadência e prescrição"),
            ("civil-jurisprudencia", "Jurisprudência e súmulas", "Jurisprudência e Súmulas do STF, STJ e TJBA"),
        ],
    },
    {
        "id": "penal-processual",
        "module": 2,
        "name": "Direito Penal e Direito Processual Penal",
        "questions": 7,
        "priority": 0.95,
        "topics": [
            ("penal-conceito-fontes", "Conceito e fontes do Direito Penal", "Conceito do Direito Penal; fontes do Direito Penal"),
            ("penal-lei", "Interpretação e lei penal", "Interpretação e integração da Lei Penal; analogia; princípio da reserva legal; lei penal no tempo e no espaço"),
            ("penal-teoria-crime", "Fato típico, dolo e culpa", "Classificação das infrações penais; fato típico; conduta; resultado; relação de causalidade; crime doloso, culposo e preterdoloso"),
            ("penal-iter", "Consumação, tentativa e arrependimentos", "Consumação e tentativa; desistência voluntária; arrependimento eficaz; arrependimento posterior; crime impossível"),
            ("penal-ilicitude", "Ilicitude e culpabilidade", "Ilicitude e suas causas excludentes; culpabilidade e suas causas excludentes; concurso de pessoas"),
            ("penal-penas", "Penas e concurso de crimes", "Sanções penais; penas privativas de liberdade; penas restritivas de direitos; pena de multa; medidas de segurança; concurso de crimes"),
            ("penal-sursis", "Sursis, livramento e punibilidade", "Suspensão condicional da execução da pena; livramento condicional; causas extintivas da punibilidade"),
            ("penal-crimes-pessoa-patrimonio", "Crimes contra pessoa, patrimônio e dignidade sexual", "Crimes contra Pessoa; Crimes contra o Patrimônio; Crimes contra a Dignidade Sexual"),
            ("penal-honra-fe-publica", "Crimes contra honra e fé pública", "Crimes contra a Honra; Crimes contra a Fé Pública"),
            ("penal-administracao", "Crimes contra a Administração", "Crimes contra a Administração Pública; Crimes contra a Administração da Justiça"),
            ("penal-leis-especiais", "Leis penais especiais do edital", "Abuso de Autoridade; ECA; hediondos; licitações; tortura; CTB; meio ambiente; lavagem; Lei Geral do Esporte; Desarmamento; recuperação judicial e falência; Maria da Penha; Drogas; organizações criminosas e Lei 15.358/2026; pessoa com deficiência; ordem tributária/econômica e consumidor"),
            ("proc-principios", "Processo Penal e princípios", "Processo Penal Brasileiro; Processo Penal Constitucional; sistemas e princípios fundamentais"),
            ("proc-aplicacao", "Aplicação da lei processual", "Aplicação da lei processual penal no tempo, no espaço e em relação às pessoas; disposições preliminares do CPP"),
            ("proc-inquerito", "Inquérito policial", "Inquérito policial"),
            ("proc-processo", "Processo, procedimento e relação processual", "Processo, procedimento e relação jurídica processual; princípios gerais e informadores; pretensão punitiva"),
            ("proc-acao", "Ação penal", "Ação penal"),
            ("proc-prova", "Prova e interceptação", "Prova; Lei nº 9.296/1996 (Interceptação Telefônica) e alterações"),
            ("proc-sujeitos", "Sujeitos do processo", "Sujeitos do Processo"),
            ("proc-prisao", "Prisão e cautelares", "Prisão, medidas cautelares e liberdade provisória; Lei nº 7.960/1989 (Prisão Temporária)"),
            ("proc-juizados", "Juizados especiais", "Lei nº 9.099/1995 e Lei nº 10.259/2001"),
            ("proc-prazos", "Prazos", "Prazos: características, princípios e contagem"),
            ("proc-nulidades", "Nulidades", "Nulidades"),
            ("proc-jurisprudencia", "Jurisprudência processual", "Jurisprudência aplicada dos tribunais superiores"),
        ],
    },
    {
        "id": "administracao-politicas",
        "module": 2,
        "name": "Administração e Políticas Públicas",
        "questions": 5,
        "priority": 0.7,
        "topics": [
            ("adm-introducao", "Introdução à Administração", "Definição e importância da administração; história e evolução da administração"),
            ("adm-funcoes", "Funções administrativas", "Planejamento, Organização, Direção e Controle"),
            ("adm-teorias", "Teorias da Administração", "Teoria clássica, relações humanas, comportamental, contingência; gestão por competências e gestão de projetos"),
            ("adm-estruturas", "Estruturas, cultura e liderança", "Estruturas funcional, matricial e projetos; cultura organizacional; estilos de liderança"),
            ("adm-planejamento", "Planejamento estratégico", "Missão, visão, valores, análise SWOT, objetivos e metas"),
            ("adm-marketing", "Marketing e vendas", "Fundamentos de marketing, segmentação, composto de marketing (4 Ps), estratégias de vendas"),
            ("adm-financeira", "Gestão financeira", "Conceitos básicos de finanças, orçamento empresarial, fluxo de caixa, indicadores financeiros"),
            ("adm-rh", "Recursos Humanos", "Recrutamento e seleção, treinamento e desenvolvimento, avaliação de desempenho, motivação e liderança"),
            ("adm-empreendedorismo", "Empreendedorismo", "Processo empreendedor, plano de negócios, inovação e criatividade"),
            ("adm-etica", "Ética e responsabilidade", "Ética na administração, responsabilidade social corporativa e sustentabilidade"),
            ("pp-conceitos", "Conceitos e ciclo de políticas públicas", "Definição e evolução; ciclo de políticas públicas: formulação, implementação, avaliação; ferramentas de análise"),
            ("pp-governanca", "Governança e relações intragovernamentais", "Federalismo e relações Estado-sociedade; governança e capacidades estatais; análise de políticas intergovernamentais"),
            ("pp-bases", "Bases quantitativas", "Estatística descritiva e inferencial; micro e macroeconomia aplicada; análise de impacto"),
            ("pp-avaliacao", "Gestão e avaliação de políticas", "Análise ex ante e ex post; avaliação de impacto; gestão de riscos"),
        ],
    },
    {
        "id": "area-atuacao",
        "module": 2,
        "name": "Conhecimentos na Área de Atuação",
        "questions": 10,
        "priority": 1.0,
        "topics": [
            ("area-atendimento", "Relações humanas e atendimento", "Qualidade no atendimento: comunicação, apresentação, atenção, cortesia, interesse, presteza, eficiência, tolerância, discrição, conduta e objetividade; trabalho em equipe"),
            ("area-defesa-riscos", "Defesa pessoal, riscos e informação", "Noções de Defesa Pessoal; análise de riscos e gestão da informação; contingências; emergência; crises; procedimentos emergenciais; graus de sigilo; ameaças e vulnerabilidades"),
            ("area-protecao-escoltas", "Proteção e escoltas", "Planejamento de proteção pessoal e de comitivas; rotas; pontos sensíveis; contingências; equipes; formações; varredura; controle de público; resposta a ameaças; condução operacional e estratégica de veículos"),
            ("area-seguranca-patrimonial", "Segurança física e patrimonial", "Proteção de áreas críticas; materiais sensíveis; planos de segurança; controle de acessos; vigilância; monitoramento; equipamentos eletrônicos; segurança corporativa e patrimonial"),
            ("area-incidentes-negociacao", "Incidentes críticos e negociação", "Incidente crítico; cadeia de comando; gerenciamento do cenário; estabilização; isolamentos e perímetros; comunicação operacional; negociação policial; escuta ativa; redução de tensão; escalonamento"),
            ("area-incendio", "Prevenção e combate a incêndio", "NR-23; proteção contra incêndio; código de segurança contra incêndio, pânico e outros riscos; brigada e órgãos de resposta; extintores; rotas e saídas; abandono e evacuação"),
            ("area-socorrismo", "Condutas do socorrista", "Medidas de segurança do local; comunicação e transferência ao atendimento especializado; Atendimento Pré-Hospitalar (APH) - Nível Básico"),
            ("area-inteligencia", "Serviços de inteligência", "Finalidade, utilização, conceitos básicos, fontes de coleta e metodologia de produção de conhecimentos"),
        ],
    },
    {
        "id": "legislacao",
        "module": 2,
        "name": "Legislação",
        "questions": 10,
        "priority": 1.1,
        "topics": [
            ("leg-maria-penha", "Lei Maria da Penha", "Lei Federal nº 11.340/2006 (Lei Maria da Penha)"),
            ("leg-drogas", "Lei de Drogas", "Lei nº 11.343/2006 (Lei de Drogas)"),
            ("leg-racismo", "Crimes de preconceito de raça ou cor", "Lei nº 7.716/1989 e alterações"),
            ("leg-eca", "Estatuto da Criança e do Adolescente", "Lei nº 8.069/1990 e alterações"),
            ("leg-ambiental", "Crimes ambientais", "Lei nº 9.605/1998 e alterações"),
            ("leg-ctb", "Código de Trânsito Brasileiro", "Lei nº 9.503/1997 e alterações"),
            ("leg-desarmamento", "Estatuto do Desarmamento", "Lei nº 10.826/2003 e alterações"),
            ("leg-abuso", "Abuso de Autoridade", "Lei nº 13.869/2019 e alterações"),
            ("leg-licitacoes", "Licitações e contratos", "Lei nº 14.133/2021"),
            ("leg-lc1", "Regime Jurídico do Município", "Lei Complementar nº 1/1991 e alterações"),
            ("leg-carreira", "Plano de Carreira da GCM", "Lei Ordinária nº 9.640/2022 e alterações"),
            ("leg-guardas", "Estatuto Geral das Guardas Municipais", "Lei nº 13.022/2014"),
            ("leg-regimento", "Regimento da GCM Salvador", "Decreto nº 27.731/2016"),
            ("leg-disciplinar", "Regime Disciplinar da GCM", "Lei nº 9.273/2017"),
            ("leg-organica-poderes", "Lei Orgânica: organização e Poderes", "Princípios fundamentais; organização do Município; competências municipais; Poder Legislativo e Poder Executivo; atribuições da Câmara Municipal, do Prefeito e dos órgãos da Administração Municipal"),
            ("leg-organica-adm", "Lei Orgânica: Administração e servidores", "Administração pública; servidores públicos; bens municipais; serviços públicos; planejamento, orçamento e finanças municipais; políticas sociais e desenvolvimento urbano"),
            ("leg-organizacao-adm", "Organização administrativa municipal", "Estrutura e funcionamento da Administração Pública Municipal; administração direta e indireta; órgãos e entidades municipais; princípios, competências e responsabilidades dos agentes públicos"),
            ("leg-tributario", "Código Tributário e de Rendas", "Lei Municipal nº 7.186/2006 e alterações: tributos municipais, obrigações tributárias, administração e fiscalização tributária"),
            ("leg-etica-transparencia", "Ética, integridade e transparência", "Normas municipais relativas à ética, integridade, transparência, acesso à informação e controle da Administração Pública; organização, prestação e fiscalização dos serviços públicos"),
            ("leg-direitos-cidadaos", "Direitos, deveres e agentes públicos", "Direitos e deveres dos cidadãos perante a Administração Municipal; normas municipais pertinentes ao exercício das atribuições dos agentes e servidores públicos"),
        ],
    },
]

syllabus = {
    "contestId": CONTEST_ID,
    "source": {
        "type": "official-notice",
        "document": "Edital nº 002/2026",
        "pages": "49-53",
        "note": "Os campos officialScope preservam o recorte do Anexo I. Rótulos menores são apenas organização didática.",
    },
    "subjects": [],
}
for s in subjects:
    syllabus["subjects"].append({
        "id": s["id"],
        "name": s["name"],
        "module": s["module"],
        "questions": s["questions"],
        "priority": s["priority"],
        "topics": [
            {"id": topic_id, "label": label, "officialScope": official}
            for topic_id, label, official in s["topics"]
        ],
    })
write_json(DATA / "syllabus" / f"{CONTEST_ID}.json", syllabus)


# Explicações didáticas personalizadas para Português e RLM; os demais tópicos recebem
# um modelo conservador, deixando claro que é resumo didático e mantendo o escopo oficial.
port_notes = {
    "interpretacao-argumentativa": (
        "Interpretar é descobrir o que o texto realmente afirma, como sustenta essa afirmação e qual conclusão pretende defender. Em texto argumentativo, procure tese, argumentos, exemplos, contrapontos e conclusão.",
        ["Leia o comando da questão.", "Localize a tese do texto.", "Marque conectivos de contraste, causa e conclusão.", "Separe informação do texto de opinião pessoal."],
        "Se o texto afirma que uma medida 'pode reduzir' um problema, uma alternativa que diga que ela 'elimina' o problema exagera o sentido.",
        "Não escolha uma alternativa só porque ela é verdadeira no mundo; ela precisa ser sustentada pelo texto.",
    ),
    "construcao-textual": (
        "Construção textual é o modo como as partes de um texto são montadas para formar uma unidade: tema, ordem das ideias, referências, conectivos e relação entre parágrafos.",
        ["Identifique o tema central.", "Veja como cada frase retoma a anterior.", "Observe pronomes e conectores.", "Pergunte qual função cada parágrafo cumpre."],
        "Em 'A equipe chegou cedo. Ela iniciou a vistoria', o pronome 'ela' retoma 'a equipe' e ajuda a ligar as frases.",
        "Uma frase pode estar gramaticalmente correta e ainda assim quebrar a construção do texto por introduzir assunto sem ligação.",
    ),
    "progressao-textual": (
        "Progressão textual é o avanço das informações. Um bom texto retoma o que já foi dito e acrescenta algo novo, em vez de girar no mesmo ponto.",
        ["Separe informação conhecida e informação nova.", "Observe causa, consequência, explicação e conclusão.", "Compare o início e o fim do parágrafo."],
        "Se o primeiro período apresenta um problema e o segundo explica sua causa, houve progressão por explicação.",
        "Repetição de palavras não significa necessariamente falta de progressão; o que importa é se a ideia avança.",
    ),
    "coesao-coerencia-intertextualidade": (
        "Coesão é a ligação linguística entre as partes; coerência é o sentido global compatível; intertextualidade é a relação de um texto com outros textos, falas ou referências culturais.",
        ["Revise pronomes, sinônimos e conectores.", "Teste se as ideias podem coexistir sem contradição.", "Reconheça citação, alusão e referência."],
        "'Pedro perdeu o ônibus. Por isso, chegou atrasado.' O conector 'por isso' marca consequência e cria coesão.",
        "Coesão e coerência não são sinônimos: um texto pode ter conectores e ainda ser incoerente.",
    ),
    "reescritura": (
        "Reescrever é mudar a forma mantendo, quando pedido, o sentido e a correção. A banca costuma alterar conectivos, ordem, voz verbal, negação ou intensidade.",
        ["Compare sujeito e tempo verbal.", "Confira negações.", "Veja se causa virou consequência.", "Leia a versão nova isoladamente."],
        "Trocar 'embora estivesse cansado, continuou' por 'apesar de estar cansado, continuou' preserva a ideia concessiva.",
        "Uma troca aparentemente pequena de 'pode' por 'deve' muda modalidade e sentido.",
    ),
    "vocabulario": (
        "Domínio vocabular é entender a palavra no contexto. A mesma palavra pode ter sentidos diferentes dependendo da frase.",
        ["Leia a frase inteira.", "Teste sinônimos no contexto.", "Observe registro formal e informal."],
        "Em 'a medida foi dura', 'dura' pode significar rigorosa, não necessariamente sólida.",
        "Sinônimo de dicionário nem sempre substitui uma palavra sem mudar o sentido contextual.",
    ),
    "estrangeirismos": (
        "Estrangeirismo é palavra ou expressão vinda de outra língua usada no português. A questão pode cobrar reconhecimento e adequação ao contexto.",
        ["Identifique a origem estrangeira.", "Observe se o uso é técnico, cotidiano ou estilístico.", "Avalie adequação ao público e ao registro."],
        "'Download' é estrangeirismo amplamente usado em informática e pode aparecer em contexto técnico.",
        "O fato de uma palavra ser estrangeira não a torna automaticamente inadequada.",
    ),
    "classes-palavras": (
        "Classes de palavras agrupam palavras pelo comportamento e função. O foco útil para prova é reconhecer substantivo, adjetivo, artigo, pronome, numeral, verbo, advérbio, preposição, conjunção e interjeição dentro de frases reais.",
        ["Identifique o núcleo da expressão.", "Veja que palavra modifica outra.", "Observe flexões e função no contexto."],
        "Em 'o agente respondeu rapidamente', 'rapidamente' modifica o verbo 'respondeu' e funciona como advérbio.",
        "A mesma forma pode mudar de classe conforme o contexto; não classifique só pela aparência.",
    ),
    "sintaxe-pontuacao": (
        "Sintaxe estuda como os termos se organizam na oração. Pontuação ajuda a mostrar essa estrutura e também relações de sentido.",
        ["Ache sujeito e verbo.", "Identifique complementos e termos acessórios.", "Revise coordenação e subordinação.", "Treine vírgula em enumeração, deslocamento e explicação."],
        "Em 'Os candidatos, cansados, aguardaram o resultado', as vírgulas isolam um termo explicativo.",
        "Vírgula não deve ser colocada apenas porque você faria uma pausa ao falar.",
    ),
    "variacao-linguistica": (
        "A língua varia conforme região, grupo, época, situação e grau de formalidade. Em prova, o ponto central costuma ser adequação ao contexto comunicativo.",
        ["Diferencie norma-padrão e variedades linguísticas.", "Observe quem fala, para quem e em qual situação."],
        "Uma mensagem entre amigos pode admitir construções informais que não seriam adequadas a um ofício administrativo.",
        "Variação linguística não significa ausência de regras; cada variedade tem padrões de uso.",
    ),
    "denotacao-conotacao": (
        "Denotação é o uso mais literal; conotação é o uso figurado ou associado. A interpretação depende do contexto.",
        ["Teste o sentido literal.", "Procure metáfora, ironia e comparação.", "Veja se o efeito expressivo é essencial."],
        "Em 'a cidade acordou assustada', a cidade não dorme literalmente: há uso figurado.",
        "Nem toda palavra com vários sentidos está em conotação; o contexto é quem decide.",
    ),
    "nova-ortografia": (
        "O Acordo Ortográfico alterou principalmente grafias, regras de hífen, acentuação e uso do trema. O estudo deve focar formas corretas atuais.",
        ["Revise acentuação.", "Revise prefixos e hífen.", "Memorize grafias recorrentes por questões."],
        "'autoescola' é escrita sem hífen; 'micro-ondas' mantém hífen.",
        "Não tente decorar todas as regras de uma vez; use listas de erros recorrentes.",
    ),
}

rlm_notes = {
    "proposicoes": ("Proposição é uma frase declarativa que pode ser verdadeira ou falsa. A lógica combina proposições por conectivos como 'e', 'ou', 'se... então' e 'se e somente se'.", ["Identifique se a frase tem valor-verdade.", "Traduza o conectivo.", "Monte tabela-verdade quando houver dúvida."], "'Salvador fica na Bahia' é uma proposição. 'Feche a porta' é uma ordem e não tem valor-verdade.", "Perguntas, ordens e frases abertas normalmente não são proposições."),
    "equivalencias": ("Duas proposições são equivalentes quando produzem os mesmos valores-verdade em todas as situações. Equivalência permite reescrever uma frase lógica sem mudar seu conteúdo.", ["Domine negações.", "Treine condicional e contrapositiva.", "Compare tabelas-verdade."], "A contrapositiva de 'Se P, então Q' é 'Se não Q, então não P'.", "Não confunda a recíproca 'Se Q, então P' com uma equivalência automática."),
    "problemas-raciocinio": ("Problemas de raciocínio fornecem relações entre pessoas, objetos, lugares ou eventos. Você deve deduzir uma configuração compatível com todas as pistas.", ["Transforme pistas em tabela.", "Elimine impossibilidades.", "Use uma pista por vez."], "Se Ana chegou antes de Bruno e Bruno antes de Caio, então Ana chegou antes de Caio.", "Evite tentar manter todas as pistas na memória; escreva relações."),
    "diagramas-graficos": ("Diagramas, tabelas e gráficos organizam informação visual. A primeira tarefa é entender título, legenda, eixos e unidade antes de calcular.", ["Leia a unidade.", "Compare valores.", "Só conclua o que o gráfico permite."], "Se um gráfico mostra 40 atendimentos em janeiro e 50 em fevereiro, o aumento foi de 10 atendimentos, ou 25% sobre janeiro.", "Não confunda aumento absoluto com aumento percentual."),
    "conjuntos": ("Conjunto é uma coleção de elementos. União reúne elementos de A ou B; interseção reúne os que pertencem aos dois; diferença mantém os de um conjunto que não estão no outro.", ["Desenhe diagramas de Venn.", "Preencha primeiro interseções.", "Depois complete as partes exclusivas."], "Se A={1,2,3} e B={3,4}, então A∩B={3} e A∪B={1,2,3,4}.", "Em problemas de contagem, não some conjuntos sem descontar interseções."),
    "numeros-operacoes": ("Naturais, inteiros, racionais e reais formam conjuntos numéricos usados em praticamente toda a matemática do edital. Você precisa operar com sinais, frações, decimais e ordem de operações.", ["Treine quatro operações.", "Domine frações e decimais.", "Respeite parênteses e prioridade de operações."], "3/4 = 0,75 = 75%.", "Erro de sinal e ordem de operação costuma destruir questões fáceis."),
    "reta-numerica": ("A reta numérica mostra ordem e distância entre números. Valores mais à direita são maiores; módulo representa distância até zero.", ["Ordene números.", "Compare negativos.", "Use distância como valor não negativo."], "-2 é maior que -5 porque está mais à direita na reta.", "Entre negativos, o número com maior valor absoluto pode ser o menor."),
    "unidades-medida": ("Converter unidades significa expressar a mesma grandeza em outra escala, como km para m, kg para g ou horas para minutos.", ["Identifique a grandeza.", "Converta antes de calcular.", "Confira a unidade final."], "2,5 km = 2.500 m; 1h30min = 90 min.", "Não misture unidades diferentes na mesma conta sem converter."),
    "plano-cartesiano": ("Um ponto no plano cartesiano é representado por (x,y). O primeiro valor indica deslocamento horizontal; o segundo, vertical.", ["Leia x antes de y.", "Reconheça quadrantes.", "Treine pontos sobre os eixos."], "O ponto (-2,3) fica à esquerda do eixo y e acima do eixo x.", "Trocar x por y muda o ponto."),
    "algebra": ("Álgebra traduz problemas em equações. Em equação do primeiro grau, a incógnita aparece com expoente 1; sistemas combinam duas ou mais equações.", ["Defina a incógnita.", "Traduza o texto.", "Isole a variável.", "Substitua para conferir."], "Se x+7=20, então x=13.", "Não mova termo de lado 'trocando o sinal' sem entender que você está fazendo a mesma operação nos dois lados."),
    "porcentagem-proporcao": ("Porcentagem é uma razão por 100. Proporcionalidade direta faz grandezas variarem no mesmo sentido; inversa faz uma aumentar quando a outra diminui, mantendo a relação adequada.", ["Converta % em fator.", "Descubra se a relação é direta ou inversa.", "Use regra de três quando couber."], "20% de 150 = 0,20×150 = 30.", "Aumentos sucessivos de 10% e 10% não equivalem exatamente a 20%; o segundo incide sobre o novo valor."),
    "sequencias-pa-pg": ("Sequência é uma lista ordenada que segue regra. Na PA a diferença entre termos consecutivos é constante; na PG a razão multiplicativa é constante.", ["Ache o padrão.", "Identifique PA ou PG.", "Só depois use fórmula."], "2,5,8,11 é PA de razão 3. 2,6,18 é PG de razão 3.", "Não confunda diferença constante com razão constante."),
    "juros": ("Juros remuneram ou encarecem um capital ao longo do tempo. Nos juros simples, o acréscimo é calculado sobre o capital inicial; nos compostos, sobre o montante acumulado.", ["Identifique capital, taxa e tempo.", "Padronize unidades de tempo.", "Descubra se é simples ou composto."], "R$1.000 a 2% ao mês por 3 meses em juros simples gera R$60 de juros.", "Taxa mensal com tempo em anos exige conversão."),
    "geometria-basica": ("Geometria básica envolve distâncias, ângulos, polígonos, circunferência, perímetro e área. Primeiro identifique a figura e a grandeza pedida.", ["Desenhe a figura.", "Separe perímetro de área.", "Use unidades corretas."], "Retângulo 4 m × 3 m: perímetro 14 m; área 12 m².", "Área usa unidade ao quadrado; perímetro usa unidade linear."),
    "semelhanca-triangulo": ("Figuras semelhantes têm mesma forma e lados proporcionais. No triângulo retângulo, relações métricas e o Teorema de Pitágoras conectam catetos e hipotenusa.", ["Identifique lados correspondentes.", "Monte proporção.", "Use Pitágoras quando houver triângulo retângulo."], "Triângulo 3-4-5 é retângulo porque 3²+4²=5².", "A hipotenusa é sempre o lado oposto ao ângulo de 90° e o maior lado."),
    "medidas-area-volume": ("Comprimento mede uma dimensão, área mede superfície e volume mede espaço ocupado. Cada grandeza usa unidades diferentes.", ["Identifique a grandeza.", "Converta unidades.", "Aplique a fórmula adequada."], "Uma caixa 2×3×4 tem volume 24 unidades cúbicas.", "Converter m² para cm² não usa o mesmo fator de m para cm; a escala é quadrática."),
    "contagem-probabilidade": ("Princípios de contagem calculam quantas possibilidades existem. Probabilidade compara casos favoráveis e possíveis quando o modelo é adequado.", ["Separe etapas.", "Use princípio multiplicativo.", "Verifique se casos são equiprováveis."], "3 camisas e 2 calças geram 3×2=6 combinações.", "Não use favoráveis/possíveis sem confirmar que os resultados têm a mesma chance."),
}


def generic_note(subject_name: str, label: str, official: str) -> tuple[str, list[str], str, str]:
    summary = (
        f"Este bloco estuda {label.lower()} dentro do recorte de {subject_name}. "
        "A referência curricular é exatamente o item do edital mostrado acima. O objetivo desta aula é criar uma base conceitual para depois consolidar por questões e consulta à fonte oficial quando houver legislação."
    )
    steps = [
        "Leia o recorte oficial do edital.",
        "Aprenda os conceitos centrais e as diferenças entre termos parecidos.",
        "Resolva questões somente deste tópico.",
        "Registre no caderno de erros qualquer regra que você confunda.",
    ]
    example = f"Ao revisar {label.lower()}, tente explicar em voz alta o conceito e criar um exemplo próprio sem consultar o resumo."
    pitfall = "Não amplie o estudo para assuntos que não aparecem no recorte do edital apenas porque pertencem à mesma disciplina."
    return summary, steps, example, pitfall


lessons: list[dict[str, Any]] = []
for subject in subjects:
    for topic_id, label, official in subject["topics"]:
        if subject["id"] == "portugues":
            note = port_notes[topic_id]
        elif subject["id"] == "rlm":
            note = rlm_notes[topic_id]
        else:
            note = generic_note(subject["name"], label, official)
        summary, steps, example, pitfall = note
        lessons.append({
            "id": f"lesson-{topic_id}",
            "contestId": CONTEST_ID,
            "subjectId": subject["id"],
            "topicId": topic_id,
            "title": label,
            "contentType": "resumo-didatico",
            "officialScope": official,
            "summary": summary,
            "sections": [
                {"title": "O que você precisa entender", "body": summary},
                {"title": "Como estudar", "items": steps},
                {"title": "Exemplo simples", "body": example},
                {"title": "Cuidado com", "body": pitfall},
                {"title": "Revisão ativa", "body": f"Sem olhar o material, explique em até 2 minutos: {label}. Depois compare com o recorte oficial e corrija o que faltou."},
            ],
            "source": {
                "type": "editais-e-guia",
                "noticePages": "49-53",
                "guide": "Guia_Guarda_Salvador_2026_Estudo.pdf",
            },
        })
write_json(DATA / "lessons" / f"{CONTEST_ID}.json", lessons)


# Fontes oficiais e referências. A aplicação exibe isso separadamente dos resumos.
laws = [
    {"id": "cf88", "name": "Constituição Federal de 1988", "url": "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm", "kind": "official"},
    {"id": "cc", "name": "Código Civil - Lei 10.406/2002", "url": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm", "kind": "official"},
    {"id": "cp", "name": "Código Penal", "url": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm", "kind": "official"},
    {"id": "cpp", "name": "Código de Processo Penal", "url": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del3689compilado.htm", "kind": "official"},
    {"id": "l11340", "name": "Lei 11.340/2006 - Maria da Penha", "url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm", "kind": "official"},
    {"id": "l11343", "name": "Lei 11.343/2006 - Drogas", "url": "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11343.htm", "kind": "official"},
    {"id": "l13022", "name": "Lei 13.022/2014 - Estatuto Geral das Guardas Municipais", "url": "https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l13022.htm", "kind": "official"},
    {"id": "l13869", "name": "Lei 13.869/2019 - Abuso de Autoridade", "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/lei/l13869.htm", "kind": "official"},
    {"id": "l14133", "name": "Lei 14.133/2021 - Licitações e Contratos", "url": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm", "kind": "official"},
    {"id": "l15358", "name": "Lei 15.358/2026", "url": "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/lei/l15358.htm", "kind": "official"},
    {"id": "fgv", "name": "Página oficial do concurso - FGV", "url": "https://conhecimento.fgv.br/concursos/pmsguarda2026", "kind": "official"},
]
write_json(DATA / "laws" / f"{CONTEST_ID}.json", laws)


# ---------- Questões autorais ----------
questions: list[dict[str, Any]] = []


def add_q(subject: str, topic: str, stem: str, options: list[str], answer: int, explanation: str, difficulty: str = "medium", tags: list[str] | None = None) -> None:
    qid = f"q-{subject}-{topic}-{len(questions)+1:04d}"
    questions.append({
        "id": qid,
        "contestId": CONTEST_ID,
        "subjectId": subject,
        "topicIds": [topic],
        "difficulty": difficulty,
        "sourceType": "authorial",
        "sourceLabel": "Questão autoral para treino - não é questão oficial da FGV",
        "stem": stem,
        "options": options,
        "answerIndex": answer,
        "explanation": explanation,
        "tags": tags or [],
    })


# Português - 48 questões distribuídas por todos os tópicos.
port_bank = [
    ("interpretacao-argumentativa", "Um artigo afirma: 'A iluminação pública não elimina a criminalidade, mas pode reduzir oportunidades para determinados delitos'. Qual alternativa preserva o sentido?", ["A iluminação pública elimina delitos.", "A iluminação pública pode contribuir para reduzir certas oportunidades de delito, sem garantir eliminação da criminalidade.", "A iluminação pública aumenta necessariamente a criminalidade.", "O texto considera iluminação irrelevante.", "O texto garante redução de todos os delitos."], 1, "O texto usa 'pode' e limita o efeito a oportunidades para determinados delitos; não faz promessa absoluta."),
    ("interpretacao-argumentativa", "Em um texto argumentativo, a tese corresponde principalmente:", ["ao exemplo mais longo", "à ideia central que o autor procura sustentar", "a qualquer dado numérico", "ao título obrigatoriamente", "à última palavra do texto"], 1, "Tese é a posição ou ideia central defendida."),
    ("interpretacao-argumentativa", "A alternativa que apresenta informação verdadeira, mas não sustentada pelo texto, deve ser:", ["aceita porque é verdadeira", "aceita se estiver em linguagem formal", "rejeitada, pois a interpretação deve se apoiar no texto", "aceita se parecer lógica", "rejeitada apenas em textos narrativos"], 2, "Interpretação exige suporte textual, não conhecimento externo solto."),
    ("interpretacao-argumentativa", "No trecho 'Embora o custo inicial seja alto, a manutenção é econômica', a palavra 'embora' introduz:", ["causa", "conclusão", "concessão", "finalidade", "explicação"], 2, "'Embora' apresenta uma concessão: reconhece um fato sem impedir a conclusão principal."),
    ("construcao-textual", "Em 'A equipe vistoriou o prédio. Depois, registrou as ocorrências', 'depois' ajuda principalmente a:", ["negar a primeira frase", "marcar sequência temporal", "introduzir oposição", "indicar causa", "substituir o sujeito"], 1, "O advérbio conecta as ações por sequência temporal."),
    ("construcao-textual", "Qual recurso contribui para ligar frases de um mesmo texto?", ["Conectivos e pronomes referenciais", "Apenas letras maiúsculas", "Somente números", "Apenas ponto final", "Qualquer palavra estrangeira"], 0, "Conectivos e referências pronominais são mecanismos clássicos de encadeamento."),
    ("construcao-textual", "Se um parágrafo introduz um assunto sem qualquer ligação com o tema anterior, ocorre principalmente um problema de:", ["acentuação", "encadeamento textual", "flexão nominal", "ortografia", "formação de plural"], 1, "A quebra é de construção/encadeamento do texto."),
    ("progressao-textual", "Há progressão textual quando:", ["o texto repete a mesma frase sem acrescentar nada", "cada parte retoma o tema e acrescenta informação", "todo período tem o mesmo tamanho", "não há conectivos", "o autor evita qualquer exemplo"], 1, "Progressão envolve avanço informacional."),
    ("progressao-textual", "Um segundo período que explica a causa do problema apresentado no primeiro realiza progressão por:", ["contradição", "explicação", "cópia", "apagamento", "pontuação"], 1, "A nova informação explica a anterior."),
    ("coesao-coerencia-intertextualidade", "Em 'Marina entregou o relatório. Ela revisou os dados antes', o pronome 'ela' exerce papel de:", ["coesão referencial", "incoerência", "interjeição", "estrangeirismo", "pontuação"], 0, "O pronome retoma 'Marina', ligando as frases."),
    ("coesao-coerencia-intertextualidade", "Um texto afirma que 'nenhum veículo entrou' e depois que 'todos os veículos que entraram foram revistados', sem contexto que resolva a diferença. O problema principal é de:", ["coerência", "acentuação", "regência", "hífen", "classe de palavra"], 0, "As ideias entram em choque, afetando a coerência global."),
    ("coesao-coerencia-intertextualidade", "Uma notícia que faz alusão explícita a uma frase conhecida de outro texto utiliza:", ["intertextualidade", "somente denotação", "erro sintático", "numeral", "proporcionalidade"], 0, "Alusão e citação são formas de intertextualidade."),
    ("reescritura", "A frase 'Apesar do atraso, a reunião ocorreu' mantém o sentido básico em:", ["Porque houve atraso, a reunião não ocorreu.", "Embora tenha havido atraso, a reunião ocorreu.", "A reunião ocorreu antes do atraso.", "Não houve atraso nem reunião.", "A reunião ocorreu para causar atraso."], 1, "'Apesar de' e 'embora' podem marcar concessão."),
    ("reescritura", "Trocar 'pode ocorrer' por 'ocorrerá' tende a:", ["preservar exatamente o grau de certeza", "aumentar o grau de certeza", "criar negação", "transformar em pergunta", "eliminar o verbo"], 1, "'Pode' marca possibilidade; o futuro assertivo é mais categórico."),
    ("reescritura", "Na reescrita de uma frase, qual elemento merece atenção especial?", ["Apenas o tamanho", "Relações de causa, condição, oposição e conclusão", "Somente a fonte tipográfica", "A cor da página", "O número de letras"], 1, "Conectivos e relações lógicas podem alterar o sentido mesmo com palavras semelhantes."),
    ("vocabulario", "Em 'a fiscalização foi rigorosa', um sinônimo contextual adequado para 'rigorosa' é:", ["descuidada", "severa", "imaginária", "silenciosa", "curta"], 1, "No contexto, 'severa' aproxima-se do sentido de rigorosa."),
    ("vocabulario", "Para escolher um sinônimo em questão de prova, o procedimento mais seguro é:", ["consultar apenas a primeira acepção mental", "avaliar a palavra dentro da frase", "ignorar o contexto", "trocar sempre por palavra mais longa", "usar qualquer antônimo"], 1, "O contexto determina o sentido relevante."),
    ("estrangeirismos", "A palavra 'download', em contexto de informática, é exemplo de:", ["estrangeirismo", "numeral", "pronome", "interjeição", "preposição"], 0, "É termo de origem inglesa incorporado ao uso tecnológico."),
    ("estrangeirismos", "Sobre estrangeirismos, é correto afirmar que:", ["são sempre inadequados", "podem ser adequados conforme contexto e uso", "não existem na informática", "só aparecem em textos literários", "são erros ortográficos obrigatórios"], 1, "A adequação depende de contexto e convenções de uso."),
    ("classes-palavras", "Em 'o atendimento foi extremamente rápido', 'extremamente' é:", ["substantivo", "advérbio", "artigo", "pronome", "preposição"], 1, "Modifica o adjetivo 'rápido', funcionando como advérbio de intensidade."),
    ("classes-palavras", "Em 'os agentes atentos observaram a entrada', a palavra 'atentos' é:", ["adjetivo", "verbo", "preposição", "artigo", "interjeição"], 0, "Caracteriza o substantivo 'agentes'."),
    ("classes-palavras", "Em 'eles chegaram cedo', 'eles' é:", ["pronome", "substantivo próprio", "conjunção", "advérbio", "numeral"], 0, "'Eles' substitui nomes e funciona como pronome pessoal."),
    ("sintaxe-pontuacao", "Qual frase separa indevidamente sujeito e verbo por vírgula?", ["Os candidatos chegaram cedo.", "Os candidatos, chegaram cedo.", "Cansados, os candidatos chegaram cedo.", "Os candidatos chegaram cedo, mas esperaram muito.", "Quando o portão abriu, os candidatos entraram."], 1, "Em ordem direta, não se separa sujeito de verbo por vírgula sem motivo sintático."),
    ("sintaxe-pontuacao", "Em 'A equipe, após a vistoria, registrou o fato', as vírgulas isolam:", ["um termo deslocado/intercalado", "o sujeito do verbo por erro", "uma pergunta", "um numeral", "um estrangeirismo"], 0, "A expressão adverbial intercalada pode ser isolada por vírgulas."),
    ("sintaxe-pontuacao", "Na frase 'O agente verificou o documento e liberou a entrada', o sujeito de 'liberou' é:", ["documento", "entrada", "o agente", "inexistente", "indeterminado obrigatoriamente"], 2, "O sujeito permanece 'o agente', oculto no segundo verbo."),
    ("sintaxe-pontuacao", "A pontuação pode:", ["apenas indicar respiração", "organizar estrutura sintática e influenciar sentido", "ser ignorada na escrita formal", "substituir todos os conectivos", "mudar a classe de qualquer palavra automaticamente"], 1, "Pontuação é recurso sintático e semântico, não só pausa de fala."),
    ("variacao-linguistica", "Uma mensagem informal entre amigos e um ofício administrativo podem exigir registros diferentes porque:", ["a língua não varia", "a adequação depende da situação comunicativa", "apenas o ofício usa palavras", "todo uso informal é incorreto", "a região elimina a gramática"], 1, "Variação e adequação consideram contexto, interlocutores e finalidade."),
    ("variacao-linguistica", "Norma-padrão e variação linguística:", ["são conceitos incompatíveis", "podem coexistir; a adequação depende do contexto", "significam exatamente a mesma coisa", "só existem na fala", "não aparecem em concursos"], 1, "O estudo reconhece variedades e também situações em que a norma-padrão é exigida."),
    ("denotacao-conotacao", "Em 'a notícia caiu como uma bomba', o trecho usa principalmente linguagem:", ["denotativa", "conotativa", "matemática", "jurídica literal", "sem sentido"], 1, "A expressão é figurada, não descreve uma explosão real."),
    ("denotacao-conotacao", "Em 'o portão tem três metros de largura', predomina sentido:", ["conotativo", "denotativo", "irônico", "metafórico", "intertextual"], 1, "A frase descreve medida literal."),
    ("nova-ortografia", "Segundo a ortografia atual, a grafia correta é:", ["auto-escola", "autoescola", "auto escola", "aútoescola", "auto-escolá"], 1, "'Autoescola' é escrita sem hífen."),
    ("nova-ortografia", "A grafia correta é:", ["microondas", "micro ondas", "micro-ondas", "mícro-ondas", "micro--ondas"], 2, "O prefixo 'micro-' mantém hífen diante de palavra iniciada por 'o'."),
]
for row in port_bank:
    add_q("portugues", *row)
# Variações adicionais de português para aumentar o banco sem copiar enunciados.
extra_port = [
    ("interpretacao-argumentativa", "Quando um autor apresenta um exemplo para sustentar sua tese, o exemplo funciona como:", ["argumento ou evidência", "pontuação", "negação automática", "título", "erro de coesão"], 0, "O exemplo pode servir de evidência que sustenta a tese."),
    ("construcao-textual", "O pronome em 'o relatório foi entregue e sua análise começou' retoma principalmente:", ["relatório", "entrega", "começou", "sua", "nenhum termo"], 0, "'Sua' relaciona a análise ao relatório no contexto."),
    ("progressao-textual", "Acrescentar uma consequência depois de apresentar uma causa contribui para:", ["progressão textual", "apagamento do tema", "erro ortográfico", "estrangeirismo", "redução vocabular"], 0, "A informação nova faz o texto avançar."),
    ("coesao-coerencia-intertextualidade", "O conector 'portanto' costuma introduzir:", ["conclusão", "oposição", "condição", "concessão", "enumeração"], 0, "'Portanto' é conectivo conclusivo."),
    ("reescritura", "Em geral, trocar 'porque' causal por 'portanto' sem alterar a ordem das orações tende a:", ["manter sempre o sentido", "mudar a relação lógica", "corrigir qualquer erro", "eliminar o verbo", "criar intertextualidade"], 1, "'Porque' pode marcar causa; 'portanto', conclusão."),
    ("vocabulario", "No contexto 'a informação é sensível', 'sensível' pode significar:", ["que sente dor fisicamente obrigatoriamente", "que exige cuidado ou proteção", "que é falsa", "que é numérica", "que é estrangeira"], 1, "Em segurança da informação, 'sensível' pode indicar dado que exige proteção."),
    ("classes-palavras", "Em 'mas o acesso permaneceu bloqueado', 'mas' é:", ["conjunção", "substantivo", "artigo", "verbo", "numeral"], 0, "'Mas' é conjunção adversativa."),
    ("sintaxe-pontuacao", "Em uma enumeração simples, a vírgula normalmente serve para:", ["separar itens", "separar sujeito e verbo obrigatoriamente", "criar pergunta", "marcar porcentagem", "substituir acento"], 0, "Vírgulas podem separar elementos de mesma função em enumeração."),
    ("variacao-linguistica", "A expressão adequada a um relatório oficial tende a privilegiar:", ["registro formal e claro", "gíria sem contexto", "abreviação incompreensível", "ambiguidade intencional", "erro ortográfico"], 0, "Situação administrativa costuma exigir clareza e formalidade."),
    ("denotacao-conotacao", "Em 'o sistema abriu uma janela', falando de interface gráfica, 'janela' é um termo técnico já convencional. Nesse contexto, a interpretação correta depende:", ["do contexto de informática", "apenas do sentido arquitetônico", "da rima", "do tamanho da palavra", "do número de sílabas"], 0, "O contexto define o sentido relevante."),
    ("nova-ortografia", "O trema em palavras portuguesas de uso comum após o Acordo Ortográfico:", ["é obrigatório em todas", "foi abolido, salvo nomes próprios estrangeiros e derivados", "substituiu o hífen", "passou a marcar plural", "virou acento agudo"], 1, "O trema deixou de ser usado em palavras portuguesas comuns."),
    ("interpretacao-argumentativa", "Uma conclusão que vai além das evidências apresentadas pelo texto é uma inferência:", ["necessariamente válida", "não sustentada", "obrigatoriamente denotativa", "sempre gramatical", "sempre intertextual"], 1, "Inferência precisa ser suportada pelas informações do texto."),
    ("sintaxe-pontuacao", "Na frase 'Se chover, o evento será remarcado', a oração inicial expressa:", ["condição", "causa obrigatória", "conclusão", "explicação", "tempo passado"], 0, "'Se' introduz condição."),
    ("classes-palavras", "Em 'três equipes chegaram', 'três' é:", ["numeral", "verbo", "advérbio", "preposição", "interjeição"], 0, "Indica quantidade numérica."),
    ("coesao-coerencia-intertextualidade", "Em 'o projeto foi aprovado; contudo, ainda depende de regulamentação', 'contudo' indica:", ["oposição/contraste", "conclusão", "finalidade", "tempo", "condição"], 0, "'Contudo' é conectivo adversativo."),
    ("reescritura", "A forma 'não apenas estudou, mas também revisou' estabelece relação de:", ["adição com reforço", "causa", "condição", "negação total", "tempo"], 0, "A estrutura adiciona duas ações e reforça a segunda."),
]
for row in extra_port:
    add_q("portugues", *row)


# RLM - geração de 64 questões concretas e variadas.
for pct, base in [(10, 240), (15, 320), (25, 180), (30, 450), (12, 275), (40, 90), (8, 625), (35, 260)]:
    correct = base * pct / 100
    distractors = [correct + 10, correct - 10, base + pct, base * (1 + pct / 100)]
    values = [correct] + distractors
    # remove duplicados preservando cinco alternativas
    uniq = []
    for v in values:
        if v not in uniq:
            uniq.append(v)
    while len(uniq) < 5:
        uniq.append(correct + 5 * len(uniq))
    random.shuffle(uniq)
    ans = uniq.index(correct)
    add_q("rlm", "porcentagem-proporcao", f"Quanto corresponde a {pct}% de {base}?", [f"{v:g}" for v in uniq], ans, f"{pct}% = {pct/100:g}. Multiplicando {base} por {pct/100:g}, obtemos {correct:g}.", "easy")

for a, b in [(3, 7), (5, 11), (8, 20), (12, 31), (15, 40), (22, 57)]:
    x = b - a
    opts = [x, x+2, x-2, b+a, b]
    random.shuffle(opts)
    add_q("rlm", "algebra", f"Resolva a equação x + {a} = {b}.", [str(v) for v in opts], opts.index(x), f"Subtraindo {a} dos dois lados: x={b}-{a}={x}.", "easy")

for terms, r in [([2,5,8,11],3), ([10,14,18,22],4), ([7,12,17,22],5)]:
    nxt=terms[-1]+r
    opts=[nxt,nxt+r,nxt-r,terms[-1]*2,terms[0]+terms[-1]]
    random.shuffle(opts)
    add_q("rlm","sequencias-pa-pg",f"Qual é o próximo termo da sequência {', '.join(map(str,terms))}, ...?",[str(x) for x in opts],opts.index(nxt),f"A diferença entre termos é constante e vale {r}; trata-se de uma PA. Próximo termo: {terms[-1]}+{r}={nxt}.","easy")

for terms, ratio in [([2,6,18],3),([5,10,20],2),([3,12,48],4)]:
    nxt=terms[-1]*ratio
    opts=[nxt,nxt+ratio,nxt-ratio,terms[-1]+ratio,terms[-1]*2]
    random.shuffle(opts)
    add_q("rlm","sequencias-pa-pg",f"Na sequência {', '.join(map(str,terms))}, ... qual é o próximo termo?",[str(x) for x in opts],opts.index(nxt),f"Cada termo é o anterior multiplicado por {ratio}; é uma PG de razão {ratio}. Próximo: {nxt}.","easy")

logic_qs = [
    ("proposicoes", "Qual das frases é uma proposição?", ["Feche a porta.", "Que horas são?", "Salvador é a capital da Bahia.", "x + 2 = 5, sem valor definido para x.", "Tomara que chova!"], 2, "A frase declarativa pode ser classificada como verdadeira ou falsa."),
    ("proposicoes", "A conjunção P e Q é verdadeira quando:", ["P e Q são verdadeiras", "apenas P é verdadeira", "apenas Q é verdadeira", "pelo menos uma é falsa", "P e Q têm valores diferentes"], 0, "A conjunção só é verdadeira se ambas forem verdadeiras."),
    ("proposicoes", "A disjunção inclusiva P ou Q é falsa quando:", ["P é verdadeira", "Q é verdadeira", "ambas são verdadeiras", "ambas são falsas", "apenas uma é verdadeira"], 3, "O 'ou' inclusivo só é falso quando as duas proposições são falsas."),
    ("equivalencias", "Uma forma equivalente a 'Se P, então Q' é:", ["P e Q", "não P ou Q", "P ou não Q", "Q e não P", "não P e não Q"], 1, "A condicional P→Q é equivalente a ¬P∨Q."),
    ("equivalencias", "A negação de 'P e Q' é:", ["não P e não Q", "não P ou não Q", "P ou Q", "P e não Q", "não P e Q"], 1, "Lei de De Morgan: ¬(P∧Q) ≡ ¬P∨¬Q."),
    ("equivalencias", "A negação de 'P ou Q' é:", ["não P e não Q", "não P ou não Q", "P e Q", "P ou não Q", "não P ou Q"], 0, "Lei de De Morgan: ¬(P∨Q) ≡ ¬P∧¬Q."),
    ("problemas-raciocinio", "Ana chegou antes de Bruno, e Bruno antes de Caio. Quem chegou primeiro?", ["Ana", "Bruno", "Caio", "Não é possível saber", "Ana e Caio juntos"], 0, "Pela transitividade das relações, Ana antecede Bruno e Caio."),
    ("problemas-raciocinio", "Em uma fila, Davi está atrás de Elisa e à frente de Fábio. Qual ordem é compatível?", ["Davi-Elisa-Fábio", "Elisa-Davi-Fábio", "Fábio-Davi-Elisa", "Elisa-Fábio-Davi", "Fábio-Elisa-Davi"], 1, "Elisa deve vir antes de Davi, e Davi antes de Fábio."),
]
for row in logic_qs: add_q("rlm", *row)

for a,b in [(4,3),(8,5),(10,6),(12,7)]:
    area=a*b
    perimeter=2*(a+b)
    opts=[area,perimeter,a+b,a*b*2,abs(a-b)]
    random.shuffle(opts)
    add_q("rlm","geometria-basica",f"Um retângulo mede {a} m por {b} m. Qual é sua área?",[f"{x} m²" for x in opts],opts.index(area),f"Área do retângulo = base × altura = {a}×{b}={area} m².","easy")

for sides in [(3,4),(6,8),(5,12)]:
    hyp=int(math.sqrt(sides[0]**2+sides[1]**2))
    opts=[hyp,hyp+1,hyp-1,sum(sides),sides[1]]
    random.shuffle(opts)
    add_q("rlm","semelhanca-triangulo",f"Um triângulo retângulo tem catetos {sides[0]} e {sides[1]}. Qual é a hipotenusa?",[str(x) for x in opts],opts.index(hyp),f"Pelo Teorema de Pitágoras: h²={sides[0]}²+{sides[1]}²={hyp*hyp}; logo h={hyp}.","medium")

measure_qs=[
    ("unidades-medida","2,5 km correspondem a:",["25 m","250 m","2.500 m","25.000 m","250.000 m"],2,"1 km = 1.000 m; 2,5 km = 2.500 m."),
    ("unidades-medida","1 hora e 45 minutos correspondem a:",["95 min","100 min","105 min","115 min","145 min"],2,"1 hora = 60 min; 60+45=105."),
    ("plano-cartesiano","O ponto (-3, 4) está:",["à direita e acima","à esquerda e acima","à esquerda e abaixo","sobre o eixo x","sobre o eixo y"],1,"x negativo: esquerda; y positivo: acima."),
    ("reta-numerica","Qual é o maior número?",["-8","-3","-5","-10","-7"],1,"Entre negativos, o mais próximo de zero é o maior."),
    ("numeros-operacoes","Quanto é 3/4 de 20?",["5","10","15","16","18"],2,"20×3/4=15."),
    ("numeros-operacoes","O valor de 2 + 3 × 4 é:",["20","14","24","18","10"],1,"Multiplicação vem antes da adição: 3×4=12; 2+12=14."),
    ("contagem-probabilidade","Com 4 camisas e 3 calças, quantas combinações de uma camisa com uma calça são possíveis?",["7","12","16","24","1"],1,"Princípio multiplicativo: 4×3=12."),
    ("contagem-probabilidade","Em um dado comum, a probabilidade de sair número par é:",["1/6","1/3","1/2","2/3","5/6"],2,"Há 3 resultados pares em 6 igualmente prováveis: 3/6=1/2."),
    ("diagramas-graficos","Uma tabela registra 80 ocorrências em março e 100 em abril. O aumento percentual, tomando março como base, foi:",["10%","20%","25%","40%","80%"],2,"Aumento=20; 20/80=0,25=25%."),
    ("conjuntos","Se A={1,2,3,4} e B={3,4,5}, então A∩B é:",["{1,2}","{3,4}","{5}","{1,2,5}","{1,2,3,4,5}"],1,"Interseção contém os elementos comuns: 3 e 4."),
    ("juros","R$ 1.000 aplicados a juros simples de 2% ao mês por 4 meses geram juros de:",["R$20","R$40","R$80","R$100","R$1.080"],2,"J=C×i×t=1000×0,02×4=80."),
    ("medidas-area-volume","Uma caixa retangular de dimensões 2 m, 3 m e 5 m tem volume de:",["10 m³","15 m³","30 m³","60 m³","150 m³"],2,"Volume=2×3×5=30 m³."),
]
for row in measure_qs: add_q("rlm", *row)

# questões de proporcionalidade direta/inversa mais contextualizadas
context_math=[
    ("porcentagem-proporcao","Uma equipe realiza 120 atendimentos em 4 horas, mantendo ritmo constante. Em 6 horas, quantos atendimentos realizará?",["160","180","200","220","240"],1,"É proporcionalidade direta: 120/4=30 por hora; 30×6=180."),
    ("porcentagem-proporcao","Quatro agentes concluem uma tarefa em 6 horas, com produtividade igual. Mantidas as condições, oito agentes concluiriam em:",["2 h","3 h","4 h","6 h","12 h"],1,"Grandezas inversamente proporcionais: dobrando agentes, o tempo cai pela metade: 3 h."),
    ("algebra","Dois números somam 30 e um deles é 8 unidades maior que o outro. O maior é:",["11","15","19","22","30"],2,"x+(x+8)=30 => 2x=22 => x=11; maior=19."),
    ("sequencias-pa-pg","Em uma PA de primeiro termo 5 e razão 4, o 6º termo é:",["21","25","29","30","33"],1,"a6=5+(6-1)×4=25."),
    ("juros","Em juros compostos de 10% ao período, R$1.000 tornam-se após dois períodos:",["R$1.100","R$1.200","R$1.210","R$1.220","R$1.300"],2,"1000×1,1²=1210."),
]
for row in context_math: add_q("rlm", *row)


# Informática - 22 questões.
info_qs=[
    ("arquivos-digitais","Qual extensão é normalmente associada a planilha do Microsoft Excel moderno?",[".xlsx",".jpg",".mp3",".pdf",".exe"],0,".xlsx é formato comum de pasta de trabalho do Excel."),
    ("arquivos-digitais","Um arquivo .jpg é normalmente associado a:",["imagem","planilha","áudio sem compressão","executável","banco SQL"],0,"JPEG/JPG é formato de imagem."),
    ("pdf","Uma característica comum do PDF é:",["preservar a apresentação do documento entre dispositivos","ser sempre editável como planilha","executar macros obrigatoriamente","ser exclusivamente áudio","não permitir impressão"],0,"PDF é voltado a distribuição com layout estável."),
    ("windows","No Windows, uma pasta é usada principalmente para:",["organizar arquivos e outras pastas","aumentar memória RAM","substituir o processador","criar senha bancária","converter monitor em impressora"],0,"Pastas organizam itens no sistema de arquivos."),
    ("windows","O mecanismo de busca do sistema operacional serve para:",["localizar arquivos, programas e recursos","formatar automaticamente todo disco","desligar a internet","alterar hardware fisicamente","criar PDF por definição"],0,"Busca ajuda a localizar recursos."),
    ("editores-texto","Cabeçalho em editor de texto é uma área normalmente:",["repetida no topo das páginas","usada apenas para fórmula de Excel","invisível e sem conteúdo","destinada a vídeo","que apaga o rodapé"],0,"Cabeçalhos podem repetir informação no topo das páginas."),
    ("editores-texto","A configuração de página pode incluir:",["margens e orientação","senha do roteador obrigatoriamente","placa de vídeo","taxa de juros","endereço IP do servidor"],0,"Margens e orientação são configurações típicas de página."),
    ("localizar-substituir","O comando localizar e substituir é útil para:",["trocar ocorrências de um texto por outro","desfragmentar memória RAM","ligar impressora fisicamente","criar usuário no Windows","medir banda da internet"],0,"A função procura um texto e pode substituí-lo em múltiplas ocorrências."),
    ("word-arquivos","Controle de alterações no Word serve para:",["registrar edições para revisão","aumentar resolução de imagens automaticamente","formatar disco","criar conexão VPN por si só","calcular juros compostos"],0,"O recurso registra inserções, exclusões e outras alterações."),
    ("word-arquivos","Uma macro em suíte de escritório é, em geral:",["sequência automatizada de comandos ou código","tipo de monitor","formato de áudio","método de impressão manual","senha obrigatória"],0,"Macros automatizam tarefas."),
    ("excel","Em uma planilha, fórmula geralmente começa com:",["=","#","@","%","&"],0,"No Excel, fórmulas usualmente começam por '='."),
    ("excel","O recurso Filtro é usado para:",["mostrar linhas que atendem critérios","apagar todas as fórmulas","converter planilha em áudio","desligar o computador","mudar tamanho físico do monitor"],0,"Filtros exibem subconjuntos conforme critérios."),
    ("excel","Ordenar uma tabela por uma coluna significa:",["reorganizar linhas conforme valores dessa coluna","somar automaticamente todas as células","remover proteção","salvar como imagem obrigatoriamente","criar uma macro"],0,"Ordenação reorganiza registros segundo uma chave."),
    ("internet-seguranca","Upload significa:",["enviar dados do dispositivo para um serviço remoto","receber dados da internet","apagar cache","criptografar obrigatoriamente","medir CPU"],0,"Upload é envio; download é recebimento."),
    ("internet-seguranca","Uma senha forte tende a:",["ser longa e difícil de adivinhar","usar apenas 123456","ser igual ao nome do usuário","ser compartilhada publicamente","ter uma única letra"],0,"Comprimento e imprevisibilidade elevam a resistência a ataques de adivinhação."),
    ("internet-seguranca","Criptografia busca principalmente:",["proteger a confidencialidade e/ou integridade por transformação controlada dos dados","aumentar tamanho da tela","imprimir mais rápido","substituir backup","desligar firewall"],0,"Criptografia transforma dados com uso de chaves/algoritmos para proteção."),
    ("internet-seguranca","Um navegador web é usado para:",["acessar e interagir com recursos da Web","editar BIOS obrigatoriamente","trocar memória RAM","medir pressão arterial","formatar papel"],0,"Browsers acessam sites e aplicações web."),
    ("internet-seguranca","Banda de uma conexão está relacionada à:",["capacidade de transferência de dados por unidade de tempo","quantidade de pastas do Windows","tamanho do teclado","número de páginas de um PDF","quantidade de cores do Word"],0,"Banda descreve capacidade de transmissão."),
    ("excel","Se A1 contém 10 e A2 contém 5, a fórmula =A1+A2 resulta em:",["5","10","15","50","105"],2,"Soma dos valores: 10+5=15."),
    ("word-arquivos","Salvar um documento com senha de proteção tem como objetivo principal:",["restringir acesso ou alteração conforme o recurso usado","aumentar o processador","melhorar a internet","criar tabela dinâmica","mudar o teclado"],0,"Proteção por senha pode limitar abertura/edição conforme configuração."),
    ("pdf","Converter um documento para PDF costuma ser útil quando se deseja:",["distribuir versão com layout mais estável","transformá-lo em executável","aumentar memória RAM","criar áudio","substituir backup automaticamente"],0,"PDF é muito usado para distribuição e impressão consistente."),
    ("internet-seguranca","Token de segurança pode ser usado como:",["fator adicional de autenticação","tipo de papel","extensão de imagem","classe gramatical","unidade de área"],0,"Tokens podem gerar ou armazenar credenciais como fator adicional."),
]
for row in info_qs: add_q("informatica", *row)


# Constitucional/Civil - 28 questões conceituais, sem inventar artigo específico quando não necessário.
cc_qs=[
    ("const-conceito-principios","A Constituição ocupa posição central no ordenamento porque:",["organiza o Estado e estabelece normas fundamentais","é simples manual administrativo","vale apenas para Municípios","não trata de direitos","é inferior a decretos"],0,"A Constituição estrutura o Estado e fixa direitos e regras fundamentais."),
    ("const-direitos","Direitos sociais integram o estudo de:",["direitos e garantias fundamentais","geometria","direito empresarial exclusivamente","ortografia","planilhas"],0,"O edital inclui direitos sociais dentro de direitos e garantias fundamentais."),
    ("const-organizacao","União, Estados, Distrito Federal e Municípios aparecem no edital dentro de:",["organização político-administrativa","direito das obrigações","teoria do crime","marketing","socorrismo"],0,"São entes estudados na organização político-administrativa."),
    ("const-administracao","O estudo constitucional da Administração Pública inclui:",["disposições gerais e servidores públicos","apenas empresas privadas","somente direito penal","apenas orçamento doméstico","marketing de vendas"],0,"É exatamente o recorte indicado no edital."),
    ("const-judiciario","O Poder Judiciário é estudado no edital quanto a:",["disposições gerais, órgãos, competências e estrutura","somente eleições","somente tributos municipais","apenas contratos privados","somente gramática"],0,"Esse é o recorte curricular expresso."),
    ("const-cnj","O CNJ está associado no edital a:",["composição e competência","cálculo de juros","competência tributária municipal apenas","controle de estoque","arquivo PDF"],0,"O edital cobra composição e competência do CNJ."),
    ("const-funcoes-justica","Qual grupo integra as funções essenciais à Justiça listadas no edital?",["Ministério Público, advocacia e defensoria pública","Banco Central, Correios e IBGE","Prefeitura, Câmara e mercado","Polícia Rodoviária e cartório apenas","empresa e sindicato"],0,"São os três blocos expressamente citados."),
    ("civil-lindb","Analogia, princípios gerais e equidade aparecem no edital dentro de:",["aplicação/interpretação da lei e LINDB","geometria","direito eleitoral","redes de computadores","TAF"],0,"O recorte de Civil reúne esses instrumentos com a LINDB."),
    ("civil-pessoas","Em Direito Civil, pessoa natural e pessoa jurídica são:",["categorias de sujeitos de direito","tipos de pena","operações matemáticas","formatos de arquivo","modalidades de corrida"],0,"São categorias fundamentais da disciplina de pessoas."),
    ("civil-pessoas","Emancipação está relacionada principalmente à:",["capacidade civil","pena privativa de liberdade","download","PA","licitação"],0,"É instituto ligado à capacidade civil."),
    ("civil-bens","Bens públicos aparecem no edital dentro do estudo de:",["bens","ação penal","probabilidade","Word","marketing"],0,"O tópico de bens inclui bens públicos."),
    ("civil-fatos","Prescrição e decadência aparecem no edital em:",["fatos jurídicos e também responsabilidade civil","apenas informática","somente geometria","TAF","políticas públicas apenas"],0,"O edital menciona prescrição/decadência em mais de um recorte civil."),
    ("civil-obrigacoes","Adimplemento significa, em linhas gerais:",["cumprimento da obrigação","criação de crime","formatação de texto","negação lógica","aumento de pena"],0,"No estudo das obrigações, adimplemento corresponde ao cumprimento."),
    ("civil-obrigacoes","Inadimplemento está ligado a:",["não cumprimento da obrigação","aumento de velocidade de download","direito político","regra de hífen","PA"],0,"É o descumprimento da prestação devida."),
    ("civil-responsabilidade","Dano moral e perda de uma chance aparecem no edital no tópico de:",["responsabilidade civil","Poder Judiciário","conjuntos","Internet","marketing"],0,"São subtemas expressamente citados em responsabilidade civil."),
    ("civil-responsabilidade","Desconsideração da personalidade jurídica busca, em determinadas hipóteses legais:",["superar a separação patrimonial para alcançar responsáveis","abolir toda pessoa jurídica","criar crime automaticamente","substituir contrato","eliminar a Constituição"],0,"O instituto permite afastar pontualmente a autonomia patrimonial quando presentes requisitos legais."),
    ("civil-jurisprudencia","O edital cita jurisprudência e súmulas de:",["STF, STJ e TJBA","apenas STF","apenas tribunais estrangeiros","somente TCU","apenas Câmara Municipal"],0,"Os três tribunais são expressamente mencionados."),
]
for row in cc_qs: add_q("constitucional-civil", *row)
# duplicar cobertura com enunciados contextuais novos
cc_extra=[
    ("const-direitos","Nacionalidade, cidadania e direitos políticos estão no edital associados a:",["direitos e garantias fundamentais","direito das coisas","processo civil","contabilidade","informática"],0,"Integram o bloco constitucional listado."),
    ("const-organizacao","Municípios são mencionados expressamente no tópico de:",["organização político-administrativa","penas","prova processual","juros","arquivos"],0,"O edital lista Municípios entre os entes."),
    ("const-administracao","Servidores públicos aparecem tanto no conteúdo constitucional quanto em legislação municipal. Isso significa que o aluno deve:",["respeitar o recorte de cada disciplina e não misturar automaticamente as normas","estudar só uma vez e ignorar diferenças","retirar o tema do cronograma","substituir por direito penal","estudar apenas marketing"],0,"O mesmo termo pode aparecer em recortes normativos diferentes; o contexto da matéria importa."),
    ("civil-fatos","Negócio jurídico pertence ao estudo de:",["fatos jurídicos","Poder Judiciário","proposições","Excel","TAF"],0,"É subtema de fatos jurídicos no edital."),
    ("civil-responsabilidade","Indenização por dano moral é associada no edital a:",["responsabilidade civil","direito eleitoral","estatística","internet","políticas públicas"],0,"Está expressamente listada no bloco de responsabilidade civil."),
    ("civil-bens","O recorte de bens do edital inclui:",["bens em si, reciprocamente considerados e bens públicos","somente bens móveis","somente imóveis privados","somente dinheiro","apenas herança"],0,"Esse é o trio indicado no Anexo I."),
    ("const-funcoes-justica","A Defensoria Pública aparece no edital como:",["função essencial à Justiça","órgão do Legislativo","empresa pública","unidade de medida","tribunal superior"],0,"A Defensoria integra as funções essenciais à Justiça."),
    ("civil-lindb","Quando o edital menciona 'aplicação da lei no tempo e no espaço', ele está no bloco de:",["Direito Civil/LINDB","Informática","RLM","TAF","Administração Financeira"],0,"É parte do recorte de Direito Civil."),
]
for row in cc_extra: add_q("constitucional-civil", *row)


# Penal/Processual - 26 questões de fundamento e associação correta ao conteúdo.
pp_qs=[
    ("penal-conceito-fontes","O princípio da reserva legal, listado no edital, está ligado à ideia de que:",["não há crime nem pena sem previsão legal anterior, conforme o princípio da legalidade","todo ato moral é crime","qualquer costume cria pena","uma portaria pode criar livremente crime","a analogia sempre cria crime"],0,"A legalidade penal exige lei anterior para definir crime e pena."),
    ("penal-lei","A lei penal no tempo integra o estudo de:",["aplicação da lei penal","Word","geometria","serviços de inteligência","marketing"],0,"É conteúdo expresso do bloco penal."),
    ("penal-teoria-crime","Crime doloso é, em linhas gerais, aquele em que:",["há vontade ou assunção do risco conforme a lei","nunca existe vontade","não existe conduta","não há resultado possível","é sempre contravenção"],0,"Dolo relaciona-se à vontade/assunção do risco nos termos legais."),
    ("penal-teoria-crime","Relação de causalidade conecta:",["conduta e resultado, quando juridicamente relevante","texto e pontuação","capital e juros","arquivo e extensão","município e estado apenas"],0,"Nexo causal é elemento estudado na teoria do fato típico."),
    ("penal-iter","Tentativa ocorre quando, em termos gerais:",["iniciada a execução, o crime não se consuma por circunstâncias alheias à vontade do agente, nos casos admitidos","o agente apenas pensa em agir","o resultado ocorre integralmente","não há qualquer ato de execução","sempre há arrependimento posterior"],0,"É a noção legal geral de tentativa."),
    ("penal-ilicitude","Legítima defesa é tradicionalmente estudada como:",["causa de exclusão da ilicitude","pena de multa","tipo de recurso","modalidade de contrato","regra de Excel"],0,"Integra o conjunto de excludentes de ilicitude."),
    ("penal-penas","Pena de multa aparece no edital junto de:",["sanções penais","direitos políticos","PDF","juros","TAF"],0,"É uma das sanções listadas."),
    ("penal-sursis","Sursis significa:",["suspensão condicional da execução da pena","prisão temporária","recurso administrativo","multa tributária","medida de Excel"],0,"O próprio edital apresenta o termo entre aspas após 'suspensão condicional'."),
    ("penal-crimes-pessoa-patrimonio","Crimes contra o patrimônio são um dos grupos expressamente cobrados em:",["Direito Penal","RLM","Informática","Administração","TAF"],0,"O edital os lista no bloco penal."),
    ("penal-administracao","Crimes contra a Administração Pública e contra a Administração da Justiça:",["são grupos distintos listados no edital","não aparecem no edital","são tópicos de matemática","são apenas administrativos sem repercussão penal","são arquivos digitais"],0,"Ambos são expressamente mencionados."),
    ("penal-leis-especiais","A Lei 15.358/2026 é mencionada pelo edital em conexão com:",["organizações criminosas","nova ortografia","Windows","juros simples","Administração clássica"],0,"O Anexo I aponta alterações introduzidas pela Lei 15.358/2026 no tema de organizações criminosas."),
    ("proc-principios","Processo Penal Constitucional e sistemas/princípios fundamentais pertencem ao bloco de:",["Processual Penal","Civil","RLM","Informática","TAF"],0,"São os primeiros itens do conteúdo processual penal."),
    ("proc-inquerito","O inquérito policial, no edital, é estudado em:",["Processual Penal","Direito Civil","Administração","Português","Geometria"],0,"É tópico expresso do processo penal."),
    ("proc-acao","A ação penal está relacionada ao exercício da pretensão punitiva perante o Judiciário e é conteúdo de:",["Processual Penal","Informática","Marketing","Geometria","TAF"],0,"Ação penal é tópico do processo penal."),
    ("proc-prova","A Lei 9.296/1996 citada no edital trata de:",["interceptação telefônica","licitações","drogas","guardas municipais","trânsito"],0,"O edital a identifica expressamente como Lei de Interceptação Telefônica."),
    ("proc-prisao","A Lei 7.960/1989 citada no edital está ligada a:",["prisão temporária","juizados especiais","licitações","crime ambiental","ECA"],0,"É a lei da prisão temporária."),
    ("proc-juizados","Quais leis aparecem juntas no tópico de Juizados Especiais?",["9.099/1995 e 10.259/2001","11.340/2006 e 11.343/2006","13.022/2014 e 13.869/2019","8.072/1990 e 9.455/1997","9.605/1998 e 9.613/1998"],0,"São as duas leis listadas no item 10 do processo penal."),
    ("proc-prazos","O edital inclui em 'Prazos':",["características, princípios e contagem","apenas datas de inscrição","somente prescrição civil","somente feriados","apenas cálculo de juros"],0,"Esse é o recorte literal do Anexo I."),
    ("proc-nulidades","Nulidades processuais integram o conteúdo de:",["Processual Penal","Excel","Português","TAF","Administração Financeira"],0,"Nulidades é item próprio do processo penal."),
]
for row in pp_qs: add_q("penal-processual", *row)


# Administração/Políticas - 16 questões.
adm_qs=[
    ("adm-funcoes","Planejamento, organização, direção e controle são:",["funções administrativas","tipos de crime","classes de palavras","etapas do TAF","formatos de arquivo"],0,"O edital lista as quatro funções administrativas."),
    ("adm-planejamento","Na análise SWOT, 'forças' e 'fraquezas' costumam representar fatores:",["internos","apenas externos","penais","gramaticais","processuais"],0,"Forças e fraquezas são elementos internos; oportunidades e ameaças são externos."),
    ("adm-planejamento","Missão de uma organização descreve principalmente:",["sua razão de existir e atuação central","apenas o orçamento anual","um crime","um arquivo PDF","uma equação"],0,"Missão expressa propósito institucional."),
    ("adm-estruturas","Estrutura matricial combina, em geral:",["mais de uma linha de autoridade, como função e projeto","apenas uma hierarquia simples obrigatória","somente marketing","somente vendas","direito penal e civil"],0,"A matriz combina dimensões organizacionais."),
    ("adm-marketing","Os 4 Ps do marketing referem-se tradicionalmente a:",["produto, preço, praça e promoção","pessoa, processo, prova e pena","plano, prazo, polícia e público","produto, prova, processo e prisão","preço, poder, política e pena"],0,"É o composto clássico cobrado no edital."),
    ("adm-financeira","Fluxo de caixa acompanha principalmente:",["entradas e saídas de recursos ao longo do tempo","classes gramaticais","tipos de crime","quadrantes","endereços web"],0,"É instrumento básico de gestão financeira."),
    ("adm-rh","Recrutamento e seleção pertencem ao campo de:",["Recursos Humanos","Geometria","Direito Penal","Internet","TAF"],0,"São processos de RH expressamente cobrados."),
    ("adm-empreendedorismo","Plano de negócios aparece no edital em:",["Empreendedorismo","Processo Penal","Nova ortografia","Windows","Constitucional"],0,"É conteúdo do processo empreendedor."),
    ("adm-etica","Sustentabilidade e responsabilidade social corporativa aparecem no tópico de:",["Ética e responsabilidade","Processo Penal","RLM","Informática","TAF"],0,"Estão listadas nesse bloco."),
    ("pp-conceitos","Formulação, implementação e avaliação formam:",["ciclo de políticas públicas","tipos de sentença penal","classes de palavras","etapas de boot","componentes de juros"],0,"São etapas clássicas do ciclo descrito no edital."),
    ("pp-governanca","Federalismo e relações Estado-sociedade aparecem em:",["governança e relações intragovernamentais","geometria","Word","Direito Civil patrimonial","TAF"],0,"É parte do recorte de políticas públicas."),
    ("pp-bases","Estatística descritiva e inferencial aparecem no edital como:",["bases quantitativas para políticas públicas","conteúdo de Português","crime","TAF","segurança patrimonial"],0,"São ferramentas quantitativas do bloco."),
    ("pp-avaliacao","Avaliação ex ante ocorre, em regra, associada à análise:",["antes da implementação/decisão principal","somente depois de tudo","apenas durante uma prova", "de arquivos", "de ortografia"],0,"Ex ante significa avaliação anterior; ex post, posterior."),
]
for row in adm_qs: add_q("administracao-politicas", *row)


# Área de atuação - 18 questões conceituais, sem ensinar táticas operacionais perigosas.
area_qs=[
    ("area-atendimento","Qualidade no atendimento, segundo o recorte do edital, inclui:",["cortesia, presteza, eficiência e objetividade","somente velocidade","apenas autoridade","apenas silêncio","somente formalidade"],0,"O edital lista vários atributos, entre eles cortesia, presteza, eficiência e objetividade."),
    ("area-atendimento","Trabalho em equipe está expressamente incluído em:",["Relações humanas e atendimento","Geometria","Direito Civil","Excel","Juros"],0,"É o item 2 desse bloco."),
    ("area-defesa-riscos","Planejamento de contingências integra:",["análise de riscos e gestão da informação","nova ortografia","direito das obrigações","marketing","plano cartesiano"],0,"É subitem expresso do tópico."),
    ("area-defesa-riscos","Ameaças e vulnerabilidades aparecem no edital dentro de:",["segurança de informações","PA","Civil","Marketing","ortografia"],0,"O recorte de riscos inclui ameaças e vulnerabilidades."),
    ("area-protecao-escoltas","Estudo de rota e pontos sensíveis aparecem no edital em:",["operações de proteção e escoltas","Excel","Direito Civil","Políticas Públicas","Português"],0,"São elementos do planejamento de proteção pessoal e comitivas."),
    ("area-protecao-escoltas","Controle de público e resposta imediata a ameaças são citados em:",["operações de proteção e escoltas","juros","Word","responsabilidade civil","conjuntos"],0,"O edital os inclui no bloco de operações."),
    ("area-seguranca-patrimonial","Credenciamento e barreiras pertencem a:",["controle de acessos","juros compostos","sintaxe","ação penal","estatística"],0,"São exemplos do controle de acesso em segurança patrimonial."),
    ("area-seguranca-patrimonial","Vigilância e monitoramento aparecem no tópico de:",["segurança física e patrimonial","direito das obrigações","PA","Word","marketing"],0,"São itens expressos do bloco."),
    ("area-incidentes-negociacao","Escuta ativa e redução de tensão são associadas no edital a:",["noções básicas de negociação policial","geometria","Excel","responsabilidade civil","juros"],0,"São elementos conceituais do bloco de negociação."),
    ("area-incidentes-negociacao","Cadeia de comando aparece no conteúdo de:",["gestão de incidentes críticos","nova ortografia","direito civil","internet","marketing"],0,"É parte do gerenciamento de incidente crítico."),
    ("area-incendio","A NR-23 é citada no edital em:",["prevenção e combate a incêndio","direito penal","informática","políticas públicas","português"],0,"A NR-23 aparece expressamente no bloco de incêndio."),
    ("area-incendio","Tipos/uso de extintores, rotas e saídas de emergência pertencem ao bloco de:",["prevenção e combate a incêndio","Excel","Direito Civil","RLM","marketing"],0,"São itens expressamente listados."),
    ("area-socorrismo","APH no edital significa:",["Atendimento Pré-Hospitalar","Administração Pública Hierárquica","Análise de Probabilidade Horária","Arquivo Protegido Híbrido","Ação Penal Homologada"],0,"O edital explicita APH - Nível Básico como Atendimento Pré-Hospitalar."),
    ("area-socorrismo","Antes de prestar atendimento, o bloco de socorrismo destaca:",["medidas de segurança do local","cálculo de juros","classificação de bens","formatação de Word","análise SWOT"],0,"Segurança do local é o primeiro subitem."),
    ("area-inteligencia","Fontes de coleta e metodologia de produção de conhecimentos pertencem a:",["serviços de inteligência","geometria","direito civil","Word","marketing"],0,"São subitens do bloco de inteligência."),
]
for row in area_qs: add_q("area-atuacao", *row)


# Legislação - 28 questões, sempre identificadas como autorais e com foco em conceitos estáveis/recorte do edital.
leg_qs=[
    ("leg-guardas","Segundo a Lei 13.022/2014, as guardas municipais são instituições de caráter:",["civil", "militar federal", "judicial", "privado", "legislativo"],0,"A Lei 13.022/2014 define as guardas como instituições de caráter civil."),
    ("leg-guardas","Entre os princípios mínimos de atuação das guardas municipais previstos na Lei 13.022/2014 está:",["proteção dos direitos humanos fundamentais", "sigilo absoluto de toda informação pública", "atuação sem limites legais", "substituição do Poder Judiciário", "cobrança de tributos"],0,"A proteção dos direitos humanos fundamentais é princípio expresso da lei."),
    ("leg-guardas","A competência geral das guardas municipais, na Lei 13.022/2014, envolve a proteção de:",["bens, serviços, logradouros públicos municipais e instalações do Município", "fronteiras internacionais exclusivamente", "qualquer empresa privada obrigatoriamente", "somente rodovias federais", "apenas fóruns estaduais"],0,"Esse é o núcleo da competência geral do art. 4º."),
    ("leg-maria-penha","A Lei Maria da Penha cria mecanismos voltados ao enfrentamento da:",["violência doméstica e familiar contra a mulher", "inadimplência tributária", "pirataria de software", "contravenção de trânsito em geral", "corrupção eleitoral apenas"],0,"Esse é o objeto central da Lei 11.340/2006."),
    ("leg-drogas","A Lei 11.343/2006 institui o:",["Sisnad", "CNJ", "SUS", "FGTS", "Sintegra"],0,"A lei institui o Sistema Nacional de Políticas Públicas sobre Drogas - Sisnad."),
    ("leg-abuso","Na Lei 13.869/2019, abuso de autoridade exige, nos tipos previstos, finalidade específica como prejudicar alguém, beneficiar a si/terceiro ou agir por:",["mero capricho ou satisfação pessoal", "qualquer erro de digitação", "simples divergência interpretativa sempre", "falta de treinamento físico", "atraso de cinco minutos"],0,"A lei prevê finalidades específicas; mera divergência de interpretação não configura, por si, abuso."),
    ("leg-abuso","A mera divergência na interpretação de lei ou avaliação de fatos e provas, segundo a Lei 13.869/2019:",["não configura abuso de autoridade por si só", "sempre configura crime", "gera prisão automática", "é irrelevante em qualquer análise", "é crime hediondo"],0,"A própria lei exclui essa conclusão automática."),
    ("leg-licitacoes","A Lei 14.133/2021 trata principalmente de:",["licitações e contratos administrativos", "drogas", "guardas municipais", "crimes ambientais exclusivamente", "direitos autorais"],0,"É a nova lei geral de licitações e contratos administrativos."),
    ("leg-ctb","A Lei 9.503/1997 corresponde ao:",["Código de Trânsito Brasileiro", "Código Civil", "Estatuto do Desarmamento", "ECA", "Código Penal Militar"],0,"É o CTB."),
    ("leg-desarmamento","A Lei 10.826/2003 é conhecida como:",["Estatuto do Desarmamento", "Lei de Drogas", "Lei de Tortura", "Lei Maria da Penha", "Lei de Licitações"],0,"É o Estatuto do Desarmamento."),
    ("leg-eca","A Lei 8.069/1990 corresponde ao:",["Estatuto da Criança e do Adolescente", "Estatuto do Idoso", "Código Civil", "CTB", "Estatuto Geral das Guardas"],0,"Lei 8.069/1990 é o ECA."),
    ("leg-ambiental","A Lei 9.605/1998 trata de:",["crimes e infrações ambientais", "drogas", "carreira da GCM", "organização do Município", "processo eleitoral"],0,"É a Lei de Crimes Ambientais."),
    ("leg-racismo","A Lei 7.716/1989 é cobrada no edital em relação a:",["crimes resultantes de preconceitos de raça ou de cor e alterações", "juros", "planilhas", "carreira administrativa", "TAF"],0,"Esse é o recorte expresso da legislação geral."),
    ("leg-lc1","A LC 1/1991, no edital, refere-se ao:",["regime jurídico dos servidores públicos do Município de Salvador", "Código Penal", "CTB", "Estatuto do Desarmamento", "SISNAD"],0,"É a lei complementar municipal de regime jurídico."),
    ("leg-carreira","A Lei 9.640/2022 trata, segundo o edital, do:",["Plano de Carreira e Vencimentos da Guarda Civil Municipal", "Código Tributário nacional", "Direito Eleitoral", "Poder Judiciário", "SUS"],0,"O edital identifica expressamente esse objeto."),
    ("leg-regimento","O Decreto 27.731/2016 é cobrado como:",["Regimento da Guarda Civil Municipal de Salvador", "Estatuto do Desarmamento", "Lei de Drogas", "Código Civil", "regulamento do CNJ"],0,"É o regimento da GCM de Salvador."),
    ("leg-disciplinar","A Lei 9.273/2017 está associada ao:",["Regime Disciplinar da Guarda Civil Municipal", "CTB", "Código Civil", "SISNAD", "Poder Judiciário"],0,"O edital a identifica como regime disciplinar da GCM."),
    ("leg-organica-poderes","A Lei Orgânica de Salvador é cobrada, entre outros pontos, quanto a:",["organização do Município, competências e Poderes", "somente crimes hediondos", "somente Windows", "juros compostos", "apenas marketing"],0,"O edital lista organização, competências, Legislativo e Executivo."),
    ("leg-organica-adm","Bens municipais, serviços públicos, planejamento e orçamento aparecem no edital dentro de:",["Lei Orgânica do Município de Salvador", "Lei de Drogas", "Word", "RLM", "TAF"],0,"São itens expressamente listados na Lei Orgânica."),
    ("leg-organizacao-adm","Administração direta e indireta do Município aparece no edital em:",["organização administrativa municipal", "direito penal especial", "geometria", "Excel", "TAF"],0,"O recorte inclui estrutura e funcionamento da administração direta e indireta."),
    ("leg-tributario","A Lei Municipal 7.186/2006 é citada no edital como:",["Código Tributário e de Rendas do Município de Salvador", "Estatuto das Guardas", "Lei de Drogas", "Código Penal", "Lei de Tortura"],0,"O edital associa a lei ao Código Tributário e de Rendas."),
    ("leg-etica-transparencia","Ética, integridade, transparência e acesso à informação aparecem no conteúdo de:",["legislação municipal", "geometria", "Word", "direito penal apenas", "TAF"],0,"São normas municipais expressamente mencionadas."),
    ("leg-direitos-cidadaos","O edital inclui direitos e deveres dos cidadãos perante:",["a Administração Municipal", "apenas empresas privadas", "apenas o Judiciário Federal", "somente bancos", "apenas a FGV"],0,"Esse é o item 17 do recorte de legislação municipal."),
]
for row in leg_qs: add_q("legislacao", *row)

# Completa o banco com questões de associação de tópico que continuam estritamente no edital,
# geradas a partir da matriz para tópicos que receberam poucas questões.
coverage = {}
for q in questions:
    for tid in q["topicIds"]:
        coverage[tid] = coverage.get(tid, 0) + 1

for subject in subjects:
    for topic_id, label, official in subject["topics"]:
        current = coverage.get(topic_id, 0)
        # Para tópicos ainda sem nenhuma questão, adicionamos UMA questão de
        # mapeamento curricular. Não repetimos o mesmo molde várias vezes.
        target = 1
        while current < target:
            options = [label]
            other_labels = [t[1] for s in subjects for t in s["topics"] if t[0] != topic_id]
            random.shuffle(other_labels)
            options += other_labels[:4]
            random.shuffle(options)
            ans = options.index(label)
            add_q(
                subject["id"],
                topic_id,
                f"O recorte oficial '{official}' corresponde a qual tópico de estudo nesta matriz?",
                options,
                ans,
                f"Esse recorte foi mapeado para '{label}'. Esta questão serve para fixar a organização exata do conteúdo do edital.",
                "easy",
                ["matriz-edital"],
            )
            current += 1

write_json(DATA / "questions" / f"{CONTEST_ID}.json", questions)

print(f"Subjects: {len(subjects)}")
print(f"Lessons: {len(lessons)}")
print(f"Questions: {len(questions)}")
