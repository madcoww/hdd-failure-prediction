"""Create the HDD fleet EDA notebook. Run from eda/; no model training."""
from pathlib import Path
import nbformat as nbf

EDA = Path(__file__).resolve().parents[2]
cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(s.strip()))
def code(s): cells.append(nbf.v4.new_code_cell(s.strip()))

md(r"""
# HDD 고장 예측 EDA v2 — 여러 HDD 모델을 위한 데이터 정리·컬럼 후보 선정

| 항목 | 내용 |
|---|---|
| 서비스 목표 | 디스크별 **향후 30일 내 고장 위험**으로 교체 우선순위를 정하고, SMART 규칙보다 헛교체를 줄인다 |
| 분석 대상 | 보유 데이터에서 SSD·DELLBOSS VD를 제외한 HDD 모델 전체 |
| 이번 범위 | **① HDD 데이터 품질·고장 사례 확인 ② SMART 기록 현황·의미를 검토해 컬럼 후보 선정** |
| 전체 기록 | 메타데이터는 2024-04-01~2026-06-30, 9개 분기 전체를 직접 집계 |
| SMART 기록 여부 | 분기별 첫날·마지막 날 **18일 표본**. 전체 기간의 SMART 값 분포·고장 예측력을 분석한 결과는 아님 |
| 기존 EDA와 관계 | `eda_v1_5%.ipynb`의 ST12000NM0008 분석은 단일 모델 사례로 유지. 그 모델의 피처 선택을 다른 모델에 그대로 적용하지 않음 |
| 아직 정하지 않는 것 | 최종 컬럼, 과거 입력 기간(30·60·90일 후보), 알고리즘, 제조사별·개별 모델 분리 여부 |

**30일은 예측할 미래 기간이다. 과거 입력 길이와 전체 학습 날짜 범위는 별개다.** 잔여수명 90일 예측은 이 노트북 범위에서 보류한다.

목차: 1. 분석 목적 → 2. 데이터셋 설명 → 3. 데이터 품질 점검 → 4. 시각화·컬럼 후보 → 5. 인사이트·다음 EDA
""")
md("""
## 1. 분석 목적

| 질문 | 이 답으로 정할 것 |
|---|---|
| 어떤 장치를 분석할 것인가? | HDD 분석 대상과 제외 목록 |
| HDD 종류별·기간별로 고장 사례가 충분한가? | 상세 분석할 대표 모델과 평가 가능한 집단 |
| 여러 HDD가 함께 기록하는 SMART는 무엇인가? | 공통 컬럼과 선택 컬럼 후보 |
| 같은 SMART 번호의 의미·단위가 호환되는가? | 통합 사용 / 모델별 변환 / 추가 확인 구분 |
| 무엇을 아직 확인하지 못했는가? | 다음 단계의 고장·정상 비교와 입력 길이 분석 |

이 단계의 ‘충분함’은 **학습 실험을 시작할 데이터 규모**를 뜻한다. 성능이나 모든 HDD에 대한 일반화를 보장하는 말이 아니다.
""")
code(r'''
from pathlib import Path
import json
import re
import duckdb
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from IPython.display import display, Markdown

cwd = Path.cwd().resolve()
ROOT = next(p for p in [cwd, cwd.parent] if (p / 'data/backblaze/summary/model_rank.csv').exists())
EDA = ROOT / 'eda'
DATA = ROOT / 'data/backblaze'
COVERAGE = EDA / 'analysis/sampled_column_check'
OUT = EDA / 'analysis/v2'
OUT.mkdir(parents=True, exist_ok=True)
con = duckdb.connect()
con.execute("SET threads=4")
con.execute("SET memory_limit='4GB'")
con.execute("SET enable_progress_bar=false")
temp_path = (OUT / 'duckdb_tmp').as_posix().replace("'", "''")
con.execute(f"SET temp_directory='{temp_path}'")
q = lambda sql: con.sql(sql).df()
pd.set_option('display.max_columns', 30)
pio.templates.default = 'plotly_white'
C_FAIL, C_OK, C_GRAY = '#eb6834', '#2a78d6', '#b5b4ae'

def show_plot(fig, name):
    fig.update_layout(font=dict(family='Malgun Gothic, sans-serif'), margin=dict(l=20,r=20,t=65,b=30))
    fig.write_html(OUT / f'{name}.html', include_plotlyjs=True)
    display({'application/vnd.plotly.v1+json': json.loads(fig.to_json())}, raw=True)

rank = pd.read_csv(DATA / 'summary/model_rank.csv')
coverage = pd.read_csv(COVERAGE / 'model_smart_coverage.csv')
manifest = json.loads((COVERAGE / 'manifest.json').read_text(encoding='utf-8'))
assert rank['model'].is_unique and coverage['model'].is_unique
assert set(rank['model']) == set(coverage['model'])
''')
md("""
## 2. 데이터셋 설명

### 2-1. 출처·단위

| 항목 | 설명 |
|---|---|
| 출처 | [Backblaze Drive Stats](https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data) |
| 1행 | 디스크 1개의 하루 관측 기록 |
| 식별 | `serial_number`는 디스크, `model`은 HDD/SSD 제품 종류. 머신러닝 알고리즘과 구분 |
| 고장 표시 | `failure=1`: 해당 날짜에 고장으로 기록. `0`: 그날 고장 표시 없음 |
| 기본 컬럼 | `date`, `serial_number`, `model`, `capacity_bytes`, `failure`, `datacenter` |
| SMART | 디스크가 기록한 상태 지표. 0은 유효한 값이고, 빈 값은 미기록·수집 누락일 수 있음 |

### 2-2. 장치 분류

제품명·모델명 계열로 HDD 75종 / SSD 21종 / DELLBOSS VD 1종을 분리한다. **모델명 기반 분류**이며 원본에 장치 유형의 공식 정답 열이 있는 것은 아니다. 모델 목록이 바뀌면 분류를 다시 검토한다.

SSD로 분류한 목록에는 `SSD`라는 문자열이 없는 IronWolf ZA250NM10002, Micron MTFDDAV 계열, Intel SSDS 계열 등도 포함한다. DELLBOSS VD는 물리 HDD 모델로 취급하지 않고 별도 제외한다.

확인 자료: [Seagate IronWolf 125 SSD](https://www.seagate.com/ca/en/support/internal-hard-drives/nas-drives/ironwolf-125-ssd/), [Micron MTFDDAV 모델 설명(Dell)](https://www.dell.com/support/home/en-tt/drivers/driversdetails?driverid=yxr1x).
""")
code(r'''
hdd_pattern = r'^(ST\d|HGST |Hitachi |TOSHIBA |WDC WUH|WUH|WDC WD\d)'
inventory = rank.copy()
inventory['device_type'] = np.select(
    [inventory['model'].str.match(hdd_pattern), inventory['model'].eq('DELLBOSS VD')],
    ['HDD', '별도 제외'], default='SSD')
assert inventory['device_type'].value_counts().to_dict() == {'HDD': 75, 'SSD': 21, '별도 제외': 1}
inventory.to_csv(OUT / 'device_inventory.csv', index=False, encoding='utf-8-sig')
hdd = inventory.loc[inventory['device_type'].eq('HDD')].copy()
hdd_models = hdd[['model']].copy()
con.register('hdd_models', hdd_models)
fleet_path = (DATA / 'fleet_slim/*.parquet').as_posix().replace("'", "''")
con.execute(f"CREATE VIEW fleet_hdd AS SELECT d.* FROM read_parquet('{fleet_path}') d JOIN hdd_models h USING(model)")
device_summary = inventory.groupby('device_type').agg(
    모델_종류=('model','size'), 모델별_디스크수_합=('disks','sum'),
    고장_표시행=('failures','sum'), 모델별_고장디스크수_합=('failed_disks','sum'))
device_summary.insert(1, '모델_종류_비율_pct', (100*device_summary['모델_종류']/device_summary['모델_종류'].sum()).round(2))
device_summary.insert(3, '디스크_수_비율_pct', (100*device_summary['모델별_디스크수_합']/device_summary['모델별_디스크수_합'].sum()).round(2))
display(device_summary)
display(Markdown('비율의 분모는 제외 전 **전체 97종 / 디스크 390,540개**다. 모델 종류 비율과 디스크 수 비율을 구분한다.'))
display(inventory.loc[~inventory['device_type'].eq('HDD'), ['model','device_type','disks','failed_disks']])
''')
md("""
### 2-3. HDD 전체 규모·정상/고장 비율

아래 집계는 **HDD 전체 메타데이터 전수 집계**다. 같은 디스크에 고장 표시가 여러 번 있어도 고장 디스크는 한 번만 센다. ‘정상’은 관측 기간 내 고장 기록 없음이라는 뜻이며 실제 남은 수명을 안다는 뜻이 아니다.
""")
code(r'''
fleet = q("""
SELECT count(*) AS drive_days, count(DISTINCT model) AS models,
       count(DISTINCT serial_number) AS disks,
       count(DISTINCT serial_number) FILTER (WHERE failure=1) AS failed_disks,
       sum(failure) AS failure_rows, min(date) AS start_date, max(date) AS end_date
FROM fleet_hdd
""")
assert int(fleet.at[0,'models']) == 75
assert int(fleet.at[0,'disks']) == hdd['disks'].sum(), '모델 간 시리얼 재사용 여부 재검토'
assert int(fleet.at[0,'failed_disks']) == hdd['failed_disks'].sum()
total = int(fleet.at[0,'disks'])
failed = int(fleet.at[0,'failed_disks'])
status = pd.DataFrame({'구분':['정상 (관측 기간 내 고장 기록 없음)','고장 (관측 기간 내 고장 기록 있음)'],
                       '디스크 수':[total-failed, failed]})
status['비율(%)'] = (100*status['디스크 수']/total).round(2)
display(fleet)
display(status)
fleet.to_csv(OUT/'hdd_fleet_summary.csv', index=False, encoding='utf-8-sig')
status.to_csv(OUT/'hdd_status_ratio.csv', index=False, encoding='utf-8-sig')
display(Markdown('이 비율은 **관측 기간 전체의 디스크별 고장 비율**이다. 연간 고장률이나 향후 30일 라벨의 양성 비율과 다르다.'))
''')
md("""
## 3. 데이터 품질 점검

### 3-1. 기본 컬럼 결측·이상 표시 (전체 기간)

수집 오류 후보를 계수한다. 이 단계에서 원본을 수정하거나 일괄 삭제하지 않는다. 용량 `-1`을 실제 용량으로 사용하지 않고, 시리얼·날짜 결측은 시계열 구성 전에 처리해야 한다.
""")
code(r'''
quality = q("""
SELECT count(*) AS rows_checked,
 count(*) FILTER (WHERE date IS NULL) AS null_date,
 count(*) FILTER (WHERE serial_number IS NULL OR trim(serial_number)='') AS missing_serial,
 count(*) FILTER (WHERE model IS NULL OR trim(model)='') AS missing_model,
 count(*) FILTER (WHERE datacenter IS NULL OR trim(datacenter)='') AS missing_datacenter,
 count(*) FILTER (WHERE capacity_bytes IS NULL OR capacity_bytes<=0) AS invalid_capacity,
 count(*) FILTER (WHERE failure IS NULL OR failure NOT IN (0,1)) AS invalid_failure
FROM fleet_hdd
""")
display(quality.T.rename(columns={0:'행 수'}).rename_axis('점검 항목'))
quality.to_csv(OUT/'metadata_quality.csv', index=False, encoding='utf-8-sig')
''')
md("""
### 3-2. 중복 고장·고장 후 기록 (전체 기간)

고장 표시 행 수와 고장 디스크 수를 구분한다. 미래 모델링용 정제에서는 **첫 고장일을 사건일로 사용하고 이후 기록을 제외**하는 정책을 기본 후보로 둔다. 수리·재투입이 확인된 경우 별도 생애로 나눌지 검토한다.
""")
code(r'''
con.execute("""
CREATE TABLE per_disk AS
SELECT serial_number, min(model) AS model, count(DISTINCT model) AS model_names,
       count(*) AS observed_rows, min(date) AS first_date, max(date) AS last_date,
       min(date) FILTER (WHERE failure=1) AS first_failure,
       count(*) FILTER (WHERE failure=1) AS failure_rows
FROM fleet_hdd GROUP BY serial_number
""")
failure_quality = q("""
SELECT count(*) FILTER (WHERE failure_rows>1) AS repeated_failure_disks,
       sum(greatest(failure_rows-1,0)) AS extra_failure_rows,
       count(*) FILTER (WHERE last_date>first_failure) AS post_failure_disks,
       count(*) FILTER (WHERE model_names>1) AS multiple_model_names
FROM per_disk
""")
post_failure = q("""
SELECT count(*) AS rows_after_first_failure FROM fleet_hdd d
JOIN per_disk p USING(serial_number) WHERE d.date>p.first_failure
""")
display(failure_quality)
display(post_failure)
display(q("SELECT * FROM per_disk WHERE failure_rows>1 OR last_date>first_failure ORDER BY failure_rows DESC LIMIT 20"))
failure_quality.to_csv(OUT/'failure_record_quality.csv', index=False, encoding='utf-8-sig')
post_failure.to_csv(OUT/'post_failure_rows.csv', index=False, encoding='utf-8-sig')
''')
md("""
### 3-3. 중복 행 점검 (18일 표본)

`(serial_number, date)`가 겹치는 행을 센다. **이 검사는 SMART 표본 날짜의 메타데이터만 검사**하며 전체 821일 중복 검사가 완료됐다고 해석하지 않는다. 전체 시계열 전처리 시 전 기간 검사도 필요하다.
""")
code(r'''
sample_days = pd.DataFrame({'sample_date':pd.to_datetime(manifest['dates']).date})
con.register('sample_days', sample_days)
duplicates = q("""
SELECT count(*) AS sampled_rows, count(*)-count(DISTINCT (serial_number,date)) AS duplicate_rows
FROM fleet_hdd WHERE date IN (SELECT sample_date FROM sample_days)
""")
display(duplicates)
duplicates.to_csv(OUT/'sample_metadata_duplicates.csv', index=False, encoding='utf-8-sig')
''')
md("""
## 4. 시각화·컬럼 후보 선정

### 4-1. 모델별 고장 사례

대표 모델의 상세 분석은 고장 사례 수와 제조사 다양성을 함께 고려한다. **고장이 100개 이상이라는 기준은 분포를 살펴보기 위한 참고 구간**이며, 학습 가능 여부를 결정하는 보편적인 기준은 아니다. 같은 디스크의 날짜별 행 수가 많아도 독립적인 고장 사건 수가 늘어나는 것은 아니다.
""")
code(r'''
model_cases = hdd[['model','disks','failed_disks','failures','drive_days']].copy()
model_cases['관측기간_고장비율_pct'] = (100*model_cases['failed_disks']/model_cases['disks']).round(2)
model_cases = model_cases.sort_values('failed_disks',ascending=False)
bins = pd.cut(model_cases['failed_disks'], bins=[-1,0,9,29,99,np.inf],
              labels=['0건','1~9건','10~29건','30~99건','100건 이상'])
display(bins.value_counts(sort=False).rename('모델 수').to_frame())
display(model_cases.head(15))
model_cases.to_csv(OUT/'hdd_model_cases.csv', index=False, encoding='utf-8-sig')
fig = px.bar(model_cases.head(15).sort_values('failed_disks'), x='failed_disks', y='model',
             orientation='h', title='그림 4-1. HDD 모델별 고장 디스크 수 — 상위 15종',
             labels={'failed_disks':'고장 디스크 수','model':'HDD 모델'}, color_discrete_sequence=[C_FAIL])
show_plot(fig,'4-1_model_failures')
''')
md("""
### 4-2. 기간별 고장 사건·연간 고장률 (전체 기간)

고장이 특정 기간에만 몰려 있지 않은지 확인한다. AFR은 `고장 표시 행 / (디스크-일 / 365) × 100`으로 계산한 원본 기준 기술 통계다. 중복 고장 표시를 제거한 사건 기반 위험률과 구분한다. 실제 모델 학습/평가에는 첫 고장 기준의 정제 자료를 쓴다.
""")
code(r'''
quarterly = q("""
SELECT year(date) AS year, quarter(date) AS quarter, count(*) AS drive_days,
       count(DISTINCT model) AS models,
       count(DISTINCT serial_number) FILTER (WHERE failure=1) AS failed_disks,
       sum(failure) AS failure_rows,
       round(100.0*sum(failure)/(count(*)/365.0),3) AS afr_pct
FROM fleet_hdd GROUP BY 1,2 ORDER BY 1,2
""")
quarterly['분기'] = quarterly['year'].astype(str)+' Q'+quarterly['quarter'].astype(str)
display(quarterly)
quarterly.to_csv(OUT/'hdd_quarterly.csv', index=False, encoding='utf-8-sig')
fig = px.bar(quarterly,x='분기',y='failed_disks',title='그림 4-2. 분기별 고장 디스크 수 — HDD 전체',
             labels={'failed_disks':'고장 디스크 수'},color_discrete_sequence=[C_FAIL])
show_plot(fig,'4-2_quarterly_failures')
display(Markdown('전체 기간에 고장이 존재해 시간 기준 평가를 검토할 수 있다. 단, HDD 종류 구성도 분기마다 바뀌므로 전체 고장률 변화를 노화 효과로 단정하지 않는다.'))
''')
md("""
### 4-3. SMART 기록 여부 — 0과 미기록 구분

| 개념 | 의미 |
|---|---|
| SMART 원시값 0 | 기록된 값. 오류 지표라면 해당 오류가 없음을 나타낼 수 있음 |
| 아래 기록률 0% | 해당 모델의 표본에서 값이 한 번도 기록되지 않았음. SMART 원시값 0과 다름 |
| 기록률 99% 이상 | 해당 모델의 표본 행 중 99% 이상이 결측 아님. 원시값이 0이어도 포함 |
| 공통 후보 | 75종 모두에서 기록률 99% 이상. 의미·단위 호환성이나 예측 성능까지 검증한 것은 아님 |

원본 ZIP의 날짜별 파일에서 집계한 **18일 표본**을 사용한다. 모델별 표본 날짜·행 수가 다르고, 날짜 사이의 보고 중단·스키마 변화를 놓칠 수 있다. 전수 확인 결과로 표현하지 않는다.
""")
code(r'''
hdd_cov = coverage.merge(hdd[['model','disks','drive_days']], on='model',how='inner',validate='one_to_one')
assert len(hdd_cov)==75 and len(manifest['dates'])==18
smart_cols = sorted([c for c in coverage if re.fullmatch(r'smart_\d+_raw',c)],key=lambda c:int(c.split('_')[1]))
assert hdd_cov[smart_cols].ge(0).all().all() and hdd_cov[smart_cols].le(100).all().all()
records=[]
for col in smart_cols:
    rates = hdd_cov[col]
    records.append({'컬럼':col,'기록한_모델수':int(rates.gt(0).sum()),
                    '99pct이상_모델수':int(rates.ge(99).sum()),
                    '모델별_최소기록률_pct':round(rates.min(),4),
                    '모델별_최대기록률_pct':round(rates.max(),4),
                    '공통후보':bool(rates.ge(99).all())})
cov_summary=pd.DataFrame(records)
display(hdd_cov[['model','sampled_days','sampled_rows']].describe())
display(cov_summary.loc[cov_summary['공통후보']])
cov_summary.to_csv(OUT/'hdd_smart_coverage_summary.csv',index=False,encoding='utf-8-sig')
hdd_cov.to_csv(OUT/'hdd_model_smart_coverage.csv',index=False,encoding='utf-8-sig')
display(Markdown(f"**{len(hdd_cov)}종 모두 포함**, 총 {len(manifest['dates'])}개 날짜 표본. 공통 후보는 **{cov_summary['공통후보'].sum()}개**. 기록 여부를 확인한 결과이며 최종 입력 컬럼 목록이 아니다."))
''')
code(r'''
names={1:'읽기 오류 관련 지표',3:'모터 회전 시작 시간',4:'회전 시작·정지 횟수',5:'재할당 섹터 수',
       7:'헤드 탐색 오류 관련 지표',9:'누적 가동 시간',10:'회전 재시도 횟수',12:'전원 인가 횟수',
       187:'정정 불가 오류',188:'명령 시간 초과',192:'전원 차단·헤드 회수 관련 지표',
       193:'헤드 로드·언로드 횟수',194:'온도',197:'대기 중 불량 섹터 수',
       198:'오프라인 복구 불가 섹터 수',199:'인터페이스 CRC 오류',241:'누적 쓰기 관련 지표',242:'누적 읽기 관련 지표'}
selected=cov_summary[cov_summary['컬럼'].isin([f'smart_{i}_raw' for i in names])].copy()
selected['지표']=selected['컬럼'].map(lambda c:f"{names[int(c.split('_')[1])]}({c.split('_')[1]})")
display(selected[['지표','컬럼','99pct이상_모델수','모델별_최소기록률_pct','공통후보']])
fig=px.bar(selected.sort_values('99pct이상_모델수'),x='99pct이상_모델수',y='지표',orientation='h',
           title='그림 4-3. SMART를 표본 행의 99% 이상 기록한 HDD 모델 수',
           labels={'99pct이상_모델수':'HDD 모델 수 (전체 75종)'},color_discrete_sequence=[C_OK])
fig.add_vline(x=75,line_dash='dot',line_color=C_GRAY)
fig.update_layout(height=700)
show_plot(fig,'4-3_smart_coverage')
''')
md("""
### 4-4. 컬럼 후보와 해석 주의점

공통으로 기록되는 컬럼이라고 모두 최종 입력으로 확정하지 않는다. 일부만 기록하는 지표도 정보가 강하면 **선택 컬럼**으로 유지할 수 있다. 결측을 0으로 바꾸면 ‘미기록’을 ‘오류 없음’으로 오해하므로 구분한다.

| 후보군 | 컬럼·의미 | 다음 검증 |
|---|---|---|
| 손상 공통 후보 | 재할당 섹터 수(5), 오프라인 복구 불가 섹터 수(198) | 고장·정상 차이, 0 초과 비율, 7·30·90일 변화. 누적/현재 상태 여부와 리셋 확인 |
| 가동·환경 공통 후보 | 가동 시간(9), 온도(194), 전원 인가 횟수(12), 회전 시작 시간(3), 회전 시작·정지 횟수(4) | 모델·시점을 맞춘 비교, 단위·펌웨어 인코딩, 나이·사용량과의 중복 확인 |
| 전송·전원 관련 공통 후보 | 인터페이스 CRC 오류(199), 전원 차단·헤드 회수 관련 지표(192) | 매체 손상과 구분. 192의 세부 의미는 제조사·모델별 확인 |
| 별도 해석이 필요한 공통 후보 | 읽기 오류 관련 지표(1), 헤드 탐색 오류 관련 지표(7) | 제조사 인코딩이 달라 raw 정수 크기를 그대로 비교하지 않음 |
| 선택 컬럼 후보 | 대기 중 불량 섹터 수(197), 정정 불가 오류(187), 명령 시간 초과(188), 헤드 로드·언로드(193), 누적 읽기·쓰기(241·242) 등 | 적용 모델과 단위 확인, 미기록 표시 유지. 누적량은 보고 단위·인코딩 확인 후 환산 |

**ST12000NM0008에서 대기 섹터(197)=오프라인 복구 불가 섹터(198), 온도 관련(190)=(194)였다는 이유로 75종 전체에서 한쪽을 제외하면 안 된다.** 중복 관계는 모델별로 재검증한다. 명령 시간 초과(188)처럼 여러 카운터가 묶인 값은 그대로 빼서 증가량을 만들지 않는다.

정의 참고: [Backblaze SMART 항목](https://www.backblaze.com/docs/cloud-storage-hard-drive-smart-stats-and-failure-rates), [Seagate SMART 해석 가이드](https://github.com/Seagate/openSeaChest/wiki/Drive-Health-and-SMART). 이 자료만으로 75종의 단위 호환 검증이 완료된 것은 아니다.
""")
md("""
## 5. 인사이트 → 다음 EDA에 반영

### 5-1. 확인한 것
""")
code(r'''
display(Markdown(f"""
- HDD **{int(fleet.at[0,'models']):,}종**, 디스크 **{total:,}개**, 고장 디스크 **{failed:,}개**({100*failed/total:.2f}%).
- 전체 기록은 **{int(fleet.at[0,'drive_days']):,} 디스크-일**. 모든 분기에 고장 기록이 있어 통합 학습 실험을 검토할 수 있다.
- 고장 사례가 없는 HDD는 **{int(model_cases['failed_disks'].eq(0).sum())}종**, 고장 100개 이상인 HDD는 **{int(model_cases['failed_disks'].ge(100).sum())}종**. 75개 전용 모델을 일괄 만드는 근거는 부족하다.
- SMART 공통 후보는 **{int(cov_summary['공통후보'].sum())}개**(18일 표본의 모델별 기록률 99% 기준). **값의 예측력·의미 호환성 검증은 아직 남아 있다.**
- 단일 모델 EDA에서 중요했던 정정 불가 오류(187)·명령 시간 초과(188)는 모든 HDD의 공통 입력이 아니다. 선택 컬럼 또는 그룹별 입력으로 검토한다.
"""))
''')
md("""
### 5-2. 전처리·피처 정책 초안

| 항목 | 정책 후보 | 상태 |
|---|---|---|
| 대상 | HDD 75종. SSD·DELLBOSS VD 제외. 원본 보존 | 분류·집계 완료 |
| 고장 기록 | 첫 고장일 기준으로 정제하고 이후 행은 제외. 수리·재투입은 별도 검토 | 이상 기록 수 확인, 정제 구현은 다음 단계 |
| SMART 결측 | 미기록과 0을 구분. 시간 보간 시 미래 값을 사용하지 않으며 과거값 채움도 최대 공백 길이·모델별 지원 여부를 검토 | 정책 후보 |
| 컬럼 | 공통 후보 + 선택 후보를 구분. 같은 번호라도 의미가 다른 경우 변환하거나 분리 | 기록률 확인 / 의미 검증 미완료 |
| 파생 컬럼 | 현재 값·0 초과 여부·7일/30일 변화량을 기본 후보로, 60일/90일 변화와 장기 추세도 비교 | 아직 계산·효과 검증하지 않음 |
| 라벨 | 시점 t 이후 **0 < 고장일-t ≤ 30일**이면 1. 고장 당일은 예측 대상에서 제외 | 정의 초안 |
| 관측 종료 | 이후 30일을 확인할 수 없는 무고장 표본을 자동으로 음성 처리하지 않음. 중도 이탈도 중도절단으로 검토 | 라벨 구현 전 검증 필요 |
| 시간 분할 | 예: 2024 Q2~2025 Q4 학습 / 2026 Q1 검증 / Q2 평가. 경계에서 라벨의 미래 30일이 다른 구간으로 넘어가지 않도록 제거·관측 유예 | 확정 전 |
| 입력 길이 | 과거 30·60·90일 후보. 90일 고정으로 확정하지 않음. 확보 가능한 이력 수와 중간 결측부터 확인 | 다음 EDA |
| 평가 | 동일 미래 기간·월 경고 수에서 규칙과 모델의 재현율·정밀도 비교. HDD 종류별 결과도 확인 | 향후 모델링 |

기존 노트북의 양성 비율 0.19%, 규칙 재현율 74%, 피처 효과 크기는 ST12000NM0008 결과다. **HDD 전체 결과로 재사용하지 않는다.**

### 5-3. 다음에 할 분석 (미완료)

1. 모델별 SMART 의미·단위를 확인하고 전 기간 결측률·이상값·리셋·중복 열을 검증한다.
2. 고장 사례가 충분한 대표 모델 몇 종(Seagate/HGST/Toshiba 등)을 골라 같은 시점의 고장·정상을 비교한다. ‘정상’에 향후 30일 내 고장 예정 디스크가 섞이지 않게 정의한다.
3. 고장 전 90~180일의 궤적과 현재 값·7/30/60/90일 변화량을 비교한다. 고장일까지 남은 기간과 과거 입력 길이를 혼동하지 않는다.
4. 과거 30/60/90일 기록을 확보할 수 있는 디스크·고장 사건의 수와 결측·보고 공백을 확인한다.
5. HDD 전체와 대표 모델별 SMART 규칙의 경고 수·정밀도·재현율을 다시 계산한다.

**여기까지 확인한 뒤 최종 컬럼과 입력 길이를 정하고, 통합 머신러닝 기준 모델을 만든다.** 이 노트북은 학습이나 성능 검증을 수행하지 않는다.
""")

nb = nbf.v4.new_notebook(cells=cells)
nb.metadata = {'kernelspec': {'display_name':'Python 3','language':'python','name':'python3'},
               'language_info': {'name':'python','version':'3.14.6'}}
nbf.validate(nb)
nbf.write(nb, EDA/'eda_v3_87%.ipynb')
print(f'Created eda_v3_87%.ipynb: {len(cells)} cells')
