"""ST12000NM0008 first comparison. Run from any directory: python ml/v1/train.py."""
from __future__ import annotations

import argparse
import gc
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import time
import warnings

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEED = 42
SPLITS = {"train": ("2024-04-01", "2025-12-01"),
          "validation": ("2026-01-01", "2026-03-01"),
          "test": ("2026-04-01", "2026-05-31")}


def log(message):
    print(time.strftime("%H:%M:%S"), message, flush=True)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def prepare(con, source, out, settings=None):
    """Use DuckDB disk tables and bounded memory; no future values in inputs."""
    cfg = settings or {}
    history = int(cfg.get("input_days", 30))
    horizon = int(cfg.get("horizon_days", 30))
    selected = list(cfg.get("smart_columns", [5,187,188,197]))
    delta_days = list(cfg.get("delta_days", [7,30]))
    splits = cfg.get("splits", SPLITS)
    if history < 1 or horizon < 1 or not selected or not delta_days:
        raise ValueError("Periods, SMART columns, and delta periods must be nonempty and positive")
    if any(type(i) is not int or not 1 <= i <= 255 for i in selected):
        raise ValueError("SMART IDs must be integers between 1 and 255")
    if any(type(d) is not int or not 1 <= d <= history for d in delta_days):
        raise ValueError("Delta periods must be positive integers <= input_days")
    rolling_cols = [i for i in selected if i != 188]
    con.read_parquet(str(source)).create_view("raw_input", replace=True)
    con.execute("create or replace view raw as select * replace (date::date as date) from raw_input")
    if con.sql("select count(*) from (select serial_number,date from raw group by all having count(*)>1)").fetchall()[0][0]:
        raise ValueError("Duplicate serial/date keys: resolve explicitly before training")
    if con.sql("select count(*) from raw where serial_number is null or date is null or failure is null or failure not in (0,1) or model != 'ST12000NM0008'").fetchall()[0][0]:
        raise ValueError("Invalid identifiers, labels, or model")
    con.execute("""create or replace table lifetimes as
        select serial_number,min(date) first_date,max(date) last_date,
          min(date) filter(where failure=1) failure_date from raw group by 1""")
    cols = sorted(set(selected) | {5,187,197,198})
    available = {r[0] for r in con.sql("describe raw").fetchall()}
    missing = [f"smart_{i}_raw" for i in cols if f"smart_{i}_raw" not in available]
    if missing:
        raise ValueError(f"Columns absent from source: {missing}")
    expressions = ",".join(f"case when smart_{i}_raw>=0 then smart_{i}_raw end as s{i}" for i in cols)
    con.execute(f"""create or replace table base as select r.serial_number,r.date,r.failure,
       l.first_date,l.last_date,l.failure_date,{expressions}
       from raw r join lifetimes l using(serial_number)
       where l.failure_date is null or r.date<=l.failure_date""")
    audit = con.sql("""select count(*) rows,count(distinct serial_number) disks,
       count(*) filter(where failure=1) failure_rows from raw""").df().iloc[0].to_dict()
    audit["quality_by_column"] = {}
    for i in cols:
        audit["quality_by_column"][str(i)] = con.sql(f"""select
          count(*) filter(where smart_{i}_raw is null) null_rows,
          count(*) filter(where smart_{i}_raw<0) negative_rows,
          min(smart_{i}_raw) minimum,max(smart_{i}_raw) maximum,
          count(distinct smart_{i}_raw) distinct_values from raw""").df().iloc[0].to_dict()
    audit["counter_decreases"] = {}
    for i in rolling_cols:
        audit["counter_decreases"][str(i)] = con.sql(f"""select count(*) from
          (select s{i},lag(s{i}) over(partition by serial_number order by date) prev from base)
          where s{i}<prev""").fetchall()[0][0]
    feature_sql = []
    for i in rolling_cols:
        feature_sql += [f"b.s{i} as smart_{i}_current",
                        f"case when b.s{i} is null then null else (b.s{i}>0)::integer end as smart_{i}_positive",
                        f"b.avg{i} as smart_{i}_mean{history}", f"b.max{i} as smart_{i}_max{history}",
                        f"b.n{i} as smart_{i}_observations{history}"]
        for days in delta_days:
            alias = f"p{days}"
            feature_sql.append(f"case when b.s{i}>={alias}.s{i} then b.s{i}-{alias}.s{i} end as smart_{i}_delta{days}")
    if 188 in selected:
        feature_sql += ["b.s188 as smart_188_current", "case when b.s188 is null then null else (b.s188>0)::integer end as smart_188_positive"]
    windows = ",".join(f"avg(s{i}) over w as avg{i},max(s{i}) over w as max{i},count(s{i}) over w as n{i}" for i in rolling_cols)
    rolling_select = f"*,{windows}" if windows else "*"
    joins = "\n".join(f"left join base p{d} on p{d}.serial_number=b.serial_number and p{d}.date=b.date-{d}" for d in delta_days) if rolling_cols else ""
    # RANGE uses calendar dates; past and present only. Delta joins use exact dates.
    con.execute(f"""create or replace table features as
      with rolling as (select {rolling_select} from base
        window w as(partition by serial_number order by date range between interval {history-1} day preceding and current row))
      select b.serial_number,b.date,b.failure_date,
        case when b.failure_date>b.date and b.failure_date<=b.date+{horizon} then 1 else 0 end::tinyint as y,
        ((coalesce(b.s5,0)>0) or (coalesce(b.s187,0)>0) or
         (coalesce(b.s197,0)>0) or (coalesce(b.s198,0)>0))::tinyint as rule,
        {','.join(feature_sql)}
      from rolling b
      {joins}
      where b.date>=b.first_date+{history} and b.failure=0
        and (b.failure_date is null or b.date<b.failure_date)
        and ((b.failure_date>b.date and b.failure_date<=b.date+{horizon}) or b.last_date>=b.date+{horizon})
    """)
    audit["exclusions"] = con.sql(f"""select
      count(*) filter(where failure_date is not null and date>=failure_date) failure_day_or_after,
      count(*) filter(where date<first_date+{history}) insufficient_initial_history,
      count(*) filter(where failure=0 and date>=first_date+{history} and
        (failure_date is null or date<failure_date) and last_date<date+{horizon} and
        not coalesce(failure_date>date and failure_date<=date+{horizon},false)) unconfirmed_future
      from raw join lifetimes using(serial_number)""").df().iloc[0].to_dict()
    audit["exclusion_note"] = "Initial history and failure-day counts may overlap; features contain only eligible rows. Split boundaries additionally exclude rows."
    audit["splits"] = {}
    for split, (start, end) in splits.items():
        audit["splits"][split] = con.sql("""select count(*) rows,sum(y) positives,
          count(distinct serial_number) disks,count(distinct serial_number) filter(where y=1) positive_disks,
          min(date) first_date,max(date) last_date from features where date between ? and ?""", params=[start,end]).df().iloc[0].to_dict()
        if not audit["splits"][split]["positives"]:
            raise ValueError(f"No positive examples in {split}")
    write_json(out/"data_audit.json", audit)
    log(f"Data audit: {audit['splits']}")
    return audit


