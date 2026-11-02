---
name: conference-matrix
description: カンファレンス企画の3Dリサーチ。EVENT/SCALE/ROLES を受け取り、規模×目的(Matrix A)と職種×目的(Matrix B)を出典URL付きで自動充填し md+tsv で出力する。
---

# conference-matrix（3Dリサーチ Matrix A+B 自動充填）

`methodology/conference-planning-framework.md` の3Dフレームを実行系に落としたスキル。考え方の正典は
`methodology/conference-planning-framework.md`。本スキルは手を動かす実行系。

## パラメータ（メソッドコール）

| パラメータ | 説明 | 既定 |
|---|---|---|
| EVENT | イベント名・想定テーマ | 必須 |
| SCALE | 規模セグメント配列 | 非IT大手 / IT大手 / メガベンチャー / ベンチャー / スタートアップ（初期候補。イベントごとに調整） |
| ROLES | 職種行配列 | BE-FS / TL / EM / SRE / INFRA / SECURITY |
| OUTDIR | 出力先 | `<event>/01-planning/` |

未指定は実行前に確認する。

## 実行手順

### Step 1: 軸確認ゲート（必須・停止点）
既定の SCALE と ROLES を表で提示し、ユーザーの確認/修正を待つ。
承認が出るまで Workflow を起動しない。OUTDIR も提示して確認する。

### Step 2: Workflow 起動
確認済みの軸で `conference-matrix` Workflow を起動する:

```js
Workflow({ name: "conference-matrix", args: {
  today: "<本日 YYYY-MM-DD>",
  event: "<EVENT>",
  scale: [<確認済み SCALE>],
  roles: [<確認済み ROLES>],
  sourceGuardA: "Matrix A の出典は IR/適時開示/中計/公式リリースに限定。技術ブログ・登壇スライド・個人記事は不可。",
}})
```

### Step 3: 返り値を md+tsv に整形して出力
返り値 `{ matrixA, matrixB, searched_sources }` を OUTDIR に書き出す:
- `matrix-a.md` … 行=SCALE、列=P1-P6。各セルは「活動レベル＋根拠＋URL＋裏取りフラグ」
- `matrix-a.tsv` … 同内容のタブ区切り（Google Sheets 貼付用）
- `matrix-b-<role>.md` … 職種ごと。各セル4セクション（課題/背景/理由/知りたいこと）を番号付きで
- `matrix-b-<role>.tsv` … 同内容のタブ区切り
  - ファイル名の `<role>` は `/`・空白を `-` に置換してから使う（例：`BE/FS`→`BE-FS`）

各ファイル冒頭に実行メモを必ず付す:
- 実行系（conference-matrix workflow・本日日付）
- 未検証セルの扱い（探索失敗で欠落した segment/role、gate_pass=false・一次情報なしセル）
- 裏取り要否（Matrix A の crosscheck_needed=true セル一覧）
- ゲート不通過（Matrix B の gate_pass=false セル一覧）

### Step 4: 完了報告
出力ファイルのパス一覧と、裏取り推奨セル数・ゲート不通過セル数を報告する。

## メモ
- ゲート定義・失敗パターンは `methodology/conference-planning-framework.md` 4.6・7章を単一の出典とする（本スキルに重複コピーしない）。
- コアテーマ抽出・ヒートマップ・セッション構造化は本スキルの範囲外（別ステップ）。
- local/vault に依存しない。出力は必ずローカル OUTDIR。

`Workflow` ツールがない環境では `docs/workflows.md` の同梱ランナーを利用する。

接続先・保存先の共通設定は `docs/configuration.md` を参照。既にユーザーが明示した条件は再確認せず、その範囲で進める。
