"""Add purpose-specific plots without rebuilding or replacing existing notebook cells."""
from pathlib import Path
import os
import json
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

eda = Path(__file__).resolve().parents[2]
os.chdir(eda)
path = eda / 'eda_v3_87%.ipynb'
nb = nbf.read(path, as_version=4)
shell = InteractiveShell.instance()
setup = next(c for c in nb.cells if c.cell_type=='code')
result = shell.run_cell(setup.source)
assert not (result.error_before_exec or result.error_in_exec)

def run(source):
    with capture_output() as captured:
        result = shell.run_cell(source)
    if result.error_before_exec or result.error_in_exec:
        raise RuntimeError(result.error_before_exec or result.error_in_exec)
    outputs = []
    if captured.stdout: outputs.append(nbf.v4.new_output('stream',name='stdout',text=captured.stdout))
    if captured.stderr: outputs.append(nbf.v4.new_output('stream',name='stderr',text=captured.stderr))
    outputs.extend(nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata) for o in captured.outputs)
    return outputs

def insert_after(marker, label, explanation, source):
    cell_id = 'v2-visual-' + label
    if any(c.id == cell_id for c in nb.cells):
        raise RuntimeError(f'Already inserted {cell_id}')
    index = next(i for i,c in enumerate(nb.cells) if c.cell_type=='code' and marker in c.source)
    note = nbf.v4.new_markdown_cell(explanation.strip())
    cell = nbf.v4.new_code_cell(source.strip(), id=cell_id)
    cell.outputs = run(cell.source)
    cell.execution_count = 1
    nb.cells[index+1:index+1] = [note,cell]

insert_after('device_summary = inventory.groupby', 'composition', '''
**그림 2-1. 장치 구성 — 모델 종류 비율과 실제 디스크 수 비율**

왼쪽은 제품 종류 수, 오른쪽은 디스크 개수다. SSD는 종류 수로는 약 22%지만 실제 디스크 수로는 1% 미만이다. 두 그래프의 분모가 다르므로 구분해서 읽는다.
''', r'''
from plotly.subplots import make_subplots
composition = pd.read_csv(OUT/'device_type_ratios.csv').set_index('device_type').reindex(['HDD','SSD','별도 제외'])
fig = make_subplots(rows=1,cols=2,specs=[[{'type':'domain'},{'type':'domain'}]],
                    subplot_titles=['모델 종류 수 기준 (전체 97종)','실제 디스크 수 기준 (전체 390,540개)'])
for column, field in enumerate(['모델_종류','모델별_디스크수_합'],start=1):
    fig.add_pie(labels=composition.index,values=composition[field],hole=0.58,
                marker=dict(colors=[C_OK,C_FAIL,C_GRAY]),sort=False,
                textinfo='none',
                hovertemplate='%{label}<br>%{value:,}<br>%{percent}<extra></extra>',row=1,col=column)
fig.add_annotation(x=0.225,y=0.5,xref='paper',yref='paper',showarrow=False,xanchor='center',yanchor='middle',
                   text='<b>모델 97종</b><br>HDD 77.32%<br>SSD 21.65%<br>별도 제외 1.03%')
fig.add_annotation(x=0.775,y=0.5,xref='paper',yref='paper',showarrow=False,xanchor='center',yanchor='middle',
                   text='<b>디스크 390,540개</b><br>HDD 99.07%<br>SSD 0.82%<br>별도 제외 0.11%')
fig.update_layout(title='그림 2-1. 모델 종류가 많은 것과 디스크가 많은 것은 다르다',
                  height=440,legend=dict(orientation='h',y=-0.05,x=0.4))
show_plot(fig,'2-1_device_composition')
''')

insert_after("show_plot(fig,'4-1_model_failures')", 'scatter', '''
**그림 4-1b. 디스크 수와 고장 수의 관계 — HDD 75종 전체**

한 점은 HDD 모델 하나다. 오른쪽은 보유 디스크가 많고, 위쪽은 고장 사례가 많다. 고장 수만으로 위험도를 판단하지 않는다. 색은 제조사 계열이고, 자세한 모델명·관측 기간 내 고장 비율은 점에 마우스를 올리면 확인할 수 있다. 노출 기간이 다르므로 이 비율을 연간 고장률로 해석하지 않는다.
''', r'''
scatter_data=pd.read_csv(OUT/'hdd_model_cases.csv')
def vendor_group(model):
    if model.startswith('ST'): return 'Seagate'
    if model.startswith(('HGST','Hitachi')): return 'HGST / Hitachi'
    if model.startswith('TOSHIBA'): return 'Toshiba'
    return 'Western Digital'
scatter_data['제조사 계열']=scatter_data['model'].map(vendor_group)
fig=px.scatter(scatter_data,x='disks',y='failed_disks',log_x=True,color='제조사 계열',
               color_discrete_map={'Seagate':'#2a78d6','HGST / Hitachi':'#eb6834','Toshiba':'#1baf7a','Western Digital':'#9b6bc9'},
               hover_name='model',hover_data={'disks':':,','failed_disks':':,','관측기간_고장비율_pct':':.2f'},
               labels={'disks':'디스크 수 (로그 축)','failed_disks':'고장 디스크 수','관측기간_고장비율_pct':'관측 기간 내 고장 비율(%)'},
               title='그림 4-1b. HDD 모델별 디스크 수와 고장 사례 수')
fig.update_traces(marker=dict(size=10,opacity=0.8,line=dict(width=1,color='white')))
fig.update_layout(height=540,legend=dict(orientation='v',y=0.98,x=0.02,yanchor='top',xanchor='left'))
show_plot(fig,'4-1b_model_scatter')
''')

