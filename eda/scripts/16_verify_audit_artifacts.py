"""Verify the audit/notebook and refresh only charts whose terminology changed."""
from pathlib import Path
import ast,json
import pandas as pd
import nbformat as nbf
import plotly.io as pio

EDA=Path(__file__).resolve().parents[1]
AUDIT=EDA/'analysis/column_definition_audit'
nb=nbf.read(EDA/'eda_v2_87%.ipynb',as_version=4)
extra='''

정의·단위 검토를 다시 수행할 때는 `scripts/13_fetch_smart_definitions.py`로 원문을 확보하고 `scripts/14_audit_smart_definitions.py`로 260개 조합을 검토한다. 이 결과의 `column_policy_summary.csv`가 노트북 2-2와 5-2의 근거다. 공개 자료의 제품군 정의와 데이터의 동작을 대조한 것이며, 누락된 펌웨어·내부 수집 변환 정보를 추정으로 채우지 않는다.
'''
tail=next(c for c in nb.cells if c.cell_type=='markdown' and '### 재현 경로' in c.source)
if '13_fetch_smart_definitions.py' not in tail.source:tail.source+=extra
nbf.validate(nb)
assert not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
for c in nb.cells:
    if c.cell_type!='code':continue
    tree=ast.parse(c.source)
    show_calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
        and n.func.id=='show' and len(n.args)>1 and isinstance(n.args[1],ast.Constant)]
    names=[n.args[1].value for n in show_calls]
    charts=[o.data['application/vnd.plotly.v1+json'] for o in c.outputs
            if o.output_type=='display_data' and 'application/vnd.plotly.v1+json' in o.data]
    assert len(names)==len(charts)
    for name,chart in zip(names,charts):
        text=json.dumps(chart,ensure_ascii=False)
        if '회전 시작 관련 raw' not in text and '회전 재시도 관련 raw' not in text:continue
        fig=pio.from_json(text)
        height=int(fig.layout.height or 600)
        fig.write_html(EDA/'analysis/detailed_v2/figures'/f'{name}.html',include_plotlyjs=True)
        fig.write_image(EDA/'analysis/detailed_v2/figures'/f'{name}.png',width=1250,height=height)
        print('Updated chart:',name,flush=True)
nbf.write(nb,EDA/'eda_v2_87%.ipynb')
matrix=pd.read_csv(AUDIT/'model_column_audit.csv')
assert len(matrix)==260 and not matrix[['model','column']].duplicated().any()
assert matrix.groupby('model').size().eq(13).all()
policy=pd.read_csv(AUDIT/'column_policy_summary.csv')
assert policy['판정'].value_counts().to_dict()=={'조건부 공통 후보':8,'기본 입력 보류':5}
assert matrix.loc[(matrix.model=='ST14000NM0138') & (matrix.column=='smart_192_raw'),'evidence'].str.contains('Dell').all()
for path in (EDA/'scripts').glob('1[3-6]_*.py'):ast.parse(path.read_text(encoding='utf-8'))
print('VERIFIED: 260 audit rows, 20 models, 13 fields, 8 conditional / 5 held; notebook outputs valid.')
