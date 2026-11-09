"""노션 4번용 화면 목업 5장 (frontend-design 방향).
- 배경: 서버 철판 회색, 정상 디스크는 조용한 회녹색, 빨강은 위험 디스크와 Pod 앞면에만.
- 디스크 위치는 자산 라벨(asset tag) 모양으로 크게.
수치·Vault 번호·시리얼은 가상. 화면 내용은 기능정의서 v1 기준."""
import os
import random
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
random.seed(11)

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700&display=block">')

CSS = """
:root{--steel:#E6E9ED;--panel:#F7F8FA;--ink:#1C2430;--sub:#5E6875;--rule:#CDD3DA;
--red:#C8202B;--amber:#E39A12;--ok:#9DB3A6;--ok-d:#7F978A;--blue:#2F5D8A}
*{box-sizing:border-box;margin:0;padding:0}
body{width:1200px;height:700px;background:var(--steel);color:var(--ink);
font-family:'IBM Plex Sans KR','Malgun Gothic',sans-serif;font-size:14px;display:flex;overflow:hidden}
.num{font-family:'Barlow Condensed','IBM Plex Sans KR',sans-serif;font-weight:600;letter-spacing:.2px}
/* 왼쪽 메뉴 */
.rail{width:168px;background:var(--panel);border-right:1px solid var(--rule);padding:22px 0;display:flex;flex-direction:column}
.brand{padding:0 20px 22px;font-weight:700;font-size:15px;line-height:1.35}
.brand small{display:block;font-weight:400;font-size:12px;color:var(--sub);margin-top:2px}
.menu a{display:block;padding:10px 20px;color:var(--sub);text-decoration:none;font-size:14px;border-left:4px solid transparent}
.menu a.on{color:var(--ink);font-weight:700;border-left-color:var(--red);background:#EEF0F3}
.menu a.later{color:#9AA3AE}
.rail .mock{margin-top:auto;padding:0 20px;font-size:11.5px;color:#8C95A1;line-height:1.5}
/* 본문 */
main{flex:1;padding:22px 26px;position:relative}
h1{font-size:22px;font-weight:700;letter-spacing:-.3px}
.head{display:flex;align-items:baseline;gap:14px;margin-bottom:16px}
.head .ctx{color:var(--sub);font-size:13.5px}
.chip{border:1px solid var(--rule);background:var(--panel);border-radius:4px;padding:5px 10px;font-size:13px}
.btn{display:inline-block;border-radius:4px;padding:8px 14px;font-weight:600;font-size:13.5px;border:1px solid var(--ink)}
.btn.go{background:var(--ink);color:#fff}
.btn.ghost{background:transparent}
.btn.sm{padding:4px 10px;font-size:12.5px}
.panel{background:var(--panel);border:1px solid var(--rule);border-radius:6px}
.foot{position:absolute;left:26px;bottom:12px;font-size:11.5px;color:#8C95A1}
/* 자산 라벨 */
.tag{display:inline-flex;align-items:stretch;border:2px solid var(--ink);border-radius:4px;background:#fff;overflow:hidden}
.tag span{padding:4px 10px;border-right:1px solid var(--ink);display:flex;flex-direction:column;justify-content:center}
.tag span:last-child{border-right:none;background:var(--red);color:#fff}
.tag i{font-style:normal;font-size:10.5px;color:var(--sub);line-height:1.2}
.tag span:last-child i{color:#ffd9dc}
.tag b{font-family:'Barlow Condensed',sans-serif;font-size:22px;font-weight:700;line-height:1.05}
.tag.small b{font-size:16px}.tag.small span{padding:2px 7px}
/* 디스크 칸 */
.d{border-radius:1.5px;background:var(--ok)}
.d.w{background:var(--amber)}.d.r{background:var(--red)}
"""

MENUS = [("대시보드", ""), ("디스크 상세", ""), ("교체 목록", ""), ("모델 비교", ""), ("알림 (검토 중)", "later")]


def page(active, body, foot):
    menu = "".join(f'<a class="{"on" if m == active else cls}">{m}</a>' for m, cls in MENUS)
    return (f'<html><head><meta charset="utf-8">{FONTS}<style>{CSS}</style></head><body>'
            f'<nav class="rail"><div class="brand">HDD 수명 예측<small>교체 지원</small></div>'
            f'<div class="menu">{menu}</div><div class="mock">목업 화면<br>수치는 가상</div></nav>'
            f'<main>{body}<div class="foot">{foot}</div></main></body></html>')


