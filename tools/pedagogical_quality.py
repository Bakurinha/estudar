#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTEST_ID = "gcm-salvador-2026"
Q_PATH = Path("data/questions/gcm-salvador-2026.json")
L_PATH = Path("data/lessons/gcm-salvador-2026.json")
S_PATH = Path("data/syllabus/gcm-salvador-2026.json")

LEGACY_FAMILIES = {
    "scope-recognition",
    "student-note-concept",
    "direct-situation-concept",
    "concept-example-pair",
}

ALLOWED_LEVELS = {"fixacao", "compreensao", "aplicacao", "transferencia"}
ALLOWED_ROLES = {
    "ensinar",
    "exemplo_resolvido",
    "comparar",
    "pratica_guiada",
    "pratica_independente",
    "transferencia",
    "revisao",
    "diagnostico",
}

FORBIDDEN_STEM_PATTERNS = [
    re.compile(r"para\s+n[aã]o\s+sair\s+do\s+conte[uú]do", re.I),
    re.compile(r"recorte\s+oficial\s+do\s+edital", re.I),
]
PLACEHOLDER_PATTERNS = [
    re.compile(r"afirma[cç][aã]o\s+incompat[ií]vel", re.I),
    re.compile(r"alternativa\s+(?:incorreta|errada)\s*\(?\d+\)?", re.I),
]
GENERIC_METHOD_MARKERS = [
    re.compile(r"explique\s+com\s+suas\s+palavras", re.I),
    re.compile(r"para\s+estudar\s+de\s+verdade,?\s+n[aã]o\s+basta\s+decorar", re.I),
    re.compile(r"reconstrua\s+o\s+conte[uú]do", re.I),
    re.compile(r"controle\s+de\s+escopo", re.I),
    re.compile(r"o\s+objetivo\s+n[aã]o\s+[eé]\s+memorizar", re.I),
    re.compile(r"feche\s+(?:o\s+texto|a\s+leitura|todas\s+as\s+p[aá]ginas)", re.I),
    re.compile(r"volte\s+ao\s+(?:material|recorte\s+oficial)", re.I),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def norm(text: Any) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[\"'“”‘’`´]", " ", text)
    text = re.sub(r"[^a-z0-9%+\-*/=<>]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def question_family(stem: str) -> str:
    n = norm(stem)
    if n.startswith("para nao sair do conteudo"):
        return "scope-recognition"
    if n.startswith("um aluno anotou"):
        return "student-note-concept"
    if n.startswith("qual situacao se relaciona mais diretamente"):
        return "direct-situation-concept"
    if n.startswith("qual par conceito exemplo esta correto"):
        return "concept-example-pair"
    if n.startswith("o que significa") or n.startswith("qual e o conceito") or n.startswith("defina"):
        return "direct-definition"
    if re.search(r"\b(?:calcule|valor|percentual|taxa|quantos|quanto|resultado)\b", n):
        return "numeric-application"
    if re.search(r"\b(?:caso|hipotese|situacao|considere|suponha|durante|joao|maria|servidor|agente|candidato)\b", n):
        return "scenario-application"
    if re.search(r"\b(?:compare|diferenca|distinguir|exceto|incorreta|correta)\b", n):
        return "comparison-evaluation"
    tokens = n.split()
    return "other:" + "-".join(tokens[:7])


def cognitive_ops(question: dict[str, Any]) -> list[str]:
    text = norm(question.get("stem", ""))
    ops: list[str] = []
    checks = [
        ("calcular", r"\b(?:calcule|quanto|quantos|valor|percentual|taxa|equacao|resultado)\b"),
        ("comparar", r"\b(?:compare|diferenca|distinguir|mais adequada|menos adequada|exceto)\b"),
        ("interpretar", r"\b(?:texto|trecho|enunciado|sentido|inferir|interpreta|argumento|tese)\b"),
        ("aplicar", r"\b(?:caso|situacao|hipotese|considere|suponha|durante|ocorreu|praticou|realizou)\b"),
        ("explicar", r"\b(?:por que|justifique|explique|razao)\b"),
        ("avaliar", r"\b(?:correta|incorreta|adequada|inadequada|verdadeira|falsa)\b"),
        ("identificar", r"\b(?:qual conceito|qual opcao|qual alternativa|identifique|relaciona)\b"),
    ]
    for name, pattern in checks:
        if re.search(pattern, text):
            ops.append(name)
    if not ops:
        ops.append("recuperar")
    return ops


def cognitive_level(question: dict[str, Any]) -> str:
    family = question_family(question.get("stem", ""))
    ops = cognitive_ops(question)
    stem_len = len(norm(question.get("stem", "")).split())
    if family in LEGACY_FAMILIES or family == "direct-definition":
        return "fixacao"
    if "aplicar" in ops or "calcular" in ops:
        if len(set(ops)) >= 2 and stem_len >= 35:
            return "transferencia"
        return "aplicacao"
    if "interpretar" in ops and ("comparar" in ops or "avaliar" in ops):
        return "transferencia"
    if any(op in ops for op in ("comparar", "interpretar", "explicar", "avaliar")):
        return "compreensao"
    return "fixacao"


def legacy_flags(question: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    stem = str(question.get("stem") or "")
    options = [str(x or "") for x in question.get("options") or []]
    if any(p.search(stem) for p in FORBIDDEN_STEM_PATTERNS):
        flags.append("metalinguagem-edital-no-enunciado")
    if any(p.search(option) for p in PLACEHOLDER_PATTERNS for option in options):
        flags.append("alternativa-placeholder")
    level = cognitive_level(question)
    if question.get("difficulty") == "hard" and level == "fixacao":
        flags.append("hard-apenas-reconhecimento")
    if question_family(stem) in LEGACY_FAMILIES:
        flags.append("familia-repetitiva-legada")
    return flags


def classify_question(question: dict[str, Any]) -> dict[str, Any]:
    topic_ids = question.get("topicIds") or []
    return {
        "subjectId": question.get("subjectId"),
        "topicId": topic_ids[0] if topic_ids else None,
        "difficulty": question.get("difficulty"),
        "templateFamily": question_family(question.get("stem", "")),
        "cognitiveLevel": cognitive_level(question),
        "cognitiveOps": cognitive_ops(question),
        "legacyFlags": legacy_flags(question),
    }


def flatten_pages(lessons: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    pages: dict[str, dict[str, Any]] = {}
    for lesson in lessons:
        topic_id = lesson.get("topicId")
        for index, page in enumerate(lesson.get("studyPages") or []):
            page_id = page.get("id") or f"{topic_id}-page-{index+1:03d}"
            pages[page_id] = {"topicId": topic_id, **page}
    return pages


def block_body(block: dict[str, Any]) -> str:
    parts = [str(block.get("body") or "")]
    parts.extend(str(x or "") for x in (block.get("items") or []))
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def is_generic_method_text(text: str) -> bool:
    return sum(bool(p.search(text)) for p in GENERIC_METHOD_MARKERS) >= 2


def question_metrics(questions: list[dict[str, Any]]) -> dict[str, Any]:
    stems = Counter(norm(q.get("stem", "")) for q in questions)
    families = Counter(question_family(q.get("stem", "")) for q in questions)
    levels = Counter(cognitive_level(q) for q in questions)
    flags = Counter(flag for q in questions for flag in legacy_flags(q))
    exact_dup_excess = sum(max(0, count - 1) for key, count in stems.items() if key)
    return {
        "total": len(questions),
        "exactStemDuplicateExcess": exact_dup_excess,
        "templateFamilies": dict(families.most_common()),
        "cognitiveLevels": dict(levels),
        "legacyFlags": dict(flags),
        "largestFamilyShare": (max(families.values()) / len(questions)) if questions else 0.0,
    }


def lesson_metrics(lessons: list[dict[str, Any]]) -> dict[str, Any]:
    pages = flatten_pages(lessons)
    body_counts: Counter[str] = Counter()
    total_chars = 0
    generic_chars = 0
    for page in pages.values():
        for block in page.get("blocks") or []:
            body = block_body(block)
            if not body:
                continue
            total_chars += len(body)
            if is_generic_method_text(body):
                generic_chars += len(body)
            if len(body) >= 120:
                body_counts[norm(body)] += 1
    duplicate_excess = sum(max(0, c - 1) for key, c in body_counts.items() if key)
    return {
        "lessons": len(lessons),
        "pages": len(pages),
        "duplicateBlockExcess": duplicate_excess,
        "genericMethodChars": generic_chars,
        "totalBlockChars": total_chars,
        "genericMethodRatio": generic_chars / total_chars if total_chars else 0.0,
    }


def load_from_git(ref: str, path: Path) -> Any | None:
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{ref}:{path.as_posix()}"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return json.loads(raw.decode("utf-8"))


def changed_questions(current: list[dict[str, Any]], previous: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if previous is None:
        return []
    before = {q.get("id"): canonical(q) for q in previous if q.get("id")}
    return [q for q in current if q.get("id") not in before or before[q.get("id")] != canonical(q)]


def changed_pages(current_lessons: list[dict[str, Any]], previous_lessons: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if previous_lessons is None:
        return []
    before = {pid: canonical(page) for pid, page in flatten_pages(previous_lessons).items()}
    current = flatten_pages(current_lessons)
    return [page for pid, page in current.items() if pid not in before or before[pid] != canonical(page)]


def near_duplicate_pairs_for_changed(
    changed: list[dict[str, Any]],
    all_questions: list[dict[str, Any]],
    threshold: float,
) -> list[tuple[str, str, float]]:
    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for q in all_questions:
        topic = (q.get("topicIds") or [None])[0]
        by_topic[str(topic)].append(q)
        by_family[question_family(q.get("stem", ""))].append(q)

    pairs: list[tuple[str, str, float]] = []
    seen: set[tuple[str, str]] = set()
    for q in changed:
        qid = str(q.get("id"))
        topic = str((q.get("topicIds") or [None])[0])
        family = question_family(q.get("stem", ""))
        candidates = by_topic.get(topic, []) + by_family.get(family, [])
        a = norm(q.get("stem", ""))
        for other in candidates:
            oid = str(other.get("id"))
            if not oid or oid == qid:
                continue
            key = tuple(sorted((qid, oid)))
            if key in seen:
                continue
            seen.add(key)
            b = norm(other.get("stem", ""))
            if not a or not b:
                continue
            at = set(a.split())
            bt = set(b.split())
            overlap = len(at & bt) / max(1, min(len(at), len(bt)))
            if overlap < 0.65:
                continue
            score = SequenceMatcher(None, a, b).ratio()
            if score >= threshold:
                pairs.append((qid, oid, score))
    return sorted(pairs, key=lambda x: x[2], reverse=True)


def strict_question_errors(
    changed: list[dict[str, Any]],
    all_questions: list[dict[str, Any]],
    near_dup_threshold: float = 0.90,
) -> list[str]:
    errors: list[str] = []
    for q in changed:
        qid = q.get("id")
        stem = str(q.get("stem") or "")
        if any(p.search(stem) for p in FORBIDDEN_STEM_PATTERNS):
            errors.append(f"{qid}: enunciado metalinguístico sobre o edital/recorte é proibido em conteúdo novo ou alterado")
        options = [str(x or "") for x in q.get("options") or []]
        if any(p.search(option) for p in PLACEHOLDER_PATTERNS for option in options):
            errors.append(f"{qid}: alternativa-placeholder é proibida")
        pedagogy = q.get("pedagogy") or {}
        required = {"templateFamily", "cognitiveLevel", "cognitiveOps", "skillTarget", "errorTarget"}
        missing = sorted(field for field in required if not pedagogy.get(field))
        if missing:
            errors.append(f"{qid}: metadados pedagógicos obrigatórios ausentes: {', '.join(missing)}")
            continue
        if pedagogy.get("cognitiveLevel") not in ALLOWED_LEVELS:
            errors.append(f"{qid}: cognitiveLevel inválido: {pedagogy.get('cognitiveLevel')}")
        ops = pedagogy.get("cognitiveOps") or []
        if not isinstance(ops, list):
            errors.append(f"{qid}: cognitiveOps deve ser lista")
            ops = []
        if q.get("difficulty") == "hard" and (
            pedagogy.get("cognitiveLevel") not in {"aplicacao", "transferencia"} or len(set(ops)) < 2
        ):
            errors.append(f"{qid}: questão hard precisa exigir aplicação/transferência e pelo menos duas operações cognitivas")

    for a, b, score in near_duplicate_pairs_for_changed(changed, all_questions, near_dup_threshold):
        errors.append(f"near-duplicate: {a} ~ {b} ({score:.1%})")
    return errors


def strict_page_errors(
    changed: list[dict[str, Any]],
    previous_lessons: list[dict[str, Any]] | None,
    all_current_lessons: list[dict[str, Any]],
    max_generic_ratio: float = 0.15,
) -> list[str]:
    if previous_lessons is None:
        return []
    prev_pages = flatten_pages(previous_lessons)
    current_pages = flatten_pages(all_current_lessons)

    global_bodies: Counter[str] = Counter()
    for page in current_pages.values():
        for block in page.get("blocks") or []:
            text = block_body(block)
            if len(text) >= 120:
                global_bodies[norm(text)] += 1

    errors: list[str] = []
    for page in changed:
        pid = str(page.get("id") or "sem-id")
        old = prev_pages.get(pid)
        if old is None:
            role = page.get("pedagogicalRole")
            if role not in ALLOWED_ROLES:
                errors.append(f"{pid}: página nova precisa de pedagogicalRole válido")

        old_bodies = {norm(block_body(b)) for b in (old or {}).get("blocks") or []}
        delta_blocks = []
        for block in page.get("blocks") or []:
            text = block_body(block)
            key = norm(text)
            if key and key not in old_bodies:
                delta_blocks.append((block, text, key))

        if not delta_blocks:
            continue
        delta_chars = sum(len(text) for _, text, _ in delta_blocks)
        generic_chars = sum(len(text) for _, text, _ in delta_blocks if is_generic_method_text(text))
        if delta_chars and generic_chars / delta_chars > max_generic_ratio:
            errors.append(
                f"{pid}: conteúdo novo/alterado tem {generic_chars/delta_chars:.1%} de metodologia genérica; limite={max_generic_ratio:.0%}"
            )
        for block, text, key in delta_blocks:
            if len(text) >= 120 and global_bodies[key] > 1 and not block.get("revisitOf"):
                errors.append(f"{pid}: bloco novo/alterado duplica literalmente outro bloco e não declara revisitOf")
            if len(text) >= 120 and not block.get("learningGain"):
                errors.append(f"{pid}: bloco novo/alterado precisa declarar learningGain")
    return errors


def ratchet_errors(current: dict[str, Any], previous: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    cq, pq = current["questions"], previous["questions"]
    cl, pl = current["lessons"], previous["lessons"]

    scalar_q = ["exactStemDuplicateExcess", "largestFamilyShare"]
    for field in scalar_q:
        if cq[field] > pq[field] + (1e-9 if isinstance(cq[field], float) else 0):
            errors.append(f"catraca: questions.{field} piorou de {pq[field]} para {cq[field]}")

    for flag, count in cq["legacyFlags"].items():
        if count > pq["legacyFlags"].get(flag, 0):
            errors.append(f"catraca: dívida '{flag}' aumentou de {pq['legacyFlags'].get(flag,0)} para {count}")

    for family in LEGACY_FAMILIES:
        current_count = cq["templateFamilies"].get(family, 0)
        previous_count = pq["templateFamilies"].get(family, 0)
        if current_count > previous_count:
            errors.append(f"catraca: família legada '{family}' aumentou de {previous_count} para {current_count}")

    if cl["duplicateBlockExcess"] > pl["duplicateBlockExcess"]:
        errors.append(
            f"catraca: blocos literalmente duplicados aumentaram de {pl['duplicateBlockExcess']} para {cl['duplicateBlockExcess']}"
        )
    if cl["genericMethodRatio"] > pl["genericMethodRatio"] + 0.001:
        errors.append(
            f"catraca: proporção de metodologia genérica aumentou de {pl['genericMethodRatio']:.2%} para {cl['genericMethodRatio']:.2%}"
        )
    return errors


def snapshot(questions: list[dict[str, Any]], lessons: list[dict[str, Any]]) -> dict[str, Any]:
    return {"questions": question_metrics(questions), "lessons": lesson_metrics(lessons)}
