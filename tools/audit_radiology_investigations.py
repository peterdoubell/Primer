#!/usr/bin/env python3
"""Audit the source-only professional reference separately from learning nodes."""
import json
from pathlib import Path
from collections import Counter
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from primer.curriculum import Curriculum
from primer.radiology_catalog import catalogue,detail


def audit():
    curr=Curriculum();rows=[]
    for item in catalogue()['investigations']:
        ref=detail(curr,item)['radiology_reference']
        rows.append({'id':item['id'],'title':item['title'],'section':item['section'],
                     'topic':item['topic'],'modality':item['modality'],'source_titles':item['source_titles'],
                     'articles':len(item['article_ids']),'images':len(ref['key_images']),
                     'template_count':len(ref['report_templates']),
                     'source_urls':[s['url'] for s in ref['reading']]})
    return {'investigations':len(rows),'source_articles':sum(r['articles'] for r in rows),
            'sections':dict(Counter(r['section'] for r in rows)),
            'image_slots':sum(r['images'] for r in rows),
            'empty_galleries':[r['id'] for r in rows if not r['images']],
            'unmapped_topics':[], 'details':rows}


if __name__=='__main__':
    result=audit();print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(bool(result['empty_galleries']))
