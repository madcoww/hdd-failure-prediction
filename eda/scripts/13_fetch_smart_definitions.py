"""Snapshot primary implementation sources for the SMART semantic audit."""
from pathlib import Path
import urllib.request,json,hashlib,datetime

OUT=Path(__file__).resolve().parents[1]/'analysis/column_definition_audit'
OUT.mkdir(parents=True,exist_ok=True)
sources={
 'drivedb.h':'https://raw.githubusercontent.com/smartmontools/smartmontools/main/drivedb/drivedb.h',
 'ataprint.cpp':'https://raw.githubusercontent.com/smartmontools/smartmontools/main/src/ataprint.cpp',
 'atacmds.cpp':'https://raw.githubusercontent.com/smartmontools/smartmontools/main/lib/atacmds.cpp',
 'seagate_smart.html':'https://github.com/Seagate/openSeaChest/wiki/Drive-Health-and-SMART',
 'backblaze_architecture.html':'https://www.backblaze.com/blog/drive-stats-data-deep-dive-the-architecture/',
 'toshiba_temperature.pdf':'https://www.toshiba-storage.com/wp/wp-content/uploads/2022/07/Toshiba_OpenE_Blogpost_July2022_final.pdf',
}
records=[]
for name,url in sources.items():
    req=urllib.request.Request(url,headers={'User-Agent':'HDD-EDA-definition-audit'})
    body=urllib.request.urlopen(req,timeout=20).read()
    (OUT/name).write_bytes(body)
    records.append({'file':name,'url':url,'sha256':hashlib.sha256(body).hexdigest(),
                    'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print(name,len(body),'bytes',flush=True)
(OUT/'source_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