insert_after("show_plot(fig,'4-3_smart_coverage')", 'heatmap', '''
**그림 4-3b. 모델별 SMART 기록률 — 고장 사례 상위 20종**

가로는 지표, 세로는 HDD 모델이다. 숫자는 **18일 표본에서 값이 기록된 행 비율(%)**이다. 여기서 0은 SMART 원시값이 0이라는 뜻이 아니라 **해당 지표가 미기록**됐다는 뜻이다. 75종 전체의 상세 기록률은 `analysis/v2/hdd_model_smart_coverage.csv`에 있다. 이 그림은 기록 여부를 비교하며 예측력이나 단위 호환성을 보여주지 않는다.
''', r'''
heat_coverage=pd.read_csv(OUT/'hdd_model_smart_coverage.csv').set_index('model')
heat_cases=pd.read_csv(OUT/'hdd_model_cases.csv').head(20)
heat_features={5:'재할당 섹터(5)',9:'가동 시간(9)',194:'온도(194)',197:'대기 섹터(197)',
               198:'복구 불가 섹터(198)',187:'정정 불가 오류(187)',188:'명령 시간 초과(188)',
               193:'헤드 로드·언로드(193)',241:'누적 쓰기(241)',242:'누적 읽기(242)'}
heat_values=heat_coverage.loc[heat_cases['model'],[f'smart_{i}_raw' for i in heat_features]]
heat_values.columns=list(heat_features.values())
fig=px.imshow(heat_values.round(1),aspect='auto',zmin=0,zmax=100,
              color_continuous_scale=[[0,'#f1f0eb'],[1,C_OK]],text_auto='.0f',
              labels={'x':'SMART 지표','y':'HDD 모델','color':'기록률(%)'},
              title='그림 4-3b. 같은 지표도 HDD 모델에 따라 기록 여부가 다르다')
fig.update_traces(hovertemplate='%{y}<br>%{x}<br>표본 기록률: %{z:.2f}%<extra></extra>')
fig.update_xaxes(tickangle=-35,side='bottom')
fig.update_layout(height=800)
show_plot(fig,'4-3b_smart_heatmap')
''')

# Use a line for the existing time-series chart; preserve the table and explanatory output.
quarter_cell=next(c for c in nb.cells if c.cell_type=='code' and "show_plot(fig,'4-2_quarterly_failures')" in c.source)
quarter_cell.source=quarter_cell.source.replace("fig = px.bar(quarterly", "fig = px.line(quarterly",1)
quarter_cell.source=quarter_cell.source.replace("color_discrete_sequence=[C_FAIL])", "color_discrete_sequence=[C_FAIL], markers=True)",1)
plot_start=quarter_cell.source.index('fig = px.line')
plot_end=quarter_cell.source.index("show_plot(fig,'4-2_quarterly_failures')")+len("show_plot(fig,'4-2_quarterly_failures')")
plot_outputs=run("quarterly=pd.read_csv(OUT/'hdd_quarterly.csv')\n"+quarter_cell.source[plot_start:plot_end])
plot_output=next(o for o in plot_outputs if o.output_type=='display_data' and 'application/vnd.plotly.v1+json' in o.data)
for i,o in enumerate(quarter_cell.outputs):
    if o.output_type=='display_data' and 'application/vnd.plotly.v1+json' in o.data:
        quarter_cell.outputs[i]=plot_output

nbf.validate(nb)
nbf.write(nb,path)

# Render the three new charts for inspection without changing their notebook outputs.
import plotly.io as pio
for label,name,width,height in [('composition','2-1_device_composition',1100,440),
                               ('scatter','4-1b_model_scatter',1100,600),
                               ('heatmap','4-3b_smart_heatmap',1250,900)]:
    cell=next(c for c in nb.cells if c.id=='v2-visual-'+label)
    chart=next(o.data['application/vnd.plotly.v1+json'] for o in cell.outputs if o.output_type=='display_data' and 'application/vnd.plotly.v1+json' in o.data)
    pio.from_json(json.dumps(chart)).write_image(eda/'analysis/v2'/f'{name}.png',width=width,height=height)
print('Added 3 visualizations, changed quarterly chart to a line, preserved existing cells and outputs.')
