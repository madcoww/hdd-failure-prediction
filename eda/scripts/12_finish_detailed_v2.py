"""Add data-derived interpretations without rerunning the full extraction or plots."""
from pathlib import Path
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

eda=Path(__file__).resolve().parents[1]
p=eda/'eda_v3_87%.ipynb'
nb=nbf.read(p,as_version=4)
assert not any(c.id=='detailed-growth-interpretation' for c in nb.cells)
shell=InteractiveShell.instance()
result=shell.run_cell(next(c.source for c in nb.cells if c.cell_type=='code'))
assert not (result.error_before_exec or result.error_in_exec)
note=nbf.v4.new_markdown_cell('''회전 시작·정지 횟수(4)와 전원 인가 횟수(12)의 모델 내 상관 중앙값은 매우 높지만, 전 기간 값을 직접 비교하면 **20종 중 1종에서만 모든 행이 동일**했다. 높은 상관만으로 두 컬럼을 전체 모델에서 동일한 열로 간주하지 않는다. 근거: `analysis/detailed_v2/start_stop_vs_power_exact.csv`.''')
idx=next(i for i,c in enumerate(nb.cells) if c.cell_type=='code' and "show(fig,'4-5_correlation'" in c.source)
nb.cells.insert(idx+1,note)
source='''growth_core=read('growth_effects_same_cohort')
growth_core['abs_r']=growth_core.rank_biserial.abs()
growth_medians=growth_core.groupby('feature').abs_r.median()
current5=growth_medians['smart_5_raw']
delta30=growth_medians['delta_smart_5_raw_30']
delta90=growth_medians['delta_smart_5_raw_90']
values=read('value_quality_by_model')
spin_values=values.loc[values.column.eq('smart_10_raw')]
constant10=spin_values['min'].eq(spin_values['max']).sum()
display(Markdown(f"**현재 값과 변화량의 실제 비교:** 동일 비교 집단에서 재할당 섹터(5)의 모델별 효과 크기 절댓값 중앙값은 현재 값 **{current5:.3f}**, 30일 변화 **{delta30:.3f}**, 90일 변화 **{delta90:.3f}**다. 이번 20종에서는 증가량이 현재 값보다 항상 더 잘 구분한다고 결론 내릴 수 없다. 둘을 함께 후보로 두고 검증한다."))
display(Markdown(f"**정보가 없는 공통 컬럼:** 회전 재시도 횟수(10)는 전 기간 **20종 중 {constant10}종에서 상수**였다. 기록 여부만으로 공통 13개를 모두 최종 입력으로 확정하지 않는다."))'''
cell=nbf.v4.new_code_cell(source,id='detailed-growth-interpretation')
with capture_output() as cap:result=shell.run_cell(source)
assert not (result.error_before_exec or result.error_in_exec)
cell.execution_count=15
cell.outputs=[nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata) for o in cap.outputs]
idx=next(i for i,c in enumerate(nb.cells) if c.cell_type=='markdown' and c.source.startswith('### 5-2.'))
nb.cells.insert(idx,cell)
nbf.validate(nb);nbf.write(nb,p)
print('Added verified growth and redundancy interpretations.')
