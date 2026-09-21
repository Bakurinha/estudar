#!/usr/bin/env python3
"""Valida consistência básica do pacote antes da publicação."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
contest='gcm-salvador-2026'
syllabus=json.loads((ROOT/'data/syllabus'/f'{contest}.json').read_text(encoding='utf-8'))
questions=json.loads((ROOT/'data/questions'/f'{contest}.json').read_text(encoding='utf-8'))
lessons=json.loads((ROOT/'data/lessons'/f'{contest}.json').read_text(encoding='utf-8'))

topic_to_subject={t['id']:s['id'] for s in syllabus['subjects'] for t in s['topics']}
errors=[]
ids=set(); stems=set();
for q in questions:
    if q['id'] in ids: errors.append(f'ID duplicado: {q["id"]}')
    ids.add(q['id'])
    norm=' '.join(q['stem'].lower().split())
    if norm in stems: errors.append(f'Enunciado duplicado: {q["stem"][:70]}')
    stems.add(norm)
    if not 0 <= q['answerIndex'] < len(q['options']): errors.append(f'Gabarito inválido: {q["id"]}')
    if len(q['options']) != 5: errors.append(f'Questão sem 5 alternativas: {q["id"]}')
    for topic in q['topicIds']:
        if topic not in topic_to_subject: errors.append(f'Tópico inexistente em {q["id"]}: {topic}')
        elif topic_to_subject[topic] != q['subjectId']: errors.append(f'Associação matéria/tópico incorreta: {q["id"]}')

lesson_topics={l['topicId'] for l in lessons}
for topic in topic_to_subject:
    if topic not in lesson_topics: errors.append(f'Tópico sem aula: {topic}')

# Regra explícita do usuário: não aceitar localStorage/sessionStorage no código fonte.
for path in ROOT.rglob('*'):
    if path.is_file() and path.suffix in {'.js','.html'}:
        text=path.read_text(encoding='utf-8',errors='ignore')
        if 'localStorage' in text or 'sessionStorage' in text:
            errors.append(f'Armazenamento proibido citado no código: {path.relative_to(ROOT)}')

if errors:
    print('\n'.join(f'ERRO: {e}' for e in errors))
    raise SystemExit(1)
print(f'OK - {len(topic_to_subject)} tópicos, {len(lessons)} aulas e {len(questions)} questões validadas.')
