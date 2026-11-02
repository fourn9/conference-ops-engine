---
description: カンファレンス企画の3Dリサーチ Matrix A+B を出典付きで自動充填する
argument-hint: <EVENT名・想定テーマ>
---

# /conference-matrix <EVENT>

`conference-matrix` スキルを起動する。EVENT（イベント名・想定テーマ）を渡すと、
規模×目的(Matrix A) と 職種×目的(Matrix B) を出典URL付きで自動充填し、
`<event>/01-planning/` に md+tsv で出力する。

## 動作
1. 既定の SCALE（規模5セグメント）と ROLES（BE-FS/TL/EM/SRE/INFRA/SECURITY）を提示し確認を取る
2. 確認後に conference-matrix Workflow を起動して探索・検証
3. md+tsv を出力し、裏取り推奨・ゲート不通過セルを報告

## 引数
- `<EVENT>` — イベント名・想定テーマ（例：「QA向けオンラインカンファ2026/12」）

## 注意
- Matrix A は IR/開示/中計/公式リリース限定（技術ブログ不可）
- 軸確認ゲートを通すまで探索は走らない
