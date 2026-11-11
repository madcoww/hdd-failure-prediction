"""고장 수 상위 5개 모델이 SMART raw 열을 얼마나 기록하는지 전 기간 기준으로 확인.

raw zip 9개에서 15일 간격으로 하루치 CSV를 골라(약 55일) 전체 열을 읽고,
모델별로 smart_*_raw 열의 '값이 있는 행 비율'을 계산한다.
출력: C:/hdd-failure-prediction/data/backblaze/summary/smart_coverage_top5.csv  (model, column, nonnull_pct, n_days)
"""
import os
import sys
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow.csv as pv
import pyarrow.compute as pc

sys.stdout.reconfigure(encoding="utf-8")

RAW = Path(os.environ.get("HDD_RAW_DIR", "C:/Users/rhkdd/OneDrive/hdd-rul/data/raw"))  # 원본 zip 폴더
OUT = Path("C:/hdd-failure-prediction/data/backblaze/summary/smart_coverage_top5.csv")
TOP5 = [
    "HGST HUH721212ALN604",
    "ST12000NM0008",
    "TOSHIBA MG07ACA14TA",
    "TOSHIBA MG08ACA16TA",
    "HGST HUH721212ALE604",
]
STEP = 15  # 15일마다 하루

rows = {}  # (model, col) -> [nonnull, total]
n_days = 0
for zpath in sorted(RAW.glob("*.zip")):
    with zipfile.ZipFile(zpath) as z:
        names = sorted(
            i.filename for i in z.infolist()
            if i.filename.endswith(".csv") and "__MACOSX" not in i.filename
        )
        for name in names[::STEP]:
            with z.open(name) as f:
                t = pv.read_csv(f)
            t = t.filter(pc.is_in(t["model"], value_set=__import__("pyarrow").array(TOP5)))
            df = t.to_pandas()
            smart = [c for c in df.columns if c.startswith("smart_") and c.endswith("_raw")]
            for m, g in df.groupby("model"):
                nn = g[smart].notna().sum()
                for c in smart:
                    a = rows.setdefault((m, c), [0, 0])
                    a[0] += int(nn[c])
                    a[1] += len(g)
            n_days += 1
    print(f"[done] {zpath.stem}", flush=True)

out = pd.DataFrame(
    [(m, c, round(100 * a / b, 2)) for (m, c), (a, b) in rows.items()],
    columns=["model", "column", "nonnull_pct"],
)
out["n_days"] = n_days
out.to_csv(OUT, index=False, encoding="utf-8")
print(f"saved {OUT} ({n_days} days)")
