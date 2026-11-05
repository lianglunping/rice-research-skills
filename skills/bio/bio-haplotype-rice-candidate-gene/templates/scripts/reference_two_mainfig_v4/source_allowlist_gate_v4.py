#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib
from pathlib import Path
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--project-root',required=True);p.add_argument('--receipt',required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
 config_path=Path(a.config).resolve();root=Path(a.project_root).resolve()
 with config_path.open(newline='') as h:c={r['field']:r['value'] for r in csv.DictReader(h,delimiter='\t')}
 source=Path(c['source_result_dir']);source=source if source.is_absolute() else root/source
 paths=[('config','config',config_path)]
 for rel in (x.strip() for x in c.get('source_required_relpaths','').split(',')):
  if rel:paths.append(('source',rel,source/rel))
 for key in (x.strip() for x in c.get('project_required_config_keys','').split(',')):
  if key:
   q=Path(c[key]);paths.append(('project',key,q if q.is_absolute() else root/q))
 for key in (x.strip() for x in c.get('external_required_config_keys','').split(',')):
  if key:paths.append(('external',key,Path(c[key])))
 now=[]
 seen=set()
 for role,key,q in paths:
  q=q.resolve()
  if q in seen:continue
  seen.add(q)
  if not q.is_file():raise SystemExit(f'allowlist input missing: role={role} key={key} path={q}')
  now.append({'role':role,'key':key,'path':str(q),'sha256':digest(q),'bytes':str(q.stat().st_size)})
 receipt=Path(a.receipt)
 if a.verify:
  with receipt.open(newline='') as h:old=list(csv.DictReader(h,delimiter='\t'))
  if now!=old:raise SystemExit('source allowlist changed after derivative preparation')
 else:
  receipt.parent.mkdir(parents=True,exist_ok=True)
  with receipt.open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=['role','key','path','sha256','bytes'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(now)
if __name__=='__main__':main()
