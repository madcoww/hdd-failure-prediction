"""노션 4번용 화면 목업 v4.
참고: DEFOG 환경 모니터링 화면(남색 바탕, 위쪽 탭, 위에서 본 랙 평면도), 건축 평면도(벽선·축선·문 표시).
수치·Vault 번호·시리얼은 가상. 랙/열 배치는 공개 데이터에 없어 도식. 내용은 기능정의서 v1 기준."""
import os
import random
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
W, H = 1440, 900
random.seed(11)

FONT = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/'
        'pretendardvariable-dynamic-subset.min.css">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap">')

CSS = f"""
:root{{--bg:#0C1322;--pn:#121B2D;--pn2:#172238;--ln:#22304A;--ink:#E6ECF6;--sub:#8E9BB4;--mute:#5E6C87;
--blue:#3D8BFF;--cyan:#4CC9F0;--red:#FF4D5E;--amb:#FFB020;--grn:#2BD47D;--bp:#7FA3D6}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;background:var(--bg);color:var(--ink);font-family:'Pretendard Variable',Pretendard,'Malgun Gothic',sans-serif;
font-size:14px;overflow:hidden;display:flex;flex-direction:column}}
.num{{font-family:Rajdhani,'Pretendard Variable',sans-serif;font-variant-numeric:tabular-nums}}
.top{{height:58px;display:flex;align-items:center;padding:0 24px;background:#0F182A;border-bottom:1px solid var(--ln);gap:28px;flex:none}}
.logo{{display:flex;align-items:center;gap:10px;font-weight:700;font-size:15.5px;letter-spacing:-.2px}}
.logo i{{width:28px;height:28px;border-radius:7px;background:linear-gradient(135deg,#3D8BFF,#4CC9F0);display:flex;align-items:center;justify-content:center}}
.tabs{{display:flex;height:100%}}
.tab{{display:flex;align-items:center;padding:0 18px;color:var(--sub);font-size:14.5px;border-bottom:2px solid transparent}}
.tab.on{{color:#fff;font-weight:600;border-bottom-color:var(--blue);background:linear-gradient(0deg,rgba(61,139,255,.12),transparent)}}
.right{{margin-left:auto;display:flex;align-items:center;gap:18px}}
.date{{display:flex;align-items:baseline;gap:8px;color:var(--sub);font-size:12.5px}}
.date b{{font-size:22px;color:#fff;font-weight:600;letter-spacing:.5px}}
.user{{display:flex;align-items:center;gap:8px;padding:5px 12px 5px 5px;border:1px solid var(--ln);border-radius:20px;font-size:13px}}
.user span{{width:26px;height:26px;border-radius:50%;background:#26365A;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}}
main{{flex:1;padding:18px 24px 0;display:flex;flex-direction:column;gap:14px;min-height:0;position:relative}}
.foot{{height:30px;display:flex;align-items:center;padding:0 24px;color:var(--mute);font-size:12px;border-top:1px solid var(--ln);flex:none;background:#0F182A}}
.card{{background:var(--pn);border:1px solid var(--ln);border-radius:10px}}
.ch{{display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--ln)}}
.ch b{{font-size:14.5px}}.ch small{{color:var(--sub);font-size:12px}}
.pill{{display:inline-flex;align-items:center;height:22px;padding:0 8px;border-radius:5px;font-size:12px;font-weight:600;
background:rgba(142,155,180,.12);color:#B4C0D6}}
.pill.r{{background:rgba(255,77,94,.15);color:#FF7D8A}}.pill.a{{background:rgba(255,176,32,.15);color:#FFC452}}
.pill.b{{background:rgba(61,139,255,.16);color:#86B6FF}}
.btn{{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 13px;border-radius:7px;font-weight:600;font-size:13px;
border:1px solid var(--ln);background:var(--pn2);color:var(--ink)}}
.btn.pri{{background:var(--blue);border-color:var(--blue);color:#fff}}
.btn.sm{{height:27px;padding:0 10px;font-size:12.5px}}
.kpi{{flex:1;padding:14px 18px;display:flex;align-items:center;gap:14px}}
.kpi .v{{font-size:42px;font-weight:700;line-height:1}}
.kpi .l{{font-size:13px;color:var(--sub)}}.kpi .l b{{display:block;color:var(--ink);font-size:14.5px;margin-bottom:3px}}
.loc{{display:inline-flex;align-items:center;gap:5px;font-size:12.5px}}
.loc span{{padding:2px 7px;border-radius:5px;background:var(--pn2);border:1px solid var(--ln);color:#C9D3E5}}
.loc span.k{{background:rgba(255,77,94,.15);border-color:rgba(255,77,94,.35);color:#FF8B96;font-weight:600}}
.seg{{display:flex;gap:2px}}.seg i{{flex:1;border-radius:1.5px;background:#23314B}}
table{{border-collapse:collapse;width:100%}}
th{{text-align:left;font-weight:500;font-size:12.5px;color:var(--sub);padding:10px 14px;border-bottom:1px solid var(--ln);background:#101929}}
td{{padding:11px 14px;border-bottom:1px solid var(--ln);font-size:13.5px}}
"""

