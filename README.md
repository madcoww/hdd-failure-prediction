# hdd-failure-prediction

(프로젝트명 미정) 데이터센터 HDD 고장 예측·교체 지원

데이터센터 하드디스크의 SMART 기록으로 **30일 안에 고장 날 디스크**를 예측하고, 교체 대상을 웹 화면으로 알린다.
목표는 고장 후 교체보다 비용이 덜 드는 **사전 교체 정책**이다.

> 포스코K뉴딜 데이터분석 3기 최종 프로젝트

## 체험해 보기
**클릭형 프로토타입: https://madcoww.github.io/hdd-failure-prediction/**

PC와 휴대폰에서 같은 주소로 열린다. 대시보드에서 위험 디스크 선택 → 디스크 상세에서 SMART 추이 · 위험 근거 확인 → 교체 목록에서 승인 또는 보류 → '교체 예정' · '보류' 상태 확인. 예시 데이터이고, 오른쪽 위 **초기화**로 처음부터 다시 할 수 있다. 소스는 [`prototype/`](prototype/).

## 데이터
- **출처**: [Backblaze Drive Stats](https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data). 실제 데이터센터에서 측정한 일별 SMART 기록
- **기간**: 2024 Q2 ~ 2026 Q2 (821일)
- 첫 모델링: `ST12000NM0008` 1종으로 4개 머신러닝 모델 비교. [실험 계획](ml/v1/README.md)
- 원본은 용량이 커서 저장소에 올리지 않았다.

## 폴더 구조

### 한눈에 보기
| 폴더 | 역할 | 저장소 |
|---|---|---|
| `data/` | 데이터와 데이터 설명 | 설명·집계표만 |
| `ml/v1/` | ST12000NM0008 전처리·4개 모델 학습·평가 | 실행 결과(`artifacts/`) 제외 |
| `docs/` | 기획 산출물: 기능정의서, Journey Map, 화면설계서, WBS | 팀 작성본만 |
| `mockups/` | 웹 화면 시안 v1~v4, 모바일 시안 | O |
| `prototype/` | 클릭형 프로토타입 (GitHub Pages로 공개) | O |
| `practice/` | 초기 실험 노트북 | X |
| `tools/` | 로컬 실행 도구 (DuckDB) | X |

