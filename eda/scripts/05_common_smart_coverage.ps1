$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$edaRoot = Split-Path $PSScriptRoot -Parent
$rankPath = Join-Path (Split-Path $edaRoot -Parent) 'data/backblaze/summary/model_rank.csv'
$duckdbPath = Join-Path (Split-Path $edaRoot -Parent) 'tools/duckdb/duckdb.exe'
$zipRoot = if ($env:HDD_RAW_DIR) { $env:HDD_RAW_DIR } else { 'C:/Users/rhkdd/OneDrive/hdd-rul/data/raw' }
$outRoot = Join-Path $edaRoot 'analysis/sampled_column_check'
$dayRoot = Join-Path $outRoot 'days'
[System.IO.Directory]::CreateDirectory($dayRoot) | Out-Null
$rankRows = Import-Csv -LiteralPath $rankPath
$seenDates = @{}
$seenModels = @{}
$zipDates = @{}
foreach ($zipPath in (Get-ChildItem -LiteralPath $zipRoot -Filter '*.zip' | Sort-Object Name)) {
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath.FullName)
    try {
        $entries = @($archive.Entries | Where-Object { $_.FullName -notlike '*__MACOSX*' -and $_.Name -match '^\d{4}-\d{2}-\d{2}\.csv$' } | Sort-Object Name)
        foreach ($entry in $entries) { $zipDates[$entry.Name.Substring(0,10)] = $zipPath.FullName }
        foreach ($entry in @($entries[0], $entries[-1])) { $seenDates[$entry.Name.Substring(0,10)] = $false }
    } finally { $archive.Dispose() }
}
function Measure-Day([string]$day) {
    $outputPath = Join-Path $dayRoot ($day + '.csv')
    if (-not (Test-Path -LiteralPath $outputPath)) {
        $archive = [System.IO.Compression.ZipFile]::OpenRead($zipDates[$day])
        $tempCsv = Join-Path $outRoot 'sample_day.csv'
        try {
            $entry = $archive.Entries | Where-Object { $_.Name -eq ($day + '.csv') -and $_.FullName -notlike '*__MACOSX*' } | Select-Object -First 1
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $tempCsv, $true)
        } finally { $archive.Dispose() }
        $csvSqlPath = $tempCsv.Replace('\','/').Replace("'","''")
        $outSqlPath = $outputPath.Replace('\','/').Replace("'","''")
        $sql = "COPY (SELECT model, count(*) AS sampled_rows, count(COLUMNS('^smart_.*_raw$')) FROM read_csv('$csvSqlPath', header=true, all_varchar=true, nullstr=['','NaN','nan','NA']) GROUP BY model) TO '$outSqlPath' (HEADER);"
        & $duckdbPath -c $sql
        if ($LASTEXITCODE -ne 0) { throw "DuckDB failed: $day" }
        Remove-Item -LiteralPath $tempCsv
    }
    foreach ($row in (Import-Csv -LiteralPath $outputPath)) { $seenModels[$row.model] = $true }
    $seenDates[$day] = $true
    Write-Output "[$day] models covered: $($seenModels.Count)"
}
foreach ($day in @($seenDates.Keys | Sort-Object)) { Measure-Day $day }
foreach ($model in $rankRows) {
    if (-not $seenModels.ContainsKey($model.model)) { Measure-Day $model.first_date }
}
$missing = @($rankRows | Where-Object { -not $seenModels.ContainsKey($_.model) })
if ($missing.Count -gt 0) { throw "Models still missing: $($missing.model -join ', ')" }
$manifest = [ordered]@{
    method = 'First and last CSV day in each quarter, plus first observed day of any missing model'
    scope = '2024-04-01 through 2026-06-30; 97 models from model_rank.csv'
    dates = @($seenDates.Keys | Where-Object { $seenDates[$_] } | Sort-Object)
    models_covered = $seenModels.Count
    note = 'Sample-based non-null coverage; does not establish semantic or unit compatibility across manufacturers.'
}
[System.IO.File]::WriteAllText((Join-Path $outRoot 'manifest.json'), ($manifest | ConvertTo-Json -Depth 5), [System.Text.UTF8Encoding]::new($false))
Write-Output 'Sampling complete.'
