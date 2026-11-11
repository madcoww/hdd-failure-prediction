"""Add one full-HDD normal/failure chart to v1, preserving all other cells."""
from pathlib import Path
import re,json
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

eda=Path(__file__).resolve().parents[1]
path=eda/'eda_v1_5%.ipynb'
original=path.read_text(encoding='utf-8')
nb=nbf.reads(original,as_version=4)
assert not any(c.id=='v1-full-hdd-ratio' for c in nb.cells)
idx=next(i for i,c in enumerate(nb.cells) if c.cell_type=='markdown' and c.source.startswith('## 3. 전처리'))
section=nb.cells[idx]
assert section.source.endswith('### 3-1. 결측치')
heading=nbf.v4.new_markdown_cell('''## 3. 전처리 (데이터 품질 점검 포함)

### 3-0. SSD 제외 후 전체 HDD의 정상·고장 비율

원본 97개 모델에서 SSD 21종과 물리 HDD 모델이 아닌 `DELLBOSS VD`를 제외해 **HDD 75종**만 집계한다. 시리얼별로 한 번이라도 고장 표시가 있으면 고장 디스크로 분류하므로 중복 고장 행은 중복 계산하지 않는다.

아래 그래프는 **전체 HDD 기준**이며, 이후 SMART 상세 분석은 기존과 같이 ST12000NM0008 한 제품 기준이다. ‘정상’은 관측 기간(2024-04-01~2026-06-30)에 고장 기록이 없다는 뜻이다. 이 비율은 연간 고장률이나 ‘30일 내 고장’ 학습 라벨의 비율과 다르다.
''')
source=r'''
# 원본 전체에서 HDD 대상만 선정 (SSD 21종 + DELLBOSS VD 제외)
all_model_rank_v1 = pd.read_csv(EDA.parent / 'data/backblaze/summary/model_rank.csv')
hdd_model_names_v1 = all_model_rank_v1.loc[
    all_model_rank_v1['model'].str.match(r'^(ST\d|HGST |Hitachi |TOSHIBA |WDC WUH|WUH|WDC WD\d)'), ['model']]
assert len(hdd_model_names_v1) == 75
con.register('hdd_model_names_v1', hdd_model_names_v1)
hdd_status_v1 = q("""
WITH per_disk AS (
    SELECT d.serial_number, max(coalesce(d.failure, 0)) AS ever_failed
    FROM 'C:/hdd-failure-prediction/data/backblaze/fleet_slim/*.parquet' d
    JOIN hdd_model_names_v1 h ON d.model=h.model
    GROUP BY d.serial_number
)
SELECT CASE WHEN ever_failed=1 THEN '고장' ELSE '정상 (고장 기록 없음)' END AS 구분,
       count(*) AS 디스크_수
FROM per_disk GROUP BY ever_failed ORDER BY ever_failed
""")
hdd_status_v1['비율_pct'] = 100*hdd_status_v1['디스크_수']/hdd_status_v1['디스크_수'].sum()
hdd_total_v1 = int(hdd_status_v1['디스크_수'].sum())
failed_count_v1 = int(hdd_status_v1.loc[hdd_status_v1['구분'].eq('고장'),'디스크_수'].iloc[0])
failed_pct_v1 = 100*failed_count_v1/hdd_total_v1
fig_hdd_ratio_v1 = go.Figure(go.Pie(
    labels=hdd_status_v1['구분'],values=hdd_status_v1['디스크_수'],hole=.66,sort=False,
    marker=dict(colors=[C_OK,C_FAIL]),textinfo='none',
    hovertemplate='%{label}<br>%{value:,}개 (%{percent})<extra></extra>'))
fig_hdd_ratio_v1.update_layout(
    title='그림 3-0. SSD 제외 후 전체 HDD의 정상·고장 비율',
    legend=dict(orientation='h',x=.5,xanchor='center',y=-.08,yanchor='top'),
    annotations=[dict(x=.5,y=.5,xref='paper',yref='paper',showarrow=False,
        xanchor='center',yanchor='middle',
        text=f'<b>전체 HDD {hdd_total_v1:,}개</b><br>정상 {100-failed_pct_v1:.2f}%<br>고장 {failed_pct_v1:.2f}%')],
    margin=dict(l=30,r=30,t=80,b=65),width=900,height=500)
ratio_fig_dir_v1=FIG/'eda_v1'
ratio_fig_dir_v1.mkdir(exist_ok=True)
fig_hdd_ratio_v1.write_image(ratio_fig_dir_v1/'3-0_full_hdd_status_ratio.png',width=900,height=500,scale=2)
from IPython.display import display
display({'application/vnd.plotly.v1+json':json.loads(fig_hdd_ratio_v1.to_json())},raw=True)
'''.strip()
# json is deliberately imported in the new cell; it does not change v1 setup.
source='import json\n'+source
cell=nbf.v4.new_code_cell(source,id='v1-full-hdd-ratio')
shell=InteractiveShell.instance()
setup=next(c for c in nb.cells if c.cell_type=='code')
result=shell.run_cell(setup.source)
assert not(result.error_before_exec or result.error_in_exec)
with capture_output() as cap:result=shell.run_cell(source)
assert not(result.error_before_exec or result.error_in_exec),cap.stdout
cell.execution_count=1
cell.outputs=[nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata) for o in cap.outputs]
assert int(shell.user_ns['hdd_total_v1'])==386919
assert int(shell.user_ns['failed_count_v1'])==10518
next_heading=nbf.v4.new_markdown_cell('### 3-1. 결측치')
replacement_cells=[heading,cell,next_heading]

# Keep the rest of the large v1 JSON byte-for-byte (including existing plot numbers).
starts=[m.start() for m in re.finditer(r'^  \{\r?\n   "cell_type":',original,re.M)]
assert len(starts)==len(nb.cells)
begin=starts[idx];end=starts[idx+1]
block=',\n'.join('\n'.join('  '+line for line in json.dumps(dict(c),ensure_ascii=False,indent=1).splitlines()) for c in replacement_cells)+',\n'
updated=original[:begin]+block+original[end:]
result_nb=nbf.reads(updated,as_version=4)
nbf.validate(result_nb)
assert len(result_nb.cells)==len(nb.cells)+2
assert result_nb.cells[:idx]==nb.cells[:idx]
assert result_nb.cells[idx+3:]==nb.cells[idx+1:]
path.write_text(updated,encoding='utf-8',newline='')
print('Added one chart in eda_v1_5%.ipynb section 3-0. Normal: 376401 (97.28%); failed: 10518 (2.72%).')
