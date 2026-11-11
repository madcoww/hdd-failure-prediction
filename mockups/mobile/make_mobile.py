"""모바일 화면 목업 v1 (웹 목업 v4와 같은 색·글꼴).
모바일은 알림 확인 · 현장 확인 · 교체 승인용. 평면도·Pod 탑뷰·모델 비교는 PC 전용.
수치·Vault 번호·시리얼은 가상."""
import os
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
W, H = 390, 844

FONT = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/'
        'pretendardvariable-dynamic-subset.min.css">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&display=swap">')

CSS = f"""
:root{{--bg:#0C1322;--pn:#121B2D;--pn2:#172238;--ln:#22304A;--ink:#E6ECF6;--sub:#8E9BB4;--mute:#5E6C87;
--blue:#3D8BFF;--cyan:#4CC9F0;--red:#FF4D5E;--amb:#FFB020;--grn:#2BD47D}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;background:var(--bg);color:var(--ink);font-family:'Pretendard Variable',Pretendard,'Malgun Gothic',sans-serif;
font-size:14px;overflow:hidden;display:flex;flex-direction:column;position:relative}}
.num{{font-family:Rajdhani,'Pretendard Variable',sans-serif;font-variant-numeric:tabular-nums}}
.sb{{height:44px;display:flex;align-items:center;justify-content:space-between;padding:0 22px;font-size:14px;font-weight:600;flex:none}}
.hd{{height:52px;display:flex;align-items:center;gap:10px;padding:0 16px;border-bottom:1px solid var(--ln);flex:none}}
.hd .t{{font-size:17px;font-weight:700}}
.hd .r{{margin-left:auto;display:flex;align-items:center;gap:14px;color:var(--sub)}}
.logo{{width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,#3D8BFF,#4CC9F0);display:flex;align-items:center;justify-content:center}}
.bell{{position:relative}}.bell i{{position:absolute;top:-4px;right:-6px;min-width:16px;height:16px;border-radius:8px;background:var(--red);
color:#fff;font-size:10px;font-style:normal;font-weight:700;display:flex;align-items:center;justify-content:center;padding:0 4px}}
main{{flex:1;overflow:hidden;padding:14px 16px;display:flex;flex-direction:column;gap:12px}}
.tabbar{{height:76px;border-top:1px solid var(--ln);background:#0F182A;display:flex;padding:8px 6px 22px;flex:none}}
.tabbar div{{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;font-size:11px;color:var(--mute)}}
.tabbar div.on{{color:var(--blue);font-weight:600}}
.card{{background:var(--pn);border:1px solid var(--ln);border-radius:12px}}
.pill{{display:inline-flex;align-items:center;height:22px;padding:0 8px;border-radius:5px;font-size:12px;font-weight:600;
background:rgba(142,155,180,.12);color:#B4C0D6}}
.pill.r{{background:rgba(255,77,94,.15);color:#FF7D8A}}.pill.a{{background:rgba(255,176,32,.15);color:#FFC452}}
.pill.b{{background:rgba(61,139,255,.16);color:#86B6FF}}.pill.g{{background:rgba(43,212,125,.14);color:#5BE39A}}
.btn{{display:flex;align-items:center;justify-content:center;gap:6px;height:44px;border-radius:10px;font-weight:600;font-size:14.5px;
border:1px solid var(--ln);background:var(--pn2);color:var(--ink)}}
.btn.pri{{background:var(--blue);border-color:var(--blue);color:#fff}}
.btn.sm{{height:36px;font-size:13.5px;border-radius:8px}}
.loc{{display:flex;flex-wrap:wrap;align-items:center;gap:5px;font-size:12px}}
.loc span{{padding:2px 7px;border-radius:5px;background:var(--pn2);border:1px solid var(--ln);color:#C9D3E5}}
.loc span.k{{background:rgba(255,77,94,.15);border-color:rgba(255,77,94,.35);color:#FF8B96;font-weight:600}}
.seg{{display:flex;gap:2px}}.seg i{{flex:1;border-radius:1.5px;background:#23314B}}
.sec{{font-size:13px;color:var(--sub);font-weight:600;margin-top:2px}}
.row{{display:flex;justify-content:space-between;align-items:center}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:0}}
"""

