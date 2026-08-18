from pathlib import Path
import csv, json, subprocess
repo=Path('/home/ubuntu/voxelcreft-repo')
data=json.loads((repo/'versions/downloads/DOWNLOADS_INDEX.json').read_text(encoding='utf-8'))
rows=[]
for r in data['downloads']:
    tag=f"voxelcraft-{r['snapshot']}"
    name=f"voxelcraft-{r['snapshot']}-source.zip"
    local=Path('/home/ubuntu/voxelcraft-version-downloads')/name
    assert local.exists()
    import hashlib
    size=local.stat().st_size
    sha256=hashlib.sha256(local.read_bytes()).hexdigest()
    raw=subprocess.check_output(['gh','api',f'repos/Mateuspp115/voxelcraft-odyssey-HTML-Build/releases/tags/{tag}','--jq',f'.assets[] | select(.name=="{name}") | .browser_download_url'],text=True).strip()
    assert raw
    rows.append({'snapshot':r['snapshot'],'latest':'true' if r['snapshot']=='v14' else 'false','commit':r['commit'],'archive':name,'size':size,'sha256':sha256,'release_url':f'https://github.com/Mateuspp115/voxelcraft-odyssey-HTML-Build/releases/tag/{tag}','asset_url':raw})
with (repo/'versions/downloads/RELEASE_MAP.tsv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter='\t'); w.writeheader(); w.writerows(rows)
(repo/'versions/downloads/DOWNLOADS_INDEX.json').write_text(json.dumps({'count':len(rows),'latest':'v14','source_only':True,'downloads':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('rows',len(rows),'urls',sum(bool(r['asset_url']) for r in rows))
