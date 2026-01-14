# HANDOVER hardening（再発防止）

## 目的
チャット切替での「情報欠落・手戻り・世界線ズレ」をゼロにする。

## 使い方（あなたの作業）
1. docs 正本があるディレクトリで `generate_handover_bundle.bat` を実行  
2. `runs\HANDOVER_BUNDLE_*.zip` が生成される  
3. 新チャットの冒頭で
   - HANDOVER.md（コピペ）
   - HANDOVER_BUNDLE_*.zip（添付）
   を投入する

## 失敗時
- lint で落ちた場合：HANDOVER.md にログ（usage/Traceback/PS> 等）が混入している可能性が高いので、
  該当箇所を削除して再生成する（または docs 正本から再生成する）。
