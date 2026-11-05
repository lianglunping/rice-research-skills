#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,zipfile
from pathlib import Path
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--release-dir',required=True);p.add_argument('--zip',required=True);p.add_argument('--manifest',required=True);a=p.parse_args();r=Path(a.release_dir);z=Path(a.zip);m=Path(a.manifest)
 roots={x.name for x in r.iterdir()};wanted={'figure','manuscript','table','README.md'}
 if roots!=wanted:raise SystemExit(f'bad release roots: {sorted(roots)}')
 records=[{'relative_path':x.relative_to(r).as_posix(),'sha256':digest(x),'bytes':x.stat().st_size} for x in sorted(p for p in r.rglob('*') if p.is_file())]
 m.parent.mkdir(parents=True,exist_ok=True)
 with m.open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=['relative_path','sha256','bytes'],delimiter='\t',lineterminator='\n');w.writeheader();w.writerows(records)
 z.parent.mkdir(parents=True,exist_ok=True);temporary=z.with_suffix(z.suffix+'.building')
 if temporary.exists():temporary.unlink()
 with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED) as o:
  for x in sorted(p for p in r.rglob('*') if p.is_file()):o.write(x,x.relative_to(r))
 temporary.replace(z)
 print(f'[zip-v4] files={len(records)} zip={z}')
if __name__=='__main__':main()
