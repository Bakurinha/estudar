#!/usr/bin/env python3
"""Validação rígida da base expandida de aulas e questões."""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CONTEST_ID = "gcm-salvador-2026"

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


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text.lower()).strip()
    return text


def fail(message: str) -> None:
    raise SystemExit(f"ERRO: {message}")


syllabus = load(DATA / "syllabus" / f"{CONTEST_ID}.json")
lessons = load(DATA / "lessons" / f"{CONTEST_ID}.json")
questions = load(DATA / "questions" / f"{CONTEST_ID}.json")

subjects = {subject["id"]: subject for subject in syllabus["subjects"]}
topics = {
    topic["id"]: (subject["id"], topic)
    for subject in syllabus["subjects"]
    for topic in subject["topics"]
}

if len(topics) != 116:
    fail(f"a matriz deveria conter 116 tópicos; encontrou {len(topics)}")

lesson_by_topic = {lesson["topicId"]: lesson for lesson in lessons}
missing_lessons = sorted(set(topics) - set(lesson_by_topic))
if missing_lessons:
    fail(f"tópicos sem aula: {missing_lessons}")

required_sections = {
    "Como usar esta aula",
    "Objetivo da aula",
    "Fundamentos explicados passo a passo",
    "Aprofundamento específico do tópico",
    "Método de resolução",
    "Exemplos comentados",
    "Diferenças que a banca pode explorar",
    "Conteúdo técnico para memorizar depois de compreender",
    "Checklist antes de fazer exercícios",
    "Prática obrigatória",
    "Mapa exato do edital",
}

for topic_id, lesson in lesson_by_topic.items():
    if topic_id not in topics:
        fail(f"aula aponta para tópico inexistente: {topic_id}")
    sections = lesson.get("sections", [])
    titles = {section.get("title") for section in sections}
    if not required_sections.issubset(titles):
        missing = sorted(required_sections - titles)
        fail(f"aula {topic_id} não recebeu todos os blocos aprofundados: {missing}")
    if lesson.get("depth") != "concurso-aprofundado-v4":
        fail(f"aula {topic_id} não está marcada como profundidade V4")
    if int(lesson.get("estimatedMinutes") or 0) < 80:
        fail(f"aula {topic_id} tem tempo planejado curto demais: {lesson.get('estimatedMinutes')}")
    if int(lesson.get("theoryMinutes") or 0) < 55:
        fail(f"aula {topic_id} tem teoria curta demais: {lesson.get('theoryMinutes')}")
    if len(sections) < 11:
        fail(f"aula {topic_id} possui poucas seções para o padrão aprofundado")

    specific = next((s for s in sections if s.get("title") == "Aprofundamento específico do tópico"), None)
    items = specific.get("items", []) if specific else []
    if len(items) < 4:
        fail(f"aula {topic_id} precisa de ao menos quatro pontos de aprofundamento específico")
    if any(len(str(item).strip()) < 45 for item in items):
        fail(f"aula {topic_id} possui aprofundamento específico curto demais")

ids: set[str] = set()
stems: set[str] = set()
coverage = Counter()
subject_count = Counter()
answers = Counter()
difficulty = Counter()

for q in questions:
    qid = q.get("id")
    if not qid or qid in ids:
        fail(f"ID ausente ou duplicado: {qid}")
    ids.add(qid)

    stem = norm(q.get("stem", ""))
    if len(stem) < 10:
        fail(f"enunciado curto demais em {qid}")
    if stem in stems:
        fail(f"enunciado duplicado em {qid}: {q.get('stem')}")
    stems.add(stem)

    options = q.get("options", [])
    if len(options) != 5:
        fail(f"{qid} deve ter exatamente cinco alternativas")
    if len({norm(str(option)) for option in options}) != 5:
        fail(f"{qid} possui alternativas duplicadas")

    answer = q.get("answerIndex")
    if not isinstance(answer, int) or not 0 <= answer < 5:
        fail(f"gabarito inválido em {qid}: {answer}")

    topic_ids = q.get("topicIds") or []
    if len(topic_ids) != 1:
        fail(f"{qid} deve ter um tópico primário explícito")
    topic_id = topic_ids[0]
    if topic_id not in topics:
        fail(f"{qid} aponta para tópico inexistente: {topic_id}")

    expected_subject = topics[topic_id][0]
    if q.get("subjectId") != expected_subject:
        fail(
            f"{qid}: tópico {topic_id} pertence a {expected_subject}, "
            f"mas questão está em {q.get('subjectId')}"
        )

    if not q.get("explanation"):
        fail(f"{qid} não possui explicação")
    if q.get("sourceType") != "authorial":
        fail(f"{qid} não está explicitamente identificado como autoral")

    coverage[topic_id] += 1
    subject_count[expected_subject] += 1
    answers[answer] += 1
    difficulty[q.get("difficulty", "unknown")] += 1

for subject_id, subject in subjects.items():
    target = TARGETS[subject_id]
    for topic in subject["topics"]:
        count = coverage[topic["id"]]
        if count < target:
            fail(f"{topic['id']} tem {count} questões; mínimo exigido={target}")

total = len(questions)
for index in range(5):
    ratio = answers[index] / total
    if ratio > 0.30:
        fail(f"gabarito armazenado excessivamente concentrado na posição {index}: {ratio:.1%}")

if total < 2650:
    fail(f"banco deveria ter ao menos 2.650 questões; encontrou {total}")

print("VALIDAÇÃO V4 OK")
print(f"Tópicos: {len(topics)}")
print(f"Aulas: {len(lessons)}")
print(f"Questões: {total}")
print("Questões por matéria:")
for subject_id, subject in subjects.items():
    print(f"  - {subject['name']}: {subject_count[subject_id]}")
print("Distribuição do gabarito armazenado A-E:")
for index, letter in enumerate("ABCDE"):
    print(f"  - {letter}: {answers[index]} ({answers[index]/total:.1%})")
print("Dificuldade:", dict(difficulty))
