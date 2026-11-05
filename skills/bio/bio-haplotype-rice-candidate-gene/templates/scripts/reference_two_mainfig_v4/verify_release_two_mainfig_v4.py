#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,re,zipfile
from pathlib import Path
def digest_bytes(data):return hashlib.sha256(data).hexdigest()
def private_path_hits(release):
 """List textual customer artifacts containing workstation paths or usernames."""
 pattern=re.compile(r'(?:/Users/|/home/|/Volumes/|REPLACE_PRIVATE_USER|[A-Za-z]:\\\\)')
 hits=[]
 for path in release.rglob('*'):
  if not path.is_file() or path.suffix.lower() not in {'.md','.tsv','.csv','.txt','.newick'}:continue
  if pattern.search(path.read_text(errors='replace')):hits.append(path.relative_to(release).as_posix())
 return hits
def main():
 p=argparse.ArgumentParser();p.add_argument('--release-dir',required=True);p.add_argument('--zip',required=True);p.add_argument('--manifest',required=True);a=p.parse_args();release=Path(a.release_dir)
 with Path(a.manifest).open(newline='') as h:manifest=list(csv.DictReader(h,delimiter='\t'))
 expected={row['relative_path']:(row['sha256'],int(row['bytes'])) for row in manifest}
 actual={path.relative_to(release).as_posix():(digest_bytes(path.read_bytes()),path.stat().st_size) for path in release.rglob('*') if path.is_file()}
 with zipfile.ZipFile(a.zip) as z:
  bad=z.testzip();names=[name for name in z.namelist() if not name.endswith('/')]
  zipped={name:(digest_bytes(z.read(name)),z.getinfo(name).file_size) for name in names}
 required_main={
  'figure/Fig1_Haplotype/Fig1_Haplotype.pdf','figure/Fig1_Haplotype/Fig1_Haplotype.png',
  'figure/Fig2_SelectionScan/Fig2_SelectionScan.pdf','figure/Fig2_SelectionScan/Fig2_SelectionScan.png',
 }
 if not required_main.issubset(names):raise SystemExit(f'missing or misplaced main figures: {sorted(required_main-set(names))}')
 roots={Path(x).parts[0] for x in names};wanted={'figure','manuscript','table','README.md'}
 if bad or roots!=wanted or expected!=actual or expected!=zipped:raise SystemExit(f'zip/manifest failure={bad}; roots={sorted(roots)} expected={len(expected)} release={len(actual)} zip={len(zipped)}')
 forbidden=[name for name in names if any(part.lower() in {'logs','scripts','audit','temp_tests','__pycache__'} for part in Path(name).parts) or name.endswith(('.log','.py','.R','.sh'))]
 if forbidden:raise SystemExit(f'forbidden internal ZIP members: {forbidden[:10]}')
 private=private_path_hits(release)
 if private:raise SystemExit(f'private absolute path or username in customer release: {private[:10]}')
 print(f'PASS\tunzip, manifest and exact nested whitelist files={len(expected)}')
if __name__=='__main__':main()
