"""Check SMART raw presence for every CSV day. Values are only counted, not analyzed.

Reads all models once so both HDD75 and top20 can be checked against the same
full-period results. Per-day checkpoints make interrupted runs resumable.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import os
import json
import time
import zipfile
import duckdb
import pandas as pd

EDA=Path(__file__).resolve().parents[1]
ROOT=EDA.parent
RAW=Path(os.environ.get('HDD_RAW_DIR','C:/Users/rhkdd/OneDrive/hdd-rul/data/raw'))  # 원본 zip 폴더
OUT=EDA/'analysis/full_column_check'
DAYS=OUT/'days'
TMP=OUT/'tmp'
for folder in (DAYS,TMP): folder.mkdir(parents=True,exist_ok=True)
rank=pd.read_csv(ROOT/'data/backblaze/summary/model_rank.csv')
jobs=[]
for zpath in sorted(RAW.glob('*.zip')):
    with zipfile.ZipFile(zpath) as archive:
        for item in archive.infolist():
            name=Path(item.filename).name
            if '__MACOSX' not in item.filename and len(name)==14 and name.endswith('.csv'):
                day=name[:-4]
                if '2024-04-01'<=day<='2026-06-30':jobs.append((day,zpath,item.filename))
jobs.sort()
expected=pd.date_range('2024-04-01','2026-06-30').strftime('%Y-%m-%d').tolist()
assert [j[0] for j in jobs]==expected and len(jobs)==821

def sql_path(p):return p.as_posix().replace("'","''")
def measure(job):
    day,zpath,entry=job
    dest=DAYS/f'{day}.csv'
    schema=DAYS/f'{day}.schema.json'
    if dest.exists() and schema.exists():
        return day,True
    temp=TMP/f'{day}.csv'
    partial=DAYS/f'{day}.pending.csv'
    with zipfile.ZipFile(zpath) as archive, archive.open(entry) as src, temp.open('wb') as dst:
        import shutil
        shutil.copyfileobj(src,dst,length=1024*1024)
    with temp.open(encoding='utf-8-sig',newline='') as f:header=next(csv.reader(f))
    con=duckdb.connect()
    try:
        con.execute("SET threads=2")
        con.execute("SET memory_limit='2GB'")
        con.execute("SET enable_progress_bar=false")
        con.execute(f"SET temp_directory='{sql_path(TMP/day)}'")
        con.execute(f"""COPY (
            SELECT model,count(*) AS observed_rows,count(COLUMNS('^smart_.*_raw$'))
            FROM read_csv('{sql_path(temp)}',header=true,all_varchar=true,nullstr=['','NaN','nan','NA'])
            GROUP BY model
        ) TO '{sql_path(partial)}' (HEADER)""")
    finally:con.close()
    df=pd.read_csv(partial)
    assert df.model.is_unique and df.observed_rows.gt(0).all()
    assert set(df.model)<=set(rank.model)
    partial.replace(dest)
    schema.write_text(json.dumps({'date':day,'zip':zpath.name,'entry':entry,'columns':header},ensure_ascii=False,indent=2),encoding='utf-8')
    temp.unlink()
    return day,False

def summarize():
    columns=set()
    frames=[]
    for day in expected:
        f=pd.read_csv(DAYS/f'{day}.csv')
        f['date']=day
        frames.append(f)
        columns.update(c for c in f if c.startswith('smart_') and c.endswith('_raw'))
    long=pd.concat(frames,ignore_index=True).fillna(0)
    cols=sorted(columns,key=lambda c:int(c.split('_')[1]))
    counts=long.groupby('model')[['observed_rows']+cols].sum()
    model_days=long.groupby('model').size()
    rows_by_model=counts['observed_rows']
    reference=rank.set_index('model')['drive_days'].sort_index()
    assert rows_by_model.sort_index().astype('int64').equals(reference.astype('int64')), 'Full raw row totals differ from fleet metadata'
    inventory=pd.read_csv(EDA/'analysis/v2/device_inventory.csv')
    hdd_names=inventory.loc[inventory.device_type.eq('HDD'),'model'].tolist()
    top20=pd.read_csv(EDA/'analysis/v2/hdd_model_cases.csv').head(20).model.tolist()
    records=[]
    for model in counts.index:
        g=long.loc[long.model.eq(model)]
        for col in cols:
            n=int(counts.at[model,col]);rows=int(rows_by_model[model])
            records.append({'model':model,'column':col,'observed_days':int(model_days[model]),
                            'days_with_values':int(g[col].gt(0).sum()),'observed_rows':rows,
                            'nonnull_rows':n,'nonnull_pct':100*n/rows})
    result=pd.DataFrame(records)
    result.to_csv(OUT/'model_smart_presence.csv',index=False,encoding='utf-8-sig')
    result.to_parquet(OUT/'model_smart_presence.parquet',index=False)
    long.to_parquet(OUT/'daily_model_counts.parquet',index=False)
    for group,names in [('hdd75',hdd_names),('top20',top20)]:
        part=result.loc[result.model.isin(names)].copy()
        part['ever_present']=part.nonnull_rows.gt(0)
        part['each_observed_day']=part.days_with_values.eq(part.observed_days)
        part['coverage_ge99']=part.nonnull_pct.ge(99)
        summary=part.groupby('column').agg(models=('model','size'),models_with_values=('ever_present','sum'),
            models_with_values_each_day=('each_observed_day','sum'),models_coverage_ge99=('coverage_ge99','sum'),
            min_nonnull_pct=('nonnull_pct','min'))
        summary=summary.reindex(cols)
        summary.to_csv(OUT/f'{group}_common_columns.csv',encoding='utf-8-sig')
        print(group,'all models ever recorded:',summary.index[summary.models_with_values.eq(len(names))].tolist(),flush=True)
        print(group,'all models >=99%:',summary.index[summary.models_coverage_ge99.eq(len(names))].tolist(),flush=True)
    manifest={'scope':'2024-04-01 through 2026-06-30','days_expected':821,'days_checked':len(frames),
              'models_checked':int(counts.shape[0]),'raw_rows_checked':int(rows_by_model.sum()),
              'operation':'Count non-null SMART raw values per model per CSV day; zero is a present value.',
              'validation':'Every date present; per-model total row counts match full fleet summary.',
              'dates':expected}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('FULL CHECK COMPLETE:',manifest['days_checked'],'days;',manifest['raw_rows_checked'],'rows',flush=True)

if __name__=='__main__':
    started=time.monotonic()
    print(f'Checking {len(jobs)} CSV dates; two workers; checkpoints in {DAYS}',flush=True)
    completed=0
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(measure,j) for j in jobs]
        for future in as_completed(futures):
            day,reused=future.result()
            completed+=1
            if completed%10==0 or completed==len(jobs):
                elapsed=time.monotonic()-started
                remaining=elapsed/completed*(len(jobs)-completed)
                print(f'{completed}/821 | latest={day} | elapsed={elapsed/60:.1f}m | estimated remaining={remaining/60:.1f}m',flush=True)
    summarize()
