"""Audit 20 models x 13 SMART fields against source defaults, family rules and real data.

An implementation rule is not a firmware-specific manufacturer attestation.
No raw values are converted by this audit.
"""
from pathlib import Path
import ast,re,json,datetime
import pandas as pd
import numpy as np
import duckdb

EDA=Path(__file__).resolve().parents[1]
OUT=EDA/'analysis/column_definition_audit'
DATA=EDA/'analysis/detailed_v2'
db=(OUT/'drivedb.h').read_text(encoding='utf-8')

# Read C entry strings while ignoring comments; do not rewrite or execute source.
token_pattern=r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/|[{},]'
records=[]; fields=None; current=''; entry_line=None
for m in re.finditer(token_pattern,db):
    tok=m.group()
    if tok.startswith(('//','/*')):continue
    if tok=='{':
        fields=[];current='';entry_line=db.count('\n',0,m.start())+1
    elif tok=='}':
        if fields is not None:
            fields.append(current)
            if len(fields)==5:records.append(dict(zip(['family','model_regex','firmware_regex','warning','presets'],fields),line=entry_line))
        fields=None
    elif fields is not None:
        if tok==',':fields.append(current);current=''
        elif tok.startswith('"'):current+=ast.literal_eval(tok)
assert len(records)>500
default=next(r for r in records if r['family']=='DEFAULT')
def options(presets):
    return {int(m.group(1)):m.group(2) for m in re.finditer(r'-v\s+(\d+),([^\s]+)',presets)}
defaults=options(default['presets'])
models=pd.read_csv(DATA/'selected_models.csv').model.tolist()
cols=json.loads((DATA/'selected_columns.json').read_text())
stats=pd.read_csv(DATA/'value_quality_by_model.csv').set_index(['model','column'])
families=[]
for model in models:
    exact=[r for r in records if r['family'] not in ('DEFAULT',) and re.fullmatch(r['model_regex'],model)]
    suffix=[r for r in records if r['family'] not in ('DEFAULT',) and re.fullmatch(r['model_regex'],model+'-__UNKNOWN_SUFFIX__')]
    matches=exact or suffix
    r=matches[0] if matches else default
    match_type='exact_model_string' if exact else 'base_model_family_inference' if suffix else 'no_family_match_default_only'
    families.append({'model':model,'family':r['family'],'match_type':match_type,
        'database_line':r['line'],'model_regex':r['model_regex'],'firmware_regex':r['firmware_regex'],
        'firmware_in_dataset':False,'presets':r['presets']})
