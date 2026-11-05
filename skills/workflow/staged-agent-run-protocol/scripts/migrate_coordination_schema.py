#!/usr/bin/env python3
"""Add required columns without dropping legacy TSV columns or backups."""
from __future__ import annotations
import argparse, csv, shutil
from pathlib import Path
from sar_utils import AUDIT_RECEIPT_HEADER, AGENT_ASSIGNMENT_HEADER, file_lock, _write_tsv_unlocked
def main() -> int:
 p=argparse.ArgumentParser(); p.add_argument('--run-dir',required=True); a=p.parse_args(); root=Path(a.run_dir)
 for rel,required in [('coordination/agent_assignments.tsv',AGENT_ASSIGNMENT_HEADER),('coordination/audit_receipts.tsv',AUDIT_RECEIPT_HEADER)]:
  path=root/rel
  if not path.exists(): continue
  with file_lock(path):
   with path.open(newline='',encoding='utf-8') as h: reader=csv.DictReader(h,delimiter='\t'); old=reader.fieldnames or []; rows=list(reader)
   header=old+[x for x in required if x not in old]
   bak=path.with_suffix(path.suffix+'.pre_migration.bak')
   if not bak.exists(): shutil.copy2(path,bak)
   _write_tsv_unlocked(path,header,rows)
 print('PASS\tMIGRATED'); return 0
if __name__=='__main__': raise SystemExit(main())
