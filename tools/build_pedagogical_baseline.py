#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict

from pedagogical_quality import CONTEST_ID, ROOT, Q_PATH, L_PATH, classify_question, load_json, snapshot

PILOT_TOPICS = [
    "interpretacao-argumentativa",
    "porcentagem-proporcao",
    "penal-ilicitude",
    "leg-guardas",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="grava baseline, classificação e relatório")
    args = parser.parse_args()

    questions = load_json(ROOT / Q_PATH)
    lessons = load_json(ROOT / L_PATH)
    snap = snapshot(questions, lessons)

    classifications = {}
    pilot = defaultdict(lambda: {"total": 0, "difficulty": Counter(), "levels": Counter(), "families": Counter(), "flags": Counter()})

    for q in questions:
        qid = q.get("id")
        if not qid:
            continue
        c = classify_question(q)
        classifications[qid] = c
        topic_id = c.get("topicId")
        if topic_id in PILOT_TOPICS:
            p = pilot[topic_id]
            p["total"] += 1
            p["difficulty"][c.get("difficulty") or "unknown"] += 1
            p["levels"][c["cognitiveLevel"]] += 1
            p["families"][c["templateFamily"]] += 1
            for flag in c["legacyFlags"]:
                p["flags"][flag] += 1

    pilot_json = {
        topic: {
            "total": item["total"],
            "difficulty": dict(item["difficulty"]),
            "cognitiveLevels": dict(item["levels"]),
            "templateFamilies": dict(item["families"].most_common()),
            "legacyFlags": dict(item["flags"]),
        }
        for topic, item in pilot.items()
    }

    baseline = {
        "schemaVersion": 1,
        "contestId": CONTEST_ID,
        "purpose": "linha de base anterior ao Quality Gate Pedagógico V2; dívida legada pode diminuir, nunca aumentar",
        **snap,
        "pilotTopics": pilot_json,
    }

    print(json.dumps(baseline, ensure_ascii=False, indent=2))
    if not args.write:
        return

    quality_dir = ROOT / "quality" / "reports"
    data_quality_dir = ROOT / "data" / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    data_quality_dir.mkdir(parents=True, exist_ok=True)

    (quality_dir / "pedagogical-baseline-gcm.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (data_quality_dir / "gcm-question-classification.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "contestId": CONTEST_ID,
                "note": "Classificação heurística inicial. Serve para auditoria e seleção do piloto; não substitui revisão humana da questão.",
                "questions": classifications,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Linha de base pedagógica — GCM Salvador 2026",
        "",
        "Esta linha de base registra a dívida legada antes da reforma pedagógica. O Quality Gate V2 usa uma **catraca**: métricas ruins podem cair, mas não podem voltar a subir.",
        "",
        f"- Questões: **{snap['questions']['total']}**",
        f"- Páginas: **{snap['lessons']['pages']}**",
        f"- Duplicação literal de enunciados (excesso): **{snap['questions']['exactStemDuplicateExcess']}**",
        f"- Maior família de template: **{snap['questions']['largestFamilyShare']:.1%}**",
        f"- Metodologia genérica nos blocos: **{snap['lessons']['genericMethodRatio']:.1%}** dos caracteres de blocos",
        "",
        "## Classificação cognitiva inicial",
    ]
    for level, count in snap["questions"]["cognitiveLevels"].items():
        lines.append(f"- {level}: {count}")
    lines += ["", "## Dívidas detectadas"]
    for flag, count in snap["questions"]["legacyFlags"].items():
        lines.append(f"- {flag}: {count}")
    lines += ["", "## Piloto"]
    for topic in PILOT_TOPICS:
        p = pilot_json.get(topic, {"total": 0, "cognitiveLevels": {}, "legacyFlags": {}})
        lines.append(f"- **{topic}**: {p['total']} questões · níveis {p['cognitiveLevels']} · flags {p['legacyFlags']}")
    lines.append("")
    (quality_dir / "pedagogical-baseline-gcm.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