def tag(parts, small=False):
    cells = "".join(f"<span><i>{k}</i><b>{v}</b></span>" for k, v in parts)
    return f'<div class="tag{" small" if small else ""}">{cells}</div>'


LOC = [("데이터센터", "sac2"), ("Vault", "1xxx"), ("Pod", "03"), ("슬롯", "17")]
GRADE_NOTE = "위험 = 30일 고장 위험 상위 1%, 주의 = 상위 1~5% (팀 기준, 확정 전)"

# 가상 배치: Vault 1xxx (Pod 20대 × 60칸)
HOT = {(3, 17), (3, 41), (11, 8), (16, 52)}
WARM = set()
while len(WARM) < 14:
    k = (random.randrange(20), random.randrange(60))
    if k not in HOT:
        WARM.add(k)


def pod_mini(p, cell=11):
    cells = "".join(
        f'<div class="d{" r" if (p, s) in HOT else " w" if (p, s) in WARM else ""}" style="height:{cell}px"></div>'
        for s in range(60))
    n = sum(1 for (pp, _) in HOT if pp == p)
    sel = p == 3
    return (f'<div style="display:flex;border:1px solid {"var(--ink)" if sel else "var(--rule)"};border-radius:3px;background:#fff;'
            f'{"box-shadow:0 0 0 2px var(--ink);" if sel else ""}">'
            f'<div style="width:6px;background:var(--red)"></div>'
            f'<div style="flex:1;padding:5px 6px 6px">'
            f'<div style="display:flex;font-size:12px;margin-bottom:4px"><b class="num" style="font-size:14px">Pod {p:02d}</b>'
            f'<span style="margin-left:auto;color:var(--red);font-weight:700">{"위험 " + str(n) if n else ""}</span></div>'
            f'<div style="display:grid;grid-template-columns:repeat(15,1fr);gap:2px">{cells}</div></div></div>')


# ---------- 1. 대시보드 ----------
total, hot_n, warm_n = 1200, 4, 14
ok_n = total - hot_n - warm_n
bar = (f'<div style="display:flex;height:14px;border-radius:3px;overflow:hidden;margin-top:8px">'
       f'<div style="width:{hot_n / total * 100 * 12:.1f}%;background:var(--red)"></div>'
       f'<div style="width:{warm_n / total * 100 * 6:.1f}%;background:var(--amber)"></div>'
       f'<div style="flex:1;background:var(--ok)"></div></div>')
triage = f"""
<div class="panel" style="padding:14px 18px;display:flex;gap:34px;align-items:center">
 <div><div class="num" style="font-size:40px;line-height:1;color:var(--red)">{hot_n}</div><div style="font-size:12.5px;color:var(--sub)">위험 디스크</div></div>
 <div><div class="num" style="font-size:40px;line-height:1;color:var(--amber)">{warm_n}</div><div style="font-size:12.5px;color:var(--sub)">주의 디스크</div></div>
 <div style="flex:1"><div style="font-size:13px;color:var(--sub)">이 Vault의 디스크 {total:,}개 중 {ok_n:,}개는 정상입니다. 위험 {hot_n}개가 이번 주 교체 후보입니다.</div>{bar}
  <div style="font-size:11px;color:#8C95A1;margin-top:4px">막대는 보기 쉽게 위험·주의 폭을 늘려 그림</div></div>
 <div class="btn go">교체 목록 열기</div>
</div>"""
vaults = "".join(
    f'<div style="display:flex;align-items:center;padding:9px 12px;border-top:1px solid var(--rule);'
    f'{"background:#fff;border-left:4px solid var(--red);padding-left:8px" if i == 0 else ""}">'
    f'<div><div style="font-size:13.5px;font-weight:{700 if i == 0 else 500}">{dc} / Vault {v}</div></div>'
    f'<div style="margin-left:auto;text-align:right;font-size:12.5px">'
    f'<b style="color:{"var(--red)" if h else "var(--sub)"}">{"위험 " + str(h) if h else "위험 0"}</b>'
    f'<span style="color:var(--sub)"> / 주의 {w}</span></div></div>'
    for i, (dc, v, h, w) in enumerate([("sac2", "1xxx", 4, 14), ("phx1", "1yyy", 1, 9), ("iad1", "1zzz", 1, 6),
                                       ("sac0", "1aaa", 0, 7), ("ams5", "1bbb", 0, 5), ("sac2", "1ccc", 0, 3),
                                       ("phx1", "1ddd", 0, 2)]))