ICON = {
    "disk": '<path d="M22 12H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><path d="M6 16h.01M10 16h.01"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "down": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5M12 15V3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "chev": '<path d="m6 9 6 6 6-6"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
}


def ic(n, s=15, c="currentColor"):
    return (f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICON[n]}</svg>')


TABS = ["대시보드", "디스크 상세", "교체 목록", "모델 비교"]


def page(active, body, note):
    tabs = "".join(f'<div class="tab{" on" if t == active else ""}">{t}</div>' for t in TABS)
    return f"""<html><head><meta charset="utf-8">{FONT}<style>{CSS}</style></head><body>
<div class="top"><div class="logo"><i>{ic("disk", 16, "#fff")}</i>디스크 수명 관리</div><div class="tabs">{tabs}</div>
 <div class="right"><div class="date">기준일<b class="num">2026.06.30</b></div><div class="user"><span>운</span>운영 담당자</div></div></div>
<main>{body}</main><div class="foot">{note}</div></body></html>"""


def loc(dc, v, p, s):
    return (f'<span class="loc">{ic("pin", 14, "#FF6B78")}<span>{dc}</span><span>Vault {v}</span>'
            f'<span>Pod {p}</span><span class="k">슬롯 {s}</span></span>')


def seg(n_on, total, color, h=14):
    return (f'<div class="seg" style="height:{h}px">' +
            "".join(f'<i style="{"background:" + color if k < n_on else ""}"></i>' for k in range(total)) + "</div>")


HOT = {(3, 17), (3, 41), (11, 8), (16, 52)}
WARM = set()
while len(WARM) < 14:
    k = (random.randrange(20), random.randrange(60))
    if k not in HOT:
        WARM.add(k)
hot_pods = {p for p, _ in HOT}
warm_pods = {p for p, _ in WARM} - hot_pods

NOTE = "목업 화면 · 수치·Vault 번호·시리얼은 가상 · 위험 = 30일 고장 위험 상위 1%, 주의 = 상위 1~5% (팀 기준, 확정 전)"

# ===================== 1. 대시보드: 데이터센터 평면도 =====================
RW, RH, RG = 60, 38, 6           # 랙 크기(위에서 본 모습)
X0 = 150
ROWS = {"A": 104, "B": 184, "C": 300, "D": 380}
VAULT_RACKS = {("B", 4): "1xxx", ("B", 5): "1xxx", ("D", 7): "1ccc", ("D", 8): "1ccc"}
RACK_STATE = {("B", 4): "r", ("B", 5): "r", ("D", 7): "a", ("A", 2): "a", ("C", 9): "a"}


def rack_x(i):
    return X0 + (i - 1) * (RW + RG)


svg = []
# 모눈
svg.append('<defs><pattern id="g" width="20" height="20" patternUnits="userSpaceOnUse">'
           '<path d="M20 0H0V20" fill="none" stroke="rgba(127,163,214,.07)" stroke-width="1"/></pattern>'
           '<marker id="ar" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><circle cx="4" cy="4" r="2.5" fill="#4CC9F0"/></marker></defs>')
svg.append('<rect width="940" height="540" fill="url(#g)"/>')
# 축선 (건축 도면처럼 번호 원 + 점선)
for i in range(1, 11):
    cx = rack_x(i) + RW / 2
    svg.append(f'<line x1="{cx}" y1="44" x2="{cx}" y2="470" stroke="rgba(127,163,214,.16)" stroke-dasharray="3 5"/>')
    svg.append(f'<circle cx="{cx}" cy="26" r="11" fill="none" stroke="#7FA3D6" stroke-width="1"/>'
               f'<text x="{cx}" y="30.5" fill="#9FB8DD" font-size="11.5" text-anchor="middle" font-family="Rajdhani">{i}</text>')
for r, y in ROWS.items():
    cy = y + RH / 2
    svg.append(f'<circle cx="96" cy="{cy}" r="11" fill="none" stroke="#7FA3D6" stroke-width="1"/>'
               f'<text x="96" y="{cy + 4.5}" fill="#9FB8DD" font-size="12" text-anchor="middle" font-family="Rajdhani" font-weight="600">{r}</text>')
# 벽 (이중선) + 문
wall = "M120 52 H880 V478 H300 M232 478 H120 Z"
svg.append(f'<path d="M120 52 H880 V478 H300 M232 478 H120 V52" fill="none" stroke="#9DB6DB" stroke-width="2.2"/>')
svg.append(f'<path d="M128 60 H872 V470 H300 M232 470 H128 V60" fill="none" stroke="#5F7DA8" stroke-width="1"/>')
svg.append('<path d="M232 478 A68 68 0 0 1 300 410" fill="none" stroke="#7FA3D6" stroke-width="1" stroke-dasharray="4 3"/>'
           '<line x1="300" y1="478" x2="300" y2="410" stroke="#9DB6DB" stroke-width="1.4"/>'
           '<text x="266" y="500" fill="#7F90AD" font-size="11.5" text-anchor="middle">출입구</text>')
