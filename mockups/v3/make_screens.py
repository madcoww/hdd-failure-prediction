"""노션 4번용 화면 목업 v3. 참고: Dribbble 'Arclink - Data Center Dashboard' 같은 밝은 SaaS 스타일
(창 테두리, 흰 화면, 아이콘 칩, 눈금 막대, 칸 지도). 수치·Vault 번호·시리얼은 가상, 내용은 기능정의서 v1 기준."""
import os
import random
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
W, H = 1440, 900
random.seed(11)

FONT = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/'
        'dist/web/variable/pretendardvariable-dynamic-subset.min.css">')

CSS = f"""
:root{{--ink:#18181B;--sub:#71717A;--mute:#A1A1AA;--line:#ECECF0;--soft:#F7F7F9;
--vio:#7C3AED;--vio-s:#F3EEFF;--red:#EF4444;--red-s:#FEF1F1;--amb:#F59E0B;--amb-s:#FFF6E5;--ok:#E4E4E9}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;font-family:'Pretendard Variable',Pretendard,'Malgun Gothic',sans-serif;color:var(--ink);
font-size:14px;letter-spacing:-.1px;overflow:hidden;
background:radial-gradient(900px 600px at 0% 0%,#E9E3FF 0%,transparent 60%),
radial-gradient(800px 600px at 100% 0%,#FFE4F1 0%,transparent 55%),
radial-gradient(900px 700px at 60% 100%,#E2E8FF 0%,transparent 60%),#F4F2FA}}
.win{{position:absolute;left:40px;top:34px;width:{W - 80}px;height:{H - 84}px;background:#fff;border-radius:16px;
box-shadow:0 1px 0 rgba(255,255,255,.6) inset,0 30px 70px -20px rgba(40,20,90,.28),0 0 0 1px rgba(20,10,60,.06);
display:flex;flex-direction:column;overflow:hidden}}
.bar{{height:52px;display:flex;align-items:center;padding:0 18px;border-bottom:1px solid var(--line);gap:16px}}
.dots span{{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:7px}}
.search{{margin:0 auto;width:380px;height:32px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;
gap:8px;padding:0 10px;color:var(--mute);font-size:13px}}
.kbd{{margin-left:auto;border:1px solid var(--line);border-radius:5px;padding:0 5px;font-size:11px}}
.body{{flex:1;display:flex;min-height:0}}
.side{{width:228px;border-right:1px solid var(--line);padding:16px 12px;display:flex;flex-direction:column;gap:2px}}
.me{{display:flex;align-items:center;gap:10px;padding:4px 8px 16px}}
.av{{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#C4B5FD,#F9A8D4);display:flex;
align-items:center;justify-content:center;font-weight:700;color:#fff;font-size:14px}}
.me b{{font-size:14px}}.me small{{display:block;font-size:11.5px;color:var(--sub);background:var(--soft);
border-radius:5px;padding:1px 6px;margin-top:2px;width:max-content}}
.grp{{font-size:11.5px;color:var(--mute);padding:14px 10px 6px;border-top:1px dashed var(--line);margin-top:8px}}
.nav{{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;color:#3F3F46;font-size:14px}}
.nav.on{{background:var(--soft);color:var(--ink);font-weight:600;box-shadow:0 0 0 1px var(--line) inset}}
.nav.dim{{color:var(--mute)}}
.nav svg{{color:#71717A}}
main{{flex:1;padding:22px 26px;min-width:0;position:relative;background:#FCFCFD}}
.hd{{display:flex;align-items:flex-end;margin-bottom:18px}}
.hd h1{{font-size:24px;font-weight:700;letter-spacing:-.5px}}
.hd p{{color:var(--sub);font-size:13.5px;margin-top:3px}}
.hd .act{{margin-left:auto;display:flex;gap:8px;align-items:center}}
.btn{{display:inline-flex;align-items:center;gap:6px;height:34px;padding:0 13px;border-radius:9px;font-weight:600;font-size:13.5px;
border:1px solid var(--line);background:#fff;color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.btn.pri{{background:var(--ink);color:#fff;border-color:var(--ink)}}
.btn.sm{{height:28px;padding:0 10px;font-size:12.5px;border-radius:7px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:0 1px 2px rgba(16,16,32,.04)}}
.ct{{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid var(--line);font-weight:600}}
.chipi{{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center}}
.pill{{display:inline-flex;align-items:center;gap:4px;height:22px;padding:0 8px;border-radius:6px;font-size:12px;font-weight:600;
background:var(--soft);color:var(--sub);border:1px solid var(--line)}}
.pill.r{{background:var(--red-s);color:#DC2626;border-color:#FBD5D5}}
.pill.a{{background:var(--amb-s);color:#B45309;border-color:#FBE3B4}}
.pill.v{{background:var(--vio-s);color:var(--vio);border-color:#E4D8FF}}
.big{{font-size:34px;font-weight:700;letter-spacing:-1px;font-variant-numeric:tabular-nums}}
.tick{{display:flex;gap:2px;height:22px}}.tick i{{flex:1;border-radius:2px;background:#E9E9EE}}
.c{{border-radius:3px;background:var(--ok)}}.c.a{{background:var(--amb)}}.c.r{{background:var(--red)}}
.loc{{display:inline-flex;align-items:center;gap:6px;font-weight:600}}
.loc span{{background:var(--soft);border:1px solid var(--line);border-radius:6px;padding:2px 7px;font-size:12.5px}}
.loc span.k{{background:var(--red-s);border-color:#FBD5D5;color:#DC2626}}
.note{{position:absolute;left:44px;bottom:16px;font-size:12px;color:#7C7896}}
table{{border-collapse:collapse;width:100%}}
th{{font-size:12.5px;color:var(--sub);font-weight:500;text-align:left;padding:10px 14px;background:var(--soft);border-bottom:1px solid var(--line)}}
td{{padding:11px 14px;border-bottom:1px solid var(--line);font-size:13.5px}}
"""

