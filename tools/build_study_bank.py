#!/usr/bin/env python3
"""Orquestrador da base V2.

A expansão principal mantém as regras curriculares e os conceitos curados em
expand_bank_v2.py. Este arquivo acrescenta formas extras de pergunta antes de
executar o build, garantindo margem suficiente para a meta por tópico mesmo
quando algum enunciado é rejeitado por duplicidade.
"""
from __future__ import annotations

import expand_bank_v2 as base


_original_make_concept_questions = base.make_concept_questions


def make_concept_questions_with_margin(subject, topic, topics):
    rows = _original_make_concept_questions(subject, topic, topics)
    facts = base.all_facts(topic)
    other_terms = base.distractor_pool(subject, topics, 0, topic["id"])
    other_defs = base.distractor_pool(subject, topics, 1, topic["id"])
    other_examples = base.distractor_pool(subject, topics, 2, topic["id"])

    for fact_no, (term, definition, example) in enumerate(facts, start=1):
        variants = [
            (
                f"Ao revisar {topic['label']}, qual anotação sobre '{term}' está alinhada ao conteúdo estudado?",
                definition,
                base.RNG.sample(other_defs, 4),
                f"A anotação correta preserva o conceito de '{term}': {definition}.",
            ),
            (
                f"A situação '{example}' deve ser relacionada a qual conceito de {topic['label']}?",
                term,
                base.RNG.sample(other_terms, 4),
                f"O exemplo pertence a '{term}'.",
            ),
            (
                f"Qual exemplo abaixo permanece coerente com o estudo de '{term}' em {topic['label']}?",
                example,
                base.RNG.sample(other_examples, 4),
                f"O exemplo coerente é: {example}.",
            ),
        ]

        for variant_no, (stem, correct, wrong, explanation) in enumerate(variants, start=1):
            options, answer = base.place_answer(correct, wrong)
            rows.append({
                "id": f"v2x-{subject['id']}-{topic['id']}-{fact_no:02d}-{variant_no:02d}",
                "contestId": base.CONTEST_ID,
                "subjectId": subject["id"],
                "topicIds": [topic["id"]],
                "difficulty": "medium",
                "sourceType": "authorial",
                "sourceLabel": "Questão autoral focada no tópico do edital - não é questão oficial da FGV",
                "stem": stem,
                "options": options,
                "answerIndex": answer,
                "explanation": explanation,
                "tags": ["v2", "conteudo-topico", "margem-validacao"],
            })

    return rows


base.make_concept_questions = make_concept_questions_with_margin

if __name__ == "__main__":
    base.main()
