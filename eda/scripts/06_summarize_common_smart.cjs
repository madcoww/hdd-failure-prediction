// Run after 05_common_smart_coverage.ps1. No external packages required.
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '../analysis/sampled_column_check');
function parseCsv(text) {
  const rows=[]; let row=[], value='', quoted=false;
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(c==='"') { if(quoted&&text[i+1]==='"'){value+='"';i++;}else quoted=!quoted; }
    else if(c===','&&!quoted){row.push(value);value='';}
    else if(c==='\n'&&!quoted){row.push(value.replace(/\r$/,''));if(row.some(Boolean))rows.push(row);row=[];value='';}
    else value+=c;
  }
  if(value||row.length){row.push(value.replace(/\r$/,''));rows.push(row);}
  const header=rows.shift();
  return rows.map(r=>Object.fromEntries(header.map((k,i)=>[k,r[i]??''])));
}
const manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));
const rank=parseCsv(fs.readFileSync(path.resolve(__dirname,'../../data/backblaze/summary/model_rank.csv'),'utf8'));
const models=new Map(rank.map(r=>[r.model,{rows:0,days:0,counts:{}}]));
const columns=new Set();
for(const date of manifest.dates){
  for(const r of parseCsv(fs.readFileSync(path.join(root,'days',date+'.csv'),'utf8'))){
    const m=models.get(r.model); if(!m)throw Error('Unexpected model '+r.model);
    m.rows+=Number(r.sampled_rows);m.days++;
    for(const [k,v] of Object.entries(r)) if(/^smart_\d+_raw$/.test(k)){columns.add(k);m.counts[k]=(m.counts[k]??0)+Number(v);}
  }
}
if(models.size!==97||[...models.values()].some(m=>!m.rows))throw Error('Missing models');
const cols=[...columns].sort((a,b)=>Number(a.split('_')[1])-Number(b.split('_')[1]));
const quote=s=>'"'+String(s).replaceAll('"','""')+'"';
const csv=rows=>rows.map(r=>r.map(quote).join(',')).join('\n')+'\n';
const percentages=(m,c)=>100*(m.counts[c]??0)/m.rows;
const summary=cols.map(c=>{
  const p=[...models.values()].map(m=>percentages(m,c));
  return {column:c,models_with_any:p.filter(v=>v>0).length,models_ge99:p.filter(v=>v>=99).length,models_ge95:p.filter(v=>v>=95).length,min_pct:Math.min(...p),max_missing_pct:100-Math.min(...p)};
});
fs.writeFileSync(path.join(root,'model_smart_coverage.csv'),csv([['model','sampled_days','sampled_rows',...cols],...[...models].map(([name,m])=>[name,m.days,m.rows,...cols.map(c=>percentages(m,c).toFixed(4))])]));
const keys=Object.keys(summary[0]);
fs.writeFileSync(path.join(root,'smart_coverage_summary.csv'),csv([keys,...summary.map(r=>keys.map(k=>typeof r[k]==='number'?Number(r[k].toFixed(4)):r[k]))]));
const labels={1:'읽기 오류 관련 지표',3:'모터 회전 시작 시간',4:'회전 시작·정지 횟수',5:'재할당 섹터 수',7:'헤드 탐색 오류 관련 지표',9:'누적 가동 시간',10:'회전 재시도 횟수',12:'전원 인가 횟수',187:'정정 불가 오류',188:'명령 시간 초과',192:'비상 헤드 회수 관련 지표',193:'헤드 로드·언로드 횟수',194:'온도',197:'대기 중 불량 섹터 수',198:'오프라인 복구 불가 섹터 수',199:'인터페이스 CRC 오류',241:'누적 쓰기 관련 지표',242:'누적 읽기 관련 지표'};
const selected=Object.keys(labels).map(id=>summary.find(r=>r.column===`smart_${id}_raw`)).filter(Boolean);
const table=['| 지표 | 값이 기록된 모델 | 표본 행의 99% 이상 기록한 모델 | 모델별 결측률 범위 |','|---|---:|---:|---:|',...selected.map(r=>{const id=r.column.split('_')[1];const ps=[...models.values()].map(m=>100-percentages(m,r.column));return `| ${labels[id]}(${id}) | ${r.models_with_any}/97 | ${r.models_ge99}/97 | ${Math.min(...ps).toFixed(2)}~${Math.max(...ps).toFixed(2)}% |`;})].join('\n');
const all=summary.filter(r=>r.models_with_any===97);
const text=`# 전체 97개 모델의 SMART 기록 현황\n\n범위: 2024-04-01~2026-06-30. 분기별 첫날·마지막 날 ${manifest.dates.length}일 표본으로 97개 모델을 모두 포함했다. 이는 821일 전체에 대한 전수 검사가 아니다. 모델별 표본 일수와 행 수는 CSV에 수록했다.\n\n${table}\n\n- '값이 기록된 모델': 해당 지표가 표본에서 한 번이라도 결측이 아닌 모델 수. 0도 기록된 값이다.\n- '99% 이상': 각 모델의 전체 표본 행 중 해당 지표가 결측이 아닌 비율이 99% 이상인 모델 수. 날짜에 해당 열이 없는 경우도 결측으로 집계한다.\n- 모델별 결측률 범위는 97개 모델의 최솟값~최댓값이며, 모델 내부의 시점별 변동을 뜻하지 않는다.\n- 모든 97개 모델에서 한 번 이상 관측된 SMART: ${all.map(r=>r.column).join(', ')||'없음'}.\n- 컬럼 이름의 공통성과 의미·단위 호환성은 별개다. 특히 오류율과 누적 읽기/쓰기 raw는 제조사별 인코딩을 확인해야 한다.\n- 97개 모델 목록에는 SSD로 표기된 제품도 포함되어 있다. HDD 전용 학습을 목표로 한다면 장치 종류를 먼저 분류하고 다시 집계해야 한다.\n\n재현: scripts/05_common_smart_coverage.ps1 → scripts/06_summarize_common_smart.cjs.\n`;
fs.writeFileSync(path.join(root,'README.md'),text);
console.log(table);console.log('All-model observed:',all.map(r=>r.column));
