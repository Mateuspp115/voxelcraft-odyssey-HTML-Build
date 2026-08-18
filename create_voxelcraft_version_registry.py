from __future__ import annotations
import csv, hashlib, json, re, subprocess, zipfile
from pathlib import Path
repo=Path('/home/ubuntu/voxelcreft-repo')
versions=repo/'versions/html'
work=Path('/home/ubuntu/voxelcraft-version-downloads'); work.mkdir(exist_ok=True)
manifest_dir=repo/'versions/manifests'; manifest_dir.mkdir(parents=True,exist_ok=True)
rows=[]; files=[]
for d in sorted([p for p in versions.iterdir() if p.is_dir()], key=lambda p: (0 if p.name=='v14' else 1, p.name)):
    name=d.name
    try: commit=subprocess.check_output(['git','log','-1','--format=%H','--','versions/html/'+name],cwd=repo,text=True).strip()
    except Exception: commit=''
    entries=[]
    for p in sorted(x for x in d.rglob('*') if x.is_file()):
        rel=p.relative_to(d).as_posix(); data=p.read_bytes(); sha=hashlib.sha256(data).hexdigest()
        e={'path':rel,'size':len(data),'sha256':sha}; entries.append(e); files.append({'snapshot':name,'path':f'versions/html/{name}/{rel}','size':len(data),'sha256':sha,'commit':commit})
    out=manifest_dir/f'{re.sub(r"[^A-Za-z0-9._-]+","_",name)}.json'; out.write_text(json.dumps({'snapshot':name,'latest':name=='v14','commit':commit,'file_count':len(entries),'files':entries},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    archive=work/f'voxelcraft-{name}-source.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(x for x in d.rglob('*') if x.is_file()): z.write(p,Path(name)/p.relative_to(d))
    rows.append({'snapshot':name,'latest':'true' if name=='v14' else 'false','commit':commit,'archive':archive.name,'size':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()})
(repo/'versions/manifest.json').write_text(json.dumps({'project':'VoxelCraft Odyssey HTML Build','snapshot_count':len(rows),'latest':'v14','files':files},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (repo/'versions/file-history.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['snapshot','path','size','sha256','commit']); w.writeheader(); w.writerows(files)
(repo/'versions/downloads').mkdir(exist_ok=True)
with (repo/'versions/downloads/RELEASE_MAP.tsv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['snapshot','latest','commit','archive','size','sha256'],delimiter='\t'); w.writeheader(); w.writerows(rows)
(repo/'versions/downloads/DOWNLOADS_INDEX.json').write_text(json.dumps({'count':len(rows),'latest':'v14','source_only':True,'downloads':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Downloads por versão — VoxelCraft Odyssey HTML Build','','A versão **v14** é a mais recente e aparece primeiro. Cada linha corresponde a um ZIP source-only do HTML daquela versão.','', '| # | Versão | Commit | ZIP local | SHA-256 |','|---:|---|---|---|---|']
for i,r in enumerate(rows,1): lines.append(f"| {i} | **`{r['snapshot']}`**{' — mais recente' if r['latest']=='true' else ''} | `{r['commit'][:7]}` | `{r['archive']}` | `{r['sha256'][:12]}…` |")
(repo/'versions/downloads/README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print({'snapshots':len(rows),'latest':rows[0]['snapshot'],'files':len(files),'download_dir':str(work)})
