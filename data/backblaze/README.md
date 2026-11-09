# Backblaze 하드디스크 데이터 README

출처: [Backblaze Drive Stats](https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data) (무료, 출처 표기 필수, 데이터 자체 판매 금지). 공식 README가 없어서 팀용으로 정리했다.

## 구조
- 하루 CSV 1개(`YYYY-MM-DD.csv`), 1행 = 그날 가동 중인 디스크 1개
- 시리얼(`serial_number`)별로 날짜순으로 이으면 **디스크별 하루 단위 다변량 시계열**이 된다
- 분기마다 컬럼이 바뀔 수 있으므로 컬럼은 **위치가 아니라 이름으로** 읽는다

## 보유 데이터
| 위치 | 내용 |
|---|---|
| `YYYY_Qn.zip` | 원본 9개 분기 (2024 Q2 ~ 2026 Q2). OneDrive `hdd-rul/data/`에 백업 |
| `raw/YYYY_Qn/` | 압축 해제본 (약 95 GB). 하루 CSV |
| `merged/st12000nm0008_2024Q2-2026Q2.csv` | Seagate ST12000NM0008 한 모델, 821일(2024-04-01~2026-06-30), 디스크 19,516개, 고장 1,118건, 21개 열. 시리얼·날짜순 정렬 |
| `practice/` | 초기 실험 노트북 3개: `full_data_dl_compare`(규칙·RF·HGB·GRU 비교, 절감 비용), `full_data_eda`(첫 EDA·모델링), `practice_pipeline`(1% 샘플 파이프라인) |

## 주요 컬럼
| 컬럼 | 의미 |
|---|---|
| `date`, `serial_number`, `model`, `capacity_bytes` | 날짜, 디스크 ID, 모델, 용량 |
| `failure` | 고장이면 1. **고장 날(= 마지막 기록)에만 1**, 그 뒤로는 기록이 없다 |
| `datacenter` | 데이터센터 위치 |
| `smart_5_raw` | 재할당 섹터 수 (손상) |
| `smart_187_raw` | 정정 불가 오류 (손상) |
| `smart_188_raw` | 명령 타임아웃 (시게이트는 여러 값을 묶어 저장해 숫자가 매우 큼) |
| `smart_197_raw` | 대기 중 불량 섹터 (손상) |
| `smart_198_raw` | 오프라인 정정 불가 섹터 (손상) |
| `smart_9_raw` | 누적 가동 시간 (디스크 나이) |
| `smart_194_raw` | 온도(℃) |
| `smart_199_raw` | 케이블·인터페이스 오류 |

## 주의
- **raw 값을 쓴다.** normalized는 제조사마다 기준이 다른 점수다
- 디스크 모델마다 보고하는 SMART 항목이 달라 빈 칸이 많다 → 모델을 정하고 그 모델의 열만 쓴다
- 고장 원인 유형은 없다 (고장 0/1뿐)
- 관측 끝까지 고장 나지 않은 디스크는 수명을 모른다(중도절단)
- 스키마 파일의 `smart_211`, `smart_212`는 `normailized`로 오타가 나 있다

## 도메인 기초
- **하드디스크**: 회전 원판, 헤드, 모터로 된 기계 장치. 표면 손상이 쌓이면 SMART 5·187·197·198이 0에서 올라간다
- **연간 고장률(AFR)** = 고장 수 ÷ (가동 일수 합 ÷ 365)
- **욕조 곡선**: 고장은 초기 불량기와 노후기에 많다 → 가동 시간이 중요한 변수
- **RAID**: 여러 디스크에 나눠 저장해 1개가 죽어도 복구 가능. 하지만 복구 중 추가 고장이 나면 데이터 손실 → 미리 교체하는 이유
- 참고: [What SMART Stats Indicate Hard Drive Failures](https://www.backblaze.com/blog/what-smart-stats-indicate-hard-drive-failures)

## 제품별 가격

2026-11-05 확인. 아래는 디스크 1개 기준의 온라인 표시가다.

| 제품 | 판매 조건 | 표시가 | 출처 |
|---|---|---:|---|
| Seagate Exos X14 12TB SATA (`ST12000NM0008`) | 다나와 해외구매 상품, 제품 상태 미확인 | 364,550원 | [다나와 상품 목록](https://search.danawa.com/dsearch.php?query=%EC%97%91%EC%86%8C%EC%8A%A4X14) |
| Seagate Exos X14 12TB SATA (`ST12000NM0008`) | 미국 판매점 리퍼비시 | US$359.95 | [goHardDrive 상품 페이지](https://www.goharddrive.com/Seagate-Exos-X14-ST12000NM0008-12TB-3-5-HDD-p/g01-1311-cr.htm) |
| Seagate Exos X14 12TB SATA (`ST12000NM0008`) | 미국 판매점 신품, 품절 | US$300.00 | [ServerPartDeals 상품 페이지](https://serverpartdeals.com/products/seagate-exos-x14-st12000nm0008-12tb-7-2k-rpm-sata-6gb-s-512e-4kn-256mb-3-5-hard-drive) |

해외구매 최종가는 재고, 배송비, 세금에 따라 달라질 수 있다.