# ---- 아이콘 (Lucide 모양을 단순화) ----
P = {
    "dash": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "disk": '<path d="M22 12H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><path d="M6 16h.01M10 16h.01"/>',
    "list": '<path d="m3 17 2 2 4-4M3 7l2 2 4-4M13 6h8M13 12h8M13 18h8"/>',
    "chart": '<path d="M3 3v18h18M18 17V9M13 17V5M8 17v-3"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4M12 17h.01"/>',
    "server": '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><path d="M6 6h.01M6 18h.01"/>',
    "cal": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "down": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5M12 15V3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "act": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "chev": '<path d="m6 9 6 6 6-6"/>',
    "wrench": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
}


def ic(name, size=16, color="currentColor", sw=1.8):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round">{P[name]}</svg>')


MENU = [("대시보드", "dash"), ("디스크 상세", "disk"), ("교체 목록", "list"), ("모델 비교", "chart")]


def window(active, body):
    nav = "".join(f'<div class="nav{" on" if m == active else ""}">{ic(i)}{m}</div>' for m, i in MENU)
    return f"""
<div class="win">
 <div class="bar"><div class="dots"><span style="background:#FF5F57"></span><span style="background:#FEBC2E"></span><span style="background:#28C840"></span></div>
  <div class="search">{ic("search", 15)}시리얼 번호나 위치로 찾기<span class="kbd">Ctrl K</span></div>
  <div style="width:80px"></div></div>
 <div class="body">
  <aside class="side">
   <div class="me"><div class="av">운</div><div><b>운영 담당자</b><small>sac2 데이터센터</small></div></div>
   {nav}
   <div class="grp">설정</div>
   <div class="nav dim">{ic("bell")}알림 (검토 중)</div>
   <div style="margin-top:auto" class="card"><div style="padding:12px;font-size:12px;color:var(--sub);line-height:1.55">
    <b style="color:var(--ink);font-size:12.5px">기준 데이터</b><br>2026년 6월 30일까지<br>Backblaze 공개 데이터</div></div>
  </aside>
  <main>{body}</main>
 </div>
</div>"""


