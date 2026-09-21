#!/usr/bin/env python3
import json, re, statistics
from pathlib import Path

DATA = Path('data')
lessons = json.loads((DATA/'lessons/gcm-salvador-2026.json').read_text(encoding='utf-8'))

pages=[]
for lesson in lessons:
    for p in lesson.get('studyPages',[]):
        pages.append((lesson,p))

print('lessons',len(lessons),'pages',len(pages))
print('subtopics',sum(len(x.get('subtopics') or []) for x in lessons))
chars=[]; blocks=[]
for _,p in pages:
    chars.append(len(json.dumps(p,ensure_ascii=False)))
    blocks.append(len(p.get('blocks') or []))
print('page chars min/median/avg/max',min(chars),int(statistics.median(chars)),round(statistics.mean(chars)),max(chars))
print('blocks min/median/avg/max',min(blocks),statistics.median(blocks),round(statistics.mean(blocks),2),max(blocks))
for li in [0,1,20,60,100]:
    lesson=lessons[li]
    print('\nLESSON',li,lesson.get('topicId'),lesson.get('title'))
    print('lesson keys',sorted(lesson.keys()))
    print('subtopics sample',json.dumps((lesson.get('subtopics') or [])[:2],ensure_ascii=False)[:2500])
    ps=lesson.get('studyPages') or []
    for pi in [0,min(1,len(ps)-1),len(ps)//2,len(ps)-1]:
        p=ps[pi]
        print(' PAGE',pi,'keys',sorted(p.keys()))
        print('  id=',p.get('id'),'title=',p.get('title'))
        print('  subtopic=',p.get('subtopic'),p.get('subtopicTitle'),p.get('subtopicIndex'))
        print('  block titles=',[b.get('title') for b in (p.get('blocks') or [])])
        print('  preview=',re.sub(r'\\s+',' ',json.dumps(p,ensure_ascii=False))[:1600])
