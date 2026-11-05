#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--table-root',required=True);a=p.parse_args();root=Path(a.table_root);fail=[]
 for directory in [root,*sorted(x for x in root.rglob('*') if x.is_dir())]:
  readme=directory/'README.md'
  if not readme.is_file():fail.append(f'missing_readme:{directory.relative_to(root)}');continue
  text=readme.read_text()
  for child in directory.iterdir():
   if child.name!='README.md' and f'`{child.name}`' not in text:fail.append(f'undocumented_child:{child}')
  for table in [x for x in directory.iterdir() if x.suffix.lower() in {'.tsv','.csv'}]:
   with table.open(newline='') as h:header=next(csv.reader(h,delimiter='\t' if table.suffix=='.tsv' else ','),[])
   for field in header:
    if not re.search(rf'^\| `{re.escape(field)}` \| .+ \|$',text,re.M):fail.append(f'undocumented_field:{table.name}:{field}')
 if fail:raise SystemExit('\n'.join(fail))
 print('PASS\trecursive README child and exact TSV/CSV field coverage')
if __name__=='__main__':main()
