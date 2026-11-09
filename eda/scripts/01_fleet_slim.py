"""1차 추출: raw zip 9개에서 전 모델의 가벼운 열만 뽑아 분기별 Parquet으로 저장.

CSV를 디스크에 풀지 않고 zip 안에서 바로 읽는다 (전체 해제 시 약 95 GB).
출력: C:/hdd-failure-prediction/data/backblaze/fleet_slim/YYYY_Qn.parquet
"""
import sys
import time
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pv
import pyarrow.parquet as pq

RAW = Path("C:/Users/rhkdd/OneDrive/hdd-rul/data/raw")
OUT = Path("C:/hdd-failure-prediction/data/backblaze/fleet_slim")
OUT.mkdir(parents=True, exist_ok=True)

COLS = ["date", "serial_number", "model", "capacity_bytes", "failure", "datacenter"]
TYPES = {
    "date": pa.date32(),
    "serial_number": pa.string(),
    "model": pa.string(),
    "capacity_bytes": pa.int64(),
    "failure": pa.int8(),
    "datacenter": pa.string(),
}
SCHEMA = pa.schema([(c, TYPES[c]) for c in COLS])


def main(quarters):
    for zpath in sorted(RAW.glob("*.zip")):
        q = zpath.stem
        if quarters and q not in quarters:
            continue
        out = OUT / f"{q}.parquet"
        if out.exists():
            print(f"[skip] {q}", flush=True)
            continue
        t0 = time.time()
        tmp = out.with_suffix(".tmp")
        writer = pq.ParquetWriter(tmp, SCHEMA, compression="zstd")
        n_rows = 0
        with zipfile.ZipFile(zpath) as z:
            names = sorted(
                i.filename for i in z.infolist()
                if i.filename.endswith(".csv") and "__MACOSX" not in i.filename
            )
            for name in names:
                with z.open(name) as f:
                    t = pv.read_csv(
                        f,
                        convert_options=pv.ConvertOptions(
                            include_columns=COLS,
                            include_missing_columns=True,
                            column_types=TYPES,
                        ),
                    )
                writer.write_table(t.select(COLS).cast(SCHEMA))
                n_rows += t.num_rows
        writer.close()
        tmp.replace(out)
        print(f"[done] {q}: {len(names)} files, {n_rows:,} rows, {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main(set(sys.argv[1:]))