ICON = {
    "disk": '<path d="M22 12H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><path d="M6 16h.01M10 16h.01"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "back": '<path d="m15 18-6-6 6-6"/>',
    "chev": '<path d="m9 18 6-6-6-6"/>',
    "mon": '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
}


def ic(n, s=18, c="currentColor", w=1.9):
    return (f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="{w}" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICON[n]}</svg>')


def seg(n_on, total, color, h=8):
    return (f'<div class="seg" style="height:{h}px">' +
            "".join(f'<i style="{"background:" + color if k < n_on else ""}"></i>' for k in range(total)) + "</div>")


def loc(dc, v, p, s):
    return (f'<div class="loc">{ic("pin", 13, "#FF6B78")}<span>{dc}</span><span>Vault {v}</span>'
            f'<span>Pod {p}</span><span class="k">슬롯 {s}</span></div>')


STATUS = ('<div class="sb"><span class="num" style="font-size:16px">9:41</span>'
          '<span style="display:flex;gap:6px;align-items:center"><svg width="18" height="11"><rect x="0" y="7" width="3" height="4" fill="#E6ECF6"/>'
          '<rect x="5" y="5" width="3" height="6" fill="#E6ECF6"/><rect x="10" y="2" width="3" height="9" fill="#E6ECF6"/>'
          '<rect x="15" y="0" width="3" height="11" fill="#E6ECF6"/></svg>'
          '<svg width="25" height="12"><rect x="0.5" y="0.5" width="21" height="11" rx="3" fill="none" stroke="#8E9BB4"/>'
          '<rect x="2.5" y="2.5" width="15" height="7" rx="1.5" fill="#E6ECF6"/><rect x="23" y="4" width="2" height="4" rx="1" fill="#8E9BB4"/></svg></span></div>')

TABS = [("home", "홈"), ("search", "디스크"), ("list", "교체 목록"), ("bell", "알림 설정")]


def tabbar(active):
    return '<div class="tabbar">' + "".join(
        f'<div class="{"on" if t == active else ""}">{ic(i, 22)}<span>{t}</span></div>' for i, t in TABS) + "</div>"


def header_main(title):
    return (f'<div class="hd"><div class="logo">{ic("disk", 15, "#fff")}</div><span class="t">{title}</span>'
            f'<div class="r"><span class="bell">{ic("bell", 21)}<i>2</i></span></div></div>')


def header_back(title, right=""):
    return f'<div class="hd">{ic("back", 22)}<span class="t">{title}</span><div class="r">{right}</div></div>'


def doc(body):
    return f'<html><head><meta charset="utf-8">{FONT}<style>{CSS}</style></head><body>{body}</body></html>'