def page(active, body, note):
    return (f'<html><head><meta charset="utf-8">{FONT}<style>{CSS}</style></head><body>'
            f'{window(active, body)}<div class="note">{note}</div></body></html>')


def loc(dc, v, p, s):
    return (f'<span class="loc">{ic("pin", 14, "#DC2626")}<span>{dc}</span><span>Vault {v}</span>'
            f'<span>Pod {p}</span><span class="k">슬롯 {s}</span></span>')


def ticks(n_on, total, color, h=22):
    return (f'<div class="tick" style="height:{h}px">' +
            "".join(f'<i style="{"background:" + color if k < n_on else ""}"></i>' for k in range(total)) + "</div>")


NOTE_BASE = "목업 화면 · 수치·Vault 번호·시리얼은 가상 · 위험 = 30일 고장 위험 상위 1%, 주의 = 상위 1~5% (팀 기준, 확정 전)"

HOT = {(3, 17), (3, 41), (11, 8), (16, 52)}
WARM = set()
while len(WARM) < 14:
    k = (random.randrange(20), random.randrange(60))
    if k not in HOT:
        WARM.add(k)

# ================= 1. 대시보드 =================
def stat(icon, bg, fg, title, num, pill):
    return (f'<div class="card" style="flex:1"><div class="ct" style="border:none;padding-bottom:4px">'
            f'<div class="chipi" style="background:{bg}">{ic(icon, 16, fg)}</div>{title}</div>'
            f'<div style="display:flex;align-items:center;padding:4px 16px 16px"><span class="big">{num}</span>'
            f'<span style="margin-left:auto">{pill}</span></div></div>')


stats = (stat("alert", "var(--red-s)", "#DC2626", "위험 디스크", 4, '<span class="pill r">상위 1%</span>')
         + stat("act", "var(--amb-s)", "#D97706", "주의 디스크", 14, '<span class="pill a">상위 1~5%</span>')
         + stat("wrench", "var(--vio-s)", "#7C3AED", "이번 주 교체 후보", 4, '<span class="pill">승인 대기 4</span>')
         + stat("server", "#F1F5F9", "#475569", "관리 중인 디스크", "1,200", '<span class="pill">Pod 20대</span>'))


def vault_item(dc, v, hot_pods, warm_pods, h, w, on=False):
    t = "".join(f'<i style="background:{"var(--red)" if k in hot_pods else "var(--amb)" if k in warm_pods else "#E9E9EE"}"></i>'
                for k in range(20))
    return (f'<div style="padding:12px 14px;border:1px solid {"#D9CCFF" if on else "var(--line)"};border-radius:12px;'
            f'{"box-shadow:0 0 0 3px var(--vio-s);" if on else ""}background:#fff;margin-bottom:8px">'
            f'<div style="display:flex;align-items:center;gap:10px"><div class="chipi" style="background:var(--soft);width:28px;height:28px">'
            f'{ic("server", 15, "#52525B")}</div><div><b style="font-size:14px">Vault {v}</b>'
            f'<div style="font-size:12px;color:var(--sub)">{dc} 데이터센터</div></div>'
            f'<span style="margin-left:auto" class="pill {"r" if h else "a"}">{"위험 " + str(h) if h else "주의 " + str(w)}</span></div>'
            f'<div style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--sub);margin:10px 0 5px">'
            f'<span>Pod 20대</span><span>위험 {h} · 주의 {w}</span></div><div class="tick" style="height:16px">{t}</div></div>')


hot_pods = {p for p, _ in HOT}
warm_pods = {p for p, _ in WARM} - hot_pods
vlist = (vault_item("sac2", "1xxx", hot_pods, warm_pods, 4, 14, True)
         + vault_item("phx1", "1yyy", {5}, {1, 9, 12, 17}, 1, 9)
         + vault_item("iad1", "1zzz", {0}, {4, 13}, 1, 6)
         + vault_item("sac0", "1aaa", set(), {2, 7, 15}, 0, 7))