# 냉복도 / 열복도
xa, xb = rack_x(1) - 8, rack_x(10) + RW + 8
for y1, y2, name in [(ROWS["A"] + RH, ROWS["B"], "냉복도 1"), (ROWS["C"] + RH, ROWS["D"], "냉복도 2")]:
    svg.append(f'<rect x="{xa}" y="{y1}" width="{xb - xa}" height="{y2 - y1}" fill="rgba(61,139,255,.16)" stroke="rgba(61,139,255,.45)" stroke-dasharray="5 4"/>'
               f'<text x="{xb + 10}" y="{(y1 + y2) / 2 + 4}" fill="#6FA6FF" font-size="11.5">{name}</text>')
svg.append(f'<text x="{xb + 10}" y="{(ROWS["B"] + RH + ROWS["C"]) / 2 + 4}" fill="#B07A84" font-size="11.5">열복도</text>')
# 랙
for r, y in ROWS.items():
    for i in range(1, 11):
        x = rack_x(i)
        st = RACK_STATE.get((r, i))
        fill, stroke = {"r": ("rgba(255,77,94,.85)", "#FF8A95"), "a": ("rgba(255,176,32,.8)", "#FFCB66")}.get(st, ("#1B2840", "#3A4D6E"))
        svg.append(f'<rect x="{x}" y="{y}" width="{RW}" height="{RH}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        # 랙 앞면 표시선 (냉복도 쪽)
        fy = y + RH - 3 if r in "AC" else y + 1
        svg.append(f'<rect x="{x + 4}" y="{fy}" width="{RW - 8}" height="2" fill="rgba(255,255,255,.35)"/>')
        svg.append(f'<text x="{x + RW / 2}" y="{y + RH / 2 + 4}" fill="{"#fff" if st else "#5F7395"}" font-size="11" text-anchor="middle" font-family="Rajdhani" font-weight="600">{r}-{i:02d}</text>')
# 선택한 Vault 표시
sx, sy = rack_x(4) - 5, ROWS["B"] - 5
svg.append(f'<rect x="{sx}" y="{sy}" width="{2 * RW + RG + 10}" height="{RH + 10}" rx="4" fill="none" stroke="#4CC9F0" stroke-width="2"/>')
svg.append(f'<path d="M{sx + 2 * RW + RG + 10} {sy + RH + 10} L{sx + 2 * RW + RG + 60} 262 H{sx + 2 * RW + RG + 120}" fill="none" stroke="#4CC9F0" stroke-width="1.2" marker-start="url(#ar)"/>')
svg.append(f'<g transform="translate({sx + 2 * RW + RG + 122},236)"><rect width="196" height="52" rx="6" fill="#0E1A2E" stroke="#4CC9F0"/>'
           '<text x="12" y="21" fill="#fff" font-size="13" font-weight="700">Vault 1xxx</text>'
           '<text x="88" y="21" fill="#8E9BB4" font-size="11.5">랙 2개 · Pod 20대</text>'
           '<text x="12" y="40" fill="#FF7D8A" font-size="12" font-weight="600">위험 4</text>'
           '<text x="60" y="40" fill="#FFC452" font-size="12" font-weight="600">주의 14</text></g>')
# 방위 표시
svg.append('<g transform="translate(846,505)"><circle r="13" fill="none" stroke="#5F7DA8"/><path d="M0 -10 L5 6 L0 2 L-5 6Z" fill="#9DB6DB"/>'
           '<text x="20" y="5" fill="#7F90AD" font-size="11" font-family="Rajdhani">N</text></g>')
floor_svg = f'<svg width="940" height="530" viewBox="0 0 940 530">{"".join(svg)}</svg>'


def pod_face(p, sel=False):
    st = "r" if p in hot_pods else "a" if p in warm_pods else ""
    led = {"r": "#FF4D5E", "a": "#FFB020"}.get(st, "#2BD47D")
    fans = "".join('<span style="width:15px;height:15px;border-radius:50%;border:1.5px solid rgba(255,255,255,.28);'
                   'background:radial-gradient(circle,rgba(0,0,0,.35) 30%,transparent 32%);flex:none"></span>' for _ in range(2))
    ring = "box-shadow:0 0 0 2px #4CC9F0,0 0 14px rgba(76,201,240,.5);" if sel else ""
    bd = "#FF4D5E" if st == "r" else "#3A1A20"
    n = sum(1 for pp, _ in HOT if pp == p)
    badge = f'<span class="pill r" style="height:18px;font-size:11px;white-space:nowrap;padding:0 5px">위험 {n}</span>' if n else ""
    return (f'<div style="height:25px;border-radius:3px;background:linear-gradient(180deg,#A3242E,#7E1820);border:1px solid {bd};{ring}'
            f'display:flex;align-items:center;padding:0 7px;gap:6px">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{led};box-shadow:0 0 6px {led}"></span>'
            f'<span class="num" style="font-size:12.5px;font-weight:700;width:44px">Pod {p:02d}</span>{fans}'
            f'<span style="margin-left:auto">{badge}</span></div>')


def rack_front(name, pods):
    faces = "".join(pod_face(p, p == 3) for p in pods)
    return (f'<div style="flex:1;min-width:0"><div style="font-size:12px;color:var(--sub);text-align:center;margin-bottom:6px" class="num">랙 {name}</div>'
            f'<div style="background:#05080F;border:2px solid #2A3550;border-radius:5px;padding:6px 6px;display:flex;flex-direction:column;gap:4px">'
            f'{faces}</div></div>')


kpis = "".join(
    f'<div class="card kpi"><span class="v num" style="color:{c}">{v}</span><div class="l"><b>{t}</b>{s}</div>'
    f'<div style="margin-left:auto;width:90px">{bar}</div></div>'
    for v, c, t, s, bar in [
        (4, "#FF4D5E", "위험 디스크", "고장 위험 상위 1%", seg(4, 20, "#FF4D5E", 26)),
        (14, "#FFB020", "주의 디스크", "상위 1~5%", seg(14, 20, "#FFB020", 26)),
        (4, "#4CC9F0", "이번 주 교체 후보", "승인 대기 4건", seg(4, 20, "#4CC9F0", 26)),
        ("1,200", "#E6ECF6", "관리 중인 디스크", "ST12000NM0008", "")])

VLIST = "".join(
    f'<div style="display:flex;align-items:center;gap:8px;padding:7px 16px;border-top:1px solid var(--ln)">'
    f'<span class="num" style="font-weight:700;width:52px;white-space:nowrap">Pod {p:02d}</span><span class="loc"><span class="k">슬롯 {sl}</span></span>'
    f'<span style="color:var(--sub);font-size:12.5px">ZJV0****{k}</span><b class="num" style="margin-left:auto;color:#FF4D5E;font-size:16px">{sc}</b></div>'
    for k, (p, sl, sc) in enumerate([(3, 17, "0.93"), (3, 41, "0.91"), (11, "08", "0.88"), (16, 52, "0.87")], 1))
dash = f"""
<div style="display:flex;gap:14px">{kpis}</div>
<div style="display:flex;gap:14px;flex:1;min-height:0;margin-bottom:14px">
 <div class="card" style="flex:1;display:flex;flex-direction:column">
  <div class="ch"><b>sac2 데이터센터 평면도</b><small>위에서 본 랙 배치, 랙을 누르면 오른쪽에 앞면이 열립니다</small>
   <div style="margin-left:auto;display:flex;gap:14px;font-size:12px;color:var(--sub)">
    <span><i style="display:inline-block;width:10px;height:10px;background:#FF4D5E;border-radius:2px"></i> 위험 있음</span>
    <span><i style="display:inline-block;width:10px;height:10px;background:#FFB020;border-radius:2px"></i> 주의 있음</span>
    <span><i style="display:inline-block;width:10px;height:10px;background:#1B2840;border:1px solid #3A4D6E;border-radius:2px"></i> 정상</span></div></div>
  <div style="flex:1;display:flex;align-items:center;justify-content:center;background:#0E1728;border-radius:0 0 10px 10px">{floor_svg}</div>
 </div>
 <div class="card" style="width:400px;display:flex;flex-direction:column">
  <div class="ch"><b>Vault 1xxx 앞면</b><small>랙 B-04, B-05</small><span class="pill r" style="margin-left:auto">위험 4</span></div>
  <div style="display:flex;gap:12px;padding:12px 16px">{rack_front("B-04", range(10))}{rack_front("B-05", range(10, 20))}</div>
  <div style="margin:0 16px;padding:11px 12px;border-radius:8px;background:rgba(76,201,240,.08);border:1px solid rgba(76,201,240,.3)">
   <div style="display:flex;align-items:center;font-size:12.5px;color:var(--sub)">선택한 Pod<span class="btn sm pri" style="margin-left:auto">위에서 보기</span></div>
   <div style="margin-top:4px;font-weight:700">Pod 03 <span style="font-weight:500;color:var(--sub);font-size:12.5px">위험 2 · 주의 3 · 정상 55</span></div>
  </div>
  <div style="padding:12px 16px 4px;font-size:12.5px;color:var(--sub)">이 Vault의 위험 디스크</div>
  {VLIST}
 </div>
</div>"""
dash_note = (NOTE + " · 위치 열(datacenter·vault_id·pod_id)은 실제 데이터, 랙·열 배치와 복도는 공개 자료에 없어 도식")

# ===================== 2. Pod 탑뷰 (도면 스타일) =====================
SEL, P_HOT, P_WARM = 17, {17, 41}, {5, 33, 58}
DW, DH, DG, CG = 112, 24, 5, 26
ox, oy = 110, 90
ps = ['<defs><pattern id="g2" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0H0V20" fill="none" '
      'stroke="rgba(127,163,214,.07)"/></pattern><marker id="ah" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto">'
      '<path d="M0 0L8 4L0 8Z" fill="#7FA3D6"/></marker><marker id="dt" markerWidth="8" markerHeight="8" refX="4" refY="4">'
      '<circle cx="4" cy="4" r="2.5" fill="#FF4D5E"/></marker></defs><rect width="900" height="600" fill="url(#g2)"/>']
cw = 4 * DW + 3 * CG
chh = 15 * DH + 14 * DG
# 섀시 외곽 (이중선)
ps.append(f'<rect x="{ox - 46}" y="{oy - 22}" width="{cw + 46 + 210}" height="{chh + 44}" fill="none" stroke="#9DB6DB" stroke-width="2"/>')
ps.append(f'<rect x="{ox - 40}" y="{oy - 16}" width="{cw + 40 + 198}" height="{chh + 32}" fill="none" stroke="#4E6A93" stroke-width="1"/>')
# 앞면 띠
ps.append(f'<rect x="{ox - 40}" y="{oy - 16}" width="24" height="{chh + 32}" fill="rgba(200,32,43,.55)" stroke="#E5484D"/>'
          f'<text x="{ox - 28}" y="{oy + chh / 2}" fill="#fff" font-size="12.5" font-weight="700" text-anchor="middle" '
          f'writing-mode="tb" letter-spacing="6">앞면</text>')
for r in range(4):
    x = ox + r * (DW + CG)
    ps.append(f'<text x="{x + DW / 2}" y="{oy - 30}" fill="#9FB8DD" font-size="12" text-anchor="middle">{r + 1}번째 줄</text>')
    for i in range(15):
        s = r * 15 + i
        y = oy + i * (DH + DG)
        if s == SEL:
            ps.append(f'<rect x="{x - 3}" y="{y - 3}" width="{DW + 6}" height="{DH + 6}" rx="4" fill="none" stroke="#FF4D5E" stroke-width="1.5" opacity=".6"/>')
            fill, stroke, tc = "#FF4D5E", "#FFB3BA", "#fff"
        else:
            fill, stroke, tc = "#18253C", "#3E5479", "#7F93B5"
        led = "#FF4D5E" if s in P_HOT else "#FFB020" if s in P_WARM else "#2BD47D"
        ps.append(f'<rect x="{x}" y="{y}" width="{DW}" height="{DH}" rx="2" fill="{fill}" stroke="{stroke}"/>')
        ps.append(f'<circle cx="{x + 10}" cy="{y + DH / 2}" r="3.5" fill="{"#fff" if s == SEL else led}"/>')
        ps.append(f'<text x="{x + DW - 8}" y="{y + DH / 2 + 4.5}" fill="{tc}" font-size="12.5" text-anchor="end" font-family="Rajdhani" font-weight="600">{s}</text>')
# 부품 영역
px = ox + cw + 22
ps.append(f'<rect x="{px}" y="{oy}" width="166" height="{chh}" fill="none" stroke="#4E6A93" stroke-dasharray="6 4"/>'
          f'<line x1="{px}" y1="{oy}" x2="{px + 166}" y2="{oy + chh}" stroke="rgba(78,106,147,.5)"/>'
          f'<text x="{px + 83}" y="{oy + chh / 2 - 6}" fill="#7F93B5" font-size="12.5" text-anchor="middle">서버 부품</text>'
          f'<text x="{px + 83}" y="{oy + chh / 2 + 13}" fill="#5E6C87" font-size="11.5" text-anchor="middle">(메인보드, 전원 등)</text>')
ps.append(f'<text x="{px + 190}" y="{oy + chh / 2}" fill="#7F93B5" font-size="12" writing-mode="tb" text-anchor="middle">뒷면</text>')
# 치수선
dy = oy + chh + 46
ps.append(f'<line x1="{ox}" y1="{dy}" x2="{ox + cw}" y2="{dy}" stroke="#7FA3D6" marker-start="url(#ah)" marker-end="url(#ah)"/>'
          f'<line x1="{ox}" y1="{dy - 8}" x2="{ox}" y2="{dy + 8}" stroke="#7FA3D6"/><line x1="{ox + cw}" y1="{dy - 8}" x2="{ox + cw}" y2="{dy + 8}" stroke="#7FA3D6"/>'
          f'<rect x="{ox + cw / 2 - 80}" y="{dy - 11}" width="160" height="22" fill="#0E1728"/>'
          f'<text x="{ox + cw / 2}" y="{dy + 4.5}" fill="#9FB8DD" font-size="12" text-anchor="middle">디스크 줄 4개 × 15개 = 60개</text>')
# 선택 디스크 지시선
selx, sely = ox + 1 * (DW + CG) + DW, oy + 2 * (DH + DG) + DH / 2
ps.append(f'<path d="M{selx + 4} {sely} H{selx + 18} L{selx + 40} {oy - 58} H{selx + 100}" fill="none" stroke="#FF4D5E" stroke-width="1.2" marker-start="url(#dt)"/>'
          f'<text x="{selx + 104}" y="{oy - 54}" fill="#FF7D8A" font-size="12.5" font-weight="700">슬롯 17 · 위험 0.93</text>')
pod_svg = f'<svg width="900" height="600" viewBox="0 0 900 600">{"".join(ps)}</svg>'

topview = f"""
<div style="display:flex;align-items:center;gap:12px"><div><div style="font-size:12.5px;color:var(--sub)">대시보드 / sac2 / Vault 1xxx / 랙 B-04</div>
 <div style="font-size:22px;font-weight:700;margin-top:2px">Pod 03 위에서 본 모습</div></div>
 <div style="margin-left:auto;display:flex;gap:6px"><span class="pill r">위험 2</span><span class="pill a">주의 3</span><span class="pill">정상 55</span></div></div>
<div style="display:flex;gap:14px;flex:1;min-height:0;margin-bottom:14px">
 <div class="card" style="flex:1;display:flex;align-items:center;justify-content:center;background:#0E1728">{pod_svg}</div>
 <div style="width:360px;display:flex;flex-direction:column;gap:12px">
  <div class="card" style="padding:16px">
   <div style="font-size:12.5px;color:var(--sub);margin-bottom:8px">선택한 디스크</div>{loc("sac2", "1xxx", "03", "17")}
   <div style="display:flex;align-items:flex-end;margin-top:16px"><div><div style="font-size:12.5px;color:var(--sub)">30일 고장 위험</div>
    <span class="num" style="font-size:46px;font-weight:700;color:#FF4D5E;line-height:1">0.93</span></div><span class="pill r" style="margin:0 0 6px auto">위험</span></div>
   <div style="margin-top:8px">{seg(28, 30, "#FF4D5E", 14)}</div>
   <div style="display:flex;justify-content:space-between;margin-top:14px"><span style="color:var(--sub)">예측 잔여수명</span><b class="num" style="font-size:17px">4일</b></div>
   <div style="display:flex;justify-content:space-between;margin-top:8px"><span style="color:var(--sub)">시리얼</span><b>ZJV0****1</b></div>
   <div style="display:flex;justify-content:space-between;margin-top:8px"><span style="color:var(--sub)">가장 큰 원인</span><b>197 대기 섹터 급증</b></div>
  </div>
  <div class="card" style="padding:14px 16px;border-color:rgba(76,201,240,.35);background:rgba(76,201,240,.07)">
   <div style="display:flex;align-items:center;gap:8px;font-weight:600;color:#7FDBF7">{ic("pin", 15, "#4CC9F0")}현장에서 찾는 법</div>
   <div style="margin-top:6px;line-height:1.65">랙 B-04 위에서 4번째 Pod를 꺼내<br>앞면 기준 2번째 줄, 위에서 3번째 칸</div>
   <div style="font-size:11.5px;color:var(--mute);margin-top:6px">랙 위치와 슬롯 번호의 줄·칸 대응은 도식 (데이터 확인 전)</div>
  </div>
  <div style="display:flex;gap:8px"><span class="btn pri" style="flex:1;justify-content:center">{ic("check", 15, "#fff")}교체 후보에 추가</span><span class="btn">디스크 상세</span></div>
 </div>
</div>"""
top_note = "목업 화면 · 디스크 60개를 15개씩 줄지어 앞쪽에 둔 구조는 Backblaze Storage Pod 6.0 설명 기준 · 부품 위치, 랙 번호, 슬롯 대응은 도식"


# ===================== 3. 디스크 상세 =====================
def area(vals, color, title, latest, unit):
    w, h = 300, 96
    mx = max(max(vals), 1)
    pts = [(i * w / (len(vals) - 1), h - v / mx * (h - 10) - 4) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    gid = "a" + str(abs(hash(title)) % 9999)
    grid = "".join(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="#1E2B43" vector-effect="non-scaling-stroke"/>' for y in (24, 48, 72))
    return (f'<div class="card" style="padding:12px 14px"><div style="display:flex;align-items:baseline">'
            f'<span style="font-size:13px;color:var(--sub)">{title}</span><b class="num" style="margin-left:auto;font-size:24px;color:{color}">{latest}'
            f'<span style="font-size:12px;color:var(--sub);font-family:Pretendard Variable"> {unit}</span></b></div>'
            f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" style="margin-top:6px;width:100%;height:170px;display:block"><defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity=".35"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
            f'{grid}<polygon points="0,{h} {line} {w},{h}" fill="url(#{gid})"/><polyline points="{line}" fill="none" stroke="{color}" stroke-width="2" vector-effect="non-scaling-stroke"/></svg></div>')


n = 30
s5 = [8 + (i // 6) * 2 + (14 if i > 24 else 0) for i in range(n)]
s187 = [0 if i < 18 else (i - 18) * 2 for i in range(n)]
s197 = [0 if i < 22 else (i - 22) * 6 for i in range(n)]
charts = (area(s197, "#FF4D5E", "197 대기 섹터", s197[-1], "개") + area(s187, "#FF4D5E", "187 복구 불가 오류", s187[-1], "건")
          + area(s5, "#FFB020", "5 재할당 섹터", s5[-1], "개") + area([0] * n, "#5E6C87", "188 명령 시간 초과", 0, "건"))
detail = f"""
<div style="display:flex;align-items:center;gap:12px">
 <div style="flex:1;max-width:420px;height:36px;border:1px solid var(--ln);background:var(--pn);border-radius:8px;display:flex;align-items:center;gap:8px;padding:0 12px;color:var(--sub)">
  {ic("search", 15)}ZJV0****1</div>
 <div style="margin-left:auto;display:flex;gap:8px"><span class="btn">{ic("down", 15)}기록 내려받기</span><span class="btn pri">{ic("check", 15, "#fff")}교체 후보에 추가</span></div></div>
<div style="display:flex;gap:14px">
 <div class="card" style="flex:1;padding:16px 18px;display:flex;align-items:center;gap:28px">
  <div><div style="font-size:20px;font-weight:700">ZJV0****1</div><div style="color:var(--sub);font-size:12.5px;margin-top:2px">ST12000NM0008</div></div>
  <div style="border-left:1px solid var(--ln);padding-left:24px"><div style="font-size:12.5px;color:var(--sub);margin-bottom:7px">위치</div>{loc("sac2", "1xxx", "03", "17")}</div>
  <div style="border-left:1px solid var(--ln);padding-left:24px;line-height:1.9;font-size:13.5px">
   <span style="color:var(--sub)">가동 시간</span> <b>3.2년</b><br><span style="color:var(--sub)">최근 온도</span> <b>31℃</b></div>
 </div>
 <div class="card" style="width:400px;padding:14px 18px">
  <div style="display:flex;align-items:center;font-size:12.5px;color:var(--sub)">30일 안에 고장 날 위험<span class="pill r" style="margin-left:auto">위험</span></div>
  <div style="display:flex;align-items:baseline;gap:16px"><span class="num" style="font-size:46px;font-weight:700;color:#FF4D5E;line-height:1.05">0.93</span>
   <span style="color:var(--sub)">예측 잔여수명 <b class="num" style="color:var(--ink);font-size:18px">4일</b></span></div>
  <div style="margin-top:6px">{seg(28, 30, "#FF4D5E", 12)}</div>
 </div>
</div>
<div style="display:flex;gap:14px;flex:1;min-height:0;margin-bottom:14px">
 <div style="flex:1">
  <div style="display:flex;align-items:center;margin-bottom:10px"><b>SMART 기록</b>
   <div style="margin-left:auto;display:flex;border:1px solid var(--ln);border-radius:7px;overflow:hidden;font-size:12.5px">
    <span style="padding:4px 12px;background:var(--blue);color:#fff">30일</span><span style="padding:4px 12px;color:var(--sub)">60일</span><span style="padding:4px 12px;color:var(--sub)">90일</span></div></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">{charts}</div>
 </div>
</div>
</div>"""
detail_note = NOTE + " · SMART 그래프는 예시 값"

# ===================== 4. 교체 목록 =====================
items = [("ZJV0****1", ("sac2", "1xxx", "03", "17"), 0.93, 4, "197 대기 섹터 급증", "r"),
         ("ZJV0****2", ("sac2", "1xxx", "03", "41"), 0.91, 6, "187 오류 30일간 증가", "r"),
         ("ZJV0****3", ("sac2", "1xxx", "11", "08"), 0.88, 9, "5 재할당 섹터 증가", "r"),
         ("ZJV0****4", ("sac2", "1xxx", "16", "52"), 0.87, 12, "197 대기 섹터 증가", "r"),
         ("ZJV0****5", ("phx1", "1yyy", "05", "22"), 0.71, 21, "187 오류 증가", "a"),
         ("ZJV0****6", ("iad1", "1zzz", "00", "30"), 0.66, 27, "5 재할당 섹터 증가", "a")]
trs = ""
for i, (sn, L, sc, rul, why, g) in enumerate(items):
    col = "#FF4D5E" if g == "r" else "#FFB020"
    status = '<span class="pill b">보류 사유 입력 중</span>' if i == 1 else '<span class="pill">승인 대기</span>'
    trs += (f'<tr style="{"background:rgba(61,139,255,.07)" if i == 1 else ""}"><td style="width:26px"><span style="display:inline-block;width:15px;height:15px;'
            f'border:1.5px solid #3A4D6E;border-radius:4px"></span></td><td>{loc(*L)}</td><td style="color:var(--sub)">{sn}</td>'
            f'<td><div style="display:flex;align-items:center;gap:8px"><b class="num" style="color:{col};font-size:17px;width:36px">{sc:.2f}</b>'
            f'<div style="width:70px">{seg(round(sc * 10), 10, col, 12)}</div></div></td>'
            f'<td><b class="num" style="font-size:16px">{rul}일</b></td><td>{why}</td><td>{status}</td>'
            f'<td style="text-align:right"><span class="btn sm pri">승인</span> <span class="btn sm">보류</span></td></tr>')
replace = f"""
<div style="display:flex;align-items:center;gap:8px">
 <div><div style="font-size:22px;font-weight:700">교체 목록</div><div style="color:var(--sub);font-size:13px;margin-top:2px">위험 점수가 높은 순서, 승인하면 승인자와 시각이 기록됩니다</div></div>
 <div style="margin-left:auto;display:flex;gap:8px"><span class="btn">{ic("clock", 15)}처리 이력</span><span class="btn">{ic("down", 15)}CSV로 내려받기</span></div></div>
<div style="display:flex;gap:8px;align-items:center">
 <span class="btn sm">등급: 전체{ic("chev", 13)}</span><span class="btn sm">데이터센터: 전체{ic("chev", 13)}</span>
 <div style="margin-left:auto;display:flex;align-items:center;gap:12px;font-size:13px"><span style="color:var(--sub)">교체 후보 기준</span>
  <div style="width:200px;height:6px;background:#1C2840;border-radius:3px;position:relative"><div style="width:14px;height:6px;background:var(--blue);border-radius:3px"></div>
   <div style="position:absolute;left:8px;top:-5px;width:16px;height:16px;border-radius:50%;background:#fff;border:3px solid var(--blue)"></div></div>
  <span class="pill b">위험 상위 1%</span></div></div>
<div class="card" style="overflow:hidden"><table>
 <tr><th></th><th>위치</th><th>시리얼</th><th>위험 점수</th><th>잔여수명</th><th>주요 원인</th><th>상태</th><th></th></tr>{trs}</table></div>
<div class="card" style="position:absolute;right:24px;bottom:16px;width:390px;padding:18px;background:var(--pn2);box-shadow:0 24px 50px -12px rgba(0,0,0,.6)">
 <div style="display:flex;align-items:center"><b>보류 사유를 적어 주세요</b><span class="pill r" style="margin-left:auto">필수</span></div>
 <div style="margin:10px 0">{loc("sac2", "1xxx", "03", "41")}</div>
 <div style="border:1px solid var(--blue);box-shadow:0 0 0 3px rgba(61,139,255,.2);border-radius:8px;height:62px;padding:9px 11px;font-size:13px;color:var(--mute);background:var(--pn)">
  예: 다음 정기 점검 때 같은 Pod의 슬롯 17과 함께 교체</div>
 <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px"><span class="btn sm">취소</span><span class="btn sm pri">보류 저장</span></div>
</div>"""

# ===================== 5. 모델 비교 =====================
cols = "".join(
    f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:8px">'
    f'<span class="pill">--개 · --원</span>'
    f'<div style="width:100px;height:330px;border-radius:6px 6px 2px 2px;border:1.5px dashed {c};'
    f'background:repeating-linear-gradient(135deg,{bg} 0 8px,transparent 8px 16px)"></div>'
    f'<b style="font-size:13.5px">{nm}</b></div>'
    for nm, c, bg in [("SMART 규칙", "#5E6C87", "rgba(94,108,135,.18)"), ("머신러닝 모델", "#3D8BFF", "rgba(61,139,255,.18)"),
                      ("딥러닝 모델", "#4CC9F0", "rgba(76,201,240,.16)")])
model = f"""
<div style="display:flex;align-items:center"><div><div style="font-size:22px;font-weight:700">모델 비교</div>
 <div style="color:var(--sub);font-size:13px;margin-top:2px">같은 시험 기간, 같은 수의 고장을 잡는다고 할 때</div></div>
 <span class="pill" style="margin-left:auto">결과 나오면 채움</span></div>
<div style="display:flex;gap:14px;flex:1;min-height:0;margin-bottom:14px">
 <div style="width:500px;display:flex;flex-direction:column;gap:14px">
  <div class="card" style="overflow:hidden"><table>
   <tr><th>방식</th><th>경보 정밀도</th><th>AP</th><th>잡은 고장</th></tr>
   <tr><td><i style="display:inline-block;width:9px;height:9px;border-radius:2px;background:#5E6C87;margin-right:8px"></i>SMART 규칙 (기준)</td><td>--%</td><td>--</td><td>-- / --</td></tr>
   <tr><td><i style="display:inline-block;width:9px;height:9px;border-radius:2px;background:#3D8BFF;margin-right:8px"></i><b>머신러닝 모델</b></td><td>--%</td><td>--</td><td>-- / --</td></tr>
   <tr><td style="border:none"><i style="display:inline-block;width:9px;height:9px;border-radius:2px;background:#4CC9F0;margin-right:8px"></i><b>딥러닝 모델</b></td><td style="border:none">--%</td><td style="border:none">--</td><td style="border:none">-- / --</td></tr>
  </table></div>
  <div class="card" style="padding:16px">
   <b>디스크 1개 가격</b><div style="font-size:12.5px;color:var(--sub);margin:3px 0 10px">바꾸면 절감액을 다시 계산합니다</div>
   <div style="display:flex;gap:8px"><div style="flex:1;height:34px;border:1px solid var(--ln);background:var(--pn2);border-radius:7px;display:flex;align-items:center;padding:0 12px">
    <span class="num" style="font-size:17px;font-weight:600">364,550</span><span style="margin-left:auto;color:var(--sub)">원</span></div><span class="btn pri">다시 계산</span></div>
  </div>
 </div>
 <div class="card" style="flex:1;display:flex;flex-direction:column">
  <div class="ch"><b>1년 동안 바꿔야 하는 디스크 수</b><small>실험 결과가 나오면 막대 높이와 절감액을 채웁니다</small></div>
  <div style="display:flex;flex:1;align-items:flex-end;padding:0 30px 22px">{cols}</div>
 </div>
</div>"""
model_note = "목업 화면 · 성능 수치는 모델 확정 후 채움 · 모델 종류도 확정 전이라 머신러닝·딥러닝 모델로 표시"

SCREENS = [("1_dashboard", "대시보드", dash, dash_note), ("2_pod_topview", "대시보드", topview, top_note),
           ("3_disk_detail", "디스크 상세", detail, detail_note), ("4_replace_list", "교체 목록", replace, NOTE),
           ("5_model_compare", "모델 비교", model, model_note)]

for name, active, body, note in SCREENS:
    html = os.path.join(BASE, name + ".html")
    with open(html, "w", encoding="utf-8") as f:
        f.write(page(active, body, note))
    png = os.path.join(BASE, name + ".png")
    if os.path.exists(png):
        os.remove(png)
    for _ in range(3):
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=10000",
                        f"--screenshot={png}", f"--window-size={W},{H}", "file:///" + html.replace("\\", "/")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            if os.path.exists(png):
                break
            time.sleep(0.5)
        if os.path.exists(png):
            break
    print("saved" if os.path.exists(png) else "FAILED", png)