# ---------- m1. 푸시 알림 (잠금 화면)
push = doc(f"""
<div style="position:absolute;inset:0;background:radial-gradient(120% 70% at 50% 0%,#24375E 0%,#0C1322 70%)"></div>
<div style="position:relative;display:flex;flex-direction:column;height:100%">
{STATUS}
<div style="text-align:center;margin-top:34px;color:#C9D6EA;font-size:16px">11월 10일 화요일</div>
<div class="num" style="text-align:center;font-size:88px;font-weight:600;line-height:1.05;letter-spacing:1px">7:05</div>
<div style="margin:40px 12px 0;display:flex;flex-direction:column;gap:10px">
 <div style="background:rgba(30,44,72,.82);border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:13px 14px;backdrop-filter:blur(8px)">
  <div class="row" style="margin-bottom:7px"><span style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:#C9D6EA">
   <span class="logo" style="width:22px;height:22px;border-radius:6px">{ic("disk", 13, "#fff")}</span>디스크 수명 관리</span>
   <span style="font-size:12px;color:#8E9BB4">지금</span></div>
  <div style="font-weight:700;font-size:15px;margin-bottom:3px">위험 디스크 2건 · 오늘 교체 검토</div>
  <div style="font-size:13.5px;color:#C9D6EA;line-height:1.45">sac2 · Vault 1xxx · Pod 03 · 슬롯 17<br>30일 위험 <b style="color:#FF7D8A">0.93</b> · 예측 잔여수명 <b>4일</b> 외 1건</div>
 </div>
 <div style="background:rgba(30,44,72,.6);border:1px solid rgba(255,255,255,.06);border-radius:18px;padding:12px 14px">
  <div class="row" style="margin-bottom:5px"><span style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:#C9D6EA">
   <span class="logo" style="width:22px;height:22px;border-radius:6px">{ic("disk", 13, "#fff")}</span>디스크 수명 관리</span>
   <span style="font-size:12px;color:#8E9BB4">어제</span></div>
  <div style="font-weight:600;font-size:14px;color:#C9D6EA">교체 승인 완료 · sac2 Pod 11 슬롯 08</div>
 </div>
</div>
<div style="margin-top:auto;text-align:center;color:#8E9BB4;font-size:12.5px;padding-bottom:16px">알림을 누르면 디스크 상세로 이동</div>
<div style="width:134px;height:5px;border-radius:3px;background:#E6ECF6;margin:0 auto 9px"></div>
</div>""")

# ---------- m2. 홈 (대시보드 요약)
def kpi(v, t, s, color, on, total=10):
    return (f'<div class="card" style="padding:12px 13px;display:flex;flex-direction:column;gap:6px">'
            f'<div class="row"><b style="font-size:13.5px">{t}</b></div>'
            f'<div class="num" style="font-size:34px;font-weight:700;line-height:1;color:{color}">{v}</div>'
            f'<div style="font-size:11.5px;color:var(--sub)">{s}</div>{seg(on, total, color, 6)}</div>')


def risk_item(pod, slot, serial, score, days, color="#FF4D5E", cls="r"):
    return (f'<div style="display:flex;align-items:center;gap:10px;padding:11px 13px;border-bottom:1px solid var(--ln)">'
            f'<div style="flex:1;display:flex;flex-direction:column;gap:5px"><div style="display:flex;gap:6px;align-items:center">'
            f'<b style="font-size:14px">Pod {pod}</b><span class="pill {cls}">슬롯 {slot}</span>'
            f'<span style="font-size:12px;color:var(--sub)">{serial}</span></div>'
            f'<div style="font-size:12px;color:var(--sub)">sac2 · Vault 1xxx · 잔여수명 <b style="color:var(--ink)">{days}일</b></div></div>'
            f'<b class="num" style="font-size:20px;color:{color}">{score}</b>{ic("chev", 16, "#5E6C87")}</div>')


home = doc(f"""{STATUS}{header_main("디스크 수명 관리")}
<main>
 <div class="row"><span style="font-size:12.5px;color:var(--sub)">기준일 <b class="num" style="font-size:17px;color:#fff;margin-left:4px">2026.06.30</b></span>
  <span class="pill b">매일 07:00 갱신</span></div>
 <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
  {kpi(4, "위험", "고장 위험 상위 1%", "#FF4D5E", 4)}{kpi(14, "주의", "상위 1~5%", "#FFB020", 7)}
  {kpi(4, "교체 후보", "승인 대기 4건", "#4CC9F0", 4)}{kpi("1,200", "관리 중", "ST12000NM0008", "#E6ECF6", 10)}
 </div>
 <div class="row" style="margin-top:2px"><span class="sec">위험 디스크</span><span style="font-size:12.5px;color:var(--blue)">교체 목록 보기</span></div>
 <div class="card" style="overflow:hidden">
  {risk_item("03", 17, "ZJV0****1", "0.93", 4)}{risk_item("03", 41, "ZJV0****2", "0.91", 6)}
  {risk_item("11", "08", "ZJV0****3", "0.88", 9)}{risk_item("16", 52, "ZJV0****4", "0.87", 12)}
 </div>
 <div style="display:flex;align-items:center;gap:8px;padding:10px 12px;border:1px dashed var(--ln);border-radius:10px;color:var(--sub);font-size:12px">
  {ic("mon", 16)}데이터센터 평면도 · Pod 탑뷰 · 모델 비교는 PC에서 볼 수 있습니다</div>
</main>{tabbar("홈")}""")

