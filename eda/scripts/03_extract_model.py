"""2차 추출: 선정한 모델 1종만 raw zip에서 전체 열(메타 + SMART raw)로 뽑는다.

사용: python 03_extract_model.py <MODEL>
출력: C:/hdd-failure-prediction/data/backblaze/<model>/YYYY_Qn.parquet (분기마다 열 구성이 다를 수 있어 분기별 저장)
"""
import sys
import time
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pv
import pyarrow.parquet as pq

RAW = Path("C:/Users/rhkdd/OneDrive/hdd-rul/data/raw")
META = ["date", "serial_number", "model", "capacity_bytes", "failure",
        "datacenter", "cluster_id", "vault_id", "pod_id", "pod_slot_num", "is_legacy_format"]


def main(model):
    out_dir = Path("C:/hdd-failure-prediction/data/backblaze") / model.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    for zpath in sorted(RAW.glob("*.zip")):
        q = zpath.stem
        out = out_dir / f"{q}.parquet"
        if out.exists():
            print(f"[skip] {q}", flush=True)
            continue
        t0 = time.time()
        tables = []
        with zipfile.ZipFile(zpath) as z:
            names = sorted(
                i.filename for i in z.infolist()
                if i.filename.endswith(".csv") and "__MACOSX" not in i.filename
            )
            for name in names:
                with z.open(name) as f:
                    header = f.readline().decode().strip().split(",")
                keep = [c for c in header if c in META or c.endswith("_raw")]
                types = {c: pa.float64() for c in keep if c.endswith("_raw")}
                types.update({"date": pa.date32(), "serial_number": pa.string(), "model": pa.string(),
                              "capacity_bytes": pa.int64(), "failure": pa.int8(), "datacenter": pa.string()})
                with z.open(name) as f:
                    t = pv.read_csv(f, convert_options=pv.ConvertOptions(
                        include_columns=keep, column_types={k: v for k, v in types.items() if k in keep}))
                tables.append(t.filter(pc.equal(t["model"], model)))
        t = pa.concat_tables(tables, promote_options="permissive")
        # 이 모델에서 전부 비어 있는 열은 버린다
        t = t.select([c for c in t.column_names if t[c].null_count < t.num_rows])
        pq.write_table(t, out, compression="zstd")
        print(f"[done] {q}: {t.num_rows:,} rows, {t.num_columns} cols, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
