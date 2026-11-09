"""노션 4번 '서비스 이용 과정 요약' 흐름 그림 (사진 없이 단계만). 내용은 노션 흐름 토글 순서도와 같다."""
import os
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
W, H = 1600, 330

FONT = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/'
        'pretendardvariable-dynamic-subset.min.css">')

ICON = {
    "dash": '<rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/>',
    "disk": '<path d="M22 12H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/><path d="M6 16h.01M10 16h.01"/>',
    "plus": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8M8 12h8"/>',
    "list": '<path d="m3 17 2 2 4-4M3 7l2 2 4-4M13 6h8M13 12h8M13 18h8"/>',
    "hist": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5M12 7v5l4 2"/>',
}


def ic(n, c):
    return (f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICON[n]}</svg>')


STEPS = [
    ("dash", "대시보드", "위험 디스크 찾기", ""),
    ("disk", "디스크 상세", "30일 위험·잔여수명,<br>SMART 추이 확인", ""),
    ("plus", "교체 후보 추가", "'승인 대기'로 등록", ""),
    ("list", "교체 목록", "", '<div class="br"><div class="ok"><i></i>승인<span>승인자·시각 기록</span></div>'
                             '<div class="hold"><i></i>보류<span>사유 필수</span></div></div>'),
    ("hist", "처리 이력", "확인,<br>CSV 내보내기", ""),
]

ARROW = ('<div class="arr"><svg width="34" height="14" viewBox="0 0 34 14"><path d="M1 7H30" stroke="#B4BDCC" stroke-width="1.8"/>'
         '<path d="M25 2l6 5-6 5" fill="none" stroke="#B4BDCC" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div>')

cards = ARROW.join(
    f'<div class="card"><div class="top"><span class="n">{i}</span><div class="ico">{ic(icn, "#2F5BD3")}</div></div>'
    f'<b>{t}</b>{f"<p>{d}</p>" if d else ""}{extra}</div>'
    for i, (icn, t, d, extra) in enumerate(STEPS, 1))

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{width:{W}px;height:{H}px;background:#fff;font-family:'Pretendard Variable',Pretendard,'Malgun Gothic',sans-serif;color:#18212F;
display:flex;flex-direction:column;justify-content:center;padding:0 36px}}
.row{{display:flex;align-items:stretch}}
.arr{{width:46px;flex:none;display:flex;align-items:center;justify-content:center}}
.card{{flex:1;border:1px solid #E2E7EF;border-radius:16px;padding:20px 20px 22px;background:linear-gradient(180deg,#FFFFFF,#F7F9FC);
box-shadow:0 1px 0 #fff inset,0 10px 24px -18px rgba(24,33,47,.35)}}
.top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}}
.n{{font-size:13px;font-weight:700;color:#2F5BD3;background:#EAF0FF;border-radius:20px;padding:3px 10px}}
.ico{{width:42px;height:42px;border-radius:12px;background:#EEF2FB;display:flex;align-items:center;justify-content:center}}
b{{display:block;font-size:20px;letter-spacing:-.4px}}
p{{font-size:14.5px;color:#5A6579;line-height:1.55;margin-top:8px}}
.br{{display:flex;flex-direction:column;gap:7px;margin-top:10px}}
.br div{{display:flex;align-items:center;gap:7px;font-size:14px;font-weight:700;padding:7px 10px;border-radius:9px}}
.br span{{font-weight:500;color:#5A6579;margin-left:auto;font-size:13px}}
.br i{{width:7px;height:7px;border-radius:50%}}
.ok{{background:#EEF3FF;color:#2449B8}}.ok i{{background:#2F5BD3}}
.hold{{background:#FFF4E5;color:#9A5300}}.hold i{{background:#E58A00}}
.foot{{margin-top:16px;font-size:12px;color:#97A1B2}}
"""


DARK = """
body{background:#0C1322;color:#E6ECF6}
.card{border-color:#22304A;background:linear-gradient(180deg,#152038,#111A2C);box-shadow:0 10px 24px -16px rgba(0,0,0,.6)}
.n{background:rgba(61,139,255,.16);color:#86B6FF}
.ico{background:rgba(61,139,255,.12)}
.ico svg{stroke:#7FB2FF}
p,.br span{color:#8E9BB4}
.ok{background:rgba(61,139,255,.14);color:#9CC2FF}.ok i{background:#3D8BFF}
.hold{background:rgba(255,176,32,.13);color:#FFC452}.hold i{background:#FFB020}
.arr path{stroke:#4A5B7A}
.foot{color:#5E6C87}
"""

for theme, extra_css in [("", ""), ("_dark", DARK)]:
    html = (f'<html><head><meta charset="utf-8">{FONT}<style>{CSS}{extra_css}</style></head><body><div class="row">{cards}</div>'
            f'<div class="foot">기준: 팀 기능정의서 1_메뉴구조_기능정의서_v1.xlsx</div></body></html>')

    path = os.path.join(BASE, "0_flow" + theme + ".html")
    open(path, "w", encoding="utf-8").write(html)
    png = os.path.join(BASE, "0_flow" + theme + ".png")
    if os.path.exists(png):
        os.remove(png)
    for _ in range(3):
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=10000",
                        "--force-device-scale-factor=2", f"--screenshot={png}", f"--window-size={W},{H}",
                        "file:///" + path.replace("\\", "/")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(20):
            if os.path.exists(png):
                break
            time.sleep(0.5)
        if os.path.exists(png):
            break
    print("saved" if os.path.exists(png) else "FAILED", png)
