-- raw 전체(2024-04-01 ~ 2026-06-30)에서 모델별 디스크 수, 고장 수, 연간 고장률(AFR) 집계
-- 실행: tools/duckdb/duckdb.exe -c ".read scripts/02_model_rank.sql"  (작업 폴더 C:/hdd-failure-prediction/eda)
COPY (
  WITH per_model AS (
    SELECT
      model,
      count(DISTINCT serial_number)                    AS disks,
      sum(failure)                                     AS failures,
      count(DISTINCT serial_number) FILTER (failure = 1) AS failed_disks,
      count(*)                                         AS drive_days,
      min(date)                                        AS first_date,
      max(date)                                        AS last_date
    FROM '../data/backblaze/fleet_slim/*.parquet'
    GROUP BY model
  )
  SELECT
    row_number() OVER (ORDER BY failures DESC)          AS rank_fail,
    model, disks, failures, failed_disks, drive_days,
    round(failures / (drive_days / 365.0) * 100, 2)     AS afr_pct,
    round(100.0 * disks / sum(disks) OVER (), 2)        AS disk_share_pct,
    round(100.0 * drive_days / sum(drive_days) OVER (), 2) AS row_share_pct,
    round(100.0 * failures / sum(failures) OVER (), 2)  AS fail_share_pct,
    first_date, last_date
  FROM per_model
  ORDER BY failures DESC
) TO '../data/backblaze/summary/model_rank.csv' (HEADER);