pods = "".join(pod_mini(p) for p in range(20))
dash = f"""
<div class="head"><h1>대시보드</h1><span class="ctx">2026년 6월 30일 기준</span>
 <span class="chip" style="margin-left:auto">기준일 변경</span></div>
{triage}
<div style="display:flex;gap:16px;margin-top:14px">
 <div class="panel" style="width:236px;overflow:hidden">
  <div style="padding:11px 12px 9px;font-weight:700">위험이 많은 Vault</div>{vaults}</div>
 <div style="flex:1">
  <div style="display:flex;align-items:baseline;margin-bottom:8px"><b>sac2 / Vault 1xxx</b>
   <span style="color:var(--sub);font-size:12.5px;margin-left:10px">Pod 20대, Pod마다 디스크 60개. 왼쪽 빨간 띠가 Pod 앞면</span></div>
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:7px">{pods}</div>
 </div>
</div>"""
dash_foot = GRADE_NOTE + " / 위치는 원본 데이터의 datacenter, vault_id, pod_id, pod_slot_num 열"

# ---------- 2. Pod 탑뷰 ----------
SEL = 17
P3_HOT, P3_WARM = {17, 41}, {5, 33, 58}
rows = ""
for r in range(4):
    drv = ""
    for i in range(15):
        s = r * 15 + i
        if s == SEL:
            st = "background:var(--red);color:#fff;box-shadow:0 0 0 3px var(--ink)"
            led = "#fff"
        else:
            st = "background:#3B434E;color:#C9D0D8"
            led = "var(--red)" if s in P3_HOT else "var(--amber)" if s in P3_WARM else "#8FD1A6"
        drv += (f'<div style="position:relative;width:88px;height:21px;border-radius:2px;{st};display:flex;align-items:center;padding:0 7px">'
                f'<span style="width:7px;height:7px;border-radius:50%;background:{led}"></span>'
                f'<span class="num" style="margin-left:auto;font-size:13px">{s}</span></div>')
    rows += (f'<div style="display:flex;flex-direction:column;gap:4px">'
             f'<div style="font-size:12px;color:var(--sub);text-align:center;margin-bottom:2px">{r + 1}번째 줄</div>{drv}</div>')
chassis = f"""
<div style="display:flex;height:452px">
 <div style="width:30px;background:var(--red);border-radius:4px 0 0 4px;display:flex;align-items:center;justify-content:center">
  <span style="writing-mode:vertical-rl;color:#fff;font-weight:700;letter-spacing:4px;font-size:13px">앞면</span></div>
 <div style="flex:1;background:#D3D8DE;border:2px solid #A9B1BB;border-left:none;border-radius:0 4px 4px 0;display:flex;padding:12px 16px;gap:22px">
  {rows}
  <div style="flex:1;border:1.5px dashed #9AA3AE;border-radius:3px;display:flex;align-items:center;justify-content:center;
   color:var(--sub);font-size:13px;text-align:center;line-height:1.6">서버 부품<br>(메인보드, 전원 등)</div>
 </div>
 <div style="width:24px;display:flex;align-items:center;justify-content:center">
  <span style="writing-mode:vertical-rl;color:var(--sub);font-size:12px">뒷면</span></div>
</div>"""
topview = f"""
<div class="head"><h1>Pod 03을 위에서 본 모습</h1><span class="ctx">대시보드에서 Pod를 누르면 열립니다</span></div>
<div style="display:flex;gap:18px">
 <div style="flex:1">{chassis}</div>
 <div style="width:296px">
  {tag(LOC)}
  <div class="panel" style="margin-top:14px;padding:14px 16px">
   <div style="font-weight:700;margin-bottom:6px">현장에서 찾는 법</div>
   <div style="font-size:14px;line-height:1.7">앞면에서 2번째 줄,<br>위에서 3번째 칸입니다.</div>
   <div style="font-size:11.5px;color:var(--sub);margin-top:6px">슬롯 번호와 줄·칸의 대응은 도식이며 데이터 확인 전입니다.</div>
  </div>
  <div class="panel" style="margin-top:12px;padding:14px 16px;font-size:14px;line-height:1.85">
   <div style="display:flex"><span style="color:var(--sub)">30일 고장 위험</span><b class="num" style="margin-left:auto;font-size:20px;color:var(--red)">0.93</b></div>
   <div style="display:flex"><span style="color:var(--sub)">예측 잔여수명</span><b class="num" style="margin-left:auto;font-size:20px">4일</b></div>
   <div style="display:flex"><span style="color:var(--sub)">가장 큰 원인</span><span style="margin-left:auto">197 대기 섹터 급증</span></div>
  </div>
  <div style="margin-top:14px;display:flex;gap:8px"><span class="btn go">교체 후보에 추가</span><span class="btn ghost">디스크 상세</span></div>
  <div style="margin-top:12px;font-size:12.5px;color:var(--sub)">이 Pod에는 위험 2개, 주의 3개가 있습니다.</div>
 </div>
</div>"""
top_foot = "디스크 60개를 15개씩 줄지어 앞쪽에 둔 구조는 Backblaze Storage Pod 6.0 설명 기준 / 부품 위치는 도식"


