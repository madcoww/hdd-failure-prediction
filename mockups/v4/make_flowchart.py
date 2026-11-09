"""서비스 이용 순서도 (흰 바탕, 시작·판단·끝 기호). 분기 내용은 1_메뉴구조_기능정의서_v1.xlsx 기준."""
import os
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
W, H = 1720, 780
S = []


def text(x, y, t, size=14, weight=500, anchor="middle"):
    lines = t.split("\n")
    y0 = y - (len(lines) - 1) * size * 0.62
    for i, ln in enumerate(lines):
        S.append(f'<text x="{x}" y="{y0 + i * size * 1.25 + size * 0.36}" font-size="{size}" font-weight="{weight}" '
                 f'text-anchor="{anchor}">{ln}</text>')


def term(x, y, t, w=150, h=46):
    S.append(f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="{h / 2}" class="s"/>')
    text(x, y, t)


def box(x, y, t, w=150, h=50):
    S.append(f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" class="s"/>')
    text(x, y, t)


def dia(x, y, t, w=120, h=84):
    S.append(f'<polygon points="{x},{y - h / 2} {x + w / 2},{y} {x},{y + h / 2} {x - w / 2},{y}" class="s"/>')
    text(x, y, t, 13.5)


def line(*pts, arrow=True):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    S.append(f'<path d="{d}" class="l"{" marker-end=\"url(#a)\"" if arrow else ""}/>')


def lab(x, y, t):
    S.append(f'<text x="{x}" y="{y}" font-size="13" font-weight="600">{t}</text>')


# 1행: 디스크 찾기
term(85, 120, "대시보드", 130)
dia(250, 120, "찾는 방법")
box(420, 60, "랙 지도에서\n디스크 칸 클릭")
box(420, 180, "시리얼 검색")
dia(600, 180, "시리얼\n있음?")
box(600, 310, "알림: 디스크를\n찾을 수 없습니다", 170, 54)
box(800, 120, "디스크 상세\n(위험·잔여수명·SMART)", 180, 58)
box(1010, 120, "[교체 후보 추가]\n버튼", 160, 54)
dia(1200, 120, "이미 목록에\n있음?", 130, 90)
box(1200, 260, "알림: 이미\n추가된 디스크", 150, 54)
box(1410, 120, "교체 목록\n'승인 대기'", 150, 54)

line((150, 120), (190, 120))
line((310, 120), (330, 120), (330, 60), (345, 60))
line((330, 120), (330, 180), (345, 180))
line((495, 180), (540, 180))
line((600, 222), (600, 283)); lab(608, 250, "No")
line((515, 310), (420, 310), (420, 205))
line((660, 180), (690, 180), (690, 120), (710, 120)); lab(664, 170, "Yes")
line((495, 60), (800, 60), (800, 91))
line((890, 120), (930, 120))
line((1090, 120), (1135, 120))
line((1265, 120), (1335, 120)); lab(1278, 110, "No")
line((1200, 165), (1200, 233)); lab(1208, 195, "Yes")
line((1125, 260), (800, 260), (800, 149))

# 2열: 승인·보류
dia(1410, 270, "승인?")
box(1410, 400, "승인자 입력 후\n승인")
box(1610, 270, "보류 사유 입력", 140)
dia(1610, 400, "사유\n입력?")
box(1410, 530, "처리 완료 알림\n상태 갱신")
box(1410, 630, "처리 이력 기록")
term(1410, 725, "이력 확인·CSV 내보내기", 220)

line((1410, 147), (1410, 228))
line((1410, 312), (1410, 375)); lab(1418, 345, "Yes")
line((1470, 270), (1535, 270)); lab(1476, 258, "No")
line((1610, 295), (1610, 358))
line((1670, 400), (1700, 400), (1700, 255), (1685, 255)); lab(1676, 390, "No")
line((1610, 442), (1610, 530), (1485, 530)); lab(1618, 475, "Yes")
line((1410, 425), (1410, 505))
line((1410, 555), (1410, 605))
line((1410, 655), (1410, 702))

S.append('<text x="30" y="765" font-size="12" fill="#8A8A8A">기준: 1_메뉴구조_기능정의서_v1.xlsx</text>')

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       '<defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
       '<path d="M0 0L8 4L0 8Z" fill="#111"/></marker></defs>'
       '<style>.s{fill:#fff;stroke:#111;stroke-width:1.6}.l{fill:none;stroke:#111;stroke-width:1.6}'
       'text{fill:#111;font-family:"Pretendard Variable",Pretendard,"Malgun Gothic",sans-serif}</style>'
       + "".join(S) + "</svg>")
html = ('<html><head><meta charset="utf-8"><link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/'
        'dist/web/variable/pretendardvariable-dynamic-subset.min.css"><style>*{margin:0}body{background:#fff}</style></head>'
        f'<body>{svg}</body></html>')

path = os.path.join(BASE, "0_flowchart.html")
open(path, "w", encoding="utf-8").write(html)
png = os.path.join(BASE, "0_flowchart.png")
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