def pod_tile(p):
    cells = "".join(f'<div class="c{" r" if (p, s) in HOT else " a" if (p, s) in WARM else ""}" style="height:9px"></div>'
                    for s in range(60))
    n = sum(1 for pp, _ in HOT if pp == p)
    on = p == 3
    return (f'<div style="border:1px solid {"#C9B5FF" if on else "var(--line)"};border-radius:10px;padding:8px 9px;background:#fff;'
            f'{"box-shadow:0 0 0 3px var(--vio-s);" if on else ""}">'
            f'<div style="display:flex;align-items:center;font-size:12.5px;margin-bottom:6px">'
            f'<span style="width:4px;height:12px;border-radius:2px;background:#E5484D;margin-right:6px"></span><b>Pod {p:02d}</b>'
            f'{"<span class=" + chr(34) + "pill r" + chr(34) + " style=" + chr(34) + "margin-left:auto;height:18px;font-size:11px" + chr(34) + ">위험 " + str(n) + "</span>" if n else ""}</div>'
            f'<div style="display:grid;grid-template-columns:repeat(15,1fr);gap:2px">{cells}</div></div>')


pods = "".join(pod_tile(p) for p in range(20))
dash = f"""
<div class="hd"><div><h1>대시보드</h1><p>sac2 데이터센터, 2026년 6월 30일 기준</p></div>
 <div class="act"><span class="btn">{ic("cal", 15)}6월 30일{ic("chev", 14)}</span><span class="btn pri">{ic("list", 15, "#fff")}교체 목록 보기</span></div></div>
<div style="display:flex;gap:14px">{stats}</div>
<div style="display:flex;gap:14px;margin-top:14px">
 <div style="width:300px">
  <div style="display:flex;align-items:center;font-size:12.5px;color:var(--sub);margin:2px 2px 10px">{ic("chev", 14)}<span style="margin-left:4px">위험이 많은 Vault</span></div>
  {vlist}
 </div>
 <div class="card" style="flex:1">
  <div class="ct"><div class="chipi" style="background:var(--soft)">{ic("server", 16, "#52525B")}</div>
   <div>Vault 1xxx 배치<div style="font-size:12px;color:var(--sub);font-weight:400">Pod 20대 × 디스크 60개, Pod를 누르면 위에서 본 모습이 열립니다</div></div>
   <div style="margin-left:auto;display:flex;gap:12px;font-size:12px;color:var(--sub);font-weight:400">
    <span><i class="c r" style="display:inline-block;width:9px;height:9px"></i> 위험</span>
    <span><i class="c a" style="display:inline-block;width:9px;height:9px"></i> 주의</span>
    <span><i class="c" style="display:inline-block;width:9px;height:9px"></i> 정상</span></div></div>
  <div style="padding:14px 16px;display:grid;grid-template-columns:repeat(5,1fr);gap:9px">{pods}</div>
 </div>
</div>"""
dash_note = NOTE_BASE + " · 위치 = 원본 데이터의 datacenter·vault_id·pod_id·pod_slot_num 열"

# ================= 2. Pod 탑뷰 =================
SEL, P_HOT, P_WARM = 17, {17, 41}, {5, 33, 58}
rows = ""
for r in range(4):
    d = ""
    for i in range(15):
        s = r * 15 + i
        if s == SEL:
            st = "background:#EF4444;color:#fff;box-shadow:0 0 0 3px #fff,0 0 0 5px #EF4444,0 6px 18px rgba(239,68,68,.45)"
            led = "#fff"
        else:
            st = "background:linear-gradient(180deg,#52525B,#3F3F46);color:#D4D4D8"
            led = "#F87171" if s in P_HOT else "#FBBF24" if s in P_WARM else "#4ADE80"
        d += (f'<div style="width:104px;height:24px;border-radius:5px;{st};display:flex;align-items:center;padding:0 8px;font-size:12px">'
              f'<span style="width:7px;height:7px;border-radius:50%;background:{led}"></span>'
              f'<span style="margin-left:auto;font-variant-numeric:tabular-nums">{s}</span></div>')
    rows += f'<div style="display:flex;flex-direction:column;gap:5px"><div style="font-size:12px;color:var(--sub);text-align:center">{r + 1}번째 줄</div>{d}</div>'
