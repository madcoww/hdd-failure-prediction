"""Write the evidence report and update only definition/policy parts of the current notebook."""
from pathlib import Path
import shutil,json,ast
import pandas as pd
import nbformat as nbf
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output

EDA=Path(__file__).resolve().parents[1]
AUDIT=EDA/'analysis/column_definition_audit'
matrix=pd.read_csv(AUDIT/'model_column_audit.csv')
summary=pd.read_csv(AUDIT/'column_policy_summary.csv')
clock=pd.read_csv(AUDIT/'power_on_time_behavior.csv')
manifest=json.loads((AUDIT/'audit_manifest.json').read_text(encoding='utf-8'))
assert len(matrix)==260 and manifest['original_schema_days_checked']==821
held={1,3,7,10,192}
summary['입력후보판정']=summary['컬럼'].map(lambda c:'기본 입력 보류' if int(c.split('_')[1]) in held else '조건부 공통 후보')
summary.to_csv(AUDIT/'column_policy_summary.csv',index=False,encoding='utf-8-sig')
refs={
 'Seagate SMART 공식 설명':'https://github.com/Seagate/openSeaChest/wiki/Drive-Health-and-SMART',
 'smartmontools 모델별 해석 규칙':'https://github.com/smartmontools/smartmontools/blob/main/drivedb/drivedb.h',
 'smartmontools raw 조합·표시 코드':'https://github.com/smartmontools/smartmontools/blob/main/lib/atacmds.cpp',
 'smartctl JSON 출력 코드':'https://github.com/smartmontools/smartmontools/blob/main/src/ataprint.cpp',
 'Toshiba 온도·SMART 예제':'https://www.toshiba-storage.com/wp/wp-content/uploads/2022/07/Toshiba_OpenE_Blogpost_July2022_final.pdf',
 'Backblaze 실제 수집 구조':'https://www.backblaze.com/blog/drive-stats-data-deep-dive-the-architecture/',
 'Dell ST14000NM0138 펌웨어 공지':'https://www.dell.com/support/home/en-pr/drivers/driversdetails?driverid=v3n1t',
}
header='''### 2-2. 공통 SMART 13개 — 정의·단위 선행 검토

**기록 여부는 821일 전수 확인, 의미·단위는 제조사 자료·해석 코드·실제 값의 동작을 별도로 대조했다.** 20종 × 13개 지표의 검토표(260행)를 만들었다. 이는 260개 모두의 펌웨어별 상세 사양을 제조사가 보증했다는 뜻이 아니다.

이번 검토의 처리 방침은 **조건부 공통 후보 8개 / 통합 기본 입력 보류 5개**다. 아래에서 ‘조건부’란 현재 데이터의 의미와 해석 근거가 비교적 일치하므로 모델 식별자·값 검증을 함께 사용하는 후보라는 뜻이다. 모든 제조사에서 같은 원시값이 같은 고장 위험이나 동일한 바이트 손상을 뜻한다는 뜻은 아니다.

- **가동 시간(9)**: 20종 모두 30일 간 증가량을 일 단위로 나눈 중앙값이 약 **23.93~24.07**이었다. 제품군의 Power On Hours 정의와도 일치해 이 데이터에서는 **시간(h)**으로 해석한다. 감소·리셋 구간은 따로 다룬다.
- **현재 온도(194)**: 제품군 문서·해석 도구는 섭씨로 정의하며, CSV는 13~112의 단일 수치다. 현재 CSV를 ℃로 사용하는 후보로 두되, 101·112 같은 극단값은 센서·수집 이상 가능성을 별도 검토한다. 원본 패킷을 확보하지 못했으므로 임의로 비트 분해하지 않는다.
- **읽기/탐색 오류(1·7)**: Seagate 공식 설명과 제품군별 해석 코드에서 복합 필드가 확인된다. raw 정수 전체를 단일 오류 횟수로 쓰거나 `raw>0`을 오류 발생으로 해석하지 않는다.
- **회전 시작(3)·회전 재시도(10)**: 현재값·평균값·집계 구간 해석을 구분해야 한다. 3은 10종, 10은 19종에서 전 기간 상수였으며 기본 입력은 보류한다.
- **비상 헤드 회수(192)**: 제조사별 집계 조건이 다르고, ST14000NM0138에는 부정확한 증가를 수정한 공식 펌웨어 공지가 있다. 현재 데이터의 펌웨어 버전이 없어 해당 오류의 영향 여부를 알 수 있으므로 기본 입력을 보류한다.

**확인 한계**: 원본 821개 CSV의 스키마에 펌웨어·수집 도구 버전·섹터 크기 필드가 없다. 현재 도구 DB와 모델명이 정확히 일치한 것은 10종, 접미사 생략으로 제품군을 추정한 것은 9종, DB 규칙을 찾지 못한 것은 1종(ST14000NM0138)이다. 이 1종은 Dell 공지에서 OEM 모델로 확인했다. 제조사 비공개 raw 수식과 Backblaze 내부 변환 코드는 확보하지 못했다.

수집 경로도 구분했다. smartctl은 raw 정수와 사람이 읽는 표시 문자열을 별도로 만들지만, Backblaze는 자체 C++ 수집기→XML→집계 모듈 구조라고 설명한다. **현재 CSV가 최신 smartctl의 `raw.value`를 그대로 저장했다는 가정은 하지 않는다.**

근거: [Seagate 공식 SMART 설명](https://github.com/Seagate/openSeaChest/wiki/Drive-Health-and-SMART), [모델별 도구 해석 규칙](https://github.com/smartmontools/smartmontools/blob/main/drivedb/drivedb.h), [Toshiba 자료](https://www.toshiba-storage.com/wp/wp-content/uploads/2022/07/Toshiba_OpenE_Blogpost_July2022_final.pdf), [Backblaze 수집 구조](https://www.backblaze.com/blog/drive-stats-data-deep-dive-the-architecture/), [Dell 펌웨어 공지](https://www.dell.com/support/home/en-pr/drivers/driversdetails?driverid=v3n1t).

상세 근거는 `analysis/column_definition_audit/model_column_audit.csv`, 제품군 매칭은 `model_family_matches.csv`, 원문·해시는 `source_manifest.json`에 있다. 원본 값과 기존 13개 탐색 통계는 보존하며, 이를 ‘13개 모두 통합 입력 검증 완료’로 해석하지 않는다.
'''
# Fix the explicitly unknown firmware impact phrasing, preserving uncertainty.
header=header.replace('해당 오류의 영향 여부를 알 수 있으므로','해당 오류의 영향 여부를 알 수 없으므로')
report=['# SMART 정의·단위 선행 검토 — HDD 20종 × 13개','',header.replace('### 2-2. 공통 SMART 13개 — 정의·단위 선행 검토','## 검토 결론'),'',
        '| 컬럼 | 의미 | 해석·단위 | 입력후보판정 |','|---|---|---|---|']
