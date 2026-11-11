"""Report full-period presence separately from the old sample-based reports."""
from pathlib import Path
import json
import pandas as pd

EDA=Path(__file__).resolve().parents[1]
OUT=EDA/'analysis/full_column_check'
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
assert manifest['days_checked']==manifest['days_expected']==821
summary=pd.read_csv(OUT/'top20_common_columns.csv')
detail=pd.read_parquet(OUT/'model_smart_presence.parquet')
top20=pd.read_csv(EDA/'analysis/v2/hdd_model_cases.csv').head(20).model.tolist()
sample=pd.read_csv(EDA/'analysis/v2/hdd_model_smart_coverage.csv').set_index('model')
names={1:'읽기 오류 관련 지표',3:'모터 회전 시작 시간',4:'회전 시작·정지 횟수',5:'재할당 섹터 수',
       7:'헤드 탐색 오류 관련 지표',9:'누적 가동 시간',10:'회전 재시도 횟수',12:'전원 인가 횟수',
       192:'전원 차단·헤드 회수 관련 지표',193:'헤드 로드·언로드 횟수',194:'온도',
       198:'오프라인 복구 불가 섹터 수',199:'인터페이스 CRC 오류'}
common=summary[summary.models_with_values.eq(20)]
stable=summary[summary.models_coverage_ge99.eq(20)]
previous={c for c in sample if c.startswith('smart_') and sample.loc[top20,c].ge(99).all()}
current=set(stable.column)
lines=['# 상위 20종의 공통 SMART — 전체 821일 확인', '',
       f"범위: {manifest['scope']}. **821/821일**을 확인했으며 97종 전체의 **{manifest['raw_rows_checked']:,}행**을 읽었다. 상위 20종과 HDD 75종 결과를 따로 집계했다.", '',
       'SMART raw 값의 존재 여부만 집계했다. 0도 기록된 값이며, 빈 값·NaN은 미기록으로 집계했다. 값의 크기나 예측력을 분석하지 않았다.', '',
       '## 상위 20종 모두에서 실제 기록값이 확인된 컬럼', '',
       '| 컬럼 | 의미 | 기록한 모델 | 매 관측일 기록한 모델 | 모델별 최소 행 기록률 |',
       '|---|---|---:|---:|---:|']
for r in common.itertuples():
    ident=int(r.column.split('_')[1])
    lines.append(f'| `{r.column}` | {names.get(ident,"SMART 지표 "+str(ident))} | {int(r.models_with_values)}/20 | {int(r.models_with_values_each_day)}/20 | {r.min_nonnull_pct:.4f}% |')
lines.extend(['',f'전체 20종에서 기록값이 있는 공통 컬럼은 **{len(common)}개**이며, 각 모델에서 행 기록률이 99% 이상인 공통 컬럼은 **{len(stable)}개**다.', '',
              '## 18일 표본과의 비교', '',f'- 99% 기준 후보 수: 기존 표본 {len(previous)}개 → 전 기간 {len(current)}개.',
              f'- 전 기간 확인 후 제외된 후보: {", ".join(sorted(previous-current)) or "없음"}.',
              f'- 전 기간 확인 후 추가된 후보: {", ".join(sorted(current-previous)) or "없음"}.','',
              '## 해석', '',
              '- ‘기록한 모델’은 전체 기간에 한 번이라도 결측이 아닌 값이 있었던 모델 수다.',
              '- ‘매 관측일 기록한 모델’은 그 모델의 행이 존재하는 모든 날짜에 해당 지표의 값이 한 행 이상 있었던 모델 수다. 매 행 100% 기록을 뜻하지 않는다.',
              '- ‘모델별 최소 행 기록률’은 20종 각각의 비결측 행 비율 중 최솟값이다. 미기록 날짜의 행도 분모에 포함한다.',
              '- 기본 정보 컬럼은 SMART 표와 별개다. 이 표는 SMART raw 컬럼만 대상으로 한다.',
              '- 같은 이름의 컬럼이 있다는 사실과 의미·단위가 호환되거나 고장 예측에 유용하다는 것은 별개다.',
              '- 기존 eda_v2_87%.ipynb의 18일 그림은 이 실행으로 변경하지 않았다. 그 그림은 표본 결과이며, 전수 결과는 이 폴더의 별도 CSV가 근거다.', '',
              '재현: `scripts/07_full_smart_presence.py` → `scripts/08_report_full_smart_presence.py`. 일별 결과·스키마와 전체 검사 날짜는 이 폴더에 보존한다.'])
(OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('\n'.join(lines[:len(common)+12]))
print('Changed candidates:', sorted(previous-current), sorted(current-previous))
