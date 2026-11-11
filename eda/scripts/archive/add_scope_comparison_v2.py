"""Add full-period scope comparison while preserving user edits and existing EDA."""
from pathlib import Path
import os
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

eda=Path(__file__).resolve().parents[2]
os.chdir(eda)
path=eda/'eda_v3_87%.ipynb'
nb=nbf.read(path,as_version=4)
assert not any(c.id=='v2-scope-comparison' for c in nb.cells)
shell=InteractiveShell.instance()
result=shell.run_cell(next(c.source for c in nb.cells if c.cell_type=='code'))
assert not (result.error_before_exec or result.error_in_exec)

def executed(source,ident):
    cell=nbf.v4.new_code_cell(source.strip(),id=ident)
    with capture_output() as cap: result=shell.run_cell(cell.source)
    assert not (result.error_before_exec or result.error_in_exec)
    cell.outputs=[nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata) for o in cap.outputs]
    cell.execution_count=1
    return cell

intro=nbf.v4.new_markdown_cell('''### 2-4. 상위 20종과 HDD 전체 75종의 범위 비교

아래 비율의 분모는 **HDD 75종 전체**다. 고장 디스크 수가 많은 순서의 상위 20종을 선택하면 실제 HDD의 **87.38%**, 고장 디스크의 **94.31%**를 포함한다.

공통 SMART 개수는 **821일 전수 확인 결과**다. 공통으로 기록된다는 뜻이며, 모든 컬럼의 의미·단위가 호환되거나 예측력이 검증됐다는 뜻은 아니다.
''')
scope=executed(r'''
case_counts=pd.read_csv(OUT/'hdd_model_cases.csv')
top20_cases=case_counts.head(20)
full_check=EDA/'analysis/full_column_check'
full_check_manifest=json.loads((full_check/'manifest.json').read_text(encoding='utf-8'))
assert full_check_manifest['days_checked']==full_check_manifest['days_expected']==821
scope_rows=[]
for label,frame,key in [('상위 20종',top20_cases,'top20'),('HDD 75종 전체',case_counts,'hdd75')]:
    verified=pd.read_csv(full_check/f'{key}_common_columns.csv')
    scope_rows.append({'대상':label,'모델 종류':len(frame),'디스크 수':int(frame.disks.sum()),
        '디스크 수 비율(%)':round(100*frame.disks.sum()/case_counts.disks.sum(),2),
        '고장 디스크 수':int(frame.failed_disks.sum()),
        '고장 디스크 비율(%)':round(100*frame.failed_disks.sum()/case_counts.failed_disks.sum(),2),
        '공통 SMART 수':int(verified.models_with_values.eq(len(frame)).sum())})
scope_comparison=pd.DataFrame(scope_rows)
display(scope_comparison)
scope_comparison.to_csv(OUT/'top20_vs_hdd75.csv',index=False,encoding='utf-8-sig')
''','v2-scope-comparison')
idx=next(i for i,c in enumerate(nb.cells) if c.cell_type=='markdown' and c.source.startswith('## 3.'))
nb.cells[idx:idx]=[intro,scope]

note=nbf.v4.new_markdown_cell('''### 4-3c. 전체 821일에서 확인한 상위 20종 공통 SMART

앞의 기록률 그래프·히트맵은 기존 **18일 표본 시각화**다. 공통 컬럼의 최종 기록 여부는 아래 **821일 전수 결과**를 사용한다. 전수 확인에서도 상위 20종의 공통 SMART는 **13개**로 같았다.

**13개 기준으로 상세 EDA를 진행한다면** 분석 대상은 상위 20종으로 좁히고, 다음 순서로 진행한다.

1. 공통 13개 지표의 모델별 의미·단위·결측·이상값·리셋을 확인한다.
2. 같은 모델·비슷한 시점의 고장/정상을 비교해 모델 차이와 고장 신호를 구분한다.
3. 고장 전 변화와 최근 7일·30일 증가량을 비교한다. 과거 30·60·90일 입력은 후보로 두고 기록 확보 여부를 확인한다.
4. 중복되거나 정보가 약한 컬럼을 검토해 최종 입력을 정하고, 단순 SMART 규칙 기준선을 계산한다.

이것은 **다음 상세 EDA의 범위 제안**이다. 현재 노트북의 전체 규모·품질 점검은 HDD 75종 기준이며, 위 상세 분석을 새로 수행한 상태는 아니다. 적용 범위도 우선 분석한 20종으로 한정한다. 향후 성능 평가 시에는 평가 기간의 고장 수를 보고 대상을 고르지 않도록 학습 기간 기준 선정도 재확인한다.
''')
columns=executed(r'''
full_top20=pd.read_csv(full_check/'top20_common_columns.csv')
common13=full_top20.loc[full_top20.models_with_values.eq(20)].copy()
common_names={1:'읽기 오류 관련 지표',3:'모터 회전 시작 시간',4:'회전 시작·정지 횟수',
    5:'재할당 섹터 수',7:'헤드 탐색 오류 관련 지표',9:'누적 가동 시간',10:'회전 재시도 횟수',
    12:'전원 인가 횟수',192:'전원 차단·헤드 회수 관련 지표',193:'헤드 로드·언로드 횟수',
    194:'온도',198:'오프라인 복구 불가 섹터 수',199:'인터페이스 CRC 오류'}
common13['의미']=common13.column.map(lambda c:common_names[int(c.split('_')[1])])
common13=common13.rename(columns={'column':'컬럼','models_with_values':'기록 모델 수',
    'models_with_values_each_day':'매 관측일 기록 모델 수','min_nonnull_pct':'모델별 최소 기록률(%)'})
assert len(common13)==13
display(common13[['컬럼','의미','기록 모델 수','매 관측일 기록 모델 수','모델별 최소 기록률(%)']])
''','v2-verified-common13')
idx=next(i for i,c in enumerate(nb.cells) if c.cell_type=='markdown' and c.source.startswith('### 4-4.'))
nb.cells[idx:idx]=[note,columns]
nbf.validate(nb)
nbf.write(nb,path)
print('Added HDD scope comparison and full-period common13 evidence; existing cells preserved.')