# ---------- m3. 디스크 상세
def spark(points, color, title, latest, unit):
    w, h = 150, 46
    mx = max(points) or 1
    pts = " ".join(f"{i * w / (len(points) - 1):.1f},{h - 4 - (p / mx) * (h - 10):.1f}" for i, p in enumerate(points))
    return (f'<div class="card" style="padding:10px 11px">'
            f'<div class="row"><span style="font-size:11.5px;color:var(--sub)">{title}</span>'
            f'<b class="num" style="font-size:18px;color:{color}">{latest}<small style="font-size:11px"> {unit}</small></b></div>'
            f'<svg width="100%" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/></svg></div>')


z30 = [0] * 18
detail = doc(f"""{STATUS}{header_back("디스크 상세", ic("search", 20))}
<main style="gap:11px">
 <div class="card" style="padding:14px">
  <div class="row"><div><b style="font-size:18px">ZJV0****1</b><div style="font-size:12px;color:var(--sub);margin-top:2px">ST12000NM0008 · 가동 3.2년 · 31°C</div></div>
   <span class="pill r">위험</span></div>
  <div style="display:flex;align-items:flex-end;gap:14px;margin:12px 0 8px">
   <div><div style="font-size:11.5px;color:var(--sub)">30일 고장 위험</div><b class="num" style="font-size:44px;line-height:1;color:var(--red)">0.93</b></div>
   <div style="padding-bottom:4px"><div style="font-size:11.5px;color:var(--sub)">예측 잔여수명</div><b class="num" style="font-size:26px">4<small style="font-size:14px">일</small></b></div>
  </div>{seg(19, 20, "#FF4D5E", 7)}
  <div style="margin-top:12px">{loc("sac2", "1xxx", "03", 17)}</div>
 </div>
 <div class="card" style="padding:12px 14px;border-color:rgba(76,201,240,.35);background:rgba(76,201,240,.06)">
  <div style="display:flex;gap:7px;align-items:center;color:var(--cyan);font-weight:700;font-size:13.5px">{ic("pin", 15, "#4CC9F0")}현장에서 찾는 법</div>
  <div style="font-size:13px;margin-top:6px;line-height:1.5">랙 B-04 위에서 4번째 Pod를 꺼내<br>앞면 기준 2번째 줄, 위에서 3번째 칸</div>
 </div>
 <div class="row"><span class="sec">SMART 기록 · 가장 큰 원인 197 급증</span>
  <span style="display:flex;border:1px solid var(--ln);border-radius:7px;overflow:hidden;font-size:11.5px">
   <span style="padding:3px 8px;background:var(--blue);color:#fff">30일</span><span style="padding:3px 8px;color:var(--sub)">60일</span><span style="padding:3px 8px;color:var(--sub)">90일</span></span></div>
 <div style="display:grid;grid-template-columns:1fr 1fr;gap:9px">
  {spark(z30 + [3, 8, 14, 22, 28, 34, 38, 40, 41, 42, 42, 42], "#FF4D5E", "197 대기 섹터", 42, "개")}
  {spark(z30 + [0, 0, 2, 5, 8, 11, 14, 16, 18, 20, 21, 22], "#FF4D5E", "187 복구 불가", 22, "건")}
  {spark([4] * 10 + [6] * 8 + [8] * 6 + [9, 10, 30, 30, 30, 30], "#FFB020", "5 재할당 섹터", 30, "개")}
  {spark([0] * 30, "#5E6C87", "188 명령 시간 초과", 0, "건")}
 </div>
</main>
<div style="display:flex;gap:9px;padding:10px 16px 26px;border-top:1px solid var(--ln);background:#0F182A">
 <div class="btn" style="flex:1">기록 내려받기</div><div class="btn pri" style="flex:1.6">{ic("check", 17, "#fff")}교체 후보에 추가</div></div>""")

