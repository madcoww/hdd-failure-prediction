"""Detailed EDA: full-period quality, monthly risk sets, matched comparisons, trajectories and rules."""
from pathlib import Path
import json,time
import duckdb,numpy as np,pandas as pd
from scipy.stats import mannwhitneyu

EDA=Path(__file__).resolve().parents[1]
OUT=EDA/'analysis/detailed_v2'
cols=json.loads((OUT/'selected_columns.json').read_text())
con=duckdb.connect()
con.execute("SET threads=4; SET memory_limit='4GB'; SET enable_progress_bar=false")
def sp(p):return p.as_posix().replace("'","''")
con.execute(f"SET temp_directory='{sp(OUT/'query_tmp')}'")
q=lambda sql:con.sql(sql).df()
def save(df,name):df.to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig');return df
def copy(sql,name):
    dest=OUT/f'{name}.parquet'
    if not dest.exists():
        started=time.monotonic();print('Computing',name,flush=True)
        pending=dest.with_suffix('.pending.parquet')
        con.execute(f"COPY ({sql}) TO '{sp(pending)}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        pending.replace(dest);print(name,'done',round(time.monotonic()-started,1),'s',flush=True)
    con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{sp(dest)}')")

manifest=json.loads((OUT/'extraction_manifest.json').read_text())
assert manifest['dates']==821 and manifest['duplicate_disk_date_rows']==0
con.execute(f"CREATE VIEW raw_values AS SELECT * FROM read_parquet('{sp(EDA.parent/'data/backblaze/top20_common13/daily/*.parquet')}')")
copy('''SELECT serial_number,min(model) AS model,min(date) AS first_date,max(date) AS last_date,
    min(date) FILTER(WHERE failure=1) AS first_failure,count(*) AS observed_rows,
    sum(failure) AS failure_rows,count(DISTINCT model) AS model_names
    FROM raw_values GROUP BY serial_number''','disks')
con.execute('''CREATE VIEW clean AS SELECT r.* FROM raw_values r JOIN disks p USING(serial_number)
    WHERE p.first_failure IS NULL OR r.date<=p.first_failure''')
save(q('''SELECT count(*) AS disks,count(*) FILTER(WHERE first_failure IS NOT NULL) AS failed_disks,
    sum(failure_rows) AS failure_rows,count(*) FILTER(WHERE failure_rows>1) AS repeated_failure_disks,
    count(*) FILTER(WHERE last_date>first_failure) AS post_failure_disks FROM disks'''),'cohort')
save(q('''SELECT count(*) AS raw_rows,count(*) FILTER(WHERE date IS NULL) AS missing_date,
    count(*) FILTER(WHERE serial_number IS NULL OR serial_number='') AS missing_serial,
    count(*) FILTER(WHERE datacenter IS NULL OR datacenter='') AS missing_datacenter,
    count(*) FILTER(WHERE capacity_bytes IS NULL OR capacity_bytes<=0) AS invalid_capacity FROM raw_values'''),'quality')
save(q('''SELECT (SELECT count(*) FROM raw_values) AS raw_rows,(SELECT count(*) FROM clean) AS clean_rows'''),'clean_scale')

aggregates=[]
for c in cols:
    aggregates.extend([f'count("{c}") AS "{c}__n"',f'count(*) FILTER(WHERE "{c}"=0) AS "{c}__zero"',
                       f'count(*) FILTER(WHERE "{c}"<0) AS "{c}__neg"',f'min("{c}") AS "{c}__min"',
                       f'max("{c}") AS "{c}__max"',f'avg("{c}") AS "{c}__mean"'])
print('Full-period value statistics',flush=True)
wide=q('SELECT model,count(*) AS rows,'+','.join(aggregates)+' FROM raw_values GROUP BY model')
records=[]
for row in wide.to_dict('records'):
    for c in cols:
        n=int(row[c+'__n']);records.append({'model':row['model'],'column':c,'rows':int(row['rows']),
            'nonnull_rows':n,'missing_pct':100*(1-n/row['rows']),'zero_pct':100*row[c+'__zero']/n if n else np.nan,
            'negative_rows':int(row[c+'__neg']),'min':row[c+'__min'],'max':row[c+'__max'],'mean':row[c+'__mean']})
stats=save(pd.DataFrame(records),'value_quality_by_model')
ref=pd.read_parquet(EDA/'analysis/full_column_check/model_smart_presence.parquet')
check=stats.merge(ref[['model','column','nonnull_rows']],on=['model','column'],suffixes=('','_presence'))
assert check.nonnull_rows.eq(check.nonnull_rows_presence).all(), 'Extraction changed presence counts'
assert stats.rows.groupby(stats.model).first().sum()==manifest['rows']
save(q('''SELECT d.model,count(*) AS drive_days,sum(d.failure) AS failures,
    count(DISTINCT d.serial_number) AS disks,round(100.0*sum(d.failure)/(count(*)/365.0),3) AS afr_pct
    FROM clean d GROUP BY d.model'''),'model_scale')
save(q('''SELECT year(date) AS year,quarter(date) AS quarter,model,count(*) AS drive_days,
    sum(failure) AS failures,100.0*sum(failure)/(count(*)/365.0) AS afr_pct
    FROM clean GROUP BY 1,2,3 ORDER BY 1,2,3'''),'quarterly_by_model')

# Window counts are calculated on ALL clean dates, then only monthly anchors are retained.
copy('''WITH w AS (
 SELECT serial_number,model,date,date-lag(date) OVER(PARTITION BY serial_number ORDER BY date) AS gap_days,
 count(*) OVER(PARTITION BY serial_number ORDER BY date RANGE BETWEEN INTERVAL 29 DAY PRECEDING AND CURRENT ROW) AS rows_30,
 count(*) OVER(PARTITION BY serial_number ORDER BY date RANGE BETWEEN INTERVAL 59 DAY PRECEDING AND CURRENT ROW) AS rows_60,
 count(*) OVER(PARTITION BY serial_number ORDER BY date RANGE BETWEEN INTERVAL 89 DAY PRECEDING AND CURRENT ROW) AS rows_90
 FROM clean)
 SELECT w.*,p.first_date,p.last_date,p.first_failure,
   CASE WHEN p.first_failure<=w.date+INTERVAL 30 DAY THEN 1 ELSE 0 END AS label_30
 FROM w JOIN disks p USING(serial_number,model)
 WHERE day(w.date)=1 AND w.date<=DATE '2026-05-31'
   AND (p.first_failure IS NULL OR w.date<p.first_failure)
   AND (p.first_failure IS NOT NULL OR p.last_date>=w.date+INTERVAL 30 DAY)''','monthly_timeline')
dates=pd.date_range('2024-04-01','2026-05-01',freq='MS')
anchor_dates=sorted({(t-pd.Timedelta(days=offset)).strftime('%Y-%m-%d') for t in dates for offset in (0,7,30,90)})
date_sql=','.join("DATE '"+d+"'" for d in anchor_dates)
copy('SELECT serial_number,model,date,'+','.join(cols)+f' FROM clean WHERE date IN ({date_sql})','anchor_values')
deltas=', '.join(f's."{c}"-h{days}."{c}" AS "delta_{c}_{days}"' for days in (7,30,90) for c in ('smart_5_raw','smart_198_raw'))
copy(f'''SELECT t.*,s.* EXCLUDE(serial_number,model,date),{deltas},
    h7.date IS NOT NULL AS endpoint_7_present,h30.date IS NOT NULL AS endpoint_30_present,
    h90.date IS NOT NULL AS endpoint_90_present
    FROM monthly_timeline t JOIN anchor_values s USING(serial_number,model,date)
    LEFT JOIN anchor_values h7 ON t.serial_number=h7.serial_number AND h7.date=t.date-INTERVAL 7 DAY
    LEFT JOIN anchor_values h30 ON t.serial_number=h30.serial_number AND h30.date=t.date-INTERVAL 30 DAY
    LEFT JOIN anchor_values h90 ON t.serial_number=h90.serial_number AND h90.date=t.date-INTERVAL 90 DAY''','snapshots')
save(q('''SELECT count(*) AS snapshots,sum(label_30) AS positive_snapshots,
    count(DISTINCT date) AS dates,100.0*avg(label_30) AS positive_pct FROM snapshots'''),'label_summary')
save(q('''SELECT label_30,count(*) AS snapshots,
    100.0*avg((rows_30=30)::int) AS complete_30_pct,
    100.0*avg((rows_60=60)::int) AS complete_60_pct,
    100.0*avg((rows_90=90)::int) AS complete_90_pct FROM snapshots GROUP BY label_30'''),'history_availability')
save(q('''SELECT model,count(*) AS snapshots,sum(label_30) AS positives,
    100.0*avg((rows_90=90)::int) AS complete_90_pct FROM snapshots GROUP BY model'''),'history_by_model')
save(q('''SELECT model,count(*) AS snapshots,100.0*avg((gap_days>1)::int) AS resumed_gap_pct,
    avg(label_30) FILTER(WHERE gap_days>1) AS risk_after_gap,
    avg(label_30) FILTER(WHERE gap_days=1) AS risk_after_daily FROM snapshots GROUP BY model'''),'gap_risk')

# Exact calendar-date AND model matching; up to five negative disk snapshots per positive.
copy('''WITH groups AS (SELECT model,date,sum(label_30) AS positives,
    sum(1-label_30) AS negatives FROM snapshots GROUP BY model,date),
    n AS (SELECT s.*,row_number() OVER(PARTITION BY s.model,s.date ORDER BY hash(s.serial_number,42)) AS rn
        FROM snapshots s WHERE label_30=0)
    SELECT s.* FROM snapshots s JOIN groups g USING(model,date)
        WHERE s.label_30=1 AND g.negatives>0
    UNION ALL BY NAME
    SELECT n.* EXCLUDE(rn) FROM n JOIN groups g USING(model,date)
        WHERE g.positives>0 AND n.rn<=5*g.positives''','matched')
matched=q('SELECT * FROM matched')
features=cols+[c for c in matched if c.startswith('delta_')]
effects=[]
for model,g in matched.groupby('model'):
    for c in features:
        a=g.loc[g.label_30.eq(1),c].dropna().to_numpy()
        b=g.loc[g.label_30.eq(0),c].dropna().to_numpy()
        if not len(a) or not len(b):continue
        u=mannwhitneyu(a,b,alternative='two-sided',method='asymptotic').statistic
        effects.append({'model':model,'feature':c,'positive_n':len(a),'negative_n':len(b),
            'rank_biserial':2*u/(len(a)*len(b))-1,'positive_median':float(np.median(a)),
            'negative_median':float(np.median(b)),'positive_gt0_pct':100*float(np.mean(a>0)),
            'negative_gt0_pct':100*float(np.mean(b>0))})
save(pd.DataFrame(effects),'effects_by_model')
save(matched.groupby(['model','label_30']).size().rename('n').reset_index(),'matched_sizes')
growth_features=[c for c in features if c.startswith('delta_')]+['smart_5_raw','smart_198_raw']
growth=matched.dropna(subset=growth_features)
growth_effects=[]
for model,g in growth.groupby('model'):
    for c in growth_features:
        a=g.loc[g.label_30.eq(1),c].to_numpy();b=g.loc[g.label_30.eq(0),c].to_numpy()
        if not len(a) or not len(b):continue
        u=mannwhitneyu(a,b,method='asymptotic').statistic
        growth_effects.append({'model':model,'feature':c,'positive_n':len(a),'negative_n':len(b),
                               'rank_biserial':2*u/(len(a)*len(b))-1})
save(pd.DataFrame(growth_effects),'growth_effects_same_cohort')
corrs=[g[cols].corr(method='spearman').to_numpy() for _,g in matched.groupby('model')]
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore',RuntimeWarning)
    med=np.nanmedian(np.stack(corrs),axis=0)
pd.DataFrame(med,index=cols,columns=cols).to_csv(OUT/'within_model_correlation.csv',encoding='utf-8-sig')
save(q('''SELECT model,count(*) AS rows,
    count(*) FILTER(WHERE smart_4_raw IS DISTINCT FROM smart_12_raw) AS different_rows
    FROM raw_values GROUP BY model'''),'start_stop_vs_power_exact')
save(q('''SELECT model,p.first_failure-d.date AS days_before,count(*) AS observed_disks,
    100.0*avg((smart_5_raw>0)::int) AS reallocated_gt0_pct,
    100.0*avg((smart_198_raw>0)::int) AS offline_gt0_pct
    FROM clean d JOIN disks p USING(serial_number,model)
    WHERE p.first_failure-d.date BETWEEN 0 AND 180
    GROUP BY model,days_before ORDER BY model,days_before'''),'trajectories')
save(q('''WITH f AS (
    SELECT d.serial_number,d.model,p.first_failure,
        min(d.date) FILTER(WHERE d.smart_5_raw>0 OR d.smart_198_raw>0) AS first_signal
    FROM clean d JOIN disks p USING(serial_number,model)
    WHERE p.first_failure IS NOT NULL
    GROUP BY d.serial_number,d.model,p.first_failure)
    SELECT *,first_failure-first_signal AS lead_days FROM f'''),'lead_times')

# Same eligible risk set for all rules, including availability of both 30-day deltas.
con.execute('''CREATE VIEW rule_set AS SELECT * FROM snapshots WHERE smart_5_raw IS NOT NULL
    AND smart_198_raw IS NOT NULL AND delta_smart_5_raw_30 IS NOT NULL AND delta_smart_198_raw_30 IS NOT NULL''')
rules={'재할당 또는 복구 불가 섹터 > 0':'(smart_5_raw>0 OR smart_198_raw>0)',
       '재할당 섹터 > 0':'smart_5_raw>0','복구 불가 섹터 > 0':'smart_198_raw>0',
       '손상 신호 + 최근 30일 증가':'(smart_5_raw>0 OR smart_198_raw>0) AND (delta_smart_5_raw_30>0 OR delta_smart_198_raw_30>0)'}
baseline=[]
for name,rule in rules.items():
    r=q(f'''SELECT count(*) AS evaluated_snapshots,count(DISTINCT date) AS months,
       sum(label_30) AS actual_positives,count(*) FILTER(WHERE {rule}) AS alerts,
       count(*) FILTER(WHERE ({rule}) AND label_30=1) AS tp,
       count(*) FILTER(WHERE ({rule}) AND label_30=0) AS fp FROM rule_set''').iloc[0].to_dict()
    r.update(rule=name,recall_pct=100*r['tp']/r['actual_positives'],
             precision_pct=100*r['tp']/r['alerts'] if r['alerts'] else np.nan,
             false_alert_share_pct=100*r['fp']/r['alerts'] if r['alerts'] else np.nan,
             monthly_alerts=r['alerts']/r['months'])
    baseline.append(r)
save(pd.DataFrame(baseline),'rule_baselines')
resets=[]
for c in ('smart_5_raw','smart_198_raw'):
    resets.append(q(f'''SELECT model,'{c}' AS feature,count({"delta_"+c+"_30"}) AS available,
       count(*) FILTER(WHERE {"delta_"+c+"_30"}<0) AS negative_deltas FROM snapshots GROUP BY model'''))
save(pd.concat(resets),'negative_deltas')
summary={'all_821_days':True,'models':20,'smart_columns':13,'raw_rows':manifest['rows'],
         'operations':['full quality','complete 30/60/90-day history counts','monthly future-30-day labels',
                       'same-model/calendar matched comparisons','failure trajectories','shared-cohort rule baselines'],
         'no_model_training':True}
(OUT/'analysis_manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('DETAILED ANALYSIS COMPLETE',flush=True)
