#!/usr/bin/env python3
"""Valida se todas as páginas podem alimentar o modo Aprender sem inventar conteúdo."""
from pathlib import Path
import base64
import gzip
import json
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]

CONTROL_TITLES = re.compile(
    r"recorte oficial|como usar|verifica[cç][aã]o conceitual|controle de escopo|regra de fidelidade|limite do conte[uú]do|fechamento",
    re.I,
)
GENERIC = re.compile(
    r"esta p[aá]gina desenvolve somente|o edital exige exatamente|todo o cap[ií]tulo abaixo|"
    r"o limite [eé] o recorte literal|reconstrua o conte[uú]do desta p[aá]gina|controle de escopo|"
    r"explique com suas palavras por que esta p[aá]gina|para estudar de verdade, n[aã]o basta decorar|"
    r"o objetivo deste cap[ií]tulo [eé] dominar|resolva primeiro quest[oõ]es apenas deste t[oó]pico",
    re.I,
)
PRACTICE = re.compile(r"treino|quest[oõ]es|exerc[ií]cios|pr[aá]tica|atividade|desafio", re.I)


def sentences(text):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text:
        return []
    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+|\s*;\s*", text)
        if 45 <= len(part.strip()) <= 520
    ]


def block_text(block):
    parts = [str(block.get("body") or "")]
    parts.extend(str(item or "") for item in (block.get("items") or []))
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def page_claims(page, lesson):
    claims = []
    blocks = page.get("blocks") or []
    preferred = []
    for block in blocks:
        body = block_text(block)
        title = str(block.get("title") or "")
        if len(body) >= 120 and not CONTROL_TITLES.search(title) and not GENERIC.search(body):
            preferred.append(body)
    if not preferred:
        preferred = [block_text(b) for b in blocks if len(block_text(b)) >= 80]
    for body in preferred:
        for sentence in sentences(body):
            if not GENERIC.search(sentence):
                claims.append(sentence)
    if not claims:
        for fallback in (page.get("editalBasis"), page.get("sourceScope"), lesson.get("officialScope")):
            claims.extend(sentences(fallback))
    unique = []
    seen = set()
    for claim in claims:
        key = re.sub(r"\W+", " ", claim.lower()).strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(claim)
    return unique


def practice_items(page):
    results = []
    for block in page.get("blocks") or []:
        title = str(block.get("title") or "")
        for item in block.get("items") or []:
            clean = re.sub(r"\s+", " ", str(item or "")).strip()
            if len(clean) >= 12:
                results.append(clean)
        if PRACTICE.search(title):
            body = re.sub(r"\s+", " ", str(block.get("body") or "")).strip()
            if len(body) >= 20:
                results.append(body)
    return results


def is_practice(page):
    return bool(PRACTICE.search(f"{page.get('title','')} {page.get('kind','')}"))


def load_gcm():
    return json.loads((ROOT / "data/lessons/gcm-salvador-2026.json").read_text(encoding="utf-8"))


def load_packed(course_id):
    parts = sorted((ROOT / "data/packages").glob(f"{course_id}.part-*.b64"))
    if not parts:
        raise SystemExit(f"Pacote não encontrado: {course_id}")
    encoded = "".join(p.read_text(encoding="utf-8") for p in parts)
    encoded = re.sub(r"\s+", "", encoded)
    raw = base64.b64decode(encoded)
    data = json.loads(gzip.decompress(raw).decode("utf-8"))
    return data["lessons"]


def audit(course_id, lessons):
    pages = []
    missing = []
    claim_counts = []
    char_counts = []
    practice_count = 0
    practice_with_items = 0

    for lesson in lessons:
        for page in lesson.get("studyPages") or []:
            pages.append(page)
            claims = page_claims(page, lesson)
            claim_counts.append(len(claims))
            chars = sum(len(block_text(block)) for block in page.get("blocks") or [])
            char_counts.append(chars)

            practice = is_practice(page)
            exercises = practice_items(page) if practice else []
            if practice:
                practice_count += 1
                if exercises:
                    practice_with_items += 1

            # Página teórica precisa de afirmação recuperável. Página prática pode
            # ser validada pelos próprios exercícios, sem inventar uma resposta.
            if not claims and not (practice and exercises):
                missing.append((
                    lesson.get("topicId"),
                    page.get("id"),
                    page.get("title"),
                    len(exercises),
                ))

    if not pages:
        raise SystemExit(f"{course_id}: nenhuma página encontrada")
    if missing:
        sample = "\n".join(map(str, missing[:20]))
        raise SystemExit(f"{course_id}: {len(missing)} páginas sem base recuperável\n{sample}")

    print(
        f"{course_id}: lessons={len(lessons)} pages={len(pages)} "
        f"practice_pages={practice_count} practice_with_items={practice_with_items} "
        f"min_claims={min(claim_counts)} median_claims={statistics.median(claim_counts)} "
        f"avg_claims={statistics.mean(claim_counts):.1f} "
        f"min_chars={min(char_counts)} avg_chars={statistics.mean(char_counts):.0f}"
    )
    return len(pages)


def main():
    totals = {
        "gcm-salvador-2026": audit("gcm-salvador-2026", load_gcm()),
        "paradigmas-python": audit("paradigmas-python", load_packed("paradigmas-python")),
        "matematica-logica": audit("matematica-logica", load_packed("matematica-logica")),
    }
    print("LEARNING METHOD GROUNDING OK", totals, "total_pages=", sum(totals.values()))


if __name__ == "__main__":
    main()
