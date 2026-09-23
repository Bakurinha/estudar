#!/usr/bin/env python3
"""Catraca estrutural: impede perda silenciosa de cobertura durante regenerações."""
from __future__ import annotations

import argparse
from pedagogical_quality import L_PATH, Q_PATH, ROOT, load_from_git, load_json, snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", default="HEAD^", help="ref Git do estado aprovado anterior")
    parser.add_argument("--max-page-drop", type=float, default=0.05)
    args = parser.parse_args()

    current_q = load_json(ROOT / Q_PATH)
    current_l = load_json(ROOT / L_PATH)
    previous_q = load_from_git(args.reference, Q_PATH)
    previous_l = load_from_git(args.reference, L_PATH)
    if previous_q is None or previous_l is None:
        print("PRESERVATION GATE: referência sem dados comparáveis; nada a bloquear")
        return

    current = snapshot(current_q, current_l)
    previous = snapshot(previous_q, previous_l)
    cq, pq = current["questions"], previous["questions"]
    cl, pl = current["lessons"], previous["lessons"]

    errors = []
    if cq["total"] < pq["total"]:
        errors.append(f"questões reduziram de {pq['total']} para {cq['total']}")

    min_pages = int(pl["pages"] * (1 - args.max_page_drop))
    if cl["pages"] < min_pages:
        errors.append(
            f"páginas reduziram de {pl['pages']} para {cl['pages']} "
            f"(queda máxima automática permitida={args.max_page_drop:.0%})"
        )

    if errors:
        print("PEDAGOGICAL PRESERVATION GATE BLOQUEADO")
        for error in errors:
            print(" -", error)
        print("Uma redução maior só pode ocorrer por migração deliberada e revisada, alterando explicitamente esta política.")
        raise SystemExit(1)

    print(
        "PEDAGOGICAL PRESERVATION GATE OK",
        f"questions={pq['total']}->{cq['total']}",
        f"pages={pl['pages']}->{cl['pages']}",
    )


if __name__ == "__main__":
    main()
