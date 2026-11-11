"""웹 목업 v4 추가: 6_alarm_settings (헤더 종 아이콘 → 알림 설정 팝업).
make_screens.py의 CSS·아이콘을 그대로 쓰고, 배경은 1_dashboard.png를 어둡게 깐다."""
import os
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(BASE, "make_screens.py"), encoding="utf-8").read()
exec(src.split("HOT = {")[0])  # BASE, EDGE, W, H, FONT, CSS, ICON, ic, page, loc, seg

ICON["bell"] = '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>'


def toggle(on):
    bg = "#3D8BFF" if on else "#2A3956"
    pos = "right:3px" if on else "left:3px"
    return (f'<span style="width:42px;height:24px;border-radius:12px;background:{bg};position:relative;flex:none;display:inline-block">'
            f'<span style="position:absolute;top:3px;{pos};width:18px;height:18px;border-radius:50%;background:#fff"></span></span>')


def radio(t, on):
    ring = "#3D8BFF" if on else "#3A4D6E"
    dot = '<span style="width:8px;height:8px;border-radius:50%;background:#3D8BFF"></span>' if on else ""
    return (f'<label style="display:flex;align-items:center;gap:9px;font-size:13.5px">'
            f'<span style="width:18px;height:18px;border-radius:50%;border:2px solid {ring};display:flex;align-items:center;justify-content:center">{dot}</span>{t}</label>')


tabs = "".join(f'<div class="tab{" on" if t == "대시보드" else ""}">{t}</div>' for t in TABS)
bg_img = "file:///" + os.path.join(BASE, "1_dashboard.png").replace("\\", "/")
html_text = f"""<html><head><meta charset="utf-8">{FONT}<style>{CSS}
.bellb{{position:relative;width:36px;height:36px;border-radius:9px;border:1px solid #3D8BFF;background:rgba(61,139,255,.14);
display:flex;align-items:center;justify-content:center;color:#fff}}
.bellb i{{position:absolute;top:-6px;right:-6px;min-width:18px;height:18px;border-radius:9px;background:#FF4D5E;color:#fff;font-size:11px;
font-style:normal;font-weight:700;display:flex;align-items:center;justify-content:center;padding:0 5px}}
.sec{{font-size:12.5px;color:var(--sub);font-weight:600;margin-bottom:8px}}
</style></head><body style="position:relative">
<img src="{bg_img}" style="position:absolute;inset:0;width:{W}px;height:{H}px">
<div style="position:absolute;inset:58px 0 0 0;background:rgba(5,9,18,.66)"></div>
<div class="top" style="position:relative;z-index:2"><div class="logo"><i>{ic("disk", 16, "#fff")}</i>디스크 수명 관리</div><div class="tabs">{tabs}</div>
 <div class="right"><div class="bellb">{ic("bell", 18)}<i>2</i></div><div class="date">기준일<b class="num">2026.06.30</b></div><div class="user"><span>운</span>운영 담당자</div></div></div>
<div style="position:absolute;z-index:3;top:66px;right:196px;width:400px;background:#141F34;border:1px solid #2C3D5E;border-radius:12px;
box-shadow:0 18px 40px rgba(0,0,0,.45);overflow:hidden">
 <div style="display:flex;align-items:center;padding:14px 18px;border-bottom:1px solid var(--ln)"><b style="font-size:15.5px">알림 설정</b>
  <span style="margin-left:auto;color:var(--sub);font-size:18px">×</span></div>
 <div style="padding:14px 18px;border-bottom:1px solid var(--ln)"><div class="sec">새 알림 2건</div>
  <div style="display:flex;flex-direction:column;gap:8px">
   <div style="display:flex;gap:10px;align-items:center;padding:9px 11px;border-radius:8px;background:rgba(255,77,94,.08);border:1px solid rgba(255,77,94,.25)">
    <span class="pill r">위험</span><span style="flex:1;font-size:13px">sac2 · Pod 03 · 슬롯 17 <b class="num" style="color:#FF7D8A;font-size:15px">0.93</b></span><small style="color:var(--sub)">07:05</small></div>
   <div style="display:flex;gap:10px;align-items:center;padding:9px 11px;border-radius:8px;background:rgba(255,77,94,.08);border:1px solid rgba(255,77,94,.25)">
    <span class="pill r">위험</span><span style="flex:1;font-size:13px">sac2 · Pod 03 · 슬롯 41 <b class="num" style="color:#FF7D8A;font-size:15px">0.91</b></span><small style="color:var(--sub)">07:05</small></div>
  </div></div>
 <div style="padding:14px 18px;display:flex;flex-direction:column;gap:14px">
  <div style="display:flex;align-items:center"><div><b style="font-size:14px">이 브라우저로 알림 받기</b>
   <div style="font-size:12px;color:var(--sub);margin-top:2px">켜면 브라우저가 알림 권한을 묻습니다</div></div><span style="margin-left:auto">{toggle(True)}</span></div>
  <div><div class="sec">받을 등급</div><div style="display:flex;gap:20px">{radio("위험만 (상위 1%)", True)}{radio("위험 + 주의 (상위 5%)", False)}</div></div>
  <div><div class="sec">이메일 요약 (매일 07:30)</div>
   <div style="display:flex;gap:8px"><div style="flex:1;height:34px;border:1px solid var(--ln);border-radius:7px;background:var(--pn2);display:flex;align-items:center;padding:0 11px;color:#C9D3E5">ops-team@example.com</div>{toggle(True)}</div></div>
  <div style="display:flex;gap:8px;justify-content:flex-end"><div class="btn">테스트 알림 보내기</div><div class="btn pri">저장</div></div>
 </div>
</div>
<div class="foot" style="position:absolute;bottom:0;left:0;right:0;z-index:2">목업 화면 · 헤더 종 아이콘을 누르면 열리는 알림 설정 팝업 · 다른 화면 목업에는 종 아이콘을 아직 넣지 않음</div>
</body></html>"""

html = os.path.join(BASE, "6_alarm_settings.html")
png = os.path.join(BASE, "6_alarm_settings.png")
with open(html, "w", encoding="utf-8") as f:
    f.write(html_text)
if os.path.exists(png):
    os.remove(png)
for _ in range(3):
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=10000",
                    "--allow-file-access-from-files", f"--screenshot={png}", f"--window-size={W},{H}", "file:///" + html.replace("\\", "/")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        if os.path.exists(png):
            break
        time.sleep(0.5)
    if os.path.exists(png):
        break
print("saved" if os.path.exists(png) else "FAILED", png)
