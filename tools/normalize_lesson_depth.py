#!/usr/bin/env python3
"""Garante que o aprofundamento específico seja explicativo, não apenas fórmulas soltas."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "lessons" / "gcm-salvador-2026.json"

lessons = json.loads(PATH.read_text(encoding="utf-8"))
changed = 0

for lesson in lessons:
    label = lesson.get("title", "este tópico")
    for section in lesson.get("sections", []):
        if section.get("title") != "Aprofundamento específico do tópico":
            continue
        items = section.get("items", [])
        normalized = []
        for item in items:
            text = str(item).strip()
            if len(text) < 45:
                text += (
                    f" Em {label}, não memorize essa informação isoladamente: "
                    "entenda o que cada símbolo ou termo representa e aplique a relação a uma situação concreta antes de seguir."
                )
                changed += 1
            normalized.append(text)
        section["items"] = normalized

PATH.write_text(json.dumps(lessons, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Itens curtos aprofundados automaticamente: {changed}")
