param()

$ErrorActionPreference = "Stop"

$ROOT = "C:\work\boatrace"
$DOC  = Join-Path $ROOT "docs"

if (-not (Test-Path $DOC)) { throw "docs dir not found: $DOC" }

function Ensure-File {
  param([string]$Path, [string]$Content)
  if (-not (Test-Path $Path)) {
    $dir = Split-Path $Path -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -Path $Path -Encoding UTF8 -Value $Content
    Write-Host ("[delta] created: " + $Path) -ForegroundColor Green
  } else {
    Write-Host ("[delta] exists : " + $Path) -ForegroundColor DarkGray
  }
}

$sync = Join-Path $DOC "CHAT_SYNC_PROTOCOL.md"
$plog = Join-Path $DOC "PATCHLOG.md"

Ensure-File -Path $sync -Content @'
# CHAT⇄LOCAL 同期プロトコル（ドキュメント整合）

## 目的
- チャット切替での「情報欠落」「バージョン違い」「手戻り」をゼロにする。
- “気を付ける”ではなく、漏れたら先に進めない仕組みにする。

## 正本の扱い（重要）
- **新チャット開始時にアップされた HANDOVER_BUNDLE_*.zip** を、そのチャットの「参照正本」として扱う。
- 以後、そのチャットで発生した docs 更新は **必ず「ZIPパッチ」** で配布し、ローカルへ反映してから次へ進む。

## 新チャット開始（ユーザの作業：1回）
1) ローカルで `docs\generate_handover.ps1`（または bundle 生成 bat）を実行して  
   - `docs\HANDOVER.md`
   - `runs\HANDOVER_BUNDLE_*.zip`
   を作る  
2) 新チャット冒頭に
   - HANDOVER.md をコピペ
   - HANDOVER_BUNDLE_*.zip を添付
   する

> これが無いと、AIは「ローカルの正本」を確認できず、方針・ルールの抜け漏れが起きます。

## チャットで docs が新規作成/更新された時（ユーザの作業：毎回）
1) AIが出した **boatrace_*patch*.zip** をダウンロード  
2) `scripts\apply_chat_patch.ps1` を実行して反映（PATCHLOG も更新される）  
3) `docs\mandatory_docs_guard.ps1` があれば必ず通す（通らない変更は採用しない）  
4) 必要なら再度 bundle を生成して次チャットへ

## 典型的な不足ポイントと対策
- **チャットで新規作成したドキュメントのDL漏れ**  
  → AIは「ZIPパッチ以外で docs を更新した扱いにしない」。ユーザは apply_chat_patch で必ず反映。
- **チャットで更新したドキュメントのローカル反映漏れ**  
  → PATCHLOG で記録が残る。新チャットでは bundle 内の PATCHLOG を見て整合確認できる。
- **ローカルからチャットへのアップ漏れ**  
  → 毎回 HANDOVER_BUNDLE をアップする運用に固定（AI側は無い場合は必ず要求する）。

'@

Ensure-File -Path $plog -Content @'
# PATCHLOG（CHAT→LOCAL 反映ログ）

このファイルは「このチャットで作られた docs/スクリプト更新が、ローカルへ反映されたか」を追跡するためのログです。

- 追記は scripts\apply_chat_patch.ps1 が行う（手動追記は原則しない）。
- 新チャットでは、HANDOVER_BUNDLE に含まれる PATCHLOG を見て「未反映がないか」を確認できる。

## entries
'@

Write-Host "[delta] OK" -ForegroundColor Green
