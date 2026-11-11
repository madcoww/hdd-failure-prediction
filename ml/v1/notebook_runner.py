"""Notebook entry points. Training identity excludes alert thresholds."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
import train

DEFAULT = {
    "input_days":30,"horizon_days":30,"smart_columns":[5,187,188,197],
    "delta_days":[7,30],"negative_ratio":20,"seed":42,"n_jobs":2,
    "xgboost_device":"auto","lightgbm_device":"auto",
    "periods":{"train":["2024-04-01","2025-12-31"],
               "validation":["2026-01-01","2026-03-31"],
               "test":["2026-04-01","2026-06-30"]},
    "model_params":{
      "logistic_regression":{"C":1.0,"max_iter":1000},
      "random_forest":{"n_estimators":150,"max_depth":14,"min_samples_leaf":10},
      "xgboost":{"n_estimators":300,"max_depth":6,"learning_rate":.05,"subsample":.8,"colsample_bytree":.8},
      "lightgbm":{"n_estimators":300,"num_leaves":31,"learning_rate":.05,"subsample":.8,"colsample_bytree":.8}}
}
MODELS=list(DEFAULT["model_params"])
LABELS={"logistic_regression":"로지스틱 회귀","random_forest":"Random Forest",
        "xgboost":"XGBoost","lightgbm":"LightGBM"}


def canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))


def normalize(raw):
    cfg=deepcopy(raw)
    for key in ["input_days","horizon_days","negative_ratio","seed","n_jobs"]:
        if type(cfg.get(key)) is not int:
            raise ValueError(f"{key}는 정수로 입력하세요.")
    if min(cfg["input_days"],cfg["horizon_days"],cfg["negative_ratio"],cfg["n_jobs"])<1:
        raise ValueError("기간·정상 축소 비율·작업 수는 1 이상이어야 합니다.")
    for key in ["smart_columns","delta_days"]:
        values=cfg[key]
        if not values or len(values)!=len(set(values)) or any(type(i) is not int or i<1 for i in values):
            raise ValueError(f"{key}에는 중복 없는 양의 정수 목록을 입력하세요.")
    if max(cfg["delta_days"])>cfg["input_days"]:
        raise ValueError("변화량 기간은 입력 기간 이하로 설정하세요.")
    for key in ["xgboost_device","lightgbm_device"]:
        if cfg[key] not in ["auto","cpu"]:
            raise ValueError(f"{key}: auto 또는 cpu를 입력하세요.")
    if set(cfg["model_params"])!=set(MODELS):
        raise ValueError("비교 모델 4개의 설정을 모두 유지하세요.")
    cfg["splits"]={}
    previous_end=None
    for split in ["train","validation","test"]:
        start,end=map(pd.Timestamp,cfg["periods"][split])
        effective_end=end-pd.Timedelta(days=cfg["horizon_days"])
        if start>effective_end:
            raise ValueError(f"{split}: 예측 기간보다 긴 구간을 지정하세요.")
        if previous_end is not None and start<=previous_end:
            raise ValueError("학습·검증·평가 기간이 겹치면 안 됩니다.")
        cfg["splits"][split]=[start.date().isoformat(),effective_end.date().isoformat()]
        previous_end=end
    return cfg


def source_identity(source):
    source=Path(source).resolve(); stat=source.stat()
    return {"source":str(source),"source_size":stat.st_size,"source_mtime_ns":stat.st_mtime_ns}


def resolve_run(folder, source, cfg, mode):
    folder=Path(folder); source=Path(source)
    identity={"settings":cfg,**source_identity(source)}
    digest=hashlib.sha256(canonical(identity).encode()).hexdigest()[:16]
    destination=folder/"artifacts/experiments"/digest
    if mode=="train":
        con=train.duckdb.connect()
        end=con.read_parquet(str(source)).aggregate("max(date)").fetchall()[0][0]
        con.close()
        if pd.Timestamp(cfg["periods"]["test"][1])>pd.Timestamp(end):
            raise ValueError("평가 구간 끝이 원본 데이터 마지막 날짜를 넘습니다.")
        train.run_training(cfg,source,destination)
        train.write_json(destination/"experiment_identity.json",identity)
        return destination
    if mode!="evaluate":
        raise ValueError('MODE는 "evaluate" 또는 "train"으로 설정하세요.')
    identity_path=destination/"experiment_identity.json"
    if identity_path.exists():
        actual=json.loads(identity_path.read_text(encoding="utf-8"))
        status=json.loads((destination/"run_config.json").read_text(encoding="utf-8"))["status"]
        if canonical(actual)==canonical(identity) and status=="complete":
            return destination
    # Original artifacts predate the notebook. Reuse only the exact original setup.
    legacy=folder/"artifacts"
    if canonical(cfg)==canonical(normalize(DEFAULT)) and (legacy/"run_config.json").exists():
        run=json.loads((legacy/"run_config.json").read_text(encoding="utf-8"))
        if run["status"]=="complete" and all(run.get(k)==v for k,v in source_identity(source).items()):
            return legacy
    raise ValueError('현재 학습 설정과 일치하는 예측이 없습니다. 첫 셀의 MODE = "train"으로 바꾸고 모두 실행하세요. 경보 비율만 바꾸면 재학습 없이 evaluate로 실행할 수 있습니다.')


def evaluate_run(run, percentages, primary_percent, show_test=False):
    percentages=list(percentages)
    if not percentages or len(percentages)!=len(set(percentages)) or any(not 0<float(p)<=100 for p in percentages):
        raise ValueError("경보 비율은 0 초과~100 이하의 중복 없는 목록이어야 합니다.")
    if primary_percent not in percentages:
        raise ValueError("선택 기준 경보 비율을 ALERT_PERCENTAGES에도 넣어주세요.")
    run=Path(run); rows=[]; baseline=[]; chosen=None
    for split in (["validation","test"] if show_test else ["validation"]):
        key_hash=None
        for model in MODELS:
            frame=pd.read_parquet(run/f"predictions_{split}_{model}.parquet")
            if not np.isfinite(frame.risk_score).all():
                raise ValueError("예측 점수에 비정상 값이 있습니다.")
            digest=hashlib.sha256(pd.util.hash_pandas_object(frame[["serial_number","date","y"]],index=False).values.tobytes()).hexdigest()
            if key_hash is not None and digest!=key_hash:
                raise ValueError("모델별 평가 표본이 일치하지 않습니다.")
            if key_hash is None:
                bm=train.alert_metrics(frame,frame.rule.to_numpy(dtype=bool))
                baseline.append({"구간":split,"방식":"SMART 규칙",**friendly_metrics(bm),"원래 고장 비율(%)":100*float(frame.y.mean())})
            key_hash=digest
            ap=float(average_precision_score(frame.y,frame.risk_score))
            # Sort once per model, then change the daily budget without inference/training.
            rank=frame.assign(position=np.arange(len(frame))).sort_values(
                ["date","risk_score","serial_number"],ascending=[True,False,True],kind="stable")
            positions=rank.position.to_numpy()
            daily_rank=rank.groupby("date",sort=False).cumcount().to_numpy()
            daily_size=rank.groupby("date",sort=False).risk_score.transform("size").to_numpy()
            for percentage in percentages:
                mask=np.zeros(len(frame),dtype=bool)
                mask[positions[daily_rank<np.ceil(daily_size*float(percentage)/100)]]=True
                m=train.alert_metrics(frame,mask)
                rows.append({"구간":split,"모델":LABELS[model],"model_id":model,"경보 비율(%)":float(percentage),
                             "PR-AUC(AP)":ap,**friendly_metrics(m)})
        if split=="validation":
            candidates=[r for r in rows if r["구간"]=="validation" and r["경보 비율(%)"]==primary_percent]
            chosen=max(candidates,key=lambda r:(r["정밀도(%)"],r["PR-AUC(AP)"]))["model_id"]
    result=pd.DataFrame(rows); baseline=pd.DataFrame(baseline)
    return result,baseline,chosen


def friendly_metrics(m):
    return {"정밀도(%)":100*m["precision"],"재현율(%)":100*m["recall"],
            "고장 디스크 탐지율(%)":100*m["failure_disk_recall"],
            "일평균 경보 수":m["mean_daily_alerts"],"일평균 헛경보 수":m["mean_daily_false_alerts"],
            "경보 건수":m["alerts"],"실제 고장으로 이어진 경보":m["true_positive_rows"],
            "헛경보 건수":m["false_alerts"]}


def save_evaluation(run, table, baseline, selected, percentages, primary_percent, show_test):
    cfg={"percentages":list(percentages),"primary_percent":primary_percent,"show_test":show_test}
    digest=hashlib.sha256(canonical(cfg).encode()).hexdigest()[:12]
    out=Path(run)/"notebook_evaluation"/digest; out.mkdir(parents=True,exist_ok=True)
    table.to_csv(out/"comparison.csv",index=False,encoding="utf-8-sig")
    baseline.to_csv(out/"smart_baseline.csv",index=False,encoding="utf-8-sig")
    train.write_json(out/"evaluation_config.json",{**cfg,"selected_on_validation":selected})
    return out
