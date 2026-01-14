param(
  [Parameter(Mandatory=$false)][string]$File = "C:\work\boatrace\docs\ERROR_COOKBOOK_BOATRACE_CAP10.md"
)
$ErrorActionPreference = "Stop"

function Ensure-Section([string]$Tag, [string]$Body){
  if (-not (Test-Path $File)) {
    New-Item -ItemType File -Force -Path $File | Out-Null
  }
  $hit = Select-String -LiteralPath $File -SimpleMatch -Pattern ("## " + $Tag) -Quiet -ErrorAction SilentlyContinue
  if (-not $hit) {
    Add-Content -LiteralPath $File -Value ("`r`n## " + $Tag + "`r`n" + $Body + "`r`n") -Encoding utf8
    Write-Host ("[append] " + $Tag) -ForegroundColor Green
  } else {
    Write-Host ("[skip] already exists: " + $Tag) -ForegroundColor DarkGray
  }
}

$bodyA = @"
**症状**  
PowerShell で複数行コピペ後、プロンプトが `>>` のまま戻らず、Enterしても終わらない／意図しない行継続になる。

**原因（多い順）**  
- バッククォート `` ` `` の行継続が途中で欠けた/余計に入った  
- `"` の閉じ忘れ（文字列が閉じていない）  
- `{}` / `()` の閉じ忘れ  
- コピペ時に全角スペースや不可視文字が混入

**対処**  
1) まず `Ctrl + C` で中断（入力状態を抜ける）  
2) **1行コマンド**に寄せる or **.ps1化**して実行  
3) 行継続が必要な場合は **行末は必ずバッククォート**で、最後の行は付けない

**予防（仕組み）**  
- 重要コマンドは `.ps1` に固定（コピペは `.\scripts\xxx.ps1` のみ）  
"@

$bodyB = @"
**症状**  
`mandatory_docs_guard.ps1 : パラメーター 'DocsDir' の引数が指定されていません` が出て止まる。

**原因**  
- `-DocsDir` の指定忘れ  
- 呼び出し側で `$DocsDir` が空のまま渡っている（変数未定義）

**対処（例）**  
`powershell -NoProfile -ExecutionPolicy Bypass -File C:\work\boatrace\docs\mandatory_docs_guard.ps1 -DocsDir C:\work\boatrace\docs`

**予防（仕組み）**  
- `.ps1` 側で `param([Parameter(Mandatory=$true)][string]$DocsDir)` を必須化  
- 呼び出し側で `if(-not $DocsDir){ throw ... }` を先に入れて即死させる  
"@

$bodyC = @"
**症状**  
`Join-Path : ChildPath に Object[] を変換できません` や `prediction scripts not found` が出る。

**原因**  
- `Join-Path $WD @('a','b')` のように **配列を一括で ChildPath に渡している**  
- そもそも `$WD` が未設定/想定外（`C:\windows\system32` で実行している等）

**対処**  
- `Join-Path` は **1つずつ**作る（for/foreach）  
- 先に `Set-Location C:\work\boatrace` / `$WD="C:\work\boatrace"` を固定してから実行

**予防（仕組み）**  
- 入口は `.\scripts\run_C_out.ps1` のような **単一コマンド**に寄せる  
- `.ps1` 内で `$WorkDir` が存在しない場合は即終了する  
"@

$bodyD = @"
**症状**  
`JSONDecodeError: Unexpected UTF-8 BOM` が出て exclusions.json が読めない。

**原因**  
- JSON が **UTF-8 BOM付き**で保存されている

**対処**  
- エディタ保存時に「UTF-8（BOMなし）」で保存  
- もしくは読み込み側を `utf-8-sig` にする（BOM許容）

**予防（仕組み）**  
- 事前チェックで JSON を `utf-8-sig` で読み、BOMなら **BOM除去版を自動生成**して以後それを使う  
"@

Ensure-Section "PowerShellで >> のまま終わらない（行継続ミス）" $bodyA
Ensure-Section "mandatory_docs_guard DocsDir 引数なし（MissingArgument）" $bodyB
Ensure-Section "Join-Path ChildPath が Object[]（配列）で失敗 / predScripts not found" $bodyC
Ensure-Section "exclusions.json が UTF-8 BOM で JSONDecodeError" $bodyD

Write-Host "[OK] updated: $File" -ForegroundColor Green
