/* 클릭형 프로토타입: 대시보드 → 디스크 상세 → 교체 목록(승인·보류) → 상태 확인
   상태는 이 브라우저(localStorage)에만 저장. 초기화 버튼으로 처음 상태로 돌아간다. */
(function () {
  const { DISKS, SMART_NAMES, SMART_UNITS, BASE_DATE, MANAGED, INITIAL_CANDIDATES } = window.HDD;
  const KEY = 'hdd-proto-v1';
  const $app = document.getElementById('app');
  const $layer = document.getElementById('layer');
  const byId = Object.fromEntries(DISKS.map((d) => [d.id, d]));
  const ui = { rack: 'B-04', range: 30, filter: 'all' };

  // ---------- 상태 ----------
  function fresh() {
    const cand = {};
    INITIAL_CANDIDATES.forEach((id) => (cand[id] = { status: 'wait' }));
    return { cand, steps: { pick: false, why: false, decide: false, check: false } };
  }
  let state = fresh();
  try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && s.cand && s.steps) state = s; } catch (e) { /* 저장소 없음: 기본값 */ }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* 무시 */ } }

  // ---------- 도우미 ----------
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const color = (d) => (d.grade === 'risk' ? 'var(--red)' : 'var(--amb)');
  const hex = (d) => (d.grade === 'risk' ? '#FF4D5E' : '#FFB020');
  const gradePill = (d) => (d.grade === 'risk' ? '<span class="pill r">위험</span>' : '<span class="pill a">주의</span>');
  const seg = (on, total, c) => '<div class="seg">' + Array.from({ length: total }, (_, k) => `<i${k < on ? ` style="background:${c}"` : ''}></i>`).join('') + '</div>';
  const loc = (d) => `<span class="loc"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#FF6B78" stroke-width="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg><span>${d.dc}</span><span>Vault ${d.vault}</span><span>Pod ${d.pod}</span><span class="k${d.grade === 'warn' ? ' w' : ''}">슬롯 ${d.slot}</span></span>`;
  const sorted = () => DISKS.slice().sort((a, b) => b.score - a.score);
  const rul = (d) => (d.rul > 90 ? '90일 이상' : d.rul + '일');
  const now = () => { const t = new Date(); const p = (n) => String(n).padStart(2, '0'); return `${p(t.getMonth() + 1)}.${p(t.getDate())} ${p(t.getHours())}:${p(t.getMinutes())}`; };

  // 위험 근거: 30일 전 대비 변화량
  function reasons(d) {
    const list = Object.keys(SMART_NAMES).map((k) => {
      const s = d.smart[k]; const before = s[59]; const cur = s[89];
      return { k, name: SMART_NAMES[k], unit: SMART_UNITS[k], before, cur, delta: cur - before };
    }).sort((a, b) => b.delta - a.delta);
    return list;
  }
  const mainCause = (d) => { const r = reasons(d)[0]; return r.delta > 0 ? `${r.name.split(' ')[0]} ${r.name.split(' ').slice(1).join(' ')} ${r.delta >= 10 ? '급증' : '증가'}` : '변화 적음'; };

  function toast(msg, action) {
    $layer.querySelectorAll('.toast').forEach((t) => t.remove());
    const el = document.createElement('div');
    el.className = 'toast'; el.setAttribute('role', 'status');
    el.innerHTML = `<span>${esc(msg)}</span>` + (action ? `<button type="button">${esc(action.label)}</button>` : '');
    if (action) el.querySelector('button').onclick = () => { el.remove(); action.run(); };
    $layer.appendChild(el);
    setTimeout(() => el.remove(), 4200);
  }

  // ---------- 체험 순서 ----------
  const STEPS = [['pick', '위험 디스크 선택'], ['why', '근거 확인'], ['decide', '승인 · 보류'], ['check', '상태 확인']];
  const HINTS = {
    pick: '대시보드에서 빨간 위험 디스크를 눌러 보세요',
    why: 'SMART 추이와 위험 근거를 확인하세요',
    decide: '교체 목록에서 승인 또는 보류를 눌러 보세요',
    check: '\'교체 예정\' 또는 \'보류\' 탭에서 상태를 확인하세요',
    done: '체험 완료 · 초기화를 누르면 처음부터 다시 할 수 있습니다',
  };
  function renderGuide() {
    const next = STEPS.find(([k]) => !state.steps[k]);
    document.getElementById('guide').innerHTML = '<span class="lbl">체험 순서</span>' + STEPS.map(([k, t], i) => {
      const cls = state.steps[k] ? 'done' : next && next[0] === k ? 'now' : '';
      return `<span class="step ${cls}"><b>${state.steps[k] ? '✓' : i + 1}</b><span>${t}</span></span>`;
    }).join('') + `<span class="hint">${HINTS[next ? next[0] : 'done']}</span>`;
  }
  function done(k) { if (!state.steps[k]) { state.steps[k] = true; save(); } }

  // ---------- 대시보드 ----------
  const ROWS = { A: 104, B: 184, C: 300, D: 380 }; const RW = 60, RH = 38, RG = 6, X0 = 150;
  const rackX = (i) => X0 + (i - 1) * (RW + RG);
  function rackState(name) {
    const ds = DISKS.filter((d) => d.rack === name);
    return ds.some((d) => d.grade === 'risk') ? 'r' : ds.length ? 'a' : '';
  }
  function floorSvg() {
    const s = ['<defs><pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" stroke="rgba(127,163,214,.07)"/></pattern></defs><rect width="940" height="530" fill="url(#g)"/>'];
    for (let i = 1; i <= 10; i++) {
      const cx = rackX(i) + RW / 2;
      s.push(`<line x1="${cx}" y1="44" x2="${cx}" y2="470" stroke="rgba(127,163,214,.16)" stroke-dasharray="3 5"/><circle cx="${cx}" cy="26" r="11" fill="none" stroke="#7FA3D6"/><text x="${cx}" y="30.5" fill="#9FB8DD" font-size="11.5" text-anchor="middle" font-family="Rajdhani">${i}</text>`);
    }
    Object.entries(ROWS).forEach(([r, y]) => s.push(`<circle cx="96" cy="${y + RH / 2}" r="11" fill="none" stroke="#7FA3D6"/><text x="96" y="${y + RH / 2 + 4.5}" fill="#9FB8DD" font-size="12" text-anchor="middle" font-family="Rajdhani" font-weight="600">${r}</text>`));
    s.push('<path d="M120 52 H880 V478 H300 M232 478 H120 V52" fill="none" stroke="#9DB6DB" stroke-width="2.2"/><path d="M128 60 H872 V470 H300 M232 470 H128 V60" fill="none" stroke="#5F7DA8"/>');
    s.push('<path d="M232 478 A68 68 0 0 1 300 410" fill="none" stroke="#7FA3D6" stroke-dasharray="4 3"/><line x1="300" y1="478" x2="300" y2="410" stroke="#9DB6DB" stroke-width="1.4"/><text x="266" y="500" fill="#7F90AD" font-size="11.5" text-anchor="middle">출입구</text>');
    const xa = rackX(1) - 8, xb = rackX(10) + RW + 8;
    [[ROWS.A + RH, ROWS.B, '냉복도 1'], [ROWS.C + RH, ROWS.D, '냉복도 2']].forEach(([y1, y2, n]) => s.push(`<rect x="${xa}" y="${y1}" width="${xb - xa}" height="${y2 - y1}" fill="rgba(61,139,255,.16)" stroke="rgba(61,139,255,.45)" stroke-dasharray="5 4"/><text x="${xb + 10}" y="${(y1 + y2) / 2 + 4}" fill="#6FA6FF" font-size="11.5">${n}</text>`));
    s.push(`<text x="${xb + 10}" y="${(ROWS.B + RH + ROWS.C) / 2 + 4}" fill="#B07A84" font-size="11.5">열복도</text>`);
    Object.entries(ROWS).forEach(([r, y]) => {
      for (let i = 1; i <= 10; i++) {
        const name = `${r}-${String(i).padStart(2, '0')}`; const st = rackState(name); const x = rackX(i);
        const [fill, stroke] = st === 'r' ? ['rgba(255,77,94,.85)', '#FF8A95'] : st === 'a' ? ['rgba(255,176,32,.8)', '#FFCB66'] : ['#1B2840', '#3A4D6E'];
        const sel = ui.rack === name ? `<rect x="${x - 5}" y="${y - 5}" width="${RW + 10}" height="${RH + 10}" rx="4" fill="none" stroke="#4CC9F0" stroke-width="2"/>` : '';
        s.push(`<g class="rack" data-rack="${name}" tabindex="0" role="button" aria-label="랙 ${name}${st === 'r' ? ' 위험 있음' : st === 'a' ? ' 주의 있음' : ''}">${sel}<rect class="body" x="${x}" y="${y}" width="${RW}" height="${RH}" rx="2" fill="${fill}" stroke="${stroke}"/><text x="${x + RW / 2}" y="${y + RH / 2 + 4}" fill="${st ? '#fff' : '#5F7395'}" font-size="11" text-anchor="middle" font-family="Rajdhani" font-weight="600" pointer-events="none">${name}</text></g>`);
      }
    });
    return `<svg viewBox="0 0 940 520" aria-label="sac2 데이터센터 평면도">${s.join('')}</svg>`;
  }
  function diskItem(d) {
    const c = state.cand[d.id];
    const st = c ? (c.status === 'scheduled' ? '<span class="pill g">교체 예정</span>' : c.status === 'hold' ? '<span class="pill a">보류</span>' : '') : '';
    return `<a class="ditem" href="#/disk/${d.id}" data-pick="1"><span class="num" style="font-weight:700;white-space:nowrap">Pod ${d.pod}</span><span class="loc"><span class="k${d.grade === 'warn' ? ' w' : ''}">슬롯 ${d.slot}</span></span><span class="sub">${d.serial}</span>${st}<b class="sc num" style="color:${color(d)}">${d.score.toFixed(2)}</b></a>`;
  }
  function rackPanel() {
    const ds = DISKS.filter((d) => d.rack === ui.rack).sort((a, b) => b.score - a.score);
    const base = ui.rack === 'B-05' ? 10 : 0;
    const pods = Array.from({ length: 10 }, (_, k) => {
      const p = String(base + k).padStart(2, '0'); const pd = ds.filter((d) => d.pod === p);
      const st = pd.some((d) => d.grade === 'risk') ? 'r' : pd.length ? 'a' : '';
      return `<div class="podrow ${st}"><span class="led"></span><span class="num" style="font-weight:700">Pod ${p}</span>${pd.length ? `<span class="pill ${st === 'r' ? 'r' : 'a'}" style="margin-left:auto;height:18px;font-size:11px">${st === 'r' ? '위험' : '주의'} ${pd.length}</span>` : ''}</div>`;
    }).join('');
    const vault = ds[0] ? ds[0].vault : '-';
    return `<div class="card" style="display:flex;flex-direction:column"><div class="ch"><b>랙 ${ui.rack} 앞면</b><small>${ds.length ? 'Vault ' + vault + ' · ' : ''}Pod 10대</small>${ds.length ? `<span class="pill ${rackState(ui.rack) === 'r' ? 'r' : 'a'}" style="margin-left:auto">${ds.length}건</span>` : ''}</div>
      <div class="pods">${pods}</div>
      <div style="padding:2px 16px 8px;font-size:12.5px;color:var(--sub)">${ds.length ? '이 랙의 위험 · 주의 디스크 (누르면 상세)' : '이 랙에는 위험 · 주의 디스크가 없습니다. 색이 칠해진 랙을 눌러 보세요.'}</div>
      <div class="dlist ${!state.steps.pick && ds.length ? 'pulse' : ''}">${ds.map(diskItem).join('')}</div></div>`;
  }
  function viewDashboard() {
    const risk = DISKS.filter((d) => d.grade === 'risk').length;
    const warn = DISKS.filter((d) => d.grade === 'warn').length;
    const vals = Object.values(state.cand);
    const sch = vals.filter((c) => c.status === 'scheduled').length;
    const wait = vals.filter((c) => c.status === 'wait').length;
    const kpi = (v, c, t, s, href) => `<a class="card kpi" href="${href}"><span class="v num" style="color:${c}">${v}</span><div class="l"><b>${t}</b>${s}</div></a>`;
    $app.innerHTML = `
      <div class="kpis">${kpi(risk, '#FF4D5E', '위험 디스크', '고장 위험 상위 1%', '#/replace')}${kpi(warn, '#FFB020', '주의 디스크', '상위 1~5%', '#/replace')}
        ${kpi(sch, '#2BD47D', '교체 예정', `승인 대기 ${wait}건`, '#/replace?f=scheduled')}${kpi(MANAGED.toLocaleString(), '#E6ECF6', '관리 중인 디스크', 'ST12000NM0008', '#/dashboard')}</div>
      <div class="dash">
        <div class="card" style="display:flex;flex-direction:column"><div class="ch"><b>sac2 데이터센터 평면도</b><small>랙을 누르면 오른쪽에 앞면이 열립니다</small>
          <div class="legend"><span><i style="background:#FF4D5E"></i>위험 있음</span><span><i style="background:#FFB020"></i>주의 있음</span><span><i style="background:#1B2840;border:1px solid #3A4D6E"></i>정상</span></div></div>
          <div class="floor">${floorSvg()}</div></div>
        <div id="rackPanel">${rackPanel()}</div>
      </div>
      <div class="mcards"><div style="display:flex;justify-content:space-between;align-items:center"><b>위험 · 주의 디스크</b><a href="#/replace" style="color:var(--blue);font-size:13px">교체 목록 보기</a></div>
        ${sorted().map((d) => `<a class="card mcard ${!state.steps.pick && d.id === 'd1' ? 'pulse' : ''}" href="#/disk/${d.id}" data-pick="1">
          <div class="row">${loc(d)}${gradePill(d)}</div>
          <div class="row"><b class="num" style="font-size:24px;color:${color(d)}">${d.score.toFixed(2)}</b><div style="flex:1;margin:0 10px">${seg(Math.round(d.score * 10), 10, hex(d))}</div><span>잔여 <b>${rul(d)}</b></span></div>
          <div class="row"><span class="note" style="color:var(--sub)">${d.serial} · ${mainCause(d)}</span><span style="color:var(--blue);font-size:12.5px;font-weight:600">상세 보기</span></div></a>`).join('')}
        <div class="note" style="padding:4px 2px">데이터센터 평면도는 PC 화면에서 볼 수 있습니다</div></div>`;
    $app.querySelectorAll('.rack').forEach((g) => {
      const pick = () => { ui.rack = g.dataset.rack; viewDashboard(); };
      g.addEventListener('click', pick);
      g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
    });
  }

  // ---------- 디스크 상세 ----------
  function chart(d, k) {
    const s = d.smart[k].slice(90 - ui.range); const W = 600, H = 150, P = 8;
    const mx = Math.max(...s, 1); const n = s.length;
    const pts = s.map((v, i) => [P + i * (W - 2 * P) / (n - 1), H - P - (v / mx) * (H - 2 * P - 10)]);
    const line = pts.map((p) => p.map((x) => x.toFixed(1)).join(',')).join(' ');
    const cur = s[n - 1]; const up = cur > s[0];
    const c = cur === 0 ? '#5E6C87' : k === '5' && d.grade === 'warn' ? '#FFB020' : up ? '#FF4D5E' : '#FFB020';
    const grid = [0.25, 0.5, 0.75].map((f) => `<line x1="0" x2="${W}" y1="${(H * f).toFixed(0)}" y2="${(H * f).toFixed(0)}" stroke="#1E2B44"/>`).join('');
    return `<div class="card chart"><div class="row"><span style="color:var(--sub);font-size:13px">${SMART_NAMES[k]}</span><b class="num" style="font-size:24px;color:${c}">${cur}<small style="font-size:12px"> ${SMART_UNITS[k]}</small></b></div>
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="${SMART_NAMES[k]} 최근 ${ui.range}일, 현재 ${cur}"><defs><linearGradient id="f${k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c}" stop-opacity=".35"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></linearGradient></defs>${grid}
      <polygon points="${P},${H - P} ${line} ${W - P},${H - P}" fill="url(#f${k})"/><polyline points="${line}" fill="none" stroke="${c}" stroke-width="2.2" vector-effect="non-scaling-stroke"/></svg>
      <div class="row note"><span>${ui.range}일 전</span><span>기준일</span></div></div>`;
  }
  function viewDisk(id) {
    const d = byId[id] || sorted()[0];
    done('pick'); done('why');
    const c = state.cand[d.id];
    const rs = reasons(d); const maxD = Math.max(rs[0].delta, 1);
    const flagged = ['5', '187', '197'].some((k) => d.smart[k][89] > 0);
    const statusBox = c
      ? `${c.status === 'scheduled' ? '<span class="pill g">교체 예정</span>' : c.status === 'hold' ? '<span class="pill a">보류</span>' : '<span class="pill">승인 대기</span>'}<a class="btn pri" href="#/replace">교체 목록에서 처리하기</a>`
      : `<button class="btn pri" type="button" id="addBtn">교체 후보에 추가</button>`;
    $app.innerHTML = `
      <div class="ph"><div><h1>디스크 상세</h1><p>위험 근거와 SMART 추이를 확인하고 교체를 판단합니다</p></div>
        <div class="acts"><label class="hide" for="pick">디스크 선택</label><select class="picker" id="pick">${sorted().map((x) => `<option value="${x.id}"${x.id === d.id ? ' selected' : ''}>${x.serial} · ${x.grade === 'risk' ? '위험' : '주의'} ${x.score.toFixed(2)}</option>`).join('')}</select>${statusBox}</div></div>
      <div class="dhead">
        <div class="card info"><div><div class="sn">${d.serial}</div><div class="k">${d.model}</div></div>
          <div><div class="k" style="margin-bottom:5px">위치</div>${loc(d)}</div>
          <div><div class="k">가동 시간</div><b>${d.age}년</b></div><div><div class="k">최근 온도</div><b>${d.temp}°C</b></div></div>
        <div class="card risk"><div style="display:flex;justify-content:space-between;align-items:center"><span style="color:var(--sub);font-size:13px">30일 안에 고장 날 위험</span>${gradePill(d)}</div>
          <div style="display:flex;align-items:baseline;gap:16px;margin:6px 0 10px"><b class="big num" style="color:${color(d)}">${d.score.toFixed(2)}</b><span style="color:var(--sub);font-size:13px">예측 잔여수명 <b class="num" style="font-size:24px;color:#fff">${rul(d)}</b></span></div>
          ${seg(Math.round(d.score * 20), 20, hex(d))}</div>
      </div>
      <div class="why">
        <div class="card"><div class="ch"><b>위험 근거</b><small>최근 30일 SMART 변화량, 큰 순서</small></div>
          ${rs.map((r, i) => `<div class="reason"><span class="t">${r.name}${i === 0 && r.delta > 0 ? ' <span class="pill r">가장 큰 원인</span>' : ''}</span><span class="bar"><i style="width:${Math.max(0, r.delta) / maxD * 100}%;${r.delta <= 0 ? 'background:#3A4D6E' : ''}"></i></span><span class="d num">${r.before} → <b style="color:${r.delta > 0 ? 'var(--red)' : 'var(--sub)'}">${r.cur}</b> ${r.unit}${r.delta > 0 ? ` (+${r.delta})` : ''}</span></div>`).join('')}
          <div style="padding:10px 16px;border-top:1px solid var(--ln)" class="note">${flagged ? '손상 지표(5 · 187 · 197)가 0보다 큼. 같은 모델 정상 디스크는 93.5%가 0이다 (EDA 4-1)' : '손상 지표는 아직 0. 다른 SMART 변화로 위험이 높게 나옴'}</div></div>
        <div style="display:flex;flex-direction:column;gap:14px">
          <div class="card findbox"><b>현장에서 찾는 법</b><div style="margin-top:6px;line-height:1.6">${d.find.map(esc).join('<br>')}</div><div class="note" style="margin-top:6px">랙 위치와 슬롯의 줄 · 칸 대응은 도식</div></div>
          <div class="card" style="padding:14px 16px"><b>판단 기준</b><div style="margin-top:6px;color:#C9D3E5;line-height:1.6">위험 점수는 같은 날 모든 디스크 중 순위로 봅니다. 상위 1%는 위험, 1~5%는 주의로 표시합니다 (예시 기준).</div></div>
          <a class="btn pri" href="#/replace" style="height:44px">다음: 교체 목록에서 승인 또는 보류</a>
        </div>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px"><b>SMART 기록</b>
        <div class="range" role="group" aria-label="기간">${[30, 60, 90].map((r) => `<button type="button" data-r="${r}" class="${ui.range === r ? 'on' : ''}">${r}일</button>`).join('')}</div></div>
      <div class="charts">${['197', '187', '5', '188'].map((k) => chart(d, k)).join('')}</div>`;
    document.getElementById('pick').onchange = (e) => (location.hash = '#/disk/' + e.target.value);
    $app.querySelectorAll('.range button').forEach((b) => (b.onclick = () => { ui.range = +b.dataset.r; viewDisk(d.id); }));
    const add = document.getElementById('addBtn');
    if (add) add.onclick = () => { state.cand[d.id] = { status: 'wait' }; save(); toast('교체 목록에 추가했습니다', { label: '교체 목록 보기', run: () => (location.hash = '#/replace') }); viewDisk(d.id); };
    renderGuide();
  }

  // ---------- 교체 목록 ----------
  const ST = { wait: ['승인 대기', ''], scheduled: ['교체 예정', 'g'], hold: ['보류', 'a'] };
  function statusHtml(c) {
    const [t, cls] = ST[c.status];
    const meta = c.status === 'scheduled' ? `운영 담당자 · ${c.at}` : c.status === 'hold' ? `${esc(c.reason)} · ${c.at}` : '';
    return `<span class="pill ${cls}">${t}</span>${meta ? `<span class="stmeta">${meta}</span>` : ''}`;
  }
  function actionHtml(id, c, big) {
    const sm = big ? '' : ' sm';
    return c.status === 'wait'
      ? `<button class="btn${sm}" type="button" data-hold="${id}"${big ? ' style="flex:1"' : ''}>보류</button><button class="btn pri${sm}" type="button" data-ok="${id}"${big ? ' style="flex:1.4"' : ''}>승인</button>`
      : `<button class="btn ghost${sm}" type="button" data-undo="${id}">되돌리기</button>`;
  }
  function viewReplace(flash) {
    const ids = Object.keys(state.cand).filter((id) => byId[id]).sort((a, b) => byId[b].score - byId[a].score);
    const count = (s) => ids.filter((id) => state.cand[id].status === s).length;
    const shown = ui.filter === 'all' ? ids : ids.filter((id) => state.cand[id].status === ui.filter);
    const tabs = [['all', '전체', ids.length], ['wait', '승인 대기', count('wait')], ['scheduled', '교체 예정', count('scheduled')], ['hold', '보류', count('hold')]];
    $app.innerHTML = `
      <div class="ph"><div><h1>교체 목록</h1><p>위험 점수가 높은 순서입니다. 승인하면 '교체 예정', 보류하면 사유와 함께 '보류'가 됩니다</p></div></div>
      <div class="filters" role="tablist">${tabs.map(([k, t, n]) => `<button class="ftab ${ui.filter === k ? 'on' : ''}" type="button" role="tab" aria-selected="${ui.filter === k}" data-f="${k}">${t}<span class="num">${n}</span></button>`).join('')}</div>
      ${shown.length ? '' : `<div class="card empty">${ui.filter === 'all' ? '교체 후보가 없습니다. 초기화를 눌러 보세요.' : '이 상태의 디스크가 없습니다.'}</div>`}
      <div class="card tablewrap ${shown.length ? '' : 'hide'}" style="overflow:hidden"><table>
        <thead><tr><th>위치</th><th>시리얼</th><th>위험 점수</th><th>잔여수명</th><th>주요 원인</th><th>상태</th><th style="text-align:right">처리</th></tr></thead>
        <tbody>${shown.map((id) => { const d = byId[id], c = state.cand[id]; return `<tr class="${flash === id ? 'flash' : ''}">
          <td>${loc(d)}</td><td><a href="#/disk/${id}" style="color:#C9D3E5;text-decoration:underline;text-underline-offset:3px">${d.serial}</a></td>
          <td><div class="scorecell"><b class="num" style="font-size:17px;color:${color(d)}">${d.score.toFixed(2)}</b>${seg(Math.round(d.score * 10), 10, hex(d))}</div></td>
          <td><b class="num" style="font-size:16px">${rul(d)}</b></td><td>${mainCause(d)}</td><td>${statusHtml(c)}</td><td><div class="acts2">${actionHtml(id, c)}</div></td></tr>`; }).join('')}</tbody></table></div>
      <div class="rcards">${shown.map((id) => { const d = byId[id], c = state.cand[id]; return `<div class="card mcard ${flash === id ? 'pulse' : ''}">
          <div class="row">${loc(d)}</div>
          <div class="row"><b class="num" style="font-size:22px;color:${color(d)}">${d.score.toFixed(2)}</b><div style="flex:1;margin:0 10px">${seg(Math.round(d.score * 10), 10, hex(d))}</div><span>잔여 <b>${rul(d)}</b></span></div>
          <div class="row"><a href="#/disk/${id}" class="note" style="color:var(--sub)">${d.serial} · ${mainCause(d)}</a><span style="text-align:right">${statusHtml(c)}</span></div>
          <div style="display:flex;gap:8px">${actionHtml(id, c, true)}</div></div>`; }).join('')}</div>`;
    $app.querySelectorAll('[data-f]').forEach((b) => (b.onclick = () => {
      ui.filter = b.dataset.f;
      if ((ui.filter === 'scheduled' || ui.filter === 'hold') && state.steps.decide) done('check');
      viewReplace(); renderGuide();
    }));
    $app.querySelectorAll('[data-ok]').forEach((b) => (b.onclick = () => decide(b.dataset.ok, 'scheduled')));
    $app.querySelectorAll('[data-hold]').forEach((b) => (b.onclick = () => holdSheet(b.dataset.hold)));
    $app.querySelectorAll('[data-undo]').forEach((b) => (b.onclick = () => { state.cand[b.dataset.undo] = { status: 'wait' }; save(); toast('승인 대기로 되돌렸습니다'); viewReplace(b.dataset.undo); }));
    renderGuide();
  }
  function decide(id, status, reason) {
    state.cand[id] = { status, reason: reason || '', at: now() };
    done('decide'); save();
    const label = status === 'scheduled' ? '교체 예정' : '보류';
    toast(`${byId[id].serial} → ${label}`, { label: `'${label}' 탭에서 보기`, run: () => { ui.filter = status; done('check'); viewReplace(id); } });
    viewReplace(id);
  }
  function holdSheet(id) {
    const d = byId[id];
    $layer.innerHTML = `<div class="dim" id="dim"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="mt"><div class="grip"></div>
      <div style="display:flex;align-items:center;gap:8px"><b id="mt" style="font-size:16px">보류 사유를 적어 주세요</b><span class="pill r" style="margin-left:auto">필수</span></div>
      ${loc(d)}<label class="hide" for="why">보류 사유</label><textarea id="why" placeholder="예: 다음 정기 점검 때 같은 Pod의 다른 디스크와 함께 교체"></textarea>
      <div class="chips">${['정기 점검 때 교체', '예비 디스크 없음', '추가 관찰'].map((t) => `<button type="button">${t}</button>`).join('')}</div>
      <div class="err" id="err" role="alert"></div>
      <div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn" type="button" id="cancel">취소</button><button class="btn pri" type="button" id="saveHold">보류 저장</button></div></div></div>`;
    const ta = document.getElementById('why');
    const close = () => { $layer.innerHTML = ''; };
    setTimeout(() => ta.focus(), 30);
    $layer.querySelectorAll('.chips button').forEach((b) => (b.onclick = () => { ta.value = b.textContent; ta.focus(); }));
    document.getElementById('cancel').onclick = close;
    document.getElementById('dim').onclick = (e) => { if (e.target.id === 'dim') close(); };
    document.addEventListener('keydown', function onEsc(e) { if (e.key === 'Escape') { close(); document.removeEventListener('keydown', onEsc); } });
    document.getElementById('saveHold').onclick = () => {
      const v = ta.value.trim();
      if (!v) { document.getElementById('err').textContent = '보류 사유를 입력하세요.'; ta.focus(); return; }
      close(); decide(id, 'hold', v);
    };
  }

  // ---------- 라우터 ----------
  function route() {
    const h = location.hash.replace(/^#\/?/, '');
    const [path, query] = h.split('?');
    const [page, id] = path.split('/');
    const tab = page === 'disk' || page === 'replace' ? page : 'dashboard';
    document.querySelectorAll('[data-tab]').forEach((a) => a.classList.toggle('on', a.dataset.tab === tab));
    $layer.querySelectorAll('.dim').forEach((x) => x.remove());
    if (tab === 'disk') viewDisk(id);
    else if (tab === 'replace') { const f = new URLSearchParams(query || '').get('f'); if (f && ST[f]) { ui.filter = f; if (state.steps.decide) done('check'); } viewReplace(); }
    else viewDashboard();
    renderGuide();
    window.scrollTo(0, 0);
  }

  document.getElementById('baseDate').textContent = BASE_DATE;
  document.getElementById('resetBtn').onclick = () => {
    state = fresh(); save(); ui.rack = 'B-04'; ui.range = 30; ui.filter = 'all';
    $layer.innerHTML = '';
    if (location.hash === '#/dashboard') route(); else location.hash = '#/dashboard';
    toast('처음 상태로 돌렸습니다');
  };
  window.addEventListener('hashchange', route);
  route();
})();