def top_mask(frame, scores, budget=None, fraction=.01):
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be greater than 0 and at most 1")
    ranked = pd.DataFrame({"date":frame.date.to_numpy(), "serial_number":frame.serial_number.to_numpy(),
                           "score":scores, "position":np.arange(len(frame))})
    ranked = ranked.sort_values(["date","score","serial_number"],ascending=[True,False,True],kind="stable")
    rank = ranked.groupby("date",sort=False).cumcount().to_numpy()
    if budget is None:
        limit = np.ceil(ranked.groupby("date",sort=False).score.transform("size").to_numpy()*fraction)
    else:
        limit = budget
    mask = np.zeros(len(frame),dtype=bool)
    mask[ranked.position.to_numpy()[rank<limit]] = True
    return mask


def alert_metrics(frame, mask):
    y = frame.y.to_numpy(dtype=bool)
    tp = int(np.sum(mask & y)); alerts = int(mask.sum()); positives = int(y.sum())
    positive_disks = frame.loc[y,"serial_number"].nunique()
    caught = frame.loc[mask & y,"serial_number"].nunique()
    counts = frame.assign(alert=mask).groupby("date").alert.sum()
    month_unique = frame.loc[mask].assign(month=lambda x:x.date.dt.to_period("M").astype(str)).groupby("month").serial_number.nunique()
    return {"precision":tp/alerts if alerts else 0., "recall":tp/positives if positives else 0.,
            "failure_disk_recall":caught/positive_disks if positive_disks else 0.,
            "alerts":alerts,"true_positive_rows":tp,"positive_rows":positives,
            "positive_disks":int(positive_disks),"caught_disks":int(caught),
            "false_alerts":alerts-tp,"mean_daily_false_alerts":(alerts-tp)/len(counts),
            "mean_daily_alerts":float(counts.mean()),"monthly_unique_alert_disks":month_unique.to_dict()}