chassis = f"""
<div style="display:flex;border-radius:14px;overflow:hidden;border:1px solid #D4D4DC;background:#EEEEF2">
 <div style="width:34px;background:linear-gradient(180deg,#E5484D,#C9353A);display:flex;align-items:center;justify-content:center">
  <span style="writing-mode:vertical-rl;color:#fff;font-weight:700;letter-spacing:5px;font-size:13px">앞면</span></div>
 <div style="flex:1;display:flex;gap:20px;padding:14px 18px">{rows}
  <div style="flex:1;border:1.5px dashed #C4C4CE;border-radius:10px;display:flex;align-items:center;justify-content:center;
   color:var(--mute);font-size:13px;text-align:center;line-height:1.6">서버 부품<br>(메인보드, 전원 등)</div></div>
 <div style="width:28px;display:flex;align-items:center;justify-content:center;border-left:1px solid #D4D4DC">
  <span style="writing-mode:vertical-rl;color:var(--mute);font-size:12px">뒷면</span></div>
</div>"""
topview = f"""
<div class="hd"><div><p style="margin:0 0 4px">대시보드 / Vault 1xxx</p><h1>Pod 03 위에서 본 모습</h1></div>
 <div class="act"><span class="pill r">위험 2</span><span class="pill a">주의 3</span><span class="pill">정상 55</span></div></div>
<div style="display:flex;gap:16px">
 <div class="card" style="flex:1;padding:16px">{chassis}</div>
 <div style="width:330px;display:flex;flex-direction:column;gap:12px">
  <div class="card" style="padding:16px">
   <div style="font-size:12.5px;color:var(--sub);margin-bottom:8px">선택한 디스크</div>{loc("sac2", "1xxx", "03", "17")}
   <div style="display:flex;align-items:flex-end;margin-top:16px"><div><div style="font-size:12.5px;color:var(--sub)">30일 고장 위험</div>
    <span class="big" style="color:#DC2626">0.93</span></div><span class="pill r" style="margin:0 0 8px auto">위험</span></div>
   {ticks(28, 30, "#EF4444", 18)}
   <div style="display:flex;justify-content:space-between;font-size:13.5px;margin-top:14px"><span style="color:var(--sub)">예측 잔여수명</span><b>4일</b></div>
   <div style="display:flex;justify-content:space-between;font-size:13.5px;margin-top:8px"><span style="color:var(--sub)">가장 큰 원인</span><b>197 대기 섹터 급증</b></div>
  </div>
  <div class="card" style="padding:14px 16px;background:var(--vio-s);border-color:#E4D8FF">
   <div style="display:flex;align-items:center;gap:8px;font-weight:600;color:#5B21B6">{ic("pin", 15, "#7C3AED")}현장에서 찾는 법</div>
   <div style="margin-top:6px;font-size:14px;line-height:1.6">앞면에서 2번째 줄, 위에서 3번째 칸</div>
   <div style="font-size:11.5px;color:#7C6BA8;margin-top:4px">슬롯 번호와 줄·칸 대응은 도식, 데이터 확인 전</div>
  </div>
  <div style="display:flex;gap:8px"><span class="btn pri" style="flex:1;justify-content:center">{ic("check", 15, "#fff")}교체 후보에 추가</span><span class="btn">디스크 상세</span></div>
 </div>
</div>"""
top_note = "목업 화면 · 디스크 60개를 15개씩 줄지어 앞쪽에 둔 구조는 Backblaze Storage Pod 6.0 설명 기준 · 부품 위치와 슬롯 대응은 도식"


