/* 예시 데이터 (가상). 시리얼·Vault 번호·수치는 실제 디스크가 아니다.
   SMART 번호: 5 재할당 섹터, 187 복구 불가 오류, 197 대기 섹터, 188 명령 시간 초과 */
(function () {
  // 같은 결과가 나오도록 고정 시드 난수
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

  // 90일 추이: onset일 전까지 base, 이후 final까지 증가
  function ramp(base, final, onset, curve) {
    const out = [];
    for (let d = 0; d < 90; d++) {
      if (d < onset) { out.push(base); continue; }
      const t = (d - onset) / (89 - onset || 1);
      const v = base + (final - base) * Math.pow(t, curve || 1);
      out.push(Math.round(v + (rnd() - 0.5) * (final - base) * 0.04));
    }
    for (let i = 1; i < 90; i++) out[i] = Math.max(out[i], out[i - 1]); // 누적값은 줄지 않음
    out[89] = final;
    return out;
  }
  const flat = (v) => Array(90).fill(v);

  const DISKS = [
    { id: 'd1', serial: 'ZJV0****1', rack: 'B-04', pod: '03', slot: 17, score: 0.93, rul: 4, age: 3.2, temp: 31,
      find: ['랙 B-04 위에서 4번째 Pod를 꺼낸다', '앞면 기준 2번째 줄, 위에서 3번째 칸'],
      smart: { 197: ramp(0, 42, 62, 1.3), 187: ramp(0, 22, 68, 1.1), 5: ramp(4, 30, 55, 2.2), 188: flat(0) } },
    { id: 'd2', serial: 'ZJV0****2', rack: 'B-04', pod: '03', slot: 41, score: 0.91, rul: 6, age: 3.1, temp: 33,
      find: ['랙 B-04 위에서 4번째 Pod를 꺼낸다', '앞면 기준 3번째 줄, 위에서 12번째 칸'],
      smart: { 197: ramp(0, 8, 70, 1), 187: ramp(0, 35, 58, 1.2), 5: ramp(0, 12, 66, 1.5), 188: ramp(0, 2, 80, 1) } },
    { id: 'd3', serial: 'ZJV0****3', rack: 'B-05', pod: '11', slot: '08', score: 0.88, rul: 9, age: 3.4, temp: 30,
      find: ['랙 B-05 위에서 2번째 Pod를 꺼낸다', '앞면 기준 1번째 줄, 위에서 9번째 칸'],
      smart: { 197: ramp(0, 6, 75, 1), 187: flat(0), 5: ramp(8, 96, 50, 1.6), 188: flat(0) } },
    { id: 'd4', serial: 'ZJV0****4', rack: 'B-05', pod: '16', slot: 52, score: 0.87, rul: 12, age: 2.9, temp: 32,
      find: ['랙 B-05 위에서 7번째 Pod를 꺼낸다', '앞면 기준 4번째 줄, 위에서 8번째 칸'],
      smart: { 197: ramp(0, 24, 60, 1.4), 187: ramp(0, 4, 78, 1), 5: ramp(0, 6, 72, 1), 188: flat(0) } },
    { id: 'd5', serial: 'ZJV0****5', rack: 'A-02', pod: '05', slot: 22, score: 0.71, rul: 21, age: 3.6, temp: 29,
      find: ['랙 A-02 위에서 6번째 Pod를 꺼낸다', '앞면 기준 2번째 줄, 위에서 8번째 칸'],
      smart: { 197: flat(0), 187: ramp(0, 9, 64, 1), 5: ramp(0, 4, 74, 1), 188: flat(0) } },
    { id: 'd6', serial: 'ZJV0****6', rack: 'C-09', pod: '02', slot: 30, score: 0.66, rul: 27, age: 3.0, temp: 34,
      find: ['랙 C-09 위에서 3번째 Pod를 꺼낸다', '앞면 기준 3번째 줄, 위에서 1번째 칸'],
      smart: { 197: flat(0), 187: flat(0), 5: ramp(2, 18, 60, 1.3), 188: flat(0) } },
    { id: 'd7', serial: 'ZJV0****7', rack: 'D-07', pod: '04', slot: '09', score: 0.58, rul: 38, age: 2.7, temp: 31,
      find: ['랙 D-07 위에서 5번째 Pod를 꺼낸다', '앞면 기준 1번째 줄, 위에서 10번째 칸'],
      smart: { 197: ramp(0, 3, 82, 1), 187: flat(0), 5: flat(0), 188: ramp(0, 5, 70, 1) } },
    { id: 'd8', serial: 'ZJV0****8', rack: 'D-07', pod: '07', slot: 44, score: 0.55, rul: 44, age: 3.3, temp: 30,
      find: ['랙 D-07 위에서 8번째 Pod를 꺼낸다', '앞면 기준 3번째 줄, 위에서 15번째 칸'],
      smart: { 197: flat(0), 187: ramp(0, 2, 84, 1), 5: ramp(0, 3, 76, 1), 188: flat(0) } },
  ];

  const VAULT = { 'B-04': '1xxx', 'B-05': '1xxx', 'A-02': '1aaa', 'C-09': '1ggg', 'D-07': '1ccc' };
  DISKS.forEach((d) => {
    d.dc = 'sac2';
    d.vault = VAULT[d.rack];
    d.model = 'ST12000NM0008';
    d.grade = d.score >= 0.85 ? 'risk' : 'warn'; // 예시 기준: 위험 = 상위 1%, 주의 = 상위 1~5%
  });

  window.HDD = {
    DISKS,
    SMART_NAMES: { 197: '197 대기 섹터', 187: '187 복구 불가 오류', 5: '5 재할당 섹터', 188: '188 명령 시간 초과' },
    SMART_UNITS: { 197: '개', 187: '건', 5: '개', 188: '건' },
    BASE_DATE: '2026.06.30',
    MANAGED: 1200,
    // 처음 교체 목록: 점수 상위 6개
    INITIAL_CANDIDATES: ['d1', 'd2', 'd3', 'd4', 'd5', 'd6'],
  };
})();