# ---------- m4. 교체 목록
def rcard(dc, v, pod, slot, serial, score, on, days, cause, status, color="#FF4D5E", hl=False):
    st = f'<span class="pill {"b" if hl else ""}">{status}</span>'
    return (f'<div class="card" style="padding:12px 13px;display:flex;flex-direction:column;gap:9px{";border-color:rgba(61,139,255,.5)" if hl else ""}">'
            f'<div class="row">{loc(dc, v, pod, slot)}</div>'
            f'<div style="display:flex;align-items:center;gap:10px"><b class="num" style="font-size:22px;color:{color};width:46px">{score}</b>'
            f'<div style="flex:1">{seg(on, 10, color, 7)}</div><span style="font-size:13px">잔여 <b>{days}일</b></span></div>'
            f'<div class="row"><span style="font-size:12.5px;color:var(--sub)">{serial} · {cause}</span>{st}</div>'
            f'<div style="display:flex;gap:8px"><div class="btn sm" style="flex:1">보류</div><div class="btn sm pri" style="flex:1">승인</div></div></div>')


rlist_body = f"""
 <div style="display:flex;gap:7px;overflow:hidden">
  <span class="pill" style="height:30px;padding:0 11px;border:1px solid var(--ln)">등급: 전체 ▾</span>
  <span class="pill" style="height:30px;padding:0 11px;border:1px solid var(--ln)">데이터센터: 전체 ▾</span>
  <span class="pill b" style="height:30px;padding:0 11px">위험 상위 1%</span></div>
 <div class="row"><span class="sec">승인 대기 4건 · 위험 점수 높은 순</span><span style="font-size:12.5px;color:var(--blue)">처리 이력</span></div>
 {rcard("sac2", "1xxx", "03", 17, "ZJV0****1", "0.93", 9, 4, "197 대기 섹터 급증", "승인 대기")}
 {rcard("sac2", "1xxx", "03", 41, "ZJV0****2", "0.91", 9, 6, "187 오류 30일간 증가", "보류 사유 입력 중", hl=True)}
 {rcard("sac2", "1xxx", "11", "08", "ZJV0****3", "0.88", 9, 9, "5 재할당 섹터 증가", "승인 대기")}
"""
rlist = doc(f"""{STATUS}{header_main("교체 목록")}<main style="gap:10px">{rlist_body}</main>{tabbar("교체 목록")}""")

# ---------- m5. 보류 바텀시트
sheet = doc(f"""{STATUS}{header_main("교체 목록")}<main style="gap:10px">{rlist_body}</main>{tabbar("교체 목록")}
<div style="position:absolute;inset:0;background:rgba(5,9,18,.62)"></div>
<div style="position:absolute;left:0;right:0;bottom:0;background:#141F34;border-top:1px solid var(--ln);border-radius:20px 20px 0 0;padding:10px 18px 30px;display:flex;flex-direction:column;gap:13px">
 <div style="width:40px;height:4px;border-radius:2px;background:#3A4D6E;margin:0 auto 4px"></div>
 <div class="row"><b style="font-size:17px">보류 사유를 적어 주세요</b><span class="pill r">필수</span></div>
 {loc("sac2", "1xxx", "03", 41)}
 <div style="height:110px;border:1.5px solid var(--blue);border-radius:10px;padding:12px;color:var(--mute);font-size:13.5px;line-height:1.5">
  예: 다음 정기 점검 때 같은 Pod의 슬롯 17과 함께 교체</div>
 <div style="display:flex;gap:7px;flex-wrap:wrap">
  <span class="pill" style="height:28px;padding:0 10px">정기 점검 때 교체</span><span class="pill" style="height:28px;padding:0 10px">예비 디스크 없음</span>
  <span class="pill" style="height:28px;padding:0 10px">추가 관찰</span></div>
 <div style="display:flex;gap:9px;margin-top:4px"><div class="btn" style="flex:1">취소</div><div class="btn pri" style="flex:1.6">보류 저장</div></div>
</div>""")