# ================= 3. 디스크 상세 =================
def area(vals, color, title, latest, unit="개"):
    w, h = 300, 92
    mx = max(max(vals), 1)
    pts = [(i * w / (len(vals) - 1), h - v / mx * (h - 8) - 4) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    fill = f"0,{h} " + line + f" {w},{h}"
    gid = "g" + title[:3].replace(" ", "")
    return (f'<div class="card" style="padding:12px 14px"><div style="display:flex;align-items:baseline">'
            f'<span style="font-size:13px;color:var(--sub)">{title}</span>'
            f'<b style="margin-left:auto;font-size:18px;color:{color}">{latest}<span style="font-size:12px;color:var(--sub);font-weight:500"> {unit}</span></b></div>'
            f'<svg width="{w}" height="{h}" style="margin-top:6px"><defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{color}" stop-opacity=".22"/><stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
            f'<polygon points="{fill}" fill="url(#{gid})"/><polyline points="{line}" fill="none" stroke="{color}" stroke-width="2"/></svg></div>')


n = 30
s5 = [8 + (i // 6) * 2 + (14 if i > 24 else 0) for i in range(n)]
s187 = [0 if i < 18 else (i - 18) * 2 for i in range(n)]
s197 = [0 if i < 22 else (i - 22) * 6 for i in range(n)]
charts = (area(s197, "#EF4444", "197 대기 섹터", s197[-1]) + area(s187, "#EF4444", "187 복구 불가 오류", s187[-1], "건")
          + area(s5, "#F59E0B", "5 재할당 섹터", s5[-1]) + area([0] * n, "#A1A1AA", "188 명령 시간 초과", 0, "건"))
shap = "".join(
    f'<div style="display:grid;grid-template-columns:130px 1fr 74px;align-items:center;gap:10px;margin:11px 0">'
    f'<span style="font-size:13px">{nm}</span><div style="height:10px;background:var(--soft);border-radius:5px">'
    f'<div style="height:10px;width:{w}%;background:{c};border-radius:5px"></div></div>'
    f'<span style="font-size:12px;color:var(--sub);text-align:right">{d}</span></div>'
    for nm, w, c, d in [("197 대기 섹터", 92, "#EF4444", "위험 올림"), ("187 복구 불가 오류", 70, "#EF4444", "위험 올림"),
                        ("5 재할당 섹터", 48, "#F87171", "위험 올림"), ("9 가동 시간", 24, "#FCA5A5", "위험 올림"),
                        ("194 온도", 16, "#86EFAC", "위험 낮춤")])
detail = f"""
<div class="hd"><div><h1>디스크 상세</h1><p>시리얼 ZJV0****1 · ST12000NM0008</p></div>
 <div class="act"><span class="btn">{ic("down", 15)}기록 내려받기</span><span class="btn pri">{ic("check", 15, "#fff")}교체 후보에 추가</span></div></div>
<div style="display:flex;gap:14px">
 <div class="card" style="flex:1;padding:16px 18px;display:flex;align-items:center;gap:30px">
  <div><div style="font-size:12.5px;color:var(--sub);margin-bottom:8px">위치</div>{loc("sac2", "1xxx", "03", "17")}</div>
  <div style="font-size:13.5px;line-height:1.9;border-left:1px solid var(--line);padding-left:24px">
   <span style="color:var(--sub)">가동 시간</span> <b>3.2년</b><br><span style="color:var(--sub)">최근 온도</span> <b>31℃</b></div>
 </div>
 <div class="card" style="width:380px;padding:16px 18px">
  <div style="display:flex;align-items:center"><span style="font-size:12.5px;color:var(--sub)">30일 안에 고장 날 위험</span><span class="pill r" style="margin-left:auto">위험</span></div>
  <div style="display:flex;align-items:baseline;gap:16px"><span class="big" style="color:#DC2626">0.93</span>
   <span style="font-size:13.5px;color:var(--sub)">예측 잔여수명 <b style="color:var(--ink)">4일</b></span></div>
  {ticks(28, 30, "#EF4444", 14)}
 </div>
</div>
<div style="display:flex;gap:14px;margin-top:14px">
 <div style="flex:1">
  <div style="display:flex;align-items:center;margin-bottom:10px"><b>SMART 기록</b>
   <div style="margin-left:auto;display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:12.5px">
    <span style="padding:4px 12px;background:var(--ink);color:#fff">30일</span><span style="padding:4px 12px">60일</span><span style="padding:4px 12px">90일</span></div></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">{charts}</div>
 </div>
 <div class="card" style="width:380px">
  <div class="ct"><div class="chipi" style="background:var(--red-s)">{ic("alert", 16, "#DC2626")}</div>
   <div>왜 위험한가<div style="font-size:12px;color:var(--sub);font-weight:400">예측에 영향을 준 항목 (SHAP 상위 5개)</div></div></div>
  <div style="padding:6px 16px 12px">{shap}</div>
 </div>
</div>"""

# ================= 4. 교체 목록 =================
items = [("ZJV0****1", ("sac2", "1xxx", "03", "17"), 0.93, 4, "197 대기 섹터 급증", "r"),
         ("ZJV0****2", ("sac2", "1xxx", "03", "41"), 0.91, 6, "187 오류 30일간 증가", "r"),
         ("ZJV0****3", ("sac2", "1xxx", "11", "08"), 0.88, 9, "5 재할당 섹터 증가", "r"),
         ("ZJV0****4", ("sac2", "1xxx", "16", "52"), 0.87, 12, "197 대기 섹터 증가", "r"),
         ("ZJV0****5", ("phx1", "1yyy", "05", "22"), 0.71, 21, "187 오류 증가", "a"),
         ("ZJV0****6", ("iad1", "1zzz", "00", "30"), 0.66, 27, "5 재할당 섹터 증가", "a")]
trs = ""
for i, (sn, L, sc, rul, why, g) in enumerate(items):
    col = "#EF4444" if g == "r" else "#F59E0B"
    status = '<span class="pill v">보류 사유 입력 중</span>' if i == 1 else '<span class="pill">승인 대기</span>'
    trs += (f'<tr style="{"background:#FBF9FF" if i == 1 else ""}"><td style="width:28px"><span style="display:inline-block;width:15px;height:15px;'
            f'border:1.5px solid #D4D4D8;border-radius:4px"></span></td><td>{loc(*L)}</td><td style="color:var(--sub)">{sn}</td>'
            f'<td><div style="display:flex;align-items:center;gap:8px"><b style="color:{col};width:34px">{sc:.2f}</b>'
            f'<div style="width:70px">{ticks(round(sc * 10), 10, col, 12)}</div></div></td>'
            f'<td><b>{rul}일</b></td><td>{why}</td><td>{status}</td>'
            f'<td style="text-align:right"><span class="btn sm pri">승인</span> <span class="btn sm">보류</span></td></tr>')
replace = f"""
<div class="hd"><div><h1>교체 목록</h1><p>위험 점수가 높은 순서, 승인하면 승인자와 시각이 기록됩니다</p></div>
 <div class="act"><span class="btn">{ic("clock", 15)}처리 이력</span><span class="btn">{ic("down", 15)}CSV로 내려받기</span></div></div>
<div style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
 <span class="btn sm">등급: 전체{ic("chev", 13)}</span><span class="btn sm">위치: 전체{ic("chev", 13)}</span>
 <div style="margin-left:auto;display:flex;align-items:center;gap:12px;font-size:13px"><span style="color:var(--sub)">교체 후보 기준</span>
  <div style="width:200px;height:6px;background:#EDEDF2;border-radius:3px;position:relative"><div style="width:14px;height:6px;background:var(--ink);border-radius:3px"></div>
   <div style="position:absolute;left:8px;top:-5px;width:16px;height:16px;border-radius:50%;background:#fff;border:2px solid var(--ink)"></div></div>
  <span class="pill v">위험 상위 1%</span></div>
</div>
<div class="card" style="overflow:hidden"><table>
 <tr><th></th><th>위치</th><th>시리얼</th><th>위험 점수</th><th>잔여수명</th><th>주요 원인</th><th>상태</th><th></th></tr>{trs}</table></div>
<div class="card" style="position:absolute;right:26px;bottom:22px;width:380px;padding:18px;box-shadow:0 24px 50px -16px rgba(40,20,90,.35)">
 <div style="display:flex;align-items:center;gap:8px"><b>보류 사유를 적어 주세요</b><span class="pill r" style="margin-left:auto">필수</span></div>
 <div style="margin:10px 0">{loc("sac2", "1xxx", "03", "41")}</div>
 <div style="border:1px solid #D9CCFF;box-shadow:0 0 0 3px var(--vio-s);border-radius:9px;height:62px;padding:9px 11px;font-size:13px;color:var(--mute)">
  예: 다음 정기 점검 때 같은 Pod의 슬롯 17과 함께 교체</div>
 <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px"><span class="btn sm">취소</span><span class="btn sm pri">보류 저장</span></div>
</div>"""

# ================= 5. 모델 비교 =================
cols = "".join(
    f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:8px">'
    f'<span class="pill">--개 · --원</span>'
    f'<div style="width:96px;height:300px;border-radius:10px 10px 4px 4px;border:1.5px dashed {c};'
    f'background:repeating-linear-gradient(135deg,{bg} 0 8px,transparent 8px 16px)"></div>'
    f'<b style="font-size:13.5px">{nm}</b></div>'
    for nm, c, bg in [("SMART 규칙", "#A1A1AA", "#F4F4F5"), ("머신러닝 모델", "#7C3AED", "#F3EEFF"), ("딥러닝 모델", "#2563EB", "#EEF3FF")])
model = f"""
<div class="hd"><div><h1>모델 비교</h1><p>같은 시험 기간, 같은 수의 고장을 잡는다고 할 때</p></div>
 <div class="act"><span class="pill">결과 나오면 채움</span></div></div>
<div style="display:flex;gap:14px">
 <div style="width:470px;display:flex;flex-direction:column;gap:14px">
  <div class="card" style="overflow:hidden"><table>
   <tr><th>방식</th><th>경보 정밀도</th><th>AP</th><th>잡은 고장</th></tr>
   <tr><td><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#A1A1AA;margin-right:8px"></span>SMART 규칙 (기준)</td><td>--%</td><td>--</td><td>-- / --</td></tr>
   <tr><td><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#7C3AED;margin-right:8px"></span><b>머신러닝 모델</b></td><td>--%</td><td>--</td><td>-- / --</td></tr>
   <tr style="border:none"><td style="border:none"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:#2563EB;margin-right:8px"></span><b>딥러닝 모델</b></td><td style="border:none">--%</td><td style="border:none">--</td><td style="border:none">-- / --</td></tr>
  </table></div>
  <div class="card" style="padding:16px">
   <b>디스크 1개 가격</b><div style="font-size:12.5px;color:var(--sub);margin:3px 0 10px">바꾸면 절감액을 다시 계산합니다</div>
   <div style="display:flex;gap:8px"><div style="flex:1;height:34px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;padding:0 12px">364,550<span style="margin-left:auto;color:var(--sub)">원</span></div>
    <span class="btn pri">다시 계산</span></div>
  </div>
 </div>
 <div class="card" style="flex:1">
  <div class="ct"><div class="chipi" style="background:var(--vio-s)">{ic("chart", 16, "#7C3AED")}</div>
   <div>1년 동안 바꿔야 하는 디스크 수<div style="font-size:12px;color:var(--sub);font-weight:400">실험 결과가 나오면 막대 높이와 절감액을 채웁니다</div></div></div>
  <div style="display:flex;height:410px;align-items:flex-end;padding:0 20px 18px">{cols}</div>
 </div>
</div>"""
model_note = "목업 화면 · 성능 수치는 모델 확정 후 채움 · 모델 종류도 확정 전이라 머신러닝·딥러닝 모델로 표시"

SCREENS = [("1_dashboard", "대시보드", dash, dash_note), ("2_pod_topview", "대시보드", topview, top_note),
           ("3_disk_detail", "디스크 상세", detail, NOTE_BASE), ("4_replace_list", "교체 목록", replace, NOTE_BASE),
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
