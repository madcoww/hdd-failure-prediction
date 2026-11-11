"""Extract actual values for the verified top20/common13 cohort, all 821 dates."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,os,zipfile,shutil,time
import duckdb,pandas as pd

EDA=Path(__file__).resolve().parents[1]
ROOT=EDA.parent
OUT=EDA/'analysis/detailed_v2'
RAW=Path(os.environ.get('HDD_RAW_DIR','C:/Users/rhkdd/OneDrive/hdd-rul/data/raw'))  # 원본 zip 폴더
DAYS=EDA.parent/'data/backblaze/top20_common13/daily'
TMP=OUT/'tmp'
for p in (OUT,DAYS,TMP):p.mkdir(parents=True,exist_ok=True)
assert shutil.disk_usage(EDA).free>8*1024**3, 'Need at least 8GB free for extraction'
models=pd.read_csv(EDA/'analysis/v2/hdd_model_cases.csv').head(20)
check=pd.read_csv(EDA/'analysis/full_column_check/top20_common_columns.csv')
cols=check.loc[check.models_with_values.eq(20),'column'].tolist()
assert len(cols)==13
models.to_csv(OUT/'selected_models.csv',index=False,encoding='utf-8-sig')
(OUT/'selected_columns.json').write_text(json.dumps(cols,indent=2),encoding='utf-8')
where=','.join("'"+m.replace("'","''")+"'" for m in models.model)
jobs=[]
for z in sorted(RAW.glob('*.zip')):
    with zipfile.ZipFile(z) as a:
        for i in a.infolist():
            name=Path(i.filename).name
            if '__MACOSX' not in i.filename and len(name)==14 and name.endswith('.csv') and '2024-04-01'<=name[:-4]<='2026-06-30':jobs.append((name[:-4],z,i.filename))
jobs.sort()
assert [j[0] for j in jobs]==pd.date_range('2024-04-01','2026-06-30').strftime('%Y-%m-%d').tolist()
def sp(p):return p.as_posix().replace("'","''")
def worker(job):
    day,z,entry=job
    dest=DAYS/f'{day}.parquet'; audit=DAYS/f'{day}.json'
    if dest.exists() and audit.exists():return
    temp=TMP/f'{day}.csv'
    with zipfile.ZipFile(z) as a,a.open(entry) as src,temp.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)
    con=duckdb.connect()
    try:
        con.execute("SET threads=2; SET memory_limit='2GB'; SET enable_progress_bar=false")
        smart=', '.join(f'try_cast("{c}" AS DOUBLE) AS "{c}"' for c in cols)
        con.execute(f"""CREATE TABLE selected AS SELECT cast(date AS DATE) AS date,serial_number,model,
            try_cast(capacity_bytes AS BIGINT) AS capacity_bytes,cast(failure AS TINYINT) AS failure,datacenter,{smart}
            FROM read_csv('{sp(temp)}',header=true,all_varchar=true,nullstr=['','NaN','nan','NA']) WHERE model IN ({where})""")
        n,dup=con.execute('SELECT count(*),count(*)-count(DISTINCT(serial_number,date)) FROM selected').fetchone()
        assert dup==0, f'Duplicate disk/date keys on {day}: {dup}'
        partial=dest.with_suffix('.pending.parquet')
        con.execute(f"COPY selected TO '{sp(partial)}' (FORMAT PARQUET,COMPRESSION ZSTD)")
        partial.replace(dest)
        audit.write_text(json.dumps({'date':day,'rows':n,'duplicate_rows':dup}),encoding='utf-8')
    finally:con.close()
    temp.unlink()
if __name__=='__main__':
    started=time.monotonic();done=0
    print('Extracting actual SMART values: 20 models, 13 columns, 821 days',flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(worker,j) for j in jobs]):
            f.result();done+=1
            if done%25==0 or done==821:print(f'{done}/821 | elapsed={(time.monotonic()-started)/60:.1f}m',flush=True)
    audits=[json.loads((DAYS/f'{j[0]}.json').read_text()) for j in jobs]
    rows=sum(a['rows'] for a in audits)
    assert rows==int(models.drive_days.sum())
    manifest={'models':models.model.tolist(),'smart_columns':cols,'dates':821,'rows':rows,
              'duplicate_disk_date_rows':sum(a['duplicate_rows'] for a in audits),
              'source':'Original Backblaze daily CSV values; no sampling'}
    (OUT/'extraction_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('EXTRACTION COMPLETE',rows,'rows',flush=True)
