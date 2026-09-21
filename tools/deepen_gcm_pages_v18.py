#!/usr/bin/env python3
"""Aprofunda cada página GCM sem ampliar o escopo oficial do edital.

A expansão é deliberadamente conservadora: novos blocos são construídos a partir
apenas do texto já presente na própria aula/página e do officialScope. Não injeta
novas leis, artigos, números ou conceitos externos.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LESSONS_PATH = DATA / "lessons" / "gcm-salvador-2026.json"
SYLLABUS_PATH = DATA / "syllabus" / "gcm-salvador-2026.json"
QUESTIONS_PATH = DATA / "questions" / "gcm-salvador-2026.json"
CONFIG_PATH = ROOT / "js" / "config.js"
SW_PATH = ROOT / "sw.js"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"

VERSION = "1.8.0"
PAGE_LAYER = "gcm-page-depth-v1.8.0"
MIN_ADDED_CHARS = 2200
EXPECTED_PAGES = 3944
EXPECTED_TOPICS = 116
EXPECTED_QUESTIONS = 2650

GENERIC_TITLES = {
    "Recorte oficial", "Como usar este capítulo", "Regra de fidelidade",
    "Verificação conceitual", "Controle de escopo e revisão ativa",
    "Prática dirigida", "Fechamento", "Leitura de precisão",
}
BOILERPLATE_FRAGMENTS = (
    "este aprofundamento decorre", "o teto desta aula continua sendo",
    "o limite é o recorte literal", "a leitura deve separar",
    "quando a questão modificar", "o núcleo deste subtópico é",
    "para estudar de verdade", "separe o que é conceito principal",
    "a pergunta central é reconhecer", "explique com suas palavras por que",
    "compare o núcleo", "defina o que pertence a cada um",
    "esta página desenvolve somente", "todo o capítulo abaixo serve",
    "os subtópicos são divisões didáticas", "reconstrua o conteúdo desta página",
)
STOP = {
    "a","o","as","os","um","uma","uns","umas","de","da","do","das","dos","e","ou","em","no","na","nos","nas",
    "por","para","com","sem","sob","sobre","entre","que","se","ser","são","é","ao","aos","à","às","como","quando",
    "onde","qual","quais","mais","menos","não","sim","seu","sua","seus","suas","este","esta","esse","essa","isso",
    "cada","também","pode","podem","deve","devem","dentro","fora","mesmo","mesma","outro","outra","apenas","todo","toda",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def all_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for item in obj:
            yield from all_strings(item)
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from all_strings(value)


def sentence_candidates(text: str) -> list[str]:
    text = norm(text)
    if not text:
        return []
    chunks = re.split(r"(?<=[.!?;:])\s+|\s+[•▪]\s+|\n+", text)
    out=[]
    seen=set()
    for raw in chunks:
        s=norm(raw).strip(" -–—•▪")
        low=s.lower()
        if len(s) < 45:
            continue
        if any(fragment in low for fragment in BOILERPLATE_FRAGMENTS):
            continue
        if len(s) > 650:
            s=s[:647].rsplit(" ",1)[0] + "…"
        key=re.sub(r"\W+"," ",s.lower()).strip()
        if key and key not in seen:
            seen.add(key); out.append(s)
    return out


def keywords(points: list[str], limit=12) -> list[str]:
    freq=Counter()
    first={}
    order=0
    for p in points:
        for token in re.findall(r"[A-Za-zÀ-ÿ0-9ºª]+(?:[-/][A-Za-zÀ-ÿ0-9ºª]+)*", p):
            clean=token.strip("-/").lower()
            if len(clean) < 5 or clean in STOP or clean.isdigit():
                continue
            freq[clean]+=1
            if clean not in first:
                first[clean]=(order,token)
                order+=1
    ranked=sorted(freq, key=lambda x:(-freq[x],first[x][0]))
    return [first[x][1] for x in ranked[:limit]]


def pick_points(lesson: dict, page: dict, page_index: int) -> list[str]:
    specific=[]
    for block in page.get("blocks") or []:
        if block.get("title") in GENERIC_TITLES:
            continue
        specific += sentence_candidates(block.get("body", ""))

    lesson_pool=[]
    for s in lesson.get("subtopics") or []:
        lesson_pool += sentence_candidates(s)
    lesson_pool += sentence_candidates(lesson.get("summary", ""))
    for section in lesson.get("sections") or []:
        # sections já pertencem ao mesmo topicId/officialScope; servem só como fallback.
        lesson_pool += sentence_candidates(" ".join(all_strings(section)))

    # Remove duplicações preservando ordem.
    def uniq(seq):
        result=[]; seen=set()
        for s in seq:
            key=re.sub(r"\W+"," ",s.lower()).strip()
            if key and key not in seen:
                seen.add(key); result.append(s)
        return result
    specific=uniq(specific)
    lesson_pool=uniq(lesson_pool)

    # Rotaciona o fallback para páginas diferentes não receberem sempre os mesmos núcleos.
    if lesson_pool:
        offset=(page_index * 3) % len(lesson_pool)
        lesson_pool=lesson_pool[offset:]+lesson_pool[:offset]
    combined=uniq(specific + lesson_pool)

    # officialScope é o último fallback, nunca uma fonte externa.
    scope=norm(lesson.get("officialScope") or page.get("sourceScope") or page.get("editalBasis"))
    if len(combined) < 4 and scope:
        combined += sentence_candidates(
            f"O recorte oficial desta aula é {scope}. O estudo desta página deve permanecer dentro desse recorte e das distinções necessárias para compreendê-lo."
        )
    if not combined:
        combined=[f"O recorte oficial desta página é {scope}."]
    while len(combined) < 4:
        combined.append(combined[len(combined) % len(combined)])
    return combined[:4]


def make_blocks(lesson: dict, page: dict, page_index: int) -> list[dict]:
    pts=pick_points(lesson,page,page_index)
    kws=keywords(pts)
    title=norm(page.get("title"))
    topic=norm(lesson.get("title"))
    scope=norm(lesson.get("officialScope") or page.get("sourceScope"))
    kw_text=", ".join(kws) if kws else "os termos centrais destacados nos núcleos abaixo"

    b1 = (
        f"Esta camada aprofunda a página “{title}” dentro de “{topic}” sem abrir conteúdo fora do recorte oficial “{scope}”. "
        "Em vez de reler o texto de forma corrida, desmonte-o em núcleos verificáveis. "
        f"Núcleo 1 — {pts[0]} Para dominar este ponto, identifique exatamente qual é a ideia principal, quais elementos estão ligados e se existe condição, limite, finalidade ou consequência. "
        f"Núcleo 2 — {pts[1]} Aqui, transforme a frase em uma explicação oral curta e depois reconstrua-a sem olhar. Preserve os termos que mudam o sentido; não substitua uma relação por outra apenas porque parecem próximas. "
        f"Núcleo 3 — {pts[2]} Leia este núcleo procurando o detalhe que permitiria eliminar uma alternativa quase correta. Pergunte o que precisaria permanecer verdadeiro para que a afirmação continue fiel ao que foi estudado. "
        f"Núcleo 4 — {pts[3]} Feche a leitura ligando este ponto aos anteriores: o objetivo é formar uma rede de relações dentro do mesmo tópico, e não memorizar quatro frases isoladas. "
        f"Vocabulário de controle desta página: {kw_text}. Esses termos servem como marcadores para localizar rapidamente o núcleo exigido pela questão, sempre conferindo o contexto em que aparecem."
    )
    b2 = (
        f"Faça uma comparação interna dos quatro núcleos da página “{title}”. Comece por “{pts[0]}” e confronte com “{pts[1]}”. "
        "Anote o elemento comum e, em seguida, a diferença que impede tratar as duas formulações como equivalentes. Depois repita o procedimento entre os núcleos 2 e 3 e entre os núcleos 3 e 4. "
        "A armadilha típica de prova não precisa apresentar um assunto completamente estranho: muitas vezes ela conserva o vocabulário correto e altera apenas alcance, condição, sujeito, relação, ordem, finalidade ou consequência. "
        f"Use como âncoras os termos {kw_text}. Para cada um, diga em qual dos quatro núcleos ele aparece e qual função exerce ali. "
        "Se um termo surgir em mais de um núcleo, explique se mantém a mesma função ou se o contexto muda sua interpretação. Se não houver informação suficiente para afirmar algo além do texto-base, marque essa lacuna em vez de completá-la por memória externa. "
        "Esse procedimento é especialmente importante em legislação: a atividade aqui organiza o conteúdo já presente, mas não substitui a redação oficial vigente aplicável ao concurso."
    )
    b3 = (
        f"Faça esta recuperação ativa sem consultar a página. 1) Explique, em uma frase, o que a página “{title}” pretende que você saiba. "
        f"2) Reconstrua o núcleo 1: {pts[0]} Em seguida, retire mentalmente um elemento importante e explique por que a versão incompleta pode mudar o sentido. "
        f"3) Reconstrua o núcleo 2: {pts[1]} Diga qual palavra ou expressão funciona como melhor pista para reconhecer esse ponto em uma alternativa. "
        f"4) A partir de “{pts[2]}”, formule uma pergunta curta que force você a recuperar a relação central, e responda usando somente o conteúdo desta aula. "
        f"5) A partir de “{pts[3]}”, produza duas versões: uma que preserve o sentido estudado e outra que altere apenas um componente. Depois identifique exatamente qual alteração tornou a segunda inadequada. "
        f"6) Volte ao recorte oficial “{scope}” e justifique por que todos os quatro núcleos continuam dentro dele. "
        "7) Por fim, registre no caderno de erros qual destes pontos você não conseguiu reconstruir de memória. Na próxima revisão, releia somente o bloco correspondente antes de tentar novamente."
    )
    return [
        {"title":"Núcleos essenciais aprofundados", "body":b1, "layer":PAGE_LAYER},
        {"title":"Relações, contrastes e armadilhas", "body":b2, "layer":PAGE_LAYER},
        {"title":"Recuperação ativa específica da página", "body":b3, "layer":PAGE_LAYER},
    ]


def replace_once(path: Path, old: str, new: str):
    text=path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Não encontrei em {path}: {old}")
    path.write_text(text.replace(old,new,1),encoding="utf-8")


def main():
    syllabus_hash=sha(SYLLABUS_PATH)
    questions_hash=sha(QUESTIONS_PATH)
    lessons=json.loads(LESSONS_PATH.read_text(encoding="utf-8"))
    questions=json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    if len(lessons)!=EXPECTED_TOPICS or len(questions)!=EXPECTED_QUESTIONS:
        raise SystemExit("Contagens-base inesperadas; expansão abortada.")

    before_topic_ids=[x.get("topicId") for x in lessons]
    before_subtopics={x["topicId"]:list(x.get("subtopics") or []) for x in lessons}
    before_page_ids={x["topicId"]:[p.get("id") for p in x.get("studyPages") or []] for x in lessons}

    page_count=0; added=[]; final_sizes=[]; new_bodies=[]
    for lesson in lessons:
        scope=lesson.get("officialScope")
        pages=lesson.get("studyPages") or []
        for idx,page in enumerate(pages):
            page_count+=1
            if page.get("qualityExpansionVersion")==PAGE_LAYER:
                raise SystemExit(f"Página já expandida por {PAGE_LAYER}: {page.get('id')}")
            if page.get("sourceScope")!=scope:
                raise SystemExit(f"Escopo divergente antes da expansão: {page.get('id')}")
            before=len(json.dumps(page,ensure_ascii=False))
            blocks=make_blocks(lesson,page,idx)
            page.setdefault("blocks",[]).extend(blocks)
            page["qualityExpansionVersion"]=PAGE_LAYER
            page["qualityExpansionBasis"]="conteúdo já existente na própria aula/página + officialScope; sem fonte externa adicionada"
            after=len(json.dumps(page,ensure_ascii=False))
            delta=after-before
            if delta < MIN_ADDED_CHARS:
                raise SystemExit(f"Expansão curta em {page.get('id')}: +{delta}")
            added.append(delta); final_sizes.append(after)
            new_bodies.append("\n".join(b["body"] for b in blocks))

        manual_chars=len(json.dumps(pages,ensure_ascii=False))
        lesson["contentCharacters"]=manual_chars
        lesson["depthVersion"]="gcm-depth-1.8.0"
        lesson["subtopicDepth"]="page-level-quality-expansion"
        theory=max(180,int(math.ceil((manual_chars/300)/5)*5))
        practice=max(45,int(lesson.get("practiceMinutes") or 45))
        lesson["theoryMinutes"]=theory
        lesson["practiceMinutes"]=practice
        lesson["estimatedMinutes"]=theory+practice

    if page_count!=EXPECTED_PAGES:
        raise SystemExit(f"Esperava {EXPECTED_PAGES} páginas; encontrei {page_count}")
    if [x.get("topicId") for x in lessons]!=before_topic_ids:
        raise SystemExit("topicIds mudaram")
    if {x["topicId"]:list(x.get("subtopics") or []) for x in lessons}!=before_subtopics:
        raise SystemExit("subtópicos mudaram")
    if {x["topicId"]:[p.get("id") for p in x.get("studyPages") or []] for x in lessons}!=before_page_ids:
        raise SystemExit("pageIds mudaram")

    # Qualidade estrutural: novos textos devem ser específicos, não um corpo idêntico copiado em massa.
    body_hashes=[hashlib.sha256(norm(x).encode()).hexdigest() for x in new_bodies]
    dup=Counter(body_hashes)
    if max(dup.values())>1:
        raise SystemExit(f"Há expansão exatamente duplicada em {max(dup.values())} páginas")
    if min(added)<MIN_ADDED_CHARS:
        raise SystemExit("Alguma página ficou abaixo do aumento mínimo")

    LESSIONS_TEXT=json.dumps(lessons,ensure_ascii=False,indent=2)
    LESSONS_PATH.write_text(LESSIONS_TEXT,encoding="utf-8")

    # Dados oficiais e questões são invariantes desta migração.
    if sha(SYLLABUS_PATH)!=syllabus_hash or sha(QUESTIONS_PATH)!=questions_hash:
        raise SystemExit("Matriz oficial ou banco de questões foi alterado; abortando")

    replace_once(CONFIG_PATH,"export const APP_VERSION = '1.7.0';","export const APP_VERSION = '1.8.0';")
    replace_once(CONFIG_PATH,"version: '2026.09.21.5',","version: '2026.09.21.6',")
    replace_once(CONFIG_PATH,"export const SEED_DATA_VERSION = '2026.09.21.8';","export const SEED_DATA_VERSION = '2026.09.21.9';")
    replace_once(SW_PATH,"const CACHE_VERSION = 'v1.7.0';","const CACHE_VERSION = 'v1.8.0';")

    changelog=CHANGELOG_PATH.read_text(encoding="utf-8")
    entry=(
        "\n## [1.8.0] - 2026-09-21\n\n"
        "### Added\n"
        "- Expansão de qualidade em todas as 3.944 páginas da GCM: núcleos essenciais aprofundados, relações/contrastes/armadilhas e recuperação ativa específica da página.\n"
        "- Validação de aumento mínimo por página, unicidade dos novos blocos e preservação integral dos IDs, subtópicos, matriz oficial e 2.650 questões.\n\n"
    )
    marker="# Changelog\n"
    if marker in changelog and "## [1.8.0]" not in changelog:
        CHANGELOG_PATH.write_text(changelog.replace(marker,marker+entry,1),encoding="utf-8")

    print(json.dumps({
        "version":VERSION,
        "topics":len(lessons),
        "subtopics":sum(len(x.get('subtopics') or []) for x in lessons),
        "pages":page_count,
        "questions":len(questions),
        "minAddedCharsPerPage":min(added),
        "avgAddedCharsPerPage":round(sum(added)/len(added)),
        "maxAddedCharsPerPage":max(added),
        "minFinalPageChars":min(final_sizes),
        "avgFinalPageChars":round(sum(final_sizes)/len(final_sizes)),
        "totalAddedChars":sum(added),
        "exactDuplicateExpansions":sum(v-1 for v in dup.values() if v>1),
        "syllabusSha256":syllabus_hash,
        "questionsSha256":questions_hash,
    },ensure_ascii=False,indent=2))
    print("GCM PAGE DEPTH 1.8.0 OK")

if __name__=="__main__":
    main()