family_df=pd.DataFrame(families)
family_df.to_csv(OUT/'model_family_matches.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(records).to_json(OUT/'parsed_drivedb.json',orient='records',force_ascii=False,indent=2)

# Dataset schema audit covers all original days, not just the extracted subset.
headers=[json.loads(p.read_text(encoding='utf-8')) for p in (EDA/'analysis/full_column_check/days').glob('*.schema.json')]
assert len(headers)==821
firmware_fields=sorted({c for h in headers for c in h['columns'] if re.search('firmware|smartctl.*version|sector_size',c,re.I)})

con=duckdb.connect()
con.execute("SET threads=4; SET memory_limit='2GB'")
anchor=(DATA/'anchor_values.parquet').as_posix()
clock=con.execute(f'''SELECT a.model,count(*) AS paired_rows,
    median((a.smart_9_raw-b.smart_9_raw)/30.0) AS median_units_per_day,
    count(*) FILTER(WHERE a.smart_9_raw<b.smart_9_raw) AS decreasing_pairs,
    100.0*avg(((a.smart_9_raw-b.smart_9_raw)/30.0 BETWEEN 20 AND 28)::int) AS pct_near_24_per_day
    FROM read_parquet('{anchor}') a JOIN read_parquet('{anchor}') b
      ON a.serial_number=b.serial_number AND b.date=a.date-INTERVAL 30 DAY
    WHERE day(a.date)=1 AND a.smart_9_raw IS NOT NULL AND b.smart_9_raw IS NOT NULL GROUP BY a.model''').df()
clock.to_csv(OUT/'power_on_time_behavior.csv',index=False,encoding='utf-8-sig')
assert clock.model.nunique()==20

names={1:'읽기 오류 관련 raw',3:'회전 시작 관련 raw',4:'시작·정지 횟수',5:'재할당 섹터 수',7:'탐색 오류 관련 raw',
       9:'누적 가동 시간',10:'회전 재시도 관련 raw',12:'전원 인가 횟수',192:'비상 전원 차단·헤드 회수 관련 횟수',
       193:'헤드 로드·언로드 횟수',194:'현재 온도',198:'오프라인 복구 불가 섹터 관련 수',199:'인터페이스 CRC 오류 횟수'}
units={1:'단일 오류 횟수 아님/모델별 raw',3:'시간 성격이지만 raw 정수 전체를 ms로 단정 금지',4:'회',
       5:'섹터 관련 개수; 바이트 환산 금지',7:'단일 오류 횟수 아님/모델별 raw',9:'데이터상 시간(h) 단위와 일치',
       10:'누적 단일 횟수로 단정 금지',12:'회',192:'회; 집계 조건은 제조사별 확인 필요',193:'회',
       194:'섭씨(℃) 해석과 일치',198:'섹터/검사 관련 개수; 누적성·바이트 단위 동일성 미확정',199:'회'}
rows=[]
for model in models:
    family=next(f for f in families if f['model']==model)
    overrides=options(family['presets'])
    vendor='Seagate' if model.startswith('ST') else 'Toshiba' if model.startswith('TOSHIBA') else 'HGST/WD'
    for c in cols:
        ident=int(c.split('_')[1]);s=stats.loc[(model,c)]
        setting=overrides.get(ident,defaults[ident]);fmt=setting.split(',')[0]
        level='implementation_default'
        if ident in overrides:level='implementation_family_override'
        observed_constant=bool(s['min']==s['max'])
        if ident in (1,7):
            policy='모델별 raw로만 탐색; 통합 오류 횟수·raw>0 오류 플래그 금지'
            evidence='Seagate 공식 문서의 복합 필드 설명' if vendor=='Seagate' else '기본 오류율 이름만 확인; 해당 펌웨어의 raw 수식은 미확정'
        elif ident==3:
            policy='단일 ms 값으로 통합하지 않음; 상수인 모델에서는 제외 후보'
            evidence='도구 기본 raw16(avg16)은 현재값·평균값 필드를 구분; Seagate 공식 설명도 건강 지표 성격'
        elif ident==10:
            policy='우선 보류; 상수/큰 복합 정수와 제조사 집계 기간 차이 확인 필요'
            evidence='Seagate는 최근 8회 시작 시도 기준; HGST 1종에서 큰 값 관측. HGST 분해 수식 미확정'
        elif ident==192:
            policy='통합 기본 입력은 보류; 공통 전원 장애 횟수로 해석하지 않음'
            evidence='도구는 Power-Off Retract, Seagate는 Emergency Retract로 정의; 세부 집계 조건 다름'
            if model=='ST14000NM0138':
                evidence='Dell 공식 RAL3 펌웨어 공지에 192의 부정확한 증가 수정이 명시됨. 현재 데이터의 펌웨어 버전은 알 수 없음'
                policy='펌웨어 영향 미확정: 이 모델의 192는 기본 입력 보류'
        elif ident==9:
            policy='관측 데이터 기준 h로 사용 가능 후보; 감소·리셋 구간 별도 처리'
            evidence='제품군 기본 Power_On_Hours 및 실제 30일 간 변화량의 하루 약 24 단위 여부 대조'
        elif ident==194:
            policy='현재 CSV 값을 ℃로 조건부 사용; 원본 패킷 추가 디코딩은 하지 않음'
            evidence='도구 tempminmax의 현재값은 하위 바이트; 모든 CSV 값은 13~112 범위. 수집기 변환 코드 미공개'
        elif ident in (5,198):
            policy='손상 유무·모델 내 값/변화 후보; 동일 바이트량·공통 교체 임계값으로 사용 금지'
            evidence='제품군/도구의 섹터 관련 정의 일치; 논리·물리 섹터 집계와 리셋·누적 조건은 별도'
        else:
            policy='횟수형 후보; 모델 식별자 포함, 공통 임계값·동일 위험 크기로 단정 금지'
            evidence='해석 도구에서 동일 계열 이름/기본 raw48. 제조사별 펌웨어 정의를 완전 입증한 것은 아님'
        evidence_urls=['https://github.com/smartmontools/smartmontools/blob/main/drivedb/drivedb.h',
                       'https://github.com/Seagate/openSeaChest/wiki/Drive-Health-and-SMART']
        if model=='ST14000NM0138' and ident==192:evidence_urls.append('https://www.dell.com/support/home/en-pr/drivers/driversdetails?driverid=v3n1t')
        rows.append({'model':model,'vendor':vendor,'family':family['family'],'column':c,'meaning':names[ident],
            'unit_or_interpretation':units[ident],'tool_format':fmt,'definition_level':level,'family_match':family['match_type'],
            'observed_min':s['min'],'observed_max':s['max'],'observed_constant':observed_constant,
            'policy':policy,'evidence':evidence,'firmware_attested':False,
            'verification_status':'해석·단위 확인 전 보류' if ident in (1,3,7,10,192) else '자료·관측 기반 조건부 후보',
            'evidence_urls':' ; '.join(evidence_urls),
            'source_url':f'https://github.com/smartmontools/smartmontools/blob/main/drivedb/drivedb.h#L{family["database_line"]}',
            'raw_integer_to_byte_mapping_verified':False})
matrix=pd.DataFrame(rows)
assert len(matrix)==260 and matrix.groupby('model').size().eq(13).all()
matrix.to_csv(OUT/'model_column_audit.csv',index=False,encoding='utf-8-sig')
summary=matrix.groupby('column',sort=False).agg(지표=('meaning','first'),해석=('unit_or_interpretation','first'),
    상수인_모델수=('observed_constant','sum'),처리방침=('policy','first')).reset_index().rename(columns={'column':'컬럼'})
summary.to_csv(OUT/'column_policy_summary.csv',index=False,encoding='utf-8-sig')
status={'models':20,'columns':13,'pairs_reviewed':260,'original_schema_days_checked':821,
    'firmware_or_version_fields':firmware_fields,'firmware_attested_pairs':0,
    'family_exact_matches':int(family_df.match_type.eq('exact_model_string').sum()),
    'family_inferred_matches':int(family_df.match_type.eq('base_model_family_inference').sum()),
    'family_unmatched':int(family_df.match_type.eq('no_family_match_default_only').sum()),
    'raw_values_modified':False,'collection_decoder_verified':False}
(OUT/'audit_manifest.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(status,ensure_ascii=False,indent=2))
print(clock[['model','median_units_per_day','pct_near_24_per_day']].to_string(index=False))
print(summary.to_string(index=False))