for r in summary.to_dict('records'):
    report.append(f"| `{r['컬럼']}` | {r['지표']} | {r['해석']} | {r['입력후보판정']} |")
report.extend(['','## 원문 자료',*[f'- [{name}]({url})' for name,url in refs.items()], '',
              '## 파일', '- `model_column_audit.csv`: 20종 × 13개 검토·처리 방침·근거·확인 한계',
              '- `model_family_matches.csv`: 정확한 모델명 매칭 / 제품군 추정 / 미일치 구분',
              '- `power_on_time_behavior.csv`: 모델별 30일 간 가동시간 변화 검증',
              '- `column_policy_summary.csv`: 지표별 요약',
              '- `audit_manifest.json`: 범위·확인 수준',
              '- `source_manifest.json`: 내려받은 원문 URL·조회 시각·SHA-256', '',
              '단위·의미 검토만 수행했다. raw 값을 변환하거나 새로운 예측 모델을 학습하지 않았다.'])
(AUDIT/'README.md').write_text('\n'.join(report)+'\n',encoding='utf-8')

path=EDA/'eda_v3_87%.ipynb'
nb=nbf.read(path,as_version=4)
backup=AUDIT/'eda_v2_before_definition_audit.ipynb'
if not backup.exists():shutil.copy2(path,backup)
replacements={'모터 회전 시작 시간':'회전 시작 관련 raw','회전 재시도 횟수':'회전 재시도 관련 raw'}
# Replacing visible terminology changes no numeric arrays or saved measurements.
def replace_text(value):
    if isinstance(value,str):
        for a,b in replacements.items():value=value.replace(a,b)
        return value
    if isinstance(value,list):return [replace_text(v) for v in value]
    if isinstance(value,dict):return {k:replace_text(v) for k,v in value.items()}
    return value
