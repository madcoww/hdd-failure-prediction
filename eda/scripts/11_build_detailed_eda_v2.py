"""Replace v2 with a full detailed top20/common13 EDA; archive the current edited notebook."""
from pathlib import Path
import shutil
import nbformat as nbf

EDA=Path(__file__).resolve().parents[1]
OUT=EDA/'analysis/detailed_v2'
assert (OUT/'analysis_manifest.json').exists(), 'Run full analysis first'
backup=EDA/'analysis/v2/eda_v2_before_detailed.ipynb'
if not backup.exists():shutil.copy2(EDA/'eda_v2_87%.ipynb',backup)
cells=[]
def md(s):cells.append(nbf.v4.new_markdown_cell(s.strip()))
def code(s):cells.append(nbf.v4.new_code_cell(s.strip()))
md('''# HDD 고장 예측 EDA v2 — 상위 20종 · 공통 SMART 13개

| 항목 | 내용 |
|---|---|
| 서비스 목표 | 향후 **30일 내 고장 위험**으로 교체 우선순위를 정하고 SMART 규칙보다 헛경보를 줄인다 |
| 분석 대상 | 고장 디스크 수 상위 HDD 20종. HDD 디스크의 **87.38%**, 고장의 **94.31%** |
| 입력 후보 | 전체 821일에서 공통 기록이 확인된 SMART raw 13개 |
| 기간 | 2024-04-01~2026-06-30, **821일 전체의 실제 값**. 18일 표본 분석이 아님 |
| 비교 방식 | 미래 30일 고장 라벨을 매월 1일 평가 시점에 만들고, 같은 모델·같은 날짜의 고장 예정/비고장 디스크를 비교 |
| 완료 범위 | 품질·분포, 모델별 차이, 상관, 고장 전 궤적, 변화량, 입력 이력 확보율, 규칙 기준선 |
| 미수행 | 머신러닝 학습·성능 평가. 잔여수명 최대 90일 예측은 범위 밖 |

전체 821일을 읽고 정제하지만, 반복 관측의 편중을 줄이기 위해 고장·정상 비교와 경고 평가는 **월별 평가 시점**을 사용한다. 이는 원본을 일부 날짜만 읽은 표본 검사와 다르다.
''')
md('''## 1. 분석 목적

| 질문 | 이 답으로 정할 것 |
|---|---|
| Q1. 어떤 공통 지표가 고장 예정·비고장 디스크를 구분하는가? | 최종 컬럼 후보 |
| Q2. 고장 징후는 언제부터 나타나며 증가량이 더 유용한가? | 현재 값·변화량 사용 여부 |
| Q3. 과거 30·60·90일 기록이 연속으로 확보되는가? | 입력 길이 후보와 데이터 손실 |
| Q4. 공통 SMART 규칙의 경고·재현율·정밀도는 어느 정도인가? | 모델이 넘어야 할 기준선 |
| Q5. 모델·기간별 차이가 큰가? | 통합 모델의 입력 해석과 모델별 평가 필요성 |
''')
code(r'''
from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from IPython.display import display, Markdown
cwd=Path.cwd().resolve()
ROOT=next(p for p in (cwd,cwd.parent) if (p/'eda/analysis/detailed_v2/analysis_manifest.json').exists())
EDA=ROOT/'eda'; OUT=EDA/'analysis/detailed_v2'; FIG=OUT/'figures'; FIG.mkdir(exist_ok=True)
def read(name):return pd.read_csv(OUT/f'{name}.csv')
def show(fig,name,height=520):
    fig.update_layout(template='plotly_white',height=height,font=dict(family='Malgun Gothic, sans-serif'),
                      margin=dict(l=30,r=30,t=75,b=70))
    fig.write_html(FIG/f'{name}.html',include_plotlyjs=True)
    fig.write_image(FIG/f'{name}.png',width=1250,height=height)
    display({'application/vnd.plotly.v1+json':json.loads(fig.to_json())},raw=True)
cols=json.loads((OUT/'selected_columns.json').read_text())
names={1:'읽기 오류 관련 지표',3:'회전 시작 관련 raw',4:'회전 시작·정지 횟수',5:'재할당 섹터 수',
       7:'헤드 탐색 오류 관련 지표',9:'누적 가동 시간',10:'회전 재시도 관련 raw',12:'전원 인가 횟수',
       192:'전원 차단·헤드 회수 관련 지표',193:'헤드 로드·언로드 횟수',194:'온도',
       198:'오프라인 복구 불가 섹터 수',199:'인터페이스 CRC 오류'}
labels={c:f"{names[int(c.split('_')[1])]}({c.split('_')[1]})" for c in cols}
def feature_name(c):
    if c in labels:return labels[c]
    if c.startswith('delta_'):
        raw,days=c[6:].rsplit('_',1)
        return f'{labels[raw]} {days}일 변화'
    return c
C_FAIL,C_OK='#eb6834','#2a78d6'
manifest=json.loads((OUT/'analysis_manifest.json').read_text())
assert manifest['all_821_days'] and manifest['models']==20 and manifest['smart_columns']==13
''')
md('''## 2. 데이터셋 설명

### 2-1. 출처·범위

[Backblaze Drive Stats](https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data)의 1행은 디스크 1개의 하루다. `failure=1`은 해당 관측일에 고장으로 기록됐다는 뜻이다. ‘정상’은 관측 기간에 고장이 없다는 뜻이며 실제 수명을 안다는 뜻은 아니다.

SSD 21종과 DELLBOSS VD 1종은 제외한다. 전체 HDD 75종에서 고장 사례가 많은 20종을 분석 대상으로 좁혔다. 75종 전체 공통 지표는 11개, 선택한 20종의 공통 지표는 13개다.
''')
code(r'''
scope=pd.read_csv(EDA/'analysis/v2/top20_vs_hdd75.csv')
display(scope)
selected=read('selected_models')
display(selected[['model','disks','failed_disks']].rename(columns={'model':'HDD 모델','disks':'디스크 수','failed_disks':'고장 디스크 수'}).reset_index(drop=True))
from plotly.subplots import make_subplots
fig=make_subplots(rows=1,cols=2,specs=[[{'type':'domain'},{'type':'domain'}]],
                  subplot_titles=['HDD 디스크 수 포함 비율','HDD 고장 디스크 포함 비율'])
for i,pct in enumerate([float(scope.iloc[0]['디스크 수 비율(%)']),float(scope.iloc[0]['고장 디스크 비율(%)'])],1):
    fig.add_pie(labels=['선택한 20종','그 외 55종'],values=[pct,100-pct],hole=.6,
                textinfo='none',sort=False,marker=dict(colors=[C_OK,'#d9dce1']),row=1,col=i)
    fig.add_annotation(x=.225 if i==1 else .775,y=.5,xref='paper',yref='paper',
        text=f'<b>{pct:.2f}%</b>',showarrow=False,xanchor='center',yanchor='middle')
fig.update_layout(title='그림 2-1. 20종으로 디스크 약 87%, 고장 약 94%를 포함',legend=dict(orientation='h',y=-.1))
show(fig,'2-1_scope',420)
''')
md('### 2-2. 공통 SMART 13개 — 정의·단위 선행 검토\n\n**기록 여부는 821일 전수 확인, 의미·단위는 제조사 자료·해석 코드·실제 값의 동작을 별도로 대조했다.** 20종 × 13개 지표의 검토표(260행)를 만들었다. 이는 260개 모두의 펌웨어별 상세 사양을 제조사가 보증했다는 뜻이 아니다.\n\n이번 검토의 처리 방침은 **조건부 공통 후보 8개 / 통합 기본 입력 보류 5개**다. 아래에서 ‘조건부’란 현재 데이터의 의미와 해석 근거가 비교적 일치하므로 모델 식별자·값 검증을 함께 사용하는 후보라는 뜻이다. 모든 제조사에서 같은 원시값이 같은 고장 위험이나 동일한 바이트 손상을 뜻한다는 뜻은 아니다.\n\n- **가동 시간(9)**: 20종 모두 30일 간 증가량을 일 단위로 나눈 중앙값이 약 **23.93~24.07**이었다. 제품군의 Power On Hours 정의와도 일치해 이 데이터에서는 **시간(h)**으로 해석한다. 감소·리셋 구간은 따로 다룬다.\n- **현재 온도(194)**: 제품군 문서·해석 도구는 섭씨로 정의하며, CSV는 13~112의 단일 수치다. 현재 CSV를 ℃로 사용하는 후보로 두되, 101·112 같은 극단값은 센서·수집 이상 가능성을 별도 검토한다. 원본 패킷을 확보하지 못했으므로 임의로 비트 분해하지 않는다.\n- **읽기/탐색 오류(1·7)**: Seagate 공식 설명과 제품군별 해석 코드에서 복합 필드가 확인된다. raw 정수 전체를 단일 오류 횟수로 쓰거나 `raw>0`을 오류 발생으로 해석하지 않는다.\n- **회전 시작(3)·회전 재시도(10)**: 현재값·평균값·집계 구간 해석을 구분해야 한다. 3은 10종, 10은 19종에서 전 기간 상수였으며 기본 입력은 보류한다.\n- **비상 헤드 회수(192)**: 제조사별 집계 조건이 다르고, ST14000NM0138에는 부정확한 증가를 수정한 공식 펌웨어 공지가 있다. 현재 데이터의 펌웨어 버전이 없어 해당 오류의 영향 여부를 알 수 없으므로 기본 입력을 보류한다.\n\n**확인 한계**: 원본 821개 CSV의 스키마에 펌웨어·수집 도구 버전·섹터 크기 필드가 없다. 현재 도구 DB와 모델명이 정확히 일치한 것은 10종, 접미사 생략으로 제품군을 추정한 것은 9종, DB 규칙을 찾지 못한 것은 1종(ST14000NM0138)이다. 이 1종은 Dell 공지에서 OEM 모델로 확인했다. 제조사 비공개 raw 수식과 Backblaze 내부 변환 코드는 확보하지 못했다.\n\n수집 경로도 구분했다. smartctl은 raw 정수와 사람이 읽는 표시 문자열을 별도로 만들지만, Backblaze는 자체 C++ 수집기→XML→집계 모듈 구조라고 설명한다. **현재 CSV가 최신 smartctl의 `raw.value`를 그대로 저장했다는 가정은 하지 않는다.**\n\n근거: [Seagate 공식 SMART 설명](https://github.com/Seagate/openSeaChest/wiki/Drive-Health-and-SMART), [모델별 도구 해석 규칙](https://github.com/smartmontools/smartmontools/blob/main/drivedb/drivedb.h), [Toshiba 자료](https://www.toshiba-storage.com/wp/wp-content/uploads/2022/07/Toshiba_OpenE_Blogpost_July2022_final.pdf), [Backblaze 수집 구조](https://www.backblaze.com/blog/drive-stats-data-deep-dive-the-architecture/), [Dell 펌웨어 공지](https://www.dell.com/support/home/en-pr/drivers/driversdetails?driverid=v3n1t).\n\n상세 근거는 `analysis/column_definition_audit/model_column_audit.csv`, 제품군 매칭은 `model_family_matches.csv`, 원문·해시는 `source_manifest.json`에 있다. 원본 값과 기존 13개 탐색 통계는 보존하며, 이를 ‘13개 모두 통합 입력 검증 완료’로 해석하지 않는다.\n')
code("audit_dir=EDA/'analysis/column_definition_audit'\npolicy_summary=pd.read_csv(audit_dir/'column_policy_summary.csv')\ndisplay(policy_summary[['컬럼','지표','해석','상수인_모델수','판정']])\ndisplay(read('cohort').rename(columns={'disks':'디스크 수','failed_disks':'고장 디스크 수','failure_rows':'고장 표시 행',\n    'repeated_failure_disks':'중복 고장 디스크','post_failure_disks':'고장 후 기록 디스크'}))")
md('''## 3. 전처리·데이터 품질

### 3-1. 전체 821일 검사와 정제

- `(serial_number, date)` 중복은 **821일 모두 검사**했다. 원본은 보존한다.
- 고장 디스크의 첫 고장일을 사건일로 사용하고 그 이후 기록을 제외한다.
- SMART의 0은 기록된 값이며 빈 값과 구분한다. 분석에서 결측을 0으로 채우지 않는다.
- 통계적으로 큰 값을 임의 삭제하지 않는다. 값의 의미·리셋 여부를 확인한다.
''')
code(r'''
display(read('quality').T.rename(columns={0:'행 수'}).rename_axis('점검 항목'))
display(read('clean_scale').rename(columns={'raw_rows':'정제 전 행 수','clean_rows':'첫 고장 이후 제거한 행 수를 제외한 전체 행'}))
extraction=json.loads((OUT/'extraction_manifest.json').read_text())
display(Markdown(f"**전체 {extraction['dates']}일의 디스크-날짜 중복: {extraction['duplicate_disk_date_rows']:,}행.**"))
quality=read('value_quality_by_model')
quality_summary=quality.groupby('column').agg(최대_모델결측률=('missing_pct','max'),
    모델별_0비율_중앙값=('zero_pct','median'),전체_음수행=('negative_rows','sum'),최솟값=('min','min'),최댓값=('max','max')).reset_index()
quality_summary['지표']=quality_summary.column.map(labels)
constant_counts=quality.assign(constant=quality['min'].eq(quality['max'])).groupby('column').constant.sum()
quality_summary['상수인_모델수']=quality_summary.column.map(constant_counts)
display(quality_summary[['지표','최대_모델결측률','모델별_0비율_중앙값','상수인_모델수','전체_음수행','최솟값','최댓값']])
z=quality.pivot(index='model',columns='column',values='zero_pct')[cols].rename(columns=labels)
fig=px.imshow(z,zmin=0,zmax=100,aspect='auto',color_continuous_scale='Blues',labels={'color':'0 비율(%)'},
    title='그림 3-1. 0이 많은 지표 — 미기록이 아니라 기록값이 0인 비율')
fig.update_xaxes(tickangle=-40)
show(fig,'3-1_zero_rates',850)
''')
md('''### 3-2. 30일 라벨·비교 시점

매월 1일을 예측 시점 t로 잡는다. **0 < 첫 고장일−t ≤ 30일이면 양성**, 그 외에는 미래 30일을 관측할 수 있을 때만 음성이다. 고장 당일 행과 관측 끝부분·중도 이탈로 미래 30일을 확인할 수 없는 무고장 표본은 제외한다.

고장·정상 비교에서는 같은 HDD 모델·같은 날짜의 양성 1개당 음성을 최대 5개 고정 난수 해시로 선택했다. 비교용 매칭 집단의 양성 비율을 실제 발생률로 사용하지 않는다. 순위 효과 크기 r을 사용하며, 같은 디스크의 반복 관측이 있어 독립 표본을 가정한 p값은 결론에 쓰지 않는다.
''')
code(r'''
display(read('label_summary').rename(columns={'snapshots':'디스크-월 표본','positive_snapshots':'30일 내 고장 표본',
    'dates':'평가 날짜 수','positive_pct':'양성 비율(%)'}))
sizes=read('matched_sizes').groupby('label_30',as_index=False).n.sum()
sizes['구분']=sizes.label_30.map({0:'30일 내 고장 없음 (매칭 음성)',1:'30일 내 고장 (매칭 양성)'})
display(sizes[['구분','n']].rename(columns={'n':'비교 표본 수'}))
''')
md('''## 4. 데이터 시각화·상세 분석

### 4-1. 모델별 규모·기간별 고장률

고장 건수가 많다는 것과 고장률이 높다는 것은 다르다. 분기 고장률은 첫 고장 이후 기록을 제외한 디스크-일 기준 AFR이다. 분기별로 HDD 구성도 변하므로 전체 변화가 노화만의 효과라고 단정하지 않는다.
''')
code(r'''
scale=read('model_scale')
scale['제조사']=scale.model.map(lambda m:'Seagate' if m.startswith('ST') else 'Toshiba' if m.startswith('TOSHIBA') else 'HGST / WD')
fig=px.scatter(scale,x='disks',y='failures',log_x=True,color='제조사',hover_name='model',hover_data=['afr_pct'],
    labels={'disks':'디스크 수 (로그)','failures':'첫 고장 수','afr_pct':'AFR(%)'},title='그림 4-1. 선택한 20종의 디스크 수와 고장 수')
fig.update_traces(marker=dict(size=12));fig.update_layout(legend=dict(x=.02,y=.98))
show(fig,'4-1_model_scale')
quarter=read('quarterly_by_model').groupby(['year','quarter'],as_index=False)[['drive_days','failures']].sum()
quarter['분기']=quarter.year.astype(str)+' Q'+quarter.quarter.astype(str)
quarter['AFR(%)']=100*quarter.failures/(quarter.drive_days/365)
fig=px.line(quarter,x='분기',y='AFR(%)',markers=True,title='그림 4-2. 선택한 20종의 분기별 연간 환산 고장률')
show(fig,'4-2_quarterly_afr')
''')
md('''### 4-2. 고장·정상 차이 — 모델 안에서 비교 (Q1)

모델별 rank-biserial r: **양수면 고장 예정 집단의 값이 큰 경향**, 0이면 순위 차이가 작고 음수면 반대다. 이는 분류 성능이나 인과관계를 뜻하지 않는다. 서로 단위가 다른 제조사 raw 값을 그대로 섞은 검정은 하지 않았다.
''')
code(r'''
effects=read('effects_by_model')
current=effects[effects.feature.isin(cols)].copy()
matrix=current.pivot(index='model',columns='feature',values='rank_biserial').reindex(columns=cols).rename(columns=labels)
fig=px.imshow(matrix,zmin=-1,zmax=1,color_continuous_scale='RdBu_r',aspect='auto',
    labels={'color':'순위 효과 r'},title='그림 4-3. 같은 모델·같은 날짜에서 비교한 고장/정상 차이')
fig.update_xaxes(tickangle=-40)
show(fig,'4-3_model_effects',850)
ranking=current.assign(abs_r=current.rank_biserial.abs()).groupby('feature').agg(
    모델별_효과크기_중앙값=('abs_r','median'),r_03이상_모델수=('abs_r',lambda s:int((s>=.3).sum())),
    비교_양성수_합=('positive_n','sum')).sort_values('모델별_효과크기_중앙값',ascending=False)
ranking.index=ranking.index.map(labels)
display(ranking)
matched=pd.read_parquet(OUT/'matched.parquet')
box=matched[['model','label_30','smart_5_raw']].dropna().copy()
box['집단']=box.label_30.map({0:'30일 내 고장 없음',1:'30일 내 고장'})
box['log1p_재할당']=np.log1p(box.smart_5_raw.clip(lower=0))
fig=px.box(box,x='log1p_재할당',y='model',color='집단',orientation='h',points=False,
    color_discrete_map={'30일 내 고장 없음':C_OK,'30일 내 고장':C_FAIL},
    title='그림 4-4. 재할당 섹터 수(5)의 모델별 분포 — log(1+값)')
fig.update_layout(legend=dict(orientation='h',y=-.15))
show(fig,'4-4_reallocated_distribution',900)
''')
md('''### 4-3. 지표 간 중복 (Q1 보충)

각 모델 안에서 계산한 Spearman 상관을 모델 간 중앙값으로 요약한다. 상수인 지표의 상관은 계산할 수 없어 비어 있다. 특정 모델에서 중복되는 관계를 20종 전체의 중복으로 단정하지 않는다.
''')
code(r'''
corr=pd.read_csv(OUT/'within_model_correlation.csv',index_col=0).rename(index=labels,columns=labels)
fig=px.imshow(corr,zmin=-1,zmax=1,color_continuous_scale='RdBu_r',aspect='auto',labels={'color':'모델 내 ρ 중앙값'},
    title='그림 4-5. 모델 내부 상관의 중앙값 — 피처 중복 검토')
fig.update_xaxes(tickangle=-40)
show(fig,'4-5_correlation',850)
''')
md('''회전 시작·정지 횟수(4)와 전원 인가 횟수(12)의 모델 내 상관 중앙값은 매우 높지만, 전 기간 값을 직접 비교하면 **20종 중 1종에서만 모든 행이 동일**했다. 높은 상관만으로 두 컬럼을 전체 모델에서 동일한 열로 간주하지 않는다. 근거: `analysis/detailed_v2/start_stop_vs_power_exact.csv`.
''')
md('''### 4-4. 고장 전 궤적 (Q2)

실제 고장 디스크에서 고장 전 180일을 돌아본 기술 통계다. 각 날짜에 실제 기록이 있는 디스크만 분모에 들어가므로 날짜별 대상 수가 다르다. **고장 당일 D-0은 설명용이며 예측 입력·라벨 평가에서는 제외**했다.
''')
code(r'''
traj=read('trajectories')
trajectory=traj.melt(id_vars=['model','days_before','observed_disks'],value_vars=['reallocated_gt0_pct','offline_gt0_pct'],
    var_name='지표',value_name='0 초과 비율(%)')
trajectory['지표']=trajectory['지표'].map({'reallocated_gt0_pct':'재할당 섹터(5)','offline_gt0_pct':'복구 불가 섹터(198)'})
fig=px.line(trajectory,x='days_before',y='0 초과 비율(%)',color='지표',facet_col='model',facet_col_wrap=4,
    hover_data=['observed_disks'],title='그림 4-6. 고장 전 손상 지표의 변화 — 20종 모두',
    labels={'days_before':'고장까지 남은 일수','observed_disks':'관측된 고장 디스크 수'})
fig.update_xaxes(autorange='reversed');fig.update_yaxes(range=[0,100])
fig.for_each_annotation(lambda a:a.update(text=a.text.replace('model=',''),font_size=9))
fig.update_layout(legend=dict(orientation='h',y=-.10))
show(fig,'4-6_trajectories',1150)
display(traj[traj.days_before.isin([90,60,30,7,1,0])].reset_index(drop=True))
lead=read('lead_times')
display(Markdown(f"**손상 지표(5 또는 198)가 끝까지 켜지지 않은 고장 디스크:** {lead.first_signal.isna().sum():,}개 / {len(lead):,}개 ({100*lead.first_signal.isna().mean():.1f}%). 첫 관측 이후 처음 신호가 켜진 시점은 고장 전 중앙값 **{lead.lead_days.median():.0f}일**이다. 관측 시작 전부터 켜져 있었을 수 있어 실제 최초 발생 시점으로 단정하지 않는다."))
fig=px.histogram(lead.dropna(subset=['lead_days']),x='lead_days',nbins=50,
    labels={'lead_days':'처음 기록된 손상 신호부터 고장까지 일수'},title='그림 4-6b. 손상 신호가 켜진 뒤에도 오래 가동하는가?')
show(fig,'4-6b_lead_time')
''')
md('''### 4-5. 현재 값과 증가량 (Q2)

7·30·90일 변화량은 정확히 그 날짜의 값이 있을 때만 계산했다. 보고가 빠진 날을 임의로 직전 값으로 채우지 않았다. 아래 비교는 **현재 값과 모든 비교 기간 값이 함께 있는 동일 집단**을 사용해, 긴 이력이 있는 디스크만 남는 효과를 줄였다.

재할당 섹터(5)나 복구 불가 섹터(198)도 감소·리셋이 있을 수 있다. 음의 변화량은 별도로 집계하며 임의로 0으로 바꾸지 않았다. 복합 인코딩 가능성이 있는 읽기 오류(1)·탐색 오류(7)의 raw 차이는 만들지 않았다.
''')
code(r'''
growth=read('growth_effects_same_cohort')
growth['지표·기간']=growth.feature.map(feature_name)
growth['효과 크기 절댓값']=growth.rank_biserial.abs()
fig=px.box(growth,x='지표·기간',y='효과 크기 절댓값',points='all',hover_data=['model','positive_n','negative_n'],
    title='그림 4-7. 현재 값 vs 7·30·90일 변화 — 동일 비교 집단의 모델별 효과')
fig.update_xaxes(tickangle=-25)
show(fig,'4-7_growth',650)
display(growth.groupby('지표·기간').agg(효과크기_중앙값=('효과 크기 절댓값','median'),
    양성_표본수=('positive_n','sum'),음성_표본수=('negative_n','sum')).sort_values('효과크기_중앙값',ascending=False))
display(read('negative_deltas').groupby('feature')[['available','negative_deltas']].sum().rename(index=labels))
''')
md('''### 4-6. 과거 입력 30·60·90일 확보율 (Q3)

전체 정제 기록에서 디스크별 날짜 순으로 창 안의 기록 수를 센다. **최근 90일의 90개 날짜가 모두 있어야 ‘90일 연속 확보’**다. 시작일·종료일만 보고 연속 이력이 있다고 추정하지 않는다. 고장·비고장 집단의 확보율 차이도 확인한다.

확보율은 데이터 사용 가능성이다. 가장 높은 예측 성능의 입력 기간을 입증하는 결과는 아니며, 90일 고정 여부는 이후 검증 기간에서 비교한다.
''')
code(r'''
history=read('history_availability')
history['집단']=history.label_30.map({0:'30일 내 고장 없음',1:'30일 내 고장'})
display(history.rename(columns={'snapshots':'디스크-월 표본 수','complete_30_pct':'30일 연속 확보(%)',
    'complete_60_pct':'60일 연속 확보(%)','complete_90_pct':'90일 연속 확보(%)'}))
histlong=history.melt(id_vars='집단',value_vars=['complete_30_pct','complete_60_pct','complete_90_pct'],
    var_name='입력 길이',value_name='연속 기록 확보율(%)')
histlong['입력 길이']=histlong['입력 길이'].map({'complete_30_pct':'30일','complete_60_pct':'60일','complete_90_pct':'90일'})
fig=px.bar(histlong,x='입력 길이',y='연속 기록 확보율(%)',color='집단',barmode='group',text_auto='.1f',
    color_discrete_map={'30일 내 고장 없음':C_OK,'30일 내 고장':C_FAIL},title='그림 4-8. 입력 이력이 길어질 때 사용 가능한 표본의 비율')
fig.update_yaxes(range=[0,105]);show(fig,'4-8_history')
display(read('gap_risk').rename(columns={'model':'HDD 모델','snapshots':'디스크-월 표본 수',
    'resumed_gap_pct':'직전 보고 공백 비율(%)','risk_after_gap':'공백 후 30일 고장 비율','risk_after_daily':'일별 보고 후 30일 고장 비율'}))
''')
md('''### 4-7. 공통 지표 규칙 기준선 (Q4)

모든 규칙을 **동일한 월별 평가 집단**에서 비교한다. 5·198의 현재 값과 30일 전 값이 모두 존재하는 표본만 사용한다. ‘양성’은 이후 30일 내 고장이고 고장 당일은 제외했다.

이 규칙들은 13개 공통 지표 범위의 새 기준선이다. 기존 단일 모델의 187·197 포함 규칙과 같은 규칙이 아니다. 월 경고에는 여러 달 반복 경고되는 디스크가 포함될 수 있다. **헛경보 비율은 실제 교체를 시뮬레이션한 헛교체율과 다르다.**
''')
code(r'''
rules=read('rule_baselines')
display(rules[['rule','months','actual_positives','monthly_alerts','recall_pct','precision_pct','false_alert_share_pct']].rename(
    columns={'rule':'규칙','months':'평가 월 수','actual_positives':'실제 양성 표본','monthly_alerts':'월평균 경고',
             'recall_pct':'재현율(%)','precision_pct':'정밀도(%)','false_alert_share_pct':'경고 중 헛경보(%)'}))
rules['표시']= ['손상 OR','재할당','복구 불가','손상 + 증가']
fig=px.scatter(rules,x='recall_pct',y='precision_pct',size='monthly_alerts',text='표시',size_max=60,
    hover_name='rule',hover_data=['monthly_alerts'],labels={'recall_pct':'재현율(%)','precision_pct':'정밀도(%)'},
    title='그림 4-9. 규칙의 탐지와 헛경보 사이 절충 — 점 크기는 월 경고 수')
fig.update_traces(textposition='top center');show(fig,'4-9_rule_tradeoff',600)
''')
md('''## 5. 인사이트 → 모델링 반영

### 5-1. 실제 결과 요약
''')
code(r'''
cohort=read('cohort').iloc[0];cleaning=read('clean_scale').iloc[0]
strong=ranking.head(3)
history_pos=history.loc[history.label_30.eq(1)].iloc[0]
base=rules.iloc[0];trend=rules.iloc[3]
display(Markdown(f"""
- **대상·기간**: HDD 20종, {int(cohort['disks']):,}개 디스크, 고장 {int(cohort['failed_disks']):,}개. 821일 실제 값을 읽었다.
- **품질**: 첫 고장 이후 {int(cleaning.raw_rows-cleaning.clean_rows):,}행을 제외했다. 모든 날짜의 디스크-날짜 중복은 0행이었다.
- **현재 값의 구분력**: 모델별 절대 순위 효과 중앙값이 큰 상위 지표는 **{', '.join(str(x) for x in strong.index)}**다. 값·단위 해석과 개별 모델 결과를 함께 확인한다.
- **입력 이력**: 고장 예정 월별 표본 중 연속 30일 확보율은 **{history_pos.complete_30_pct:.1f}%**, 60일은 **{history_pos.complete_60_pct:.1f}%**, 90일은 **{history_pos.complete_90_pct:.1f}%**다.
- **손상 OR 규칙**: 월평균 경고 **{base.monthly_alerts:,.0f}개**, 재현율 **{base.recall_pct:.1f}%**, 정밀도 **{base.precision_pct:.2f}%**.
- **30일 증가 조건 추가**: 월평균 경고 **{trend.monthly_alerts:,.0f}개**, 재현율 **{trend.recall_pct:.1f}%**, 정밀도 **{trend.precision_pct:.2f}%**. 경고 감소와 고장 누락을 함께 평가한다.
"""))
''')
code(r'''
growth_core=read('growth_effects_same_cohort')
growth_core['abs_r']=growth_core.rank_biserial.abs()
growth_medians=growth_core.groupby('feature').abs_r.median()
current5=growth_medians['smart_5_raw']; delta30=growth_medians['delta_smart_5_raw_30']; delta90=growth_medians['delta_smart_5_raw_90']
values=read('value_quality_by_model')
spin_values=values.loc[values.column.eq('smart_10_raw')]
constant10=spin_values['min'].eq(spin_values['max']).sum()
display(Markdown(f"**현재 값과 변화량의 실제 비교:** 동일 비교 집단에서 재할당 섹터(5)의 모델별 효과 크기 절댓값 중앙값은 현재 값 **{current5:.3f}**, 30일 변화 **{delta30:.3f}**, 90일 변화 **{delta90:.3f}**다. 이번 20종에서는 증가량이 현재 값보다 항상 더 잘 구분한다고 결론 내릴 수 없다. 둘을 함께 후보로 두고 검증한다."))
display(Markdown(f"**정보가 없는 공통 컬럼:** 회전 재시도 관련 raw(10)는 전 기간 **20종 중 {constant10}종에서 상수**였다. 기록 여부만으로 공통 13개를 모두 최종 입력으로 확정하지 않는다."))
''')
md('''### 5-2. 컬럼 후보 결정표

13개를 무조건 모두 입력하는 것이 아니라 실제 결과를 바탕으로 후보의 우선순위를 정한다. 효과 크기는 탐색적 관계이며 최종 선정은 학습 기간 안에서 확인한다.
''')
code("effect_data=read('effects_by_model')\ncurrent_effects=effect_data[effect_data.feature.isin(cols)].copy()\neffect_summary=current_effects.assign(abs_r=current_effects.rank_biserial.abs()).groupby('feature').abs_r.median().rename('효과크기_중앙값').reset_index()\ndecision=pd.read_csv(EDA/'analysis/column_definition_audit/column_policy_summary.csv')\ndecision=decision.merge(effect_summary,left_on='컬럼',right_on='feature',how='left').drop(columns='feature')\ndisplay(decision[['컬럼','지표','판정','효과크기_중앙값','처리방침']])")
md('''### 5-3. 적용 범위·한계·다음 단계

- 이 결과는 **선택한 20종**의 EDA다. 나머지 55종과 새로운 HDD 모델에 대한 성능은 보장하지 않는다.
- 20종 선정에 전체 기간의 고장 수를 사용한 탐색 분석이다. 최종 평가에서는 미래 고장 수를 보지 않고 학습 기간에서 대상을 정하는 절차도 검토한다.
- 월별 평가라 매일 경고하는 운영 시스템과 다르다. 규칙 결과는 전체 기간의 탐색적 기준선이며 별도 미래 테스트 성능이 아니다.
- 매칭 집단의 지표별 결측과 모델별 양성 수는 비교 표에 있다. 효과 크기·상관은 반복 관측과 상수 지표의 제약이 있다.
- 원본에 고장 원인은 없다. 미관측·탈락은 정상 수명 완료가 아니다. 수리·재투입 기록을 첫 고장 이후 제거해 하나의 생애만 사용했다.
- SMART 정의·원시값 인코딩은 모델·펌웨어별 확인이 더 필요하다. 컬럼 이름만 같다는 이유로 단위를 통일하지 않는다.
- 다음 단계는 30일 라벨을 유지하고 현재 값·변화량 후보로 통합 기준 모델을 학습하는 것이다. 입력 30·60·90일은 검증 기간에서 비교하며, 제조사별/개별 모델별 학습은 기본 모델 결과를 보고 결정한다.
- 시간 분할 시 학습 표본의 미래 30일 라벨이 검증 구간으로 넘어가지 않도록 경계 표본을 제외한다. 마지막 평가 구간도 완전한 미래 30일을 확인할 수 있는 시점만 쓴다.

### 재현 경로

1. `scripts/09_extract_top20_common13.py`: 원본 821일에서 실제 값 추출·일별 중복 검사
2. `scripts/10_analyze_top20_common13.py`: 첫 고장 정제·월별 라벨·매칭·전체 품질·궤적·규칙 계산
3. `scripts/11_build_detailed_eda_v2.py`: 이 노트북 구성
4. `scripts/execute_eda_v2.py`: 셀 실행·실제 출력 저장

중간값·결과 CSV/Parquet은 `analysis/detailed_v2/`에 있으며, 이전 사용자 편집 노트북은 `analysis/v2/eda_v2_before_detailed.ipynb`에 보존한다. 새 세션에서 원본 단계부터 재현하려면 1→2→3→4 순서로 실행한다.
''')
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.14.6'}})
nbf.validate(nb);nbf.write(nb,EDA/'eda_v2_87%.ipynb')
print('Built detailed notebook:',len(cells),'cells',flush=True)