def evaluate(name, split, frame, scores, seconds, device, budget, out):
    metrics = {"model":name,"split":split,"training_seconds":seconds,"device":device,
               "average_precision":float(average_precision_score(frame.y,scores)),
               "top_1pct":alert_metrics(frame,top_mask(frame,scores)),
               "rule_budget":alert_metrics(frame,top_mask(frame,scores,budget))}
    predicted = frame[["serial_number","date","failure_date","y","rule"]].copy()
    predicted["risk_score"] = scores.astype(np.float32)
    predicted["top_1pct_alert"] = top_mask(frame,scores)
    predicted.to_parquet(out/f"predictions_{split}_{name}.parquet",index=False)
    return metrics


def get_models(settings=None):
    cfg = settings or {}
    seed = int(cfg.get("seed", SEED))
    jobs = int(cfg.get("n_jobs", 2))
    rng=np.random.default_rng(SEED)
    tiny=rng.random((128,4)).astype(np.float32); target=np.tile([0,1],64)
    device_x="cpu"; device_l="cpu"
    try:
        if cfg.get("xgboost_device", "auto") == "cpu":
            raise RuntimeError("CPU selected in settings")
        probe=XGBClassifier(n_estimators=2,max_depth=2,tree_method="hist",device="cuda",n_jobs=2)
        probe.fit(tiny,target)
        actual=json.loads(probe.get_booster().save_config())["learner"]["generic_param"]["device"]
        if actual.startswith("cuda"): device_x="cuda"
    except Exception as exc:
        log(f"XGBoost GPU unavailable: {exc}")
    try:
        if cfg.get("lightgbm_device", "auto") == "cpu":
            raise RuntimeError("CPU selected in settings")
        probe=LGBMClassifier(n_estimators=2,device_type="gpu",verbosity=-1,n_jobs=2,min_child_samples=2)
        probe.fit(tiny,target)
        device_l="gpu"
    except Exception as exc:
        log(f"LightGBM GPU unavailable: {exc}")
    log(f"Devices: XGBoost={device_x}, LightGBM={device_l}")
    models = [
      ("logistic_regression",make_pipeline(FunctionTransformer(np.log1p),StandardScaler(),
          LogisticRegression(max_iter=1000,random_state=seed)),"cpu"),
      ("random_forest",RandomForestClassifier(n_estimators=150,max_depth=14,min_samples_leaf=10,
          n_jobs=jobs,random_state=seed),"cpu"),
      ("xgboost",XGBClassifier(n_estimators=300,max_depth=6,learning_rate=.05,subsample=.8,
          colsample_bytree=.8,tree_method="hist",device=device_x,max_bin=255,
          eval_metric="logloss",n_jobs=jobs,random_state=seed),device_x),
      ("lightgbm",LGBMClassifier(n_estimators=300,num_leaves=31,learning_rate=.05,
          subsample=.8,subsample_freq=1,colsample_bytree=.8,device_type=device_l,
          max_bin=255,n_jobs=jobs,random_state=seed,verbosity=-1),device_l)]
    overrides = cfg.get("model_params", {})
    for name, model, _ in models:
        params = overrides.get(name, {})
        if name == "logistic_regression":
            model.named_steps["logisticregression"].set_params(**params)
        else:
            model.set_params(**params)
    return models