nb=nbf.from_dict(replace_text(dict(nb)))
section=next(c for c in nb.cells if c.cell_type=='markdown' and c.source.startswith('### 2-2.'))
section.source=header
shell=InteractiveShell.instance()
setup=next(c for c in nb.cells if c.cell_type=='code')
result=shell.run_cell(setup.source)
assert not(result.error_before_exec or result.error_in_exec)
def execute(source,ident):
    cell=nbf.v4.new_code_cell(source.strip(),id=ident)
    with capture_output() as cap:result=shell.run_cell(cell.source)
    assert not(result.error_before_exec or result.error_in_exec), cap.stdout
    cell.execution_count=1
    cell.outputs=[nbf.v4.new_output('display_data',data=o.data,metadata=o.metadata) for o in cap.outputs]
    return cell
existing=next(c for c in nb.cells if c.cell_type=='code' and "display(pd.DataFrame({'컬럼':cols" in c.source)
audit_source='''audit_dir=EDA/'analysis/column_definition_audit'
policy_summary=pd.read_csv(audit_dir/'column_policy_summary.csv')
display(policy_summary[['컬럼','지표','해석','상수인_모델수','입력후보판정']])
display(read('cohort').rename(columns={'disks':'디스크 수','failed_disks':'고장 디스크 수','failure_rows':'고장 표시 행',
    'repeated_failure_disks':'중복 고장 디스크','post_failure_disks':'고장 후 기록 디스크'}))'''
replacement=execute(audit_source,existing.id)
existing.source=replacement.source;existing.outputs=replacement.outputs

policy_header=next(c for c in nb.cells if c.cell_type=='markdown' and c.source.startswith('### 5-2.'))
policy_header.source='''### 5-2. 정의·단위 검토를 먼저 반영한 컬럼 후보 결정표

효과 크기가 커도 의미·단위가 미확정인 지표를 자동 채택하지 않는다. 가동 시간(9)·온도(194)와 횟수·손상 지표 6개는 조건부 후보, 읽기 오류(1)·회전 시작(3)·탐색 오류(7)·회전 재시도(10)·비상 헤드 회수(192)는 통합 기본 입력 보류다. **이는 학습 성능으로 정한 최종 피처 목록이 아니라 선행 의미 검토의 처리 방침**이다.'''
decision_cell=next(c for c in nb.cells if c.cell_type=='code' and c.source.startswith('decision=ranking.reset_index()'))
decision_source='''effect_data=read('effects_by_model')
current_effects=effect_data[effect_data.feature.isin(cols)].copy()
effect_summary=current_effects.assign(abs_r=current_effects.rank_biserial.abs()).groupby('feature').abs_r.median().rename('효과크기_중앙값').reset_index()
decision=pd.read_csv(EDA/'analysis/column_definition_audit/column_policy_summary.csv')
decision=decision.merge(effect_summary,left_on='컬럼',right_on='feature',how='left').drop(columns='feature')
display(decision[['컬럼','지표','입력후보판정','효과크기_중앙값','처리방침']])'''
replacement=execute(decision_source,decision_cell.id)
decision_cell.source=replacement.source;decision_cell.outputs=replacement.outputs
for c in nb.cells:
    if c.cell_type=='code':ast.parse(c.source)
nbf.validate(nb);nbf.write(nb,path)
print('Updated v2 definition section and candidate policies; numeric EDA results preserved.')

# The builder must reproduce the same definition section and policies, not restore the vague text.
builder=EDA/'scripts/11_build_detailed_eda_v2.py'
text=builder.read_text(encoding='utf-8')
begin=text.index("md('''### 2-2.")
end=text.index("''')",begin)+4
text=text[:begin]+'md('+repr(header)+')'+text[end:]
begin=text.index("code(r'''\ndisplay(pd.DataFrame({'컬럼':cols")
end=text.index("''')",begin)+4
text=text[:begin]+'code('+repr(audit_source)+')'+text[end:]
begin=text.index("code(r'''\ndecision=ranking.reset_index()")
end=text.index("''')",begin)+4
text=text[:begin]+'code('+repr(decision_source)+')'+text[end:]
for a,b in replacements.items():text=text.replace(a,b)
ast.parse(text)
builder.write_text(text,encoding='utf-8')
print('Builder synchronized with audited definitions and policy cells.')
