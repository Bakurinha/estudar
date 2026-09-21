#!/usr/bin/env python3
"""Expande a base de estudo da GCM Salvador 2026 sem sair do Anexo I.

A matriz em data/syllabus/gcm-salvador-2026.json é a fonte curricular. Este
script NÃO cria matérias/tópicos novos. Ele apenas:
- aprofunda as aulas existentes com conceitos explicitamente ligados ao tópico;
- amplia o banco até uma quantidade mínima por tópico;
- balanceia o gabarito A-E no arquivo gerado;
- evita duplicatas literais e padrões de enunciado excessivamente repetidos.

As questões adicionais são autorais e são identificadas como tais no JSON.
"""
from __future__ import annotations

import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONTEST_ID = "gcm-salvador-2026"
RNG = random.Random(20260921_12)

TARGETS = {
    "portugues": 25,
    "rlm": 30,
    "informatica": 20,
    "constitucional-civil": 20,
    "penal-processual": 20,
    "administracao-politicas": 20,
    "area-atuacao": 20,
    "legislacao": 25,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\d+(?:[.,]\d+)?", "#", text.lower())
    text = re.sub(r"[^a-z0-9#]+", " ", text)
    return " ".join(text.split())


def split_scope(scope: str) -> list[str]:
    parts = re.split(r";|(?<!nº):|, (?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", scope)
    return [p.strip(" .") for p in parts if len(p.strip(" .")) >= 3]


# Dois conceitos seguros por tópico. O terceiro eixo de cada tópico é sempre o
# próprio recorte oficial do edital, carregado do syllabus. Isso impede que a
# expansão crie conteúdo fora da matriz.
FACTS: dict[str, list[tuple[str, str, str]]] = {
    # Língua Portuguesa
    "interpretacao-argumentativa": [
        ("tese", "ideia ou posição central que o autor procura sustentar", "identificar a afirmação principal defendida no texto"),
        ("argumento", "razão, dado, exemplo ou relação usada para sustentar uma tese", "separar a opinião central das razões apresentadas para defendê-la"),
    ],
    "construcao-textual": [
        ("encadeamento", "organização das partes do texto para que uma ideia se conecte à seguinte", "observar como um parágrafo retoma e desenvolve o anterior"),
        ("referencia textual", "mecanismo que retoma ou antecipa elementos do texto", "reconhecer a que termo um pronome se refere"),
    ],
    "progressao-textual": [
        ("informação nova", "conteúdo acrescentado ao texto para fazê-lo avançar", "um período apresenta a causa de um problema já mencionado"),
        ("retomada temática", "recuperação do tema anterior antes de acrescentar novo conteúdo", "usar expressão equivalente para manter o assunto em foco"),
    ],
    "coesao-coerencia-intertextualidade": [
        ("coesão", "ligações linguísticas entre palavras, orações e partes do texto", "um pronome retoma um substantivo citado antes"),
        ("coerência", "compatibilidade lógica e semântica das ideias do texto", "evitar afirmações contraditórias sem explicação"),
        ("intertextualidade", "relação de um texto com outro texto, fala ou referência reconhecível", "uma notícia faz alusão a uma frase famosa"),
    ],
    "reescritura": [
        ("preservação de sentido", "manutenção da relação lógica original durante a reformulação", "trocar 'embora' por construção concessiva equivalente"),
        ("modalização", "marcação de certeza, possibilidade, obrigação ou avaliação na frase", "perceber que trocar 'pode' por 'deve' altera o sentido"),
    ],
    "vocabulario": [
        ("sentido contextual", "significado assumido pela palavra dentro da frase concreta", "testar um sinônimo na frase antes de considerá-lo equivalente"),
        ("polissemia", "possibilidade de uma mesma palavra assumir sentidos diferentes conforme o contexto", "a palavra 'banco' pode indicar assento ou instituição financeira"),
    ],
    "estrangeirismos": [
        ("estrangeirismo", "palavra ou expressão de outra língua empregada no português", "'download' em contexto de informática"),
        ("adequação lexical", "escolha vocabular compatível com público, finalidade e situação comunicativa", "avaliar se um termo técnico estrangeiro é compreensível ao leitor"),
    ],
    "classes-palavras": [
        ("classe gramatical", "categoria definida pelo comportamento e função da palavra no contexto", "reconhecer advérbio modificando verbo ou adjetivo"),
        ("função contextual", "papel que a palavra exerce na construção em que aparece", "uma mesma forma pode assumir classificação diferente conforme o uso"),
    ],
    "sintaxe-pontuacao": [
        ("sintaxe", "organização e relação dos termos dentro da oração e do período", "identificar sujeito, verbo e complementos antes de pontuar"),
        ("vírgula", "sinal que pode separar termos, orações ou elementos deslocados conforme a estrutura sintática", "não separar sujeito e verbo apenas por pausa de fala"),
    ],
    "variacao-linguistica": [
        ("variação linguística", "mudança no uso da língua conforme região, grupo, época ou situação", "comparar fala cotidiana e redação administrativa"),
        ("adequação comunicativa", "uso do registro apropriado ao interlocutor, finalidade e contexto", "preferir registro formal e claro em documento oficial"),
    ],
    "denotacao-conotacao": [
        ("denotação", "emprego predominantemente literal de uma palavra ou expressão", "'a sala mede vinte metros quadrados'"),
        ("conotação", "emprego figurado ou associado de uma palavra ou expressão", "'a notícia caiu como uma bomba'"),
    ],
    "nova-ortografia": [
        ("hífen", "sinal cuja utilização segue regras específicas, especialmente em formações com prefixos", "distinguir 'autoescola' de 'micro-ondas'"),
        ("acentuação atual", "regras de acento gráfico vigentes após o Acordo Ortográfico", "reconhecer grafias atuais sem acentos abolidos pelo acordo"),
    ],

    # Raciocínio Lógico-Matemático
    "proposicoes": [
        ("proposição", "frase declarativa à qual se pode atribuir valor verdadeiro ou falso", "'Salvador fica na Bahia' pode ser julgada verdadeira"),
        ("conectivo lógico", "operador que combina ou modifica proposições", "usar 'e', 'ou', 'se... então' e 'se e somente se'"),
    ],
    "equivalencias": [
        ("equivalência lógica", "duas expressões que têm os mesmos valores-verdade em todas as combinações", "comparar uma condicional com 'não P ou Q'"),
        ("leis de De Morgan", "regras de negação de conjunções e disjunções", "negar 'P e Q' como 'não P ou não Q'"),
    ],
    "problemas-raciocinio": [
        ("dedução", "conclusão obtida necessariamente das relações fornecidas", "de A antes de B e B antes de C concluir A antes de C"),
        ("restrição lógica", "condição que elimina configurações incompatíveis em um problema", "usar pistas de posição para excluir ordens impossíveis"),
    ],
    "diagramas-graficos": [
        ("leitura de gráfico", "interpretação de eixos, legenda, escala e valores antes de calcular", "comparar valores de dois meses em um gráfico"),
        ("variação percentual", "mudança relativa calculada em relação ao valor de referência", "passar de 80 para 100 representa aumento de 25% sobre 80"),
    ],
    "conjuntos": [
        ("união", "conjunto dos elementos que pertencem a pelo menos um dos conjuntos considerados", "reunir elementos de A ou B sem duplicar"),
        ("interseção", "conjunto dos elementos comuns aos conjuntos considerados", "identificar quem pertence simultaneamente a A e B"),
    ],
    "numeros-operacoes": [
        ("conjuntos numéricos", "naturais, inteiros, racionais e reais usados conforme suas propriedades", "reconhecer uma fração como número racional"),
        ("ordem de operações", "prioridade de parênteses, potências, multiplicações/divisões e adições/subtrações", "calcular multiplicação antes da soma quando não há parênteses"),
    ],
    "reta-numerica": [
        ("ordem na reta", "números posicionados mais à direita representam valores maiores", "-2 é maior que -5"),
        ("distância", "valor não negativo que mede separação entre posições na reta", "a distância entre -3 e 4 é 7"),
    ],
    "unidades-medida": [
        ("conversão de distância", "transformação entre unidades equivalentes como quilômetro e metro", "2,5 km correspondem a 2.500 m"),
        ("conversão de tempo", "transformação entre horas, minutos e segundos", "1h30min correspondem a 90 minutos"),
    ],
    "plano-cartesiano": [
        ("coordenada x", "primeiro valor do par ordenado, associado à posição horizontal", "x negativo posiciona o ponto à esquerda do eixo vertical"),
        ("coordenada y", "segundo valor do par ordenado, associado à posição vertical", "y positivo posiciona o ponto acima do eixo horizontal"),
    ],
    "algebra": [
        ("equação do primeiro grau", "igualdade com incógnita de expoente um que deve ser determinada", "resolver x + 7 = 20"),
        ("sistema linear", "conjunto de equações cujas incógnitas devem satisfazer todas simultaneamente", "usar duas relações para descobrir dois valores desconhecidos"),
    ],
    "porcentagem-proporcao": [
        ("porcentagem", "razão cujo denominador de referência é cem", "20% de 150 corresponde a 30"),
        ("proporcionalidade inversa", "relação em que uma grandeza aumenta enquanto a outra diminui de modo proporcional", "dobrar trabalhadores pode reduzir pela metade o tempo em modelo ideal"),
    ],
    "sequencias-pa-pg": [
        ("progressão aritmética", "sequência em que a diferença entre termos consecutivos é constante", "2, 5, 8, 11 tem razão 3"),
        ("progressão geométrica", "sequência em que a razão entre termos consecutivos é constante", "2, 6, 18 tem razão 3"),
    ],
    "juros": [
        ("juros simples", "juros calculados periodicamente sobre o capital inicial", "capital de 1.000 a 2% por três períodos gera 60 de juros simples"),
        ("juros compostos", "juros calculados sobre o montante acumulado a cada período", "aplicar sucessivamente o fator 1+i"),
    ],
    "geometria-basica": [
        ("perímetro", "medida do contorno de uma figura plana", "somar os quatro lados de um retângulo"),
        ("área", "medida da superfície ocupada por uma figura plana", "multiplicar base pela altura de um retângulo"),
    ],
    "semelhanca-triangulo": [
        ("semelhança", "relação entre figuras de mesma forma e lados correspondentes proporcionais", "montar proporção entre lados correspondentes"),
        ("Teorema de Pitágoras", "no triângulo retângulo, o quadrado da hipotenusa é a soma dos quadrados dos catetos", "reconhecer o triângulo 3-4-5"),
    ],
    "medidas-area-volume": [
        ("comprimento", "grandeza linear expressa em unidades como metro, centímetro e quilômetro", "converter 250 cm em 2,5 m"),
        ("volume", "medida do espaço tridimensional ocupado por um corpo", "multiplicar comprimento, largura e altura de um paralelepípedo"),
    ],
    "contagem-probabilidade": [
        ("princípio multiplicativo", "contagem de escolhas sucessivas multiplicando as quantidades de possibilidades", "4 camisas e 3 calças geram 12 combinações"),
        ("probabilidade", "razão entre casos favoráveis e casos possíveis em modelo equiprovável", "três resultados pares em seis faces dão probabilidade 1/2"),
    ],

    # Informática
    "arquivos-digitais": [
        ("extensão de arquivo", "sufixo que ajuda a identificar formato e aplicação associada", "'.xlsx' indica normalmente uma pasta de trabalho do Excel"),
        ("formato digital", "estrutura usada para armazenar tipos de dados como texto, imagem, áudio ou vídeo", "JPEG é usado para imagens e MP3 para áudio"),
    ],
    "pdf": [
        ("PDF", "formato de documento portátil voltado à preservação da apresentação entre ambientes", "distribuir documento mantendo paginação e layout"),
        ("portabilidade", "capacidade de visualizar o documento de forma consistente em sistemas diferentes", "abrir o mesmo PDF em dispositivos distintos com layout semelhante"),
    ],
    "windows": [
        ("sistema de arquivos", "estrutura usada pelo Windows para organizar pastas e arquivos", "criar pastas para agrupar documentos"),
        ("mecanismo de busca", "recurso para localizar arquivos, programas e configurações", "procurar um documento pelo nome"),
    ],
    "editores-texto": [
        ("formatação", "ajuste da apresentação de texto, parágrafos, páginas, tabelas e outros objetos", "alterar fonte, alinhamento ou margens"),
        ("cabeçalho e rodapé", "áreas recorrentes no topo e na base das páginas", "inserir número da página no rodapé"),
    ],
    "localizar-substituir": [
        ("localizar", "recurso que procura ocorrências de texto ou padrão dentro do documento", "encontrar todas as ocorrências de uma palavra"),
        ("substituir", "recurso que troca ocorrências encontradas por outro conteúdo", "alterar repetidamente uma expressão em documento longo"),
    ],
    "word-arquivos": [
        ("controle de alterações", "recurso que registra modificações para posterior revisão", "visualizar inserções e exclusões feitas por revisores"),
        ("macro", "sequência automatizada de comandos ou código usada para repetir tarefas", "automatizar uma rotina recorrente de formatação"),
    ],
    "excel": [
        ("fórmula", "expressão calculada a partir de valores, operadores e referências de células", "usar =A1+A2 para somar duas células"),
        ("filtro e ordenação", "recursos para selecionar registros por critérios e reorganizar sua ordem", "mostrar apenas linhas de uma categoria e ordenar valores"),
    ],
    "internet-seguranca": [
        ("upload e download", "upload envia dados ao serviço remoto; download recebe dados no dispositivo", "enviar arquivo para nuvem e depois baixá-lo"),
        ("autenticação segura", "uso de credenciais fortes e fatores adicionais para reduzir acesso indevido", "combinar senha longa com token de segundo fator"),
    ],

    # Constitucional e Civil
    "const-conceito-principios": [
        ("Constituição", "norma fundamental que organiza o Estado e estabelece direitos e estruturas essenciais", "consultar princípios fundamentais antes de interpretar normas inferiores"),
        ("princípios fundamentais", "diretrizes constitucionais básicas sobre Estado, fundamentos e objetivos", "relacionar atuação estatal aos fundamentos constitucionais"),
    ],
    "const-direitos": [
        ("direitos fundamentais", "conjunto constitucional que inclui direitos individuais, coletivos e sociais", "identificar proteção constitucional à liberdade e à igualdade"),
        ("direitos políticos", "regras ligadas à participação do cidadão na vida política", "distinguir direitos políticos de nacionalidade e direitos sociais"),
    ],
    "const-organizacao": [
        ("federalismo", "organização política com entes dotados de autonomia nos limites constitucionais", "distinguir União, Estados, Distrito Federal e Municípios"),
        ("competência", "atribuição constitucional conferida a determinado ente para agir ou legislar", "verificar qual ente recebeu determinada matéria"),
    ],
    "const-administracao": [
        ("Administração Pública", "atividade e estrutura estatal submetidas aos princípios constitucionais aplicáveis", "analisar atuação administrativa à luz de legalidade e impessoalidade"),
        ("servidor público", "agente investido em vínculo funcional com a Administração conforme regime jurídico aplicável", "distinguir regras gerais de servidores de regras específicas da carreira"),
    ],
    "const-judiciario": [
        ("Poder Judiciário", "Poder estatal encarregado do exercício da jurisdição pelos órgãos constitucionais", "identificar órgão e competência previstos na Constituição"),
        ("competência jurisdicional", "parcela de atribuição conferida a determinado órgão judicial", "distinguir estrutura de competência"),
    ],
    "const-cnj": [
        ("CNJ", "Conselho Nacional de Justiça, órgão constitucional de controle administrativo e financeiro do Judiciário e de deveres funcionais de magistrados", "distinguir controle administrativo do exercício da jurisdição"),
        ("composição e competência", "dois eixos expressamente exigidos pelo edital para o estudo do CNJ", "revisar quem integra o Conselho e quais matérias são de sua atuação"),
    ],
    "const-funcoes-justica": [
        ("Ministério Público", "instituição permanente essencial à função jurisdicional do Estado, com funções constitucionais próprias", "distinguir Ministério Público de órgão do Judiciário"),
        ("Defensoria Pública", "instituição essencial à função jurisdicional voltada à orientação jurídica e defesa dos necessitados nos termos constitucionais", "distinguir defesa pública da advocacia privada"),
    ],
    "civil-lindb": [
        ("LINDB", "Lei de Introdução às Normas do Direito Brasileiro, com regras gerais sobre vigência, aplicação e interpretação", "examinar efeitos da lei no tempo e no espaço"),
        ("analogia", "técnica de integração utilizada diante de lacuna, observados os limites jurídicos", "buscar solução em hipótese semelhante quando o ordenamento admite integração"),
    ],
    "civil-pessoas": [
        ("pessoa natural", "ser humano reconhecido como sujeito de direitos e deveres na ordem civil", "estudar personalidade, capacidade e domicílio"),
        ("emancipação", "instituto relacionado à antecipação da capacidade civil plena nas hipóteses legais", "distinguir emancipação de maioridade etária"),
    ],
    "civil-bens": [
        ("bem público", "bem pertencente às pessoas jurídicas de direito público e submetido ao regime jurídico pertinente", "distinguir bens públicos de bens particulares"),
        ("classificação dos bens", "organização jurídica dos bens conforme características e relação entre eles", "diferenciar bens considerados em si mesmos e reciprocamente"),
    ],
    "civil-fatos": [
        ("negócio jurídico", "manifestação de vontade destinada a produzir efeitos jurídicos reconhecidos pelo ordenamento", "analisar validade e efeitos do ato negocial"),
        ("prescrição e decadência", "institutos ligados ao decurso do tempo, com objetos e efeitos jurídicos distintos", "não tratar prescrição e decadência como sinônimos"),
    ],
    "civil-obrigacoes": [
        ("adimplemento", "cumprimento da prestação devida e consequente satisfação da obrigação", "pagar corretamente dívida no tempo, modo e lugar devidos"),
        ("inadimplemento", "descumprimento total ou parcial da obrigação, com consequências previstas no direito", "distinguir atraso de impossibilidade definitiva conforme o caso"),
    ],
    "civil-responsabilidade": [
        ("responsabilidade civil", "dever jurídico de reparar dano quando presentes os pressupostos aplicáveis", "analisar conduta, dano e nexo conforme o regime incidente"),
        ("dano moral", "lesão a interesse extrapatrimonial juridicamente protegido que pode gerar reparação", "distinguir prejuízo moral de mero cálculo patrimonial"),
    ],
    "civil-jurisprudencia": [
        ("jurisprudência", "conjunto de decisões e entendimentos construídos pelos tribunais sobre questões jurídicas", "consultar julgados atuais do STF, STJ e TJBA"),
        ("súmula", "enunciado que sintetiza orientação jurisprudencial consolidada segundo as regras do tribunal", "revisar súmulas pertinentes e conferir vigência"),
    ],

    # Penal e Processo Penal
    "penal-conceito-fontes": [
        ("Direito Penal", "ramo jurídico que define infrações penais e consequências jurídicas nos limites constitucionais", "distinguir norma penal de regra meramente administrativa"),
        ("fonte penal", "origem formal ou material das normas e princípios utilizados no Direito Penal", "reconhecer a lei como fonte formal imediata das incriminações"),
    ],
    "penal-lei": [
        ("reserva legal", "exigência de lei anterior para definir crime e cominar pena", "não criar crime por analogia em prejuízo do acusado"),
        ("lei penal no tempo", "regras que determinam qual norma penal incide diante de sucessão de leis", "verificar anterioridade e eventual retroatividade benéfica"),
    ],
    "penal-teoria-crime": [
        ("dolo", "vontade consciente de realizar o tipo ou assunção do risco nos termos legais", "distinguir intenção de mera negligência"),
        ("culpa", "violação do dever de cuidado nas modalidades previstas sem vontade do resultado típico", "analisar imprudência, negligência ou imperícia quando cabíveis"),
    ],
    "penal-iter": [
        ("tentativa", "início da execução sem consumação por circunstâncias alheias à vontade do agente", "distinguir tentativa de desistência voluntária"),
        ("crime impossível", "hipótese legal em que a consumação é inviável pelas condições previstas no Código Penal", "avaliar ineficácia absoluta do meio ou impropriedade absoluta do objeto"),
    ],
    "penal-ilicitude": [
        ("ilicitude", "contrariedade do fato típico ao ordenamento, salvo causa de justificação", "verificar legítima defesa ou estado de necessidade quando presentes requisitos"),
        ("culpabilidade", "juízo de reprovação pessoal analisado após tipicidade e ilicitude na estrutura tradicional", "distinguir excludente de culpabilidade de excludente de ilicitude"),
    ],
    "penal-penas": [
        ("pena privativa de liberdade", "sanção penal que restringe a liberdade nos regimes e condições previstos em lei", "distinguir reclusão e detenção conforme previsão legal"),
        ("pena restritiva de direitos", "sanção alternativa aplicada nas hipóteses e requisitos legais", "não confundir restrição de direitos com medida cautelar processual"),
    ],
    "penal-sursis": [
        ("sursis", "suspensão condicional da execução da pena quando preenchidos os requisitos legais", "distinguir sursis de livramento condicional"),
        ("extinção da punibilidade", "situação legal que elimina a possibilidade de aplicação ou execução da sanção penal", "identificar causas previstas em lei sem confundi-las com absolvição de mérito"),
    ],
    "penal-crimes-pessoa-patrimonio": [
        ("crimes contra a pessoa", "grupo de tipos penais que tutela bens como vida e integridade pessoal", "distinguir esse título dos crimes patrimoniais"),
        ("crimes contra o patrimônio", "grupo de tipos que tutela relações patrimoniais conforme o Código Penal", "diferenciar subtração patrimonial de ofensa à honra"),
    ],
    "penal-honra-fe-publica": [
        ("crimes contra a honra", "tipos penais que protegem dimensões da honra conforme definições legais", "distinguir calúnia, difamação e injúria pelos elementos do tipo"),
        ("fé pública", "confiança coletiva na autenticidade e veracidade de determinados documentos, sinais e atos", "relacionar falsidades documentais ao bem jurídico correspondente"),
    ],
    "penal-administracao": [
        ("Administração Pública", "bem jurídico protegido por diversos crimes funcionais e praticados por particulares contra o Estado", "distinguir peculato de corrupção ativa conforme sujeitos e condutas"),
        ("Administração da Justiça", "regular funcionamento da atividade de justiça protegido por tipos penais específicos", "reconhecer que não se confunde com a administração pública em sentido amplo"),
    ],
    "penal-leis-especiais": [
        ("legislação penal especial", "leis fora do núcleo do Código Penal que tipificam crimes ou disciplinam temas penais específicos cobrados no edital", "separar Lei de Drogas, Tortura, Desarmamento e outras leis listadas"),
        ("atualização legislativa", "necessidade de estudar a redação vigente das leis expressamente indicadas no edital", "conferir alterações recentes como a Lei 15.358/2026 quando vinculada ao tema"),
    ],
    "proc-principios": [
        ("processo penal constitucional", "leitura do processo penal à luz das garantias e princípios constitucionais", "relacionar devido processo, defesa e imparcialidade ao procedimento"),
        ("sistema processual", "modelo de distribuição de funções entre acusar, defender e julgar", "não confundir função de acusação com função jurisdicional"),
    ],
    "proc-aplicacao": [
        ("lei processual no tempo", "regra de incidência temporal das normas processuais penais conforme o regime legal", "identificar aplicação aos atos processuais praticados sob sua vigência"),
        ("disposições preliminares do CPP", "normas iniciais que orientam aplicação e alcance do Código de Processo Penal", "consultar a redação vigente do CPP"),
    ],
    "proc-inquerito": [
        ("inquérito policial", "procedimento investigatório destinado a apurar elementos sobre infração e autoria", "distinguir investigação preliminar de processo judicial"),
        ("caráter informativo", "função de reunir elementos de informação para subsidiar decisões e eventual ação penal", "não tratar o inquérito como sentença ou julgamento"),
    ],
    "proc-processo": [
        ("processo", "relação jurídica desenvolvida perante órgão jurisdicional para exercício da pretensão punitiva segundo garantias processuais", "distinguir processo de mero procedimento investigativo"),
        ("procedimento", "sequência ordenada de atos prevista para desenvolvimento de determinada atividade processual", "identificar rito sem confundi-lo com a relação processual"),
    ],
    "proc-acao": [
        ("ação penal", "instrumento jurídico para provocar a jurisdição penal nas hipóteses e condições legais", "distinguir espécies de ação penal conforme titularidade e iniciativa"),
        ("pretensão punitiva", "pretensão estatal de aplicação da consequência penal por meio do devido processo", "não confundir pretensão punitiva com execução da pena já imposta"),
    ],
    "proc-prova": [
        ("prova", "elemento produzido e valorado no processo conforme regras legais para formação da decisão", "distinguir prova de mero elemento informativo do inquérito"),
        ("interceptação telefônica", "medida submetida aos requisitos da Lei 9.296/1996 e controle judicial", "não confundir interceptação com gravação feita por um dos interlocutores"),
    ],
    "proc-sujeitos": [
        ("juiz", "sujeito processual responsável pelo exercício imparcial da jurisdição", "não acumular conceitualmente as funções de acusar e julgar"),
        ("partes e auxiliares", "participantes do processo com funções distintas previstas em lei", "distinguir acusação, defesa e auxiliares da justiça"),
    ],
    "proc-prisao": [
        ("prisão cautelar", "restrição de liberdade processual sujeita a fundamento e requisitos legais, não equivalente a pena definitiva", "distinguir prisão preventiva de condenação"),
        ("liberdade provisória", "regime processual que permite responder solto nas condições legais", "analisar eventual imposição de medidas cautelares diversas"),
    ],
    "proc-juizados": [
        ("Lei 9.099/1995", "diploma que disciplina Juizados Especiais, incluindo regras aplicáveis ao juizado criminal", "estudar institutos despenalizadores dentro do recorte legal"),
        ("Lei 10.259/2001", "diploma dos Juizados Especiais Federais expressamente listado no edital", "distinguir seu âmbito federal do sistema da Lei 9.099/1995"),
    ],
    "proc-prazos": [
        ("prazo processual", "período previsto para prática de ato processual segundo regras de contagem e características próprias", "identificar termo inicial e forma de contagem antes de calcular"),
        ("contagem", "aplicação das regras legais para determinar início, curso e término do prazo", "não importar automaticamente regras de outro ramo processual"),
    ],
    "proc-nulidades": [
        ("nulidade", "consequência processual associada a vício relevante conforme disciplina legal", "avaliar prejuízo e regime da nulidade quando exigidos"),
        ("vício processual", "desconformidade na prática de ato que deve ser analisada segundo as regras de validade do processo", "não concluir que todo defeito produz automaticamente o mesmo efeito"),
    ],
    "proc-jurisprudencia": [
        ("precedente", "decisão anterior que pode orientar solução de casos posteriores conforme o sistema jurídico", "acompanhar entendimentos atuais dos tribunais superiores"),
        ("jurisprudência superior", "conjunto de entendimentos do STF e STJ relevante à aplicação do processo penal", "conferir atualização antes da prova"),
    ],

    # Administração e Políticas Públicas
    "adm-introducao": [
        ("administração", "processo de coordenar recursos e pessoas para alcançar objetivos", "organizar trabalho para entregar resultado com eficiência"),
        ("evolução administrativa", "mudança histórica das teorias e práticas de gestão", "comparar foco em tarefas, pessoas e ambiente"),
    ],
    "adm-funcoes": [
        ("planejamento", "definição antecipada de objetivos e caminhos para alcançá-los", "estabelecer meta antes de executar uma atividade"),
        ("controle", "comparação entre resultado realizado e planejado para corrigir desvios", "acompanhar indicador e ajustar a ação"),
    ],
    "adm-teorias": [
        ("teoria clássica", "abordagem que enfatiza estrutura, funções e organização formal", "analisar divisão do trabalho e princípios administrativos"),
        ("contingência", "abordagem segundo a qual a solução de gestão depende das condições do ambiente e da situação", "evitar tratar uma estrutura como ideal para todo contexto"),
    ],
    "adm-estruturas": [
        ("estrutura funcional", "agrupamento organizacional por especialidades ou funções", "reunir finanças, RH e operações em unidades funcionais"),
        ("estrutura matricial", "arranjo que combina mais de uma dimensão de autoridade, frequentemente função e projeto", "profissional responder a gestor funcional e de projeto"),
    ],
    "adm-planejamento": [
        ("missão", "razão de existir da organização e seu propósito atual", "distinguir missão de visão de futuro"),
        ("SWOT", "análise de forças, fraquezas, oportunidades e ameaças", "separar fatores internos de externos"),
    ],
    "adm-marketing": [
        ("4 Ps", "composto de marketing formado por produto, preço, praça e promoção", "avaliar decisão de distribuição como componente de praça"),
        ("segmentação", "divisão do mercado em grupos com características relevantes para a estratégia", "adaptar oferta a públicos diferentes"),
    ],
    "adm-financeira": [
        ("fluxo de caixa", "registro de entradas e saídas financeiras ao longo do tempo", "avaliar necessidade de recursos em determinado período"),
        ("orçamento", "planejamento quantitativo de receitas, despesas e recursos para período futuro", "comparar previsto e realizado"),
    ],
    "adm-rh": [
        ("recrutamento e seleção", "processos de atrair candidatos e escolher pessoas adequadas às necessidades", "distinguir atração de candidatos de escolha final"),
        ("avaliação de desempenho", "processo de acompanhar resultados e comportamentos segundo critérios definidos", "usar feedback para desenvolvimento"),
    ],
    "adm-empreendedorismo": [
        ("plano de negócios", "documento estruturado que analisa proposta, mercado, operação e viabilidade", "organizar hipótese de empreendimento antes da execução"),
        ("inovação", "implementação de novidade que gera valor ou melhora resultado", "distinguir ideia criativa de inovação efetivamente aplicada"),
    ],
    "adm-etica": [
        ("ética administrativa", "orientação da conduta por princípios e deveres compatíveis com interesse público", "evitar conflito entre interesse particular e dever funcional"),
        ("sustentabilidade", "consideração integrada de impactos ambientais, sociais e econômicos nas decisões", "reduzir desperdício mantendo capacidade de atendimento"),
    ],
    "pp-conceitos": [
        ("política pública", "curso de ação ou intervenção estatal voltada ao enfrentamento de problema público", "definir problema antes de formular alternativas"),
        ("ciclo de políticas", "modelo analítico com etapas como formulação, implementação e avaliação", "usar o ciclo como ferramenta de análise, não como sequência sempre rígida"),
    ],
    "pp-governanca": [
        ("governança", "mecanismos de direção, coordenação, controle e relacionamento para produzir valor público", "articular atores e responsabilidades"),
        ("federalismo", "distribuição constitucional de poder e competências entre entes federativos", "analisar cooperação intergovernamental"),
    ],
    "pp-bases": [
        ("estatística descritiva", "técnicas de organizar e resumir dados observados", "usar média, proporção e medidas de dispersão para descrever dados"),
        ("análise de impacto", "avaliação destinada a estimar efeitos atribuíveis a uma política ou intervenção", "comparar resultados com cenário de referência adequado"),
    ],
    "pp-avaliacao": [
        ("avaliação ex ante", "análise realizada antes da implementação para examinar problema, alternativas e desenho", "avaliar viabilidade antes de executar"),
        ("avaliação ex post", "análise realizada após ou durante a execução para examinar resultados e efeitos", "verificar se objetivos foram alcançados"),
    ],

    # Área de Atuação
    "area-atendimento": [
        ("comunicação no atendimento", "transmissão clara, objetiva, respeitosa e adequada à situação", "ouvir a demanda antes de orientar o cidadão"),
        ("trabalho em equipe", "cooperação coordenada entre integrantes para objetivo comum", "compartilhar informação relevante e respeitar funções"),
    ],
    "area-defesa-riscos": [
        ("análise de riscos", "identificação e avaliação de ameaças, vulnerabilidades e possíveis impactos", "priorizar tratamento de risco mais relevante"),
        ("contingência", "planejamento de resposta para manter ou recuperar atividades diante de evento adverso", "definir previamente responsáveis e alternativas de resposta"),
    ],
    "area-protecao-escoltas": [
        ("planejamento de proteção", "preparação de recursos, rotas, equipes e contingências para atividade de proteção", "avaliar previamente pontos sensíveis do deslocamento"),
        ("controle de público", "organização preventiva do fluxo de pessoas para reduzir riscos e preservar segurança", "orientar circulação sem criar obstruções desnecessárias"),
    ],
    "area-seguranca-patrimonial": [
        ("controle de acesso", "procedimentos para autorizar, registrar e fiscalizar entrada e saída de pessoas ou bens", "usar credenciamento compatível com a área protegida"),
        ("monitoramento", "acompanhamento contínuo de ambiente ou sistema para identificar eventos relevantes", "integrar observação humana e recursos eletrônicos"),
    ],
    "area-incidentes-negociacao": [
        ("incidente crítico", "evento de elevada complexidade que exige comando, coordenação, isolamento e resposta organizada", "estabelecer cadeia de comando e comunicação operacional"),
        ("escuta ativa", "técnica de comunicação que busca compreender e demonstrar atenção ao interlocutor", "usar perguntas e confirmação de entendimento para reduzir tensão"),
    ],
    "area-incendio": [
        ("prevenção de incêndio", "conjunto de medidas destinadas a reduzir probabilidade e consequências de incêndios", "manter rotas de saída desobstruídas e sinalizadas"),
        ("extintor", "equipamento de primeira resposta cujo agente deve ser compatível com a classe de fogo", "identificar o tipo adequado antes de uma tentativa segura de combate inicial"),
    ],
    "area-socorrismo": [
        ("segurança da cena", "verificação inicial de riscos para vítima, socorrista e terceiros antes do atendimento", "não ingressar em ambiente inseguro sem controle do risco"),
        ("APH básico", "atendimento inicial pré-hospitalar com medidas compatíveis com treinamento até transferência ao serviço especializado", "acionar ajuda e comunicar informações essenciais"),
    ],
    "area-inteligencia": [
        ("fonte de coleta", "origem de dados ou informações utilizados na atividade de inteligência", "avaliar confiabilidade antes de transformar dado em conhecimento"),
        ("produção de conhecimento", "processo metodológico de tratar e analisar dados para apoiar decisão", "distinguir dado bruto de conhecimento analisado"),
    ],

    # Legislação
    "leg-maria-penha": [
        ("violência doméstica e familiar", "ação ou omissão baseada no gênero, nos âmbitos previstos em lei, que cause os danos definidos pela Lei 11.340/2006", "reconhecer que relação íntima de afeto não exige coabitação"),
        ("formas de violência", "categorias legais como física, psicológica, sexual, patrimonial, moral e, na redação vigente em 2026, violência vicária", "classificar retenção de bens como violência patrimonial"),
    ],
    "leg-drogas": [
        ("Sisnad", "Sistema Nacional de Políticas Públicas sobre Drogas instituído pela Lei 11.343/2006", "articular prevenção, atenção, reinserção e repressão às condutas ilícitas previstas"),
        ("tratamento legal diferenciado", "a Lei de Drogas distingue condutas e consequências conforme elementos legais de cada tipo", "não tratar porte para consumo e tráfico como tipos idênticos"),
    ],
    "leg-racismo": [
        ("Lei 7.716/1989", "diploma que define crimes resultantes de discriminação ou preconceito nos termos de sua redação vigente", "identificar condutas discriminatórias tipificadas pela lei"),
        ("igualdade e não discriminação", "valor jurídico protegido pelo conjunto normativo antidiscriminatório", "distinguir tratamento discriminatório de critério legítimo previsto em lei"),
    ],
    "leg-eca": [
        ("proteção integral", "princípio estruturante do ECA que reconhece crianças e adolescentes como sujeitos de direitos", "priorizar proteção e desenvolvimento conforme o Estatuto"),
        ("criança e adolescente", "para o ECA, criança é pessoa até doze anos incompletos e adolescente aquela entre doze e dezoito anos, ressalvadas previsões legais", "classificar corretamente a faixa etária"),
    ],
    "leg-ambiental": [
        ("Lei 9.605/1998", "diploma que dispõe sobre sanções penais e administrativas derivadas de condutas e atividades lesivas ao meio ambiente", "identificar crime ambiental sem confundi-lo com mera regra civil"),
        ("responsabilidade ambiental", "regime que pode alcançar pessoas físicas e jurídicas conforme os requisitos legais", "analisar a responsabilidade da pessoa jurídica quando presentes condições da lei"),
    ],
    "leg-ctb": [
        ("CTB", "Código de Trânsito Brasileiro, Lei 9.503/1997, que disciplina trânsito e o Sistema Nacional de Trânsito", "consultar regras de circulação, infrações, penalidades e crimes de trânsito"),
        ("segurança e educação no trânsito", "eixos presentes nas competências e políticas do sistema de trânsito", "relacionar fiscalização a ações de segurança e educação"),
    ],
    "leg-desarmamento": [
        ("Sinarm", "Sistema Nacional de Armas previsto na Lei 10.826/2003", "relacionar registro e controle de armas ao sistema legal"),
        ("posse e porte", "situações jurídicas distintas submetidas a requisitos e restrições próprias", "não tratar autorização de posse como autorização geral de porte"),
    ],
    "leg-abuso": [
        ("finalidade específica", "a Lei 13.869/2019 exige, nos tipos previstos, finalidade específica como prejudicar, beneficiar ou agir por capricho/satisfação pessoal", "não concluir abuso apenas pela existência de decisão posteriormente revista"),
        ("divergência interpretativa", "a mera divergência na interpretação de lei ou avaliação de fatos e provas não configura abuso de autoridade por si só", "distinguir erro ou divergência de conduta típica dolosa com finalidade exigida"),
    ],
    "leg-licitacoes": [
        ("Lei 14.133/2021", "lei geral de licitações e contratos administrativos", "estudar planejamento, seleção do fornecedor e execução contratual dentro do regime atual"),
        ("modalidades", "formas legais de licitação previstas na Lei 14.133/2021, como concorrência, pregão, concurso, leilão e diálogo competitivo", "distinguir modalidade de critério de julgamento"),
    ],
    "leg-lc1": [
        ("regime estatutário municipal", "a LC 1/1991 disciplina o regime jurídico dos servidores da administração direta, autarquias e fundações de Salvador nos termos vigentes", "distinguir servidor público de cargo público"),
        ("deveres e proibições", "a legislação municipal estabelece deveres funcionais e condutas vedadas ao servidor", "revisar especialmente os dispositivos de conduta funcional indicados pela CGM"),
    ],
    "leg-carreira": [
        ("Plano de Carreira GCM", "a Lei 9.640/2022 disciplina carreira e vencimentos do cargo efetivo de Guarda Civil Municipal de Salvador", "distinguir progressão de promoção na estrutura da carreira"),
        ("carreira única", "o cargo é organizado em carreira com classes e níveis segundo a Lei 9.640/2022", "reconhecer a 3ª Classe como classe inicial de ingresso"),
    ],
    "leg-guardas": [
        ("caráter civil", "a Lei 13.022/2014 define as guardas municipais como instituições de caráter civil, uniformizadas e armadas conforme a lei", "distinguir guarda municipal de força militar"),
        ("competência geral", "proteção de bens, serviços, logradouros públicos municipais e instalações do Município, sem prejuízo das competências específicas", "relacionar atuação preventiva à proteção municipal"),
    ],
    "leg-regimento": [
        ("Decreto 27.731/2016", "decreto municipal que aprovou o Regimento da Guarda Civil Municipal de Salvador", "consultar natureza, estrutura e competências regimentais"),
        ("organização regimental", "distribuição interna de órgãos, atribuições e relações funcionais da GCM", "usar o regimento para identificar a estrutura administrativa da corporação"),
    ],
    "leg-disciplinar": [
        ("Regime Disciplinar", "a Lei 9.273/2017 define deveres, direitos e tipifica infrações disciplinares dos integrantes da GCM Salvador", "distinguir infração disciplinar de crime penal"),
        ("hierarquia e disciplina", "bases institucionais definidas pela Lei 9.273/2017 para ordenar autoridade e cumprimento do dever funcional", "executar ordens legais e buscar esclarecimento em caso de dúvida"),
    ],
    "leg-organica-poderes": [
        ("Lei Orgânica", "norma fundamental do Município de Salvador que organiza sua estrutura político-administrativa nos limites constitucionais", "estudar competências municipais e funções de Legislativo e Executivo"),
        ("competência municipal", "atribuição conferida ao Município pela Constituição e pela Lei Orgânica", "distinguir competência do Município de atribuição específica de um órgão"),
    ],
    "leg-organica-adm": [
        ("Administração municipal", "estrutura e atividade administrativa disciplinadas pela Lei Orgânica e legislação complementar", "relacionar servidores, bens e serviços públicos ao regime municipal"),
        ("planejamento e orçamento", "instrumentos de organização das prioridades e finanças públicas municipais", "distinguir planejamento público de execução isolada de despesa"),
    ],
    "leg-organizacao-adm": [
        ("administração direta", "conjunto de órgãos integrantes da estrutura das pessoas políticas sem personalidade jurídica própria", "identificar secretaria municipal como estrutura da administração direta"),
        ("administração indireta", "conjunto de entidades com personalidade jurídica própria criadas ou autorizadas nos termos legais para funções administrativas", "distinguir autarquia de órgão da administração direta"),
    ],
    "leg-tributario": [
        ("Código Tributário de Salvador", "Lei 7.186/2006, com alterações, que institui o Código Tributário e de Rendas do Município", "consultar tributos municipais, obrigações e fiscalização na versão consolidada"),
        ("obrigação tributária", "relação jurídica decorrente da legislação tributária com prestações principais ou acessórias conforme o regime aplicável", "distinguir obrigação de crédito já constituído"),
    ],
    "leg-etica-transparencia": [
        ("integridade pública", "conjunto de valores, regras e mecanismos destinados a orientar conduta íntegra e prevenir desvios na Administração", "relacionar dever funcional a legalidade, impessoalidade e moralidade"),
        ("transparência e acesso", "deveres e mecanismos que favorecem publicidade, acesso à informação e controle da Administração nos limites legais", "distinguir publicidade de exposição indevida de informação protegida"),
    ],
    "leg-direitos-cidadaos": [
        ("direitos do cidadão", "garantias de relacionamento com a Administração, como acesso a serviços e informações nos limites legais", "formular pedido administrativo de modo identificável e objetivo"),
        ("dever funcional do agente", "obrigação de atuar dentro da competência, normas e princípios aplicáveis ao serviço público", "tratar o cidadão com objetividade e respeito sem favorecer interesse privado"),
    ],
}

SUBJECT_PITFALLS = {
    "portugues": "Leia o texto e a relação de sentido antes de aplicar regra isolada; a alternativa precisa ser sustentada pelo enunciado.",
    "rlm": "Não pule unidades, sinais ou condições. Uma conta correta com interpretação errada continua produzindo resposta errada.",
    "informatica": "Diferencie recurso, formato e finalidade. Nomes parecidos de comandos não significam a mesma função.",
    "constitucional-civil": "Separe conceitos constitucionais dos civis e confira a redação legal/jurisprudencial atual quando o tópico exigir.",
    "penal-processual": "Não misture Direito Penal material com Processo Penal. Leia requisitos e exceções antes de generalizar.",
    "administracao-politicas": "Diferencie conceitos próximos e observe se a questão fala de estrutura, processo, estratégia ou avaliação.",
    "area-atuacao": "Priorize princípios, prevenção, cadeia de comando, comunicação e segurança. Não transforme noções de prova em improvisação operacional.",
    "legislacao": "Lei é conteúdo de atualização contínua: confirme sempre a redação vigente e não confunda leis federais com normas municipais.",
}


def scope_fact(topic: dict[str, Any]) -> tuple[str, str, str]:
    return (
        "recorte oficial do edital",
        topic["officialScope"],
        f"revisar exatamente os itens previstos em '{topic['label']}' sem acrescentar matéria estranha ao edital",
    )


def all_facts(topic: dict[str, Any]) -> list[tuple[str, str, str]]:
    facts = list(FACTS.get(topic["id"], []))
    facts.append(scope_fact(topic))
    return facts


def place_answer(correct: str, distractors: list[str]) -> tuple[list[str], int]:
    options: list[str] = []
    for value in [correct, *distractors]:
        if value and value not in options:
            options.append(value)
    while len(options) < 5:
        options.append(f"Alternativa incompatível com o recorte {len(options) + 1}")
    options = options[:5]
    RNG.shuffle(options)
    return options, options.index(correct)


def topic_index(syllabus: dict[str, Any]) -> tuple[dict[str, dict], dict[str, dict]]:
    subjects: dict[str, dict] = {}
    topics: dict[str, dict] = {}
    for subject in syllabus["subjects"]:
        subjects[subject["id"]] = subject
        for topic in subject["topics"]:
            topics[topic["id"]] = {**topic, "subjectId": subject["id"], "subjectName": subject["name"]}
    return subjects, topics


def distractor_pool(subject: dict, topics: dict[str, dict], field: int, exclude_topic: str) -> list[str]:
    values: list[str] = []
    for topic in subject["topics"]:
        if topic["id"] == exclude_topic:
            continue
        for fact in all_facts(topics[topic["id"]]):
            values.append(fact[field])
    return values


def make_concept_questions(subject: dict, topic: dict, topics: dict[str, dict]) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    facts = all_facts(topic)
    other_terms = distractor_pool(subject, topics, 0, topic["id"])
    other_defs = distractor_pool(subject, topics, 1, topic["id"])
    other_examples = distractor_pool(subject, topics, 2, topic["id"])

    for fact_no, (term, definition, example) in enumerate(facts, start=1):
        other_fact_pool = [
            fact
            for other_topic in subject["topics"]
            if other_topic["id"] != topic["id"]
            for fact in all_facts(topics[other_topic["id"]])
        ]
        forms = [
            (
                f"No estudo de {topic['label']}, o que melhor descreve '{term}'?",
                definition,
                RNG.sample(other_defs, min(4, len(other_defs))),
                f"'{term}' deve ser entendido como {definition}.",
            ),
            (
                f"Qual conceito de {topic['label']} corresponde à definição: {definition}?",
                term,
                RNG.sample(other_terms, min(4, len(other_terms))),
                f"A definição apresentada corresponde a '{term}'.",
            ),
            (
                f"Qual situação se relaciona mais diretamente a '{term}' dentro de {topic['label']}?",
                example,
                RNG.sample(other_examples, min(4, len(other_examples))),
                f"O exemplo adequado é: {example}.",
            ),
            (
                f"Assinale a associação correta sobre {topic['label']} (bloco {fact_no}).",
                f"{term} — {definition}",
                [f"{x[0]} — {definition}" for x in RNG.sample(other_fact_pool, 4)],
                f"A associação correta é '{term} — {definition}'.",
            ),
            (
                f"Em uma revisão de {topic['label']}, qual afirmação está correta sobre '{term}'?",
                f"{term} se relaciona a {definition}.",
                [f"{term} se relaciona a {d}." for d in RNG.sample(other_defs, min(4, len(other_defs)))],
                f"A afirmação correta preserva a definição do conceito: {definition}.",
            ),
            (
                f"Um aluno anotou: '{example}'. Essa anotação serve como exemplo de qual conceito?",
                term,
                RNG.sample(other_terms, min(4, len(other_terms))),
                f"A situação foi cadastrada como exemplo de '{term}' dentro do tópico.",
            ),
            (
                f"Para não sair do conteúdo de {topic['label']}, qual opção permanece no recorte correto?",
                definition,
                RNG.sample(other_defs, min(4, len(other_defs))),
                f"O item correto pertence diretamente ao tópico e é descrito como: {definition}.",
            ),
            (
                f"Em uma questão aplicada de {topic['label']}, qual exemplo está corretamente relacionado a '{term}'?",
                example,
                RNG.sample(other_examples, min(4, len(other_examples))),
                f"O exemplo compatível com '{term}' é: {example}.",
            ),
            (
                f"Qual par conceito-exemplo está correto dentro de {topic['label']}?",
                f"{term} — {example}",
                [f"{x[0]} — {example}" for x in RNG.sample(other_fact_pool, 4)],
                f"O par correto é '{term} — {example}'.",
            ),
        ]

        for form_no, (stem, correct, wrong, explanation) in enumerate(forms, start=1):
            if len(wrong) < 4:
                continue
            options, answer = place_answer(correct, wrong)
            generated.append({
                "id": f"v2-{subject['id']}-{topic['id']}-{fact_no:02d}-{form_no:02d}",
                "contestId": CONTEST_ID,
                "subjectId": subject["id"],
                "topicIds": [topic["id"]],
                "difficulty": "easy" if term == "recorte oficial do edital" else ("medium" if form_no < 5 else "hard"),
                "sourceType": "authorial",
                "sourceLabel": "Questão autoral focada no tópico do edital - não é questão oficial da FGV",
                "stem": stem,
                "options": options,
                "answerIndex": answer,
                "explanation": explanation,
                "tags": ["v2", "conteudo-topico"] + (["matriz-edital"] if term == "recorte oficial do edital" else []),
            })
    return generated


def numeric_rlm_questions() -> dict[str, list[dict[str, Any]]]:
    """Questões numéricas adicionais para que RLM não vire só flashcard conceitual."""
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add(topic: str, stem: str, correct: str, wrong: list[str], explanation: str, diff: str = "medium") -> None:
        options, answer = place_answer(correct, wrong)
        out[topic].append({
            "id": f"v2-rlm-{topic}-calc-{len(out[topic])+1:03d}",
            "contestId": CONTEST_ID,
            "subjectId": "rlm",
            "topicIds": [topic],
            "difficulty": diff,
            "sourceType": "authorial",
            "sourceLabel": "Questão autoral de RLM - não é questão oficial da FGV",
            "stem": stem,
            "options": options,
            "answerIndex": answer,
            "explanation": explanation,
            "tags": ["v2", "calculo"],
        })

    add("numeros-operacoes", "Calcule 18 - 3 × 4 + 2.", "8", ["62", "14", "20", "5"], "Faça a multiplicação primeiro: 3×4=12; depois 18-12+2=8.", "easy")
    add("numeros-operacoes", "Qual fração é equivalente a 0,375?", "3/8", ["3/5", "5/8", "37/100", "1/4"], "0,375=375/1000=3/8 após simplificação.")
    add("numeros-operacoes", "O resultado de (-6) + 14 - 9 é:", "-1", ["1", "-11", "17", "-29"], "-6+14=8 e 8-9=-1.", "easy")
    add("reta-numerica", "Na reta numérica, qual é a distância entre -7 e 5?", "12", ["2", "-12", "7", "35"], "Distância = |5-(-7)|=12.", "easy")
    add("reta-numerica", "Em ordem crescente, qual sequência está correta?", "-5, -2, 0, 3", ["-2, -5, 0, 3", "3, 0, -2, -5", "-5, 0, -2, 3", "0, -2, -5, 3"], "Na reta, valores menores ficam à esquerda.")
    add("unidades-medida", "Uma rota de 3,6 km corresponde a quantos metros?", "3.600 m", ["36 m", "360 m", "36.000 m", "3.060 m"], "1 km=1.000 m; 3,6×1.000=3.600.", "easy")
    add("unidades-medida", "Um treinamento durou 2 h 15 min. Qual foi a duração total em minutos?", "135 min", ["115 min", "125 min", "145 min", "215 min"], "2 h=120 min; 120+15=135.", "easy")
    add("unidades-medida", "2,4 kg equivalem a:", "2.400 g", ["24 g", "240 g", "24.000 g", "2.040 g"], "1 kg=1.000 g; 2,4 kg=2.400 g.", "easy")
    add("plano-cartesiano", "Em qual quadrante está o ponto (4,-3)?", "IV quadrante", ["I quadrante", "II quadrante", "III quadrante", "sobre o eixo y"], "x positivo e y negativo caracterizam o IV quadrante.")
    add("plano-cartesiano", "O ponto (0,5) está localizado:", "sobre o eixo y", ["sobre o eixo x", "no I quadrante", "no II quadrante", "na origem"], "Quando x=0, o ponto está no eixo y.", "easy")
    add("algebra", "Resolva 3x - 7 = 20.", "9", ["7", "8", "11", "27"], "3x=27; x=9.", "easy")
    add("algebra", "Um número somado ao seu dobro resulta em 36. Esse número é:", "12", ["9", "18", "24", "36"], "x+2x=36 => 3x=36 => x=12.")
    add("algebra", "No sistema x+y=18 e x-y=4, o valor de x é:", "11", ["7", "9", "14", "22"], "Somando as equações: 2x=22, logo x=11.", "hard")
    add("porcentagem-proporcao", "Um valor de R$ 800 recebeu desconto de 15%. Qual é o novo valor?", "R$ 680", ["R$ 120", "R$ 685", "R$ 720", "R$ 920"], "15% de 800=120; 800-120=680.")
    add("porcentagem-proporcao", "Uma quantidade passou de 200 para 250. O aumento percentual foi de:", "25%", ["20%", "50%", "12,5%", "125%"], "Aumento de 50 sobre base 200: 50/200=25%.")
    add("porcentagem-proporcao", "Se 6 pessoas executam uma tarefa em 10 dias, no modelo de produtividade idêntica, 12 pessoas executariam em:", "5 dias", ["20 dias", "12 dias", "8 dias", "2 dias"], "Quantidade de pessoas e tempo são inversamente proporcionais: dobrar pessoas reduz o tempo à metade.", "hard")
    add("sequencias-pa-pg", "Na PA 7, 11, 15, 19, ..., qual é o 8º termo?", "35", ["31", "39", "32", "43"], "a8=7+(8-1)×4=35.")
    add("sequencias-pa-pg", "Na PG 3, 6, 12, 24, ..., o próximo termo é:", "48", ["30", "36", "42", "96"], "A razão é 2; 24×2=48.", "easy")
    add("sequencias-pa-pg", "A sequência 1, 4, 9, 16, 25, ... segue o padrão dos quadrados. O próximo termo é:", "36", ["30", "32", "35", "49"], "Os termos são 1²,2²,3²,4²,5²; o próximo é 6²=36.")
    add("juros", "R$ 2.000 a juros simples de 3% ao mês durante 5 meses geram juros de:", "R$ 300", ["R$ 30", "R$ 150", "R$ 2.300", "R$ 600"], "J=C×i×t=2000×0,03×5=300.")
    add("juros", "R$ 1.000 aplicados a 10% ao período por 3 períodos, em juros compostos, resultam em:", "R$ 1.331", ["R$ 1.300", "R$ 1.210", "R$ 1.030", "R$ 1.100"], "M=1000×1,1³=1.331.", "hard")
    add("juros", "Em juros simples, se capital e tempo permanecem constantes e a taxa dobra, os juros:", "dobram", ["caem pela metade", "não mudam", "quadruplicam", "viram zero"], "J=C×i×t; com C e t constantes, J é diretamente proporcional à taxa.")
    add("geometria-basica", "Um terreno retangular mede 12 m por 8 m. Seu perímetro é:", "40 m", ["20 m", "96 m", "48 m", "80 m"], "P=2(12+8)=40 m.", "easy")
    add("geometria-basica", "Um quadrado de lado 7 m possui área de:", "49 m²", ["14 m²", "28 m²", "42 m²", "56 m²"], "A=l²=7²=49 m².", "easy")
    add("geometria-basica", "A soma dos ângulos internos de um triângulo é:", "180°", ["90°", "270°", "360°", "540°"], "Todo triângulo plano possui soma interna de 180°.")
    add("semelhanca-triangulo", "Um triângulo retângulo tem catetos 5 e 12. A hipotenusa mede:", "13", ["10", "15", "17", "60"], "h²=5²+12²=169; h=13.")
    add("semelhanca-triangulo", "Dois triângulos semelhantes têm razão de semelhança 2. Se um lado do menor mede 6, o correspondente no maior mede:", "12", ["3", "6", "8", "18"], "Lados correspondentes mantêm a razão: 6×2=12.")
    add("medidas-area-volume", "Um bloco retangular de 4 m × 3 m × 2 m tem volume de:", "24 m³", ["9 m³", "12 m³", "18 m³", "36 m³"], "V=4×3×2=24 m³.")
    add("medidas-area-volume", "Uma área de 2 m² corresponde a quantos cm²?", "20.000 cm²", ["200 cm²", "2.000 cm²", "200.000 cm²", "20 cm²"], "1 m²=10.000 cm²; portanto 2 m²=20.000 cm².", "hard")
    add("contagem-probabilidade", "Uma senha tem 2 posições, cada uma podendo usar 4 símbolos distintos, com repetição permitida. Quantas senhas são possíveis?", "16", ["6", "8", "12", "24"], "Princípio multiplicativo: 4×4=16.")
    add("contagem-probabilidade", "Em uma urna há 3 bolas azuis e 2 vermelhas. Retirando uma ao acaso, a probabilidade de azul é:", "3/5", ["2/5", "1/2", "3/2", "1/5"], "Há 3 casos favoráveis em 5 possíveis.", "easy")
    add("conjuntos", "Em um grupo, 30 estudam Português, 20 Matemática e 8 estudam ambos. Quantos estudam pelo menos uma das duas matérias?", "42", ["50", "58", "22", "38"], "|P∪M|=30+20-8=42.", "hard")
    add("conjuntos", "Se A={1,2,3,4} e B={3,4,5,6}, A-B é:", "{1,2}", ["{3,4}", "{5,6}", "{1,2,5,6}", "{1,2,3,4,5,6}"], "A-B contém elementos de A que não pertencem a B.")
    add("diagramas-graficos", "Uma tabela mostra 120 atendimentos na segunda e 90 na terça. A redução absoluta foi de:", "30", ["25", "33", "90", "210"], "120-90=30.", "easy")
    add("diagramas-graficos", "Uma série mensal registra 50, 65 e 80 ocorrências. O aumento do primeiro para o terceiro valor é:", "30", ["15", "20", "65", "130"], "80-50=30.")
    add("proposicoes", "Se P é verdadeira e Q é falsa, o valor de P e Q é:", "falso", ["verdadeiro", "indeterminado", "equivalente a P", "equivalente a Q verdadeiro"], "A conjunção só é verdadeira quando ambas são verdadeiras.")
    add("proposicoes", "Se P é falsa e Q é verdadeira, o valor de P ou Q (ou inclusivo) é:", "verdadeiro", ["falso", "indeterminado", "sempre falso", "não é proposição"], "A disjunção inclusiva é verdadeira quando pelo menos uma proposição é verdadeira.")
    add("equivalencias", "A contrapositiva de 'Se estudo, então melhoro' é:", "Se não melhoro, então não estudo", ["Se melhoro, então estudo", "Se não estudo, então não melhoro", "Estudo e melhoro", "Não estudo ou não melhoro"], "P→Q é equivalente a ¬Q→¬P.")
    add("equivalencias", "A negação de 'Todos os candidatos estudaram' é:", "Pelo menos um candidato não estudou", ["Nenhum candidato estudou", "Todos os candidatos não estudaram", "Alguns estudaram", "Todos estudaram novamente"], "Negar o quantificador universal exige ao menos um contraexemplo.", "hard")
    add("problemas-raciocinio", "Lia está antes de Nara; Nara está antes de Rui; Rui está antes de Caio. Quem necessariamente está depois de Lia?", "Nara, Rui e Caio", ["apenas Nara", "apenas Caio", "ninguém", "apenas Rui"], "A relação de ordem é transitiva.")
    add("problemas-raciocinio", "Três salas A, B e C têm cores diferentes. A não é azul; B é verde; C não é vermelha. Se as cores são azul, verde e vermelha, qual cor é A?", "vermelha", ["azul", "verde", "não é possível saber", "azul ou verde"], "B=verde. A não é azul nem verde, então A=vermelha; C=azul.", "hard")

    return out


def enrich_lessons(lessons: list[dict], topics: dict[str, dict], subjects: dict[str, dict]) -> None:
    for lesson in lessons:
        topic = topics.get(lesson["topicId"])
        if not topic:
            continue
        facts = all_facts(topic)
        subject_id = topic["subjectId"]
        scope_parts = split_scope(topic["officialScope"])
        concept_items = [f"{term}: {definition}" for term, definition, _ in facts if term != "recorte oficial do edital"]
        example_items = [example for term, _, example in facts if term != "recorte oficial do edital"]
        existing_titles = {section.get("title") for section in lesson.get("sections", [])}
        additions = [
            {"title": "Mapa exato do edital", "items": scope_parts or [topic["officialScope"]]},
            {"title": "Conceitos que você precisa dominar", "items": concept_items},
            {"title": "Aplicações e exemplos", "items": example_items},
            {"title": "Como isso costuma virar questão", "items": [
                "definição e distinção entre conceitos próximos",
                "aplicação do conceito em situação concreta",
                "identificação de alternativa incompatível com o recorte",
                "combinação do tópico com outro subitem expressamente listado no mesmo conteúdo oficial",
            ]},
            {"title": "Armadilha de prova", "body": SUBJECT_PITFALLS[subject_id]},
            {"title": "Meta de domínio", "body": f"Leia a teoria, faça pelo menos 20 questões de {topic['label']} e busque 80% ou mais em duas sessões separadas antes de considerar o tópico dominado."},
        ]
        for section in additions:
            if section["title"] not in existing_titles:
                lesson.setdefault("sections", []).append(section)
        lesson["depth"] = "concurso-aprofundado-v2"
        lesson["questionTarget"] = TARGETS[subject_id]
        lesson.setdefault("source", {})["officialScope"] = topic["officialScope"]
        lesson["source"]["note"] = "A teoria é organizada pelo recorte do Anexo I; questões adicionais são autorais."


def main() -> None:
    syllabus_path = DATA / "syllabus" / f"{CONTEST_ID}.json"
    lessons_path = DATA / "lessons" / f"{CONTEST_ID}.json"
    questions_path = DATA / "questions" / f"{CONTEST_ID}.json"

    syllabus = load_json(syllabus_path)
    lessons = load_json(lessons_path)
    questions = load_json(questions_path)
    subjects, topics = topic_index(syllabus)

    missing_facts = sorted(topic_id for topic_id in topics if topic_id not in FACTS)
    if missing_facts:
        raise SystemExit(f"Tópicos sem curadoria FACTS: {missing_facts}")

    enrich_lessons(lessons, topics, subjects)

    seen_ids = {q["id"] for q in questions}
    seen_stems = {norm(q["stem"]) for q in questions}
    coverage = Counter(q["topicIds"][0] for q in questions if q.get("topicIds"))

    numeric = numeric_rlm_questions()
    for topic_id, rows in numeric.items():
        for q in rows:
            if q["id"] in seen_ids or norm(q["stem"]) in seen_stems:
                continue
            questions.append(q)
            seen_ids.add(q["id"])
            seen_stems.add(norm(q["stem"]))
            coverage[topic_id] += 1

    for subject_id, subject in subjects.items():
        target = TARGETS[subject_id]
        for topic_stub in subject["topics"]:
            topic = topics[topic_stub["id"]]
            candidates = make_concept_questions(subject, topic, topics)
            RNG.shuffle(candidates)
            for q in candidates:
                if coverage[topic["id"]] >= target:
                    break
                fingerprint = norm(q["stem"])
                if q["id"] in seen_ids or fingerprint in seen_stems:
                    continue
                questions.append(q)
                seen_ids.add(q["id"])
                seen_stems.add(fingerprint)
                coverage[topic["id"]] += 1

            if coverage[topic["id"]] < target:
                raise SystemExit(f"Banco insuficiente em {topic['id']}: {coverage[topic['id']]}/{target}")

    subject_order = {subject["id"]: i for i, subject in enumerate(syllabus["subjects"])}
    topic_order = {
        topic["id"]: i
        for subject in syllabus["subjects"]
        for i, topic in enumerate(subject["topics"])
    }
    questions.sort(key=lambda q: (
        subject_order.get(q["subjectId"], 999),
        topic_order.get(q["topicIds"][0], 999),
        q["id"],
    ))

    write_json(lessons_path, lessons)
    write_json(questions_path, questions)

    print(f"Aulas enriquecidas: {len(lessons)}")
    print(f"Questões totais: {len(questions)}")
    for subject_id, subject in subjects.items():
        total = sum(coverage[t["id"]] for t in subject["topics"])
        minimum = min(coverage[t["id"]] for t in subject["topics"])
        print(f"{subject['name']}: {total} questões; mínimo por tópico={minimum}")


if __name__ == "__main__":
    main()
