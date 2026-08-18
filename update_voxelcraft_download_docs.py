from pathlib import Path
import csv,json
repo=Path('/home/ubuntu/voxelcreft-repo')
rows=list(csv.DictReader((repo/'versions/downloads/RELEASE_MAP.tsv').open(encoding='utf-8'),delimiter='\t'))
(repo/'versions/downloads/DOWNLOADS_INDEX.json').write_text(json.dumps({'count':len(rows),'latest':'v14','source_only':True,'downloads':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Downloads por versão — VoxelCraft Odyssey HTML Build','','A versão **v14** é a mais recente e aparece primeiro. Cada linha corresponde a um ZIP source-only do HTML daquela versão, anexado à release GitHub correspondente.','', '| # | Versão | Commit | Download | Release | SHA-256 |','|---:|---|---|---|---|---|']
for i,r in enumerate(rows,1):
    lines.append(f"| {i} | **`{r['snapshot']}`**{' — mais recente' if r['snapshot']=='v14' else ''} | `{r['commit'][:7]}` | [ZIP source-only]({r['asset_url']}) | [release]({r['release_url']}) | `{r['sha256'][:12]}…` |")
(repo/'versions/downloads/README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('rows',len(rows),'first',rows[0]['snapshot'],'urls',sum(bool(r['asset_url']) for r in rows))