# ---------- 3. 디스크 상세 ----------
def spark(vals, color, label, latest):
    w, h = 270, 96
    mx = max(max(vals), 1)
    pts = " ".join(f"{i * w / (len(vals) - 1):.0f},{h - v / mx * (h - 6) - 3:.0f}" for i, v in enumerate(vals))
    return (f'<div class="panel" style="padding:10px 12px"><div style="display:flex;font-size:13px">'
            f'<span>{label}</span><b class="num" style="margin-left:auto;font-size:17px;color:{color}">{latest}</b></div>'
            f'<svg width="{w}" height="{h}" style="margin-top:4px"><polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/></svg></div>')


n = 30
s5 = [8 + (i // 6) * 2 + (14 if i > 24 else 0) for i in range(n)]
s187 = [0 if i < 18 else (i - 18) * 2 for i in range(n)]
s197 = [0 if i < 22 else (i - 22) * 6 for i in range(n)]
s188 = [0] * n
sparks = (spark(s197, "var(--red)", "197 대기 섹터", s197[-1]) + spark(s187, "var(--red)", "187 복구 불가 오류", s187[-1])
          + spark(s5, "var(--amber)", "5 재할당 섹터", s5[-1]) + spark(s188, "var(--ok-d)", "188 명령 시간 초과", 0))
shap = "".join(
    f'<div style="display:flex;align-items:center;gap:10px;margin:8px 0"><div style="width:128px;font-size:13px">{nm}</div>'
    f'<div style="width:124px"><div style="height:12px;width:{w}px;background:{c};border-radius:1px"></div></div>'
    f'<span style="font-size:12px;color:var(--sub);white-space:nowrap">{d}</span></div>'
    for nm, w, c, d in [("197 대기 섹터", 118, "var(--red)", "위험을 올림"), ("187 복구 불가 오류", 88, "var(--red)", "위험을 올림"),
                        ("5 재할당 섹터", 60, "var(--red)", "위험을 올림"), ("9 가동 시간", 30, "var(--red)", "위험을 올림"),
                        ("194 온도", 22, "var(--ok-d)", "위험을 낮춤")])
detail = f"""
<div class="head"><h1>디스크 상세</h1>
 <span class="chip" style="margin-left:auto;width:220px;color:#8C95A1">시리얼 번호로 찾기</span><span class="btn go sm">찾기</span></div>
<div style="display:flex;gap:16px;align-items:stretch">
 <div class="panel" style="flex:1;padding:16px 18px;display:flex;gap:26px;align-items:center">
  {tag(LOC)}
  <div style="font-size:13.5px;line-height:1.8"><span style="color:var(--sub)">시리얼</span> ZJV0****1<br>
   <span style="color:var(--sub)">모델</span> ST12000NM0008<br><span style="color:var(--sub)">가동</span> 3.2년, 최근 온도 31℃</div>
 </div>
 <div class="panel" style="width:300px;padding:16px 18px;border-left:6px solid var(--red)">
  <div style="font-size:13px;color:var(--sub)">30일 안에 고장 날 위험</div>
  <div style="display:flex;align-items:baseline;gap:10px"><b class="num" style="font-size:44px;color:var(--red);line-height:1.1">0.93</b>
   <span style="font-weight:700;color:var(--red)">위험</span></div>
  <div style="font-size:13.5px">예측 잔여수명 <b class="num" style="font-size:18px">4일</b></div>
 </div>
</div>
<div style="display:flex;gap:16px;margin-top:16px">
 <div style="flex:1">
  <div style="display:flex;align-items:baseline;margin-bottom:8px"><b>SMART 기록, 최근 30일</b>
   <span style="margin-left:auto;font-size:12.5px"><b>30일</b> <span style="color:var(--sub)">60일 90일</span></span></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">{sparks}</div>
 </div>
 <div class="panel" style="width:330px;padding:14px 16px">
  <b>왜 위험한가</b><div style="font-size:12px;color:var(--sub);margin:2px 0 6px">예측에 영향을 준 항목 (SHAP 상위 5개)</div>{shap}
  <div style="margin-top:16px"><span class="btn go">교체 후보에 추가</span></div>
 </div>
</div>"""

# ---------- 4. 교체 목록 ----------
items = [("ZJV0****1", ("sac2", "1xxx", "03", "17"), 0.93, "4일", "197 대기 섹터 급증", "r"),
         ("ZJV0****2", ("sac2", "1xxx", "03", "41"), 0.91, "6일", "187 오류가 30일간 증가", "r"),
         ("ZJV0****3", ("sac2", "1xxx", "11", "08"), 0.88, "9일", "5 재할당 섹터 증가", "r"),
         ("ZJV0****4", ("sac2", "1xxx", "16", "52"), 0.87, "12일", "197 대기 섹터 증가", "r"),
         ("ZJV0****5", ("phx1", "1yyy", "05", "22"), 0.71, "21일", "187 오류 증가", "w"),
         ("ZJV0****6", ("iad1", "1zzz", "00", "30"), 0.66, "27일", "5 재할당 섹터 증가", "w")]
trs = ""
for i, (sn, (dc, v, p, s), sc, rul, why, g) in enumerate(items):
    col = "var(--red)" if g == "r" else "var(--amber)"
    trs += (f'<tr style="border-top:1px solid var(--rule);{"background:#fff" if i == 1 else ""}">'
            f'<td style="padding:9px 10px;border-left:4px solid {col}">{tag([("", dc), ("", v), ("", "P" + p), ("", "S" + s)], small=True).replace("<span><i></i><b>S", f'<span style="background:{col}"><i></i><b>S')}</td>'
            f'<td>{sn}</td><td><b class="num" style="font-size:18px;color:{col}">{sc:.2f}</b></td>'
            f'<td class="num" style="font-size:16px">{rul}</td><td>{why}</td>'
            f'<td style="color:var(--sub)">{"보류 사유 입력 중" if i == 1 else "승인 대기"}</td>'
            f'<td style="text-align:right;padding-right:12px"><span class="btn go sm">승인</span> <span class="btn ghost sm">보류</span></td></tr>')
replace = f"""
<div class="head"><h1>교체 목록</h1><span class="ctx">위험 점수가 높은 순서</span>
 <span style="margin-left:auto;display:flex;gap:8px"><span class="btn ghost sm">처리 이력</span><span class="btn ghost sm">CSV로 내려받기</span></span></div>
<div style="display:flex;gap:10px;align-items:center;margin-bottom:12px">
 <span class="chip">등급: 전체</span><span class="chip">위치: 전체</span>
 <span style="margin-left:18px;font-size:13.5px">교체 후보 기준</span>
 <div style="width:180px;height:4px;background:var(--rule);position:relative;border-radius:2px">
  <div style="position:absolute;left:0;width:18px;height:4px;background:var(--ink)"></div>
  <div style="position:absolute;left:12px;top:-6px;width:16px;height:16px;border-radius:50%;background:var(--ink)"></div></div>
 <b style="font-size:13.5px">위험 상위 1%</b>
</div>
<div class="panel" style="overflow:hidden"><table style="border-collapse:collapse;width:100%;font-size:13.5px">
<tr style="color:var(--sub);font-size:12.5px;text-align:left">
 <th style="padding:9px 14px;font-weight:500">위치 (데이터센터, Vault, Pod, 슬롯)</th><th style="font-weight:500">시리얼</th>
 <th style="font-weight:500">위험 점수</th><th style="font-weight:500">잔여수명</th><th style="font-weight:500">주요 원인</th>
 <th style="font-weight:500">상태</th><th></th></tr>{trs}</table></div>
<div class="panel" style="position:absolute;right:26px;bottom:40px;width:350px;padding:16px 18px;border:2px solid var(--ink)">
 <b>보류 사유를 적어 주세요</b><div style="font-size:12.5px;color:var(--sub);margin:2px 0 8px">ZJV0****2, sac2 / 1xxx / P03 / S41</div>
 <div class="chip" style="height:54px;color:#8C95A1">예: 다음 정기 점검 때 같은 Pod의 S17과 함께 교체</div>
 <div style="text-align:right;margin-top:10px"><span class="btn ghost sm">취소</span> <span class="btn go sm">보류 저장</span></div>
</div>"""
replace_foot = GRADE_NOTE + " / 승인하면 승인자와 시각이 기록됩니다"

# ---------- 5. 모델 비교 ----------
bars = "".join(
    f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end">'
    f'<div style="font-size:12.5px;color:var(--sub);margin-bottom:6px;text-align:center">1년 교체 --개<br>절감액 --원</div>'
    f'<div style="width:84px;height:230px;border:2px dashed {c};background:repeating-linear-gradient(45deg,transparent 0 6px,rgba(0,0,0,.04) 6px 12px)"></div>'
    f'<div style="margin-top:8px;font-weight:600">{nm}</div></div>'
    for nm, h, c in [("SMART 규칙", 260, "#A9B1BB"), ("머신러닝 모델", 170, "var(--ink)"), ("딥러닝 모델", 190, "var(--blue)")])
model = f"""
<div class="head"><h1>모델 비교</h1><span class="ctx">같은 시험 기간, 같은 수의 고장을 잡는다고 할 때</span></div>
<div style="display:flex;gap:16px">
 <div style="width:430px">
  <div class="panel" style="overflow:hidden"><table style="border-collapse:collapse;width:100%;font-size:13.5px">
   <tr style="color:var(--sub);font-size:12.5px;text-align:left"><th style="padding:10px 14px;font-weight:500">방식</th>
    <th style="font-weight:500">경보 정밀도</th><th style="font-weight:500">AP</th><th style="font-weight:500">잡은 고장</th></tr>
   <tr style="border-top:1px solid var(--rule)"><td style="padding:11px 14px">SMART 규칙 (기준)</td><td>--%</td><td>--</td><td>-- / --</td></tr>
   <tr style="border-top:1px solid var(--rule)"><td style="padding:11px 14px;font-weight:600">머신러닝 모델</td><td>--%</td><td>--</td><td>-- / --</td></tr>
   <tr style="border-top:1px solid var(--rule)"><td style="padding:11px 14px;font-weight:600">딥러닝 모델</td><td>--%</td><td>--</td><td>-- / --</td></tr>
  </table></div>
  <div class="panel" style="margin-top:14px;padding:14px 16px">
   <b>디스크 1개 가격</b><div style="font-size:12.5px;color:var(--sub);margin:2px 0 8px">바꾸면 절감액을 다시 계산합니다</div>
   <div style="display:flex;gap:8px"><span class="chip" style="width:150px">364,550원</span><span class="btn go sm">다시 계산</span></div>
  </div>
 </div>
 <div class="panel" style="flex:1;padding:16px 18px">
  <b>1년 동안 바꿔야 하는 디스크 수</b><div style="font-size:12.5px;color:var(--sub);margin-top:2px">실험 결과가 나오면 막대 높이를 채웁니다</div>
  <div style="display:flex;height:440px;align-items:flex-end;padding-top:10px">{bars}</div>
 </div>
</div>"""
model_foot = "성능 수치는 모델 확정 후 채움 / 모델 종류도 확정 전이라 머신러닝·딥러닝 모델로 표시"

SCREENS = [("1_dashboard", "대시보드", dash, dash_foot), ("2_pod_topview", "대시보드", topview, top_foot),
           ("3_disk_detail", "디스크 상세", detail, GRADE_NOTE), ("4_replace_list", "교체 목록", replace, replace_foot),
           ("5_model_compare", "모델 비교", model, model_foot)]

for name, active, body, foot in SCREENS:
    html = os.path.join(BASE, name + ".html")
    with open(html, "w", encoding="utf-8") as f:
        f.write(page(active, body, foot))
    png = os.path.join(BASE, name + ".png")
    if os.path.exists(png):
        os.remove(png)
    for _ in range(3):  # Edge가 가끔 파일을 못 쓰고 끝나서 다시 시도
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=8000",
                        f"--screenshot={png}", "--window-size=1200,700", "file:///" + html.replace("\\", "/")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            if os.path.exists(png):
                break
            time.sleep(0.5)
        if os.path.exists(png):
            break
    print("saved" if os.path.exists(png) else "FAILED", png)
