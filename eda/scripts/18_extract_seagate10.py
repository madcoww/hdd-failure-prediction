"""EDA v3: Seagate 10종(고장 수 상위 20종 중 Seagate)의 10종 모두 기록한 SMART raw 컬럼을 821일 전체에서 추출한다.

원본 zip 폴더는 환경변수 HDD_RAW_DIR 로 지정한다. 일별 파일은 중단 후 이어서 실행할 수 있다.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,os,sys,zipfile,shutil,time
import duckdb,pandas as pd

EDA=Path(__file__).resolve().parents[1]
ROOT=EDA.parent
if not os.environ.get('HDD_RAW_DIR'):sys.exit('환경변수 HDD_RAW_DIR(원본 zip 폴더)을 지정하세요.')
RAW=Path(os.environ['HDD_RAW_DIR'])
OUT=EDA/'analysis/v3'
BASE=ROOT/'data/backblaze/seagate10'
DAYS=BASE/'daily'
TMP=OUT/'tmp'
for p in (OUT,DAYS,TMP):p.mkdir(parents=True,exist_ok=True)
assert shutil.disk_usage(EDA).free>8*1024**3,'Need at least 8GB free'
top=pd.read_csv(ROOT/'data/backblaze/summary/top20_models.csv',encoding='utf-8-sig')
models=top[top.model.str.startswith('ST')].reset_index(drop=True)
assert len(models)==10
presence=pd.read_csv(EDA/'analysis/full_column_check/model_smart_presence.csv')
p=presence[presence.model.isin(models.model)]
g=p.groupby('column').agg(n=('nonnull_rows',lambda x:(x>0).sum()),full=('nonnull_pct',lambda x:(x>=99.9).sum()))
cols=sorted(g.index[(g.n==10)&(g.full==10)],key=lambda c:int(c.split('_')[1]))
assert len(cols)==20,len(cols)
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
def sp(q):return q.as_posix().replace("'","''")
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
        assert dup==0,f'Duplicate disk/date keys on {day}: {dup}'
        partial=dest.with_suffix('.pending.parquet')
        con.execute(f"COPY selected TO '{sp(partial)}' (FORMAT PARQUET,COMPRESSION ZSTD)")
        partial.replace(dest)
        audit.write_text(json.dumps({'date':day,'rows':n,'duplicate_rows':dup}),encoding='utf-8')
    finally:con.close()
    temp.unlink()
if __name__=='__main__':
    started=time.monotonic();done=0
    print(f'Seagate {len(models)}종, SMART {len(cols)}개, {len(jobs)}일 추출',flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for f in as_completed([pool.submit(worker,j) for j in jobs]):
            f.result();done+=1
            if done%25==0 or done==len(jobs):print(f'{done}/{len(jobs)} | elapsed={(time.monotonic()-started)/60:.1f}m',flush=True)
    audits=[json.loads((DAYS/f'{j[0]}.json').read_text()) for j in jobs]
    rows=sum(a['rows'] for a in audits)
    assert rows==int(models.drive_days.sum()),(rows,int(models.drive_days.sum()))
    merged=BASE/'seagate10_2024Q2-2026Q2.parquet'
    con=duckdb.connect()
    con.execute(f"COPY (SELECT * FROM read_parquet('{sp(DAYS)}/*.parquet') ORDER BY serial_number,date) TO '{sp(merged)}' (FORMAT PARQUET,COMPRESSION ZSTD)")
    mrows=con.execute(f"SELECT count(*) FROM read_parquet('{sp(merged)}')").fetchone()[0]
    assert mrows==rows
    manifest={'models':models.model.tolist(),'smart_columns':cols,'dates':len(jobs),'rows':rows,
              'source':'Original Backblaze daily CSV values; no sampling'}
    (OUT/'extraction_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('EXTRACTION COMPLETE',rows,'rows',flush=True)
