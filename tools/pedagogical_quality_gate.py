#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pedagogical_quality import (
    L_PATH,
    Q_PATH,
    ROOT,
    changed_pages,
    changed_questions,
    load_from_git,
    load_json,
    ratchet_errors,
    snapshot,
    strict_page_errors,
    strict_question_errors,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", default="HEAD^", help="ref Git usada como estado aprovado anterior")
    parser.add_argument("--report", default=None, help="arquivo JSON opcional para relatório")
    args = parser.parse_args()

    current_q = load_json(ROOT / Q_PATH)
    current_l = load_json(ROOT / L_PATH)
    previous_q = load_from_git(args.reference, Q_PATH)
    previous_l = load_from_git(args.reference, L_PATH)

    current = snapshot(current_q, current_l)
    previous = snapshot(previous_q, previous_l) if previous_q is not None and previous_l is not None else None

    changed_q = changed_questions(current_q, previous_q)
    changed_p = changed_pages(current_l, previous_l)

    errors: list[str] = []
    if previous is not None:
        errors.extend(ratchet_errors(current, previous))

    errors.extend(strict_question_errors(changed_q, current_q, near_dup_threshold=0.90))
    errors.extend(strict_page_errors(changed_p, previous_l, current_l, max_generic_ratio=0.15))

    report = {
        "reference": args.reference,
        "current": current,
        "previous": previous,
        "changedQuestions": len(changed_q),
        "changedPages": len(changed_p),
        "errors": errors,
    }
    if args.report:
        path = Path(args.report)
        if not path.is_absolute():
            path = ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("QUALITY GATE PEDAGÓGICO V2")
    print(f"reference={args.reference} changed_questions={len(changed_q)} changed_pages={len(changed_p)}")
    print(
        "questions:",
        f"total={current['questions']['total']}",
        f"dup_stems={current['questions']['exactStemDuplicateExcess']}",
        f"largest_family={current['questions']['largestFamilyShare']:.1%}",
        f"flags={current['questions']['legacyFlags']}",
    )
    print(
        "lessons:",
        f"pages={current['lessons']['pages']}",
        f"duplicate_blocks={current['lessons']['duplicateBlockExcess']}",
        f"generic_ratio={current['lessons']['genericMethodRatio']:.1%}",
    )

    if errors:
        print("\nBLOQUEADO:")
        for error in errors[:100]:
            print(" -", error)
        if len(errors) > 100:
            print(f" ... e mais {len(errors)-100} erro(s)")
        raise SystemExit(1)

    print("QUALITY GATE PEDAGÓGICO V2 OK")


if __name__ == "__main__":
    main()
