"""Small fixtures check calendar windows, censoring, and daily alert budgets."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import duckdb
import numpy as np
import pandas as pd
from train import prepare, top_mask, alert_metrics


class TrainingChecks(unittest.TestCase):
    def test_temporal_features_and_labels(self):
        records=[]
        for group, anchor in enumerate(["2025-11-01","2026-02-01","2026-05-01"]):
            anchor=pd.Timestamp(anchor)
            for kind in ["failed","normal"]:
                for offset in range(-40,41):
                    if kind=="normal" and offset==-7:
                        continue
                    value=offset+100 if offset<=0 else 10000
                    records.append(dict(date=anchor+pd.Timedelta(days=offset),
                        serial_number=f"{group}_{kind}",model="ST12000NM0008",
                        failure=int(kind=="failed" and offset==20),
                        **{f"smart_{i}_raw":value for i in [5,187,188,197,198]}))
        with TemporaryDirectory() as tmp:
            path=Path(tmp); source=path/"fixture.parquet"
            pd.DataFrame(records).to_parquet(source,index=False)
            con=duckdb.connect()
            prepare(con,source,path)
            row=con.sql("select * from features where serial_number='0_failed' and date='2025-11-01'").df().iloc[0]
            self.assertEqual(row.y,1)
            self.assertEqual(row.smart_5_delta30,30)
            self.assertAlmostEqual(row.smart_5_mean30,85.5)
            self.assertEqual(row.smart_5_max30,100) # no future spike
            missing=con.sql("select smart_5_delta7 from features where serial_number='0_normal' and date='2025-11-01'").fetchall()[0][0]
            self.assertIsNone(missing) # missing calendar date is not previous 7th row
            self.assertEqual(con.sql("select count(*) from features where serial_number='0_failed' and date>='2025-11-21'").fetchall()[0][0],0)
            self.assertEqual(con.sql("select count(*) from features where serial_number='0_normal' and date>'2025-11-11'").fetchall()[0][0],0)
            self.assertEqual(con.sql("select min(date) from features where serial_number='0_normal'").fetchall()[0][0].isoformat(),"2025-10-22")
            # Changing notebook settings must change real labels/windows/columns.
            prepare(con,source,path,{"input_days":7,"horizon_days":7,
                "smart_columns":[5,188],"delta_days":[3,7]})
            custom=con.sql("select * from features where serial_number='0_failed' and date='2025-11-01'").df().iloc[0]
            self.assertEqual(custom.y,0) # failure is 20 days away, outside 7-day horizon
            self.assertAlmostEqual(custom.smart_5_mean7,97)
            self.assertEqual(custom.smart_5_delta3,3)
            self.assertNotIn("smart_187_current",custom.index)
            self.assertNotIn("smart_5_mean30",custom.index)
            self.assertEqual(con.sql("select y from features where serial_number='0_failed' and date='2025-11-16'").fetchall()[0][0],1)
            con.close()

    def test_alert_budget_per_day_and_unique_disks(self):
        frame=pd.DataFrame({"date":pd.to_datetime(["2026-01-01"]*100+["2026-01-02"]*100),
                            "serial_number":[f"disk{i:03d}" for i in range(100)]*2,
                            "y":[1]+[0]*99+[1]+[0]*99})
        scores=np.tile(np.arange(100)[::-1],2)
        mask=top_mask(frame,scores)
        self.assertEqual(int(mask.sum()),2)
        self.assertEqual(alert_metrics(frame,mask)["caught_disks"],1)
        self.assertEqual(alert_metrics(frame,mask)["precision"],1)
        tied=top_mask(frame,np.zeros(200))
        self.assertEqual(frame.loc[tied,"serial_number"].tolist(),["disk000","disk000"])
        self.assertEqual(int(top_mask(frame,scores,fraction=.10).sum()),20)

    def test_notebook_cache_identity_and_period_boundaries(self):
        from notebook_runner import DEFAULT, normalize, resolve_run
        from copy import deepcopy
        cfg=normalize(DEFAULT)
        self.assertEqual(cfg["splits"]["train"][1],"2025-12-01")
        altered=deepcopy(DEFAULT); altered["horizon_days"]=7
        self.assertEqual(normalize(altered)["splits"]["train"][1],"2025-12-24")
        altered=deepcopy(DEFAULT); altered["input_days"]=7
        with self.assertRaises(ValueError):
            normalize(altered) # 30-day delta exceeds 7-day history
        with TemporaryDirectory() as tmp:
            source=Path(tmp)/"dummy.parquet"; source.write_bytes(b"dummy")
            with self.assertRaisesRegex(ValueError,"MODE"):
                resolve_run(Path(tmp),source,cfg,"evaluate")


if __name__=="__main__":
    unittest.main()
