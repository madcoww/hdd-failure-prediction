# 클릭형 프로토타입

**주소: https://madcoww.github.io/hdd-failure-prediction/**

발표 QR로 여는 체험용 화면이다. HTML · CSS · JavaScript와 예시 데이터만 쓴다. 서버와 실제 모델은 없다.

## 체험 흐름
1. 대시보드에서 위험 디스크를 고른다. PC에서는 랙 지도, 모바일에서는 카드를 누른다
2. 디스크 상세에서 SMART 추이와 위험 근거를 본다
3. 교체 목록에서 승인하거나 보류한다. 보류할 때는 사유가 필요하다
4. '교체 예정' 또는 '보류' 탭에서 상태를 확인한다

오른쪽 위 **초기화**를 누르면 처음 상태로 돌아간다. 상태는 각자의 브라우저(localStorage)에만 저장되어 관객끼리 섞이지 않는다.

## 파일
| 파일 | 내용 |
|---|---|
| `index.html` | 시작 화면. PC와 모바일이 같은 주소를 쓴다 (폭 820px 이하는 모바일 배치) |
| `css/style.css` | 목업 v4와 같은 색 · 글꼴 |
| `js/data.js` | 예시 디스크 8개와 SMART 90일 추이 (가상) |
| `js/app.js` | 화면 이동(#/dashboard, #/disk/d1, #/replace), 승인 · 보류, 초기화 |
| `assets/favicon.svg` | 탭 아이콘 |

## 로컬 실행
```bash
python -m http.server 8765 --directory prototype
```
그다음 http://localhost:8765 를 연다.

## 기준 문서
- 화면설계서: `docs/v1/5_화면설계서_웹SB_v1.pptx`, `docs/v1/5_화면설계서_모바일SB_v1.pptx`
- 디자인: `mockups/v4`, `mockups/mobile`

수치 · 시리얼 · Vault 번호는 가상이다. 위험(상위 1%) · 주의(상위 1~5%)는 예시 기준이고, 랙 배치는 도식이다.