### 전체 구조
```
hdd-failure-prediction/
├─ README.md                      이 문서
├─ .gitignore                     저장소 제외 목록
├─ LICENSE                        MIT (코드 대상. 데이터는 Backblaze 이용 조건을 따름)
│
├─ data/backblaze/                ── 데이터
│   ├─ README.md                  데이터 설명: 열 의미, 주의점, 도메인 기초, 디스크 가격
│   ├─ merged/ *                  ST12000NM0008 전체 기간 통합본 (Parquet 약 1.2GB)
│   ├─ fleet_slim/ *              분기별 전 모델 경량 데이터 (약 1GB)
│   ├─ summary/                   집계표
│   │   ├─ model_rank.csv         모델별 디스크 수·고장 수·AFR 순위
│   │   ├─ smart_coverage_top5.csv  상위 5개 모델의 SMART 열 기록률
│   │   ├─ top20_models.csv       고장 수 상위 HDD 20종
│   │   └─ common13_columns.json  상위 20종 공통 SMART 열 13개
│   ├─ top20_common13/ *          상위 20종 일별 추출 데이터 (약 3.6GB)
│   └─ raw/ *                     원본 압축 해제 위치 (원본 zip은 따로 보관)
│
├─ ml/v1/                         ── 첫 머신러닝 비교 실험
│   ├─ README.md                  입력·라벨·분할·평가 계획
│   ├─ ml_v1.ipynb                첫 셀에서 수치 변경·재학습·재평가
│   ├─ notebook_runner.py         설정 확인·경보 비율별 비교
│   ├─ train.py                   로지스틱 회귀·RF·XGBoost·LightGBM 비교
│   ├─ test_training.py           시간 처리·경보 예산 검증
│   ├─ requirements.txt           실행 패키지
│   └─ artifacts/ *               학습 데이터·모델·실제 평가 결과
│
├─ docs/                          ── 기획 산출물
│   ├─ v1/                        팀 작성본
│   │   ├─ 1_메뉴구조_기능정의서_v1.xlsx
│   │   ├─ 2_Journey_Map_v1.pptx
│   │   ├─ 3_서비스구조도_화면설계서_v1.pptx
│   │   ├─ 4_WBS_v1.xlsx
│   │   ├─ 5_화면설계서_웹SB_v1.pptx
│   │   └─ 5_화면설계서_모바일SB_v1.pptx
│   ├─ 양식/ *                    수업 제공 양식 4종 + 화면설계서 예시
│   ├─ journey_map/               Journey Map 이미지
│   ├─ notion_cover/              노션 표지 이미지
│   └─ qr_prototype.png           프로토타입 주소 QR
│
├─ mockups/                       ── 화면 시안 (v4가 최신)
│   ├─ v1/                        첫 시안 4장
│   ├─ v2/, v3/                   화면 5개 시안 (HTML + PNG, make_screens.py로 생성)
│   ├─ v4/                        최신 웹 시안
│   │   ├─ 0_flow*, 0_flowchart   서비스 이용 흐름도·순서도
│   │   ├─ 1_dashboard            대시보드 (요약 카드, 데이터센터 평면도, Vault 앞면)
│   │   ├─ 2_pod_topview          Pod 탑뷰 (디스크 60개 배치, 선택 디스크 위치)
│   │   ├─ 3_disk_detail          디스크 상세 (30일 위험, 잔여수명, SMART 기록)
│   │   ├─ 4_replace_list         교체 목록 (승인·보류, 처리 이력)
│   │   ├─ 5_model_compare        모델 비교 (방식별 성능·절감액)
│   │   └─ 6_alarm_settings       알림 설정 팝업
│   └─ mobile/                    모바일 시안 6장 (푸시, 홈, 디스크 상세, 교체 목록, 보류, 알림 설정)
│
├─ prototype/                     ── 클릭형 프로토타입 (gh-pages 브랜치로 배포)
│   ├─ index.html                 시작 화면 (PC · 모바일 같은 주소)
│   ├─ css/ · js/ · assets/       스타일, 예시 데이터와 화면 동작, 아이콘
│   └─ README.md                  체험 흐름 · 실행 방법
│
├─ practice/ *                    초기 실험 노트북
└─ tools/duckdb/ *                DuckDB 실행 파일 (pip install duckdb 로 대체 가능)
```
`*` 표시는 용량·저작권·개인 자료라서 저장소에 올리지 않는다.

## 진행 상황
- [x] 주제·데이터 선정
- [x] 기획 산출물: 기능정의서, Journey Map, 화면설계서(웹·모바일), WBS
- [x] 클릭형 프로토타입 (예시 데이터)
- [x] 첫 모델링 대상: ST12000NM0008 1종. 다른 제품 확대는 후속 단계
- [x] 모델링 v1: ST12000NM0008에서 규칙 기준선과 머신러닝 4개 비교 ([첫 결과](ml/v1/RESULTS.md)). 튜닝·확대·교체 시뮬레이션은 후속 단계
- [ ] 웹 알림 화면

## 라이선스
코드는 [MIT](LICENSE). 데이터는 아래 Backblaze 이용 조건을 따른다.

## 출처 표기
이 저장소의 데이터 출처는 **Backblaze**다: [Backblaze Drive Stats](https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data)

Backblaze가 밝힌 이용 조건을 따른다.
1. 데이터를 쓰면 출처를 Backblaze로 밝힌다
2. 데이터 사용에 대한 책임은 사용자에게 있다
3. 데이터를 바탕으로 만든 결과물은 팔 수 있다
4. 데이터 자체는 팔 수 없다(무료)