# ---------- m6. 알림 설정
def toggle(on):
    bg = "var(--blue)" if on else "#2A3956"
    pos = "right:3px" if on else "left:3px"
    return (f'<span style="width:48px;height:28px;border-radius:14px;background:{bg};position:relative;flex:none">'
            f'<span style="position:absolute;top:3px;{pos};width:22px;height:22px;border-radius:50%;background:#fff"></span></span>')


def radio(t, on):
    dot = (f'<span style="width:20px;height:20px;border-radius:50%;border:2px solid {"var(--blue)" if on else "#3A4D6E"};'
           f'display:flex;align-items:center;justify-content:center">'
           + ('<span style="width:10px;height:10px;border-radius:50%;background:var(--blue)"></span>' if on else "") + "</span>")
    return f'<div style="display:flex;align-items:center;gap:10px;padding:12px 14px;border-top:1px solid var(--ln)">{dot}<span>{t}</span></div>'


alarm = doc(f"""{STATUS}{header_main("알림 설정")}
<main>
 <div class="card"><div class="row" style="padding:14px">
  <div><b style="font-size:15px">이 기기로 알림 받기</b><div style="font-size:12px;color:var(--sub);margin-top:3px">새 위험 디스크가 생기면 바로 알립니다</div></div>{toggle(True)}</div></div>
 <span class="sec">받을 등급</span>
 <div class="card" style="overflow:hidden">{radio("위험만 (상위 1%)", True).replace("border-top:1px solid var(--ln);", "")}{radio("위험 + 주의 (상위 5%)", False)}</div>
 <span class="sec">이메일 요약 (하루 1번)</span>
 <div class="card" style="padding:12px 14px;display:flex;flex-direction:column;gap:10px">
  <div class="row"><span>매일 07:30 요약 메일</span>{toggle(True)}</div>
  <div style="height:42px;border:1px solid var(--ln);border-radius:9px;padding:0 12px;display:flex;align-items:center;color:#C9D3E5;background:var(--pn2)">ops-team@example.com</div></div>
 <div class="btn">테스트 알림 보내기</div>
 <div style="padding:11px 13px;border-radius:10px;background:rgba(255,176,32,.08);border:1px solid rgba(255,176,32,.3);font-size:12.5px;line-height:1.5;color:#E8D3A6">
  <b style="color:#FFC452">아이폰은 홈 화면에 추가해야 알림을 받습니다</b><br>Safari 공유 버튼 → 홈 화면에 추가 → 추가한 아이콘으로 열기</div>
</main>{tabbar("알림 설정")}""")

SCREENS = [("m1_push", push), ("m2_home", home), ("m3_disk_detail", detail),
           ("m4_replace_list", rlist), ("m5_hold_sheet", sheet), ("m6_alarm_settings", alarm)]

for name, html_text in SCREENS:
    html = os.path.join(BASE, name + ".html")
    with open(html, "w", encoding="utf-8") as f:
        f.write(html_text)
    png = os.path.join(BASE, name + ".png")
    if os.path.exists(png):
        os.remove(png)
    for _ in range(3):
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=10000",
                        "--force-device-scale-factor=2", f"--screenshot={png}", f"--window-size={W},{H}",
                        "file:///" + html.replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            if os.path.exists(png):
                break
            time.sleep(0.5)
        if os.path.exists(png):
            break
    print("saved" if os.path.exists(png) else "FAILED", png)
