#!/usr/bin/env python3
"""Sanitiza alternativas do banco final preservando o gabarito correto.

A rotina é aplicada inclusive às questões antigas do seed. Ela remove alternativas
que se tornam idênticas após normalização de caixa/acentos/espaços e completa o
item com distratores neutros únicos somente quando necessário.
"""
from __future__ import annotations

import json
import random
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "questions" / "gcm-salvador-2026.json"
RNG = random.Random(20260921_120)


def norm(text: str) -> str:
    value = unicodedata.normalize("NFKD", str(text))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"\s+", " ", value.lower()).strip(" .;,:-")
    return value


questions = json.loads(PATH.read_text(encoding="utf-8"))
repaired = 0

for q in questions:
    options = list(q.get("options") or [])
    answer = q.get("answerIndex")
    if len(options) != 5 or not isinstance(answer, int) or not 0 <= answer < len(options):
        continue

    correct = options[answer]
    if len({norm(option) for option in options}) == 5:
        continue

    new_options = [correct]
    seen = {norm(correct)}
    for option in options:
        key = norm(option)
        if not key or key in seen:
            continue
        seen.add(key)
        new_options.append(option)

    filler_no = 1
    while len(new_options) < 5:
        filler = f"Alternativa incompatível com o conteúdo desta questão ({filler_no})"
        filler_no += 1
        key = norm(filler)
        if key in seen:
            continue
        seen.add(key)
        new_options.append(filler)

    new_options = new_options[:5]
    RNG.shuffle(new_options)
    q["options"] = new_options
    q["answerIndex"] = new_options.index(correct)
    q.setdefault("tags", []).append("alternativas-sanitizadas")
    repaired += 1

PATH.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Questões com alternativas sanitizadas: {repaired}")