def save_report(out, results, audit, winner, budget, settings=None):
    cfg = settings or {}
    horizon = cfg.get("horizon_days", 30)
    ratio = cfg.get("negative_ratio", 20)
    write_json(out/"metrics.json",{"selected_on_validation":winner,"fixed_rule_budget":budget,"results":results})
    records=[]
    for r in results:
        m=r["top_1pct"]
        records.append({"split":r["split"],"model":r["model"],"average_precision":r["average_precision"],
          "precision_top1pct":m["precision"],"recall_top1pct":m["recall"],
          "disk_recall_top1pct":m["failure_disk_recall"],"training_seconds":r["training_seconds"],"device":r["device"]})
    pd.DataFrame(records).to_csv(out/"comparison.csv",index=False,encoding="utf-8-sig")
    lines=["# ML v1 첫 비교 결과", "", f"검증 구간에서 선택한 모델: **{winner}**", "",
      "상위 1% 정밀도를 우선하고 PR-AUC(AP)를 보조 기준으로 선택했다. 최종 평가로 다시 선택하지 않았다.","",
      "| 구간 | 모델 | PR-AUC(AP) | 상위 1% 정밀도 | 상위 1% 재현율 | 고장 디스크 탐지율 | 학습 초 | 장치 |",
      "|---|---|---:|---:|---:|---:|---:|---|"]
    for r in records:
        lines.append(f"| {r['split']} | {r['model']} | {r['average_precision']:.4f} | {r['precision_top1pct']:.2%} | {r['recall_top1pct']:.2%} | {r['disk_recall_top1pct']:.2%} | {r['training_seconds']:.1f} | {r['device']} |")
    lines += ["", "- ST12000NM0008 한 제품, 일별 표본 기준의 초기 비교다. 대규모 튜닝은 하지 않았다.",
      f"- 음성은 미래 {horizon}일 관측이 확인되는 기록만 사용했다. 고장일·고장 이후 입력은 제외했다.",
      "- 동일 디스크가 과거 학습과 미래 평가에 등장할 수 있다. 새 제품·새 디스크 전용 평가가 아니다.",
      f"- 학습 정상 행만 최대 {ratio}:1로 축소했다. 검증·평가 비율은 유지했다. 출력 점수는 보정된 고장 확률이 아니다.",
      f"- 검증 규칙의 일평균 경보 수를 올림한 공통 예산: 매일 {budget}개. metrics.json의 rule_budget에서 모델별 결과를 확인할 수 있다.",
      "- SMART 규칙의 원래 경보 수와 성능은 baseline.json에 있다. 경보량이 다르면 상위 1% 결과와 직접 우열을 비교하지 않는다.",
      "- 실제 교체·고장 회피·비용 절감은 검증하지 않았다. 경보 반복은 월별 고유 디스크 수와 별도로 집계했다.",
      "", "입력·제외 수·기간: data_audit.json / 설정·버전: run_config.json / 예측: predictions_*.parquet"]
    (out/"RESULTS.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def run_training(settings, source, out):
    cfg = settings
    splits = cfg.get("splits", SPLITS)
    seed = int(cfg.get("seed", SEED))
    ratio = int(cfg.get("negative_ratio", 20))
    source = Path(source).resolve()
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    write_json(out/"run_config.json", {"status":"running", "settings":cfg})
    warnings.simplefilter("error",ConvergenceWarning)
    con=duckdb.connect(str(out/"features.duckdb"))
    con.execute("set memory_limit='768MB'"); con.execute("set threads=2")
    con.execute("set preserve_insertion_order=false")
    con.execute("set temp_directory=?",[str(out/"duckdb_tmp")])
    write_json(out/"experiment_settings.json", cfg)
    log("Preparing calendar-based features; bounded RAM, full period")
    audit=prepare(con,source,out,cfg)
    columns=[r[0] for r in con.sql("describe features").fetchall() if r[0].startswith("smart_")]
    a,b=splits["train"]
    npos=con.sql("select count(*) from features where date between ? and ? and y=1",params=[a,b]).fetchall()[0][0]
    log(f"Training sample: all {npos} positives, up to {npos*ratio} negatives")
    train=con.sql(f"""with eligible as(select * from features where date between ? and ?),
      negatives as(select * from eligible where y=0 order by hash(serial_number,date,{seed}) limit ?)
      select * from eligible where y=1 union all select * from negatives""",params=[a,b,npos*ratio]).df()
    train=train.sample(frac=1,random_state=seed).reset_index(drop=True)
    y=train.y.to_numpy()
    imputer=SimpleImputer(strategy="median",add_indicator=True,keep_empty_features=True)
    X=imputer.fit_transform(train[columns].to_numpy(dtype=np.float32)).astype(np.float32)
    joblib.dump(imputer,out/"imputer.joblib")
    write_json(out/"feature_names.json",columns)
    train[["serial_number","date","y"]].to_parquet(out/"training_keys.parquet",index=False)
    del train; gc.collect()
    va,vb=splits["validation"]
    budget=math.ceil(con.sql("""select avg(n) from (select date,sum(rule) n from features
      where date between ? and ? group by date)""",params=[va,vb]).fetchall()[0][0])
    baselines={}
    for split in ["validation","test"]:
        a,b=splits[split]
        frame=con.sql("select serial_number,date,y,rule from features where date between ? and ? order by date,serial_number",params=[a,b]).df()
        baselines[split]=alert_metrics(frame,frame.rule.to_numpy(dtype=bool))
        del frame; gc.collect()
    write_json(out/"baseline.json",baselines)
    models=get_models(cfg)
    write_json(out/"run_config.json",{"status":"running","seed":seed,"splits":splits,
      "source":str(source),"source_size":source.stat().st_size,
      "source_mtime_ns":source.stat().st_mtime_ns,"input_days":cfg.get("input_days",30),"horizon_days":cfg.get("horizon_days",30),
      "train_positive_rows":int(npos),"train_rows":len(y),"negative_ratio_max":ratio,
      "features":columns,"packages":{p:importlib.metadata.version(p) for p in
        ["scikit-learn","xgboost","lightgbm","duckdb","pandas","numpy","joblib"]},
      "python":platform.python_version(),"models":{name:{"device":device,"params":str(model.get_params())} for name,model,device in models}})
    results=[]; times={}
    # Compare all four on validation before opening final test predictions.
    for name,model,device in models:
        log(f"Training {name} on {device}"); start=time.perf_counter()
        model.fit(X,y)
        times[name]=time.perf_counter()-start
        joblib.dump(model,out/f"{name}.joblib")
        a,b=splits["validation"]
        frame=con.sql("select * from features where date between ? and ? order by date,serial_number",params=[a,b]).df()
        inp=imputer.transform(frame[columns].to_numpy(dtype=np.float32)).astype(np.float32)
        scores=model.predict_proba(inp)[:,1]
        metrics=evaluate(name,"validation",frame,scores,times[name],device,budget,out)
        results.append(metrics)
        log(f"{name}: AP={metrics['average_precision']:.4f}, precision@1%={metrics['top_1pct']['precision']:.4f}, train={times[name]:.1f}s")
        del frame,inp,scores; gc.collect()
        write_json(out/"validation_progress.json",results)
    winner=max(results,key=lambda r:(r["top_1pct"]["precision"],r["average_precision"]))["model"]
    write_json(out/"selected_model.json",{"name":winner,"selection_data":"validation","frozen_before_test":True})
    log(f"Selected using validation only: {winner}")
    del X,y; gc.collect()
    for name,model,device in models:
        a,b=splits["test"]
        frame=con.sql("select * from features where date between ? and ? order by date,serial_number",params=[a,b]).df()
        inp=imputer.transform(frame[columns].to_numpy(dtype=np.float32)).astype(np.float32)
        scores=model.predict_proba(inp)[:,1]
        metrics=evaluate(name,"test",frame,scores,times[name],device,budget,out)
        results.append(metrics)
        log(f"TEST {name}: AP={metrics['average_precision']:.4f}, precision@1%={metrics['top_1pct']['precision']:.4f}")
        del frame,inp,scores; gc.collect()
    save_report(out,results,audit,winner,budget,cfg)
    cfg=json.loads((out/"run_config.json").read_text(encoding="utf-8")); cfg["status"]="complete"
    write_json(out/"run_config.json",cfg)
    con.close()
    log(f"Complete: {out/'RESULTS.md'}")
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--data",type=Path,default=ROOT/"data/backblaze/merged/st12000nm0008_2024Q2-2026Q2.parquet")
    parser.add_argument("--output",type=Path,default=HERE/"artifacts")
    parser.add_argument("--config",type=Path,help="JSON configuration; notebook is the easier interface")
    args=parser.parse_args()
    settings=json.loads(args.config.read_text(encoding="utf-8")) if args.config else {}
    run_training(settings,args.data,args.output)


if __name__=="__main__":
    main()
