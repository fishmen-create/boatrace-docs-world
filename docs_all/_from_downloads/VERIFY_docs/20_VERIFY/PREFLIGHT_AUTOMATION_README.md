# Preflight 自動化（簡易）

## 目的
- `_whatif/` の成果物を走査し、preflight PASS/FAIL をCSV化して比較対象を確定する。

## 実行（PowerShell）
```powershell
# これはあなたの作業です
cd C:\work\boatrace
powershell -ExecutionPolicy Bypass -File .\tools\preflight_check_whatif.ps1 `
  -WhatIfRoot ".\_whatif" `
  -OutCsv ".\runs\preflight_whatif_report.csv"
```

## 出力
- `runs\preflight_whatif_report.csv`
- `runs\preflight_whatif_report_summary.txt`

## 判定
- `status=PASS` のみを比較・採用判断に使用する（FAILは隔離）。
