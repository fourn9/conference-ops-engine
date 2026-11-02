---
description: 確定済みの登壇テーマで登壇候補のディープリサーチを回し、確定/保留候補を出典付きで出す
argument-hint: <確定済みの登壇テーマ>
---

# /speaker-deep-research <テーマ>

`speaker-deep-research` スキルを起動する。事前に確定したテーマ（自然文）を渡すと、
テーマ×角度の並列探索＋候補別ゲート検証（speaker-deep-research Workflow）を回し、
`<event>/02-speakers/` に確定/保留候補を md+tsv で出力する。

## 動作
1. PREFLIGHT 4点（テーマ確定／コアターゲット近接／既出名簿／ゲート判別ルール）を確認（停止点）
2. 確認後に探索角度・gateFRules・excluded を組み立て、speaker-deep-research Workflow を起動
3. 確定/保留リストを md+tsv で出力し、件数と未検証候補(dropped)を報告

## 引数
- `<テーマ>` — 事前議論で確定した登壇テーマ（例：「認証認可・ゼロトラストの実装当事者」）

## 注意
- テーマが未確定なら探索に入らない（先にテーマを固める）
- 当事者発信に絞る（解説・他社事例まとめは不採用）。判定の正典は methodology / 公開版の方法論
- 実 Web リサーチで複数エージェントが走る（コスト発生）
