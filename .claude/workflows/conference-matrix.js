// カンファレンス企画 3Dリサーチ Matrix A+B 自動充填（公開版の方法論）
//
// 使い方（Workflow ツールから起動。SKILL.md が args を組み立てる）:
//   Workflow({ name: "conference-matrix", args: {
//     today: "YYYY-MM-DD",          // 必須（Workflow 内で Date は使えない）
//     event: "QA向けオンラインカンファ2026",  // 必須
//     scale: ["ベンチャー/スタートアップ", "メガベンチャー", "IT大手"], // 必須：規模セグメント
//     roles: ["BE-FS","TL","EM","SRE","INFRA","SECURITY"],                  // 必須：職種行
//     sourceGuardA: "Matrix A の出典は IR/適時開示/中計/公式リリースに限定。技術ブログ不可。", // 必須
//   }})
// 返り値は { matrixA, matrixB, searched_sources }。整形・出力は呼び出し側（SKILL.md）。

export const meta = {
  name: 'conference-matrix',
  description: 'カンファレンス企画 3Dリサーチ：Matrix A(規模×目的) と Matrix B(職種×目的) を出典付き自動充填',
  whenToUse: 'conference-matrix スキルが軸確認後に Matrix A/B を埋めるとき',
  phases: [
    { title: 'MatrixA', detail: '規模セグメント×目的を IR限定探索で活動レベル判定' },
    { title: 'MatrixB', detail: '職種×目的を4セクション構造＋採否ゲートで充填' },
  ],
}

// args は呼び出し系によっては JSON 文字列で渡る場合があるため正規化する
let ARGS
try {
  ARGS = (args && typeof args === 'string') ? JSON.parse(args) : (args || {})
} catch (e) {
  throw new Error('args の JSON 解析に失敗（文字列で渡す場合は正しい JSON にすること）: ' + e.message)
}
if (!ARGS.today || !ARGS.event || !ARGS.scale || !ARGS.roles || !ARGS.sourceGuardA) {
  throw new Error('args に today / event / scale / roles / sourceGuardA が必要（ファイル冒頭の使い方コメント参照）')
}
if (!Array.isArray(ARGS.scale) || !ARGS.scale.length || !Array.isArray(ARGS.roles) || !ARGS.roles.length || ![...ARGS.scale, ...ARGS.roles].every(x => typeof x === 'string' && x.trim())) throw new Error('scale and roles must be non-empty string arrays')
if (typeof ARGS.today !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(ARGS.today)) throw new Error('today must be YYYY-MM-DD')
const SINCE = ARGS.since || ARGS.today.slice(0, 4) + '-01-01'
const TODAY = ARGS.today
const EVENT = ARGS.event
const SCALE = ARGS.scale
const ROLES = ARGS.roles
const GUARD_A = ARGS.sourceGuardA
const PURPOSES = ['P1立上', 'P2拡張', 'P3統合', 'P4刷新', 'P5 AI組込', 'P6 AIネイティブ']

const A_ROW_SCHEMA = {
  type: 'object',
  properties: {
    segment: { type: 'string' },
    cells: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          purpose: { type: 'string', description: 'P1立上〜P6 AIネイティブ のいずれか' },
          level: { type: 'string', description: '活動レベル ◎/○/△/× のいずれか' },
          evidence: { type: 'string', description: '判定根拠（IR/中計/開示の記述。40-80字）' },
          url: { type: 'string', description: 'IR/適時開示/中計/公式リリースのURL。技術ブログ不可' },
          crosscheck_needed: { type: 'boolean', description: 'claude.ai裏取り推奨か（一次情報が弱い場合true）' },
        },
        required: ['purpose', 'level', 'evidence', 'url', 'crosscheck_needed'],
      },
    },
    sources: { type: 'array', items: { type: 'string' } },
  },
  required: ['segment', 'cells', 'sources'],
}

const B_ROW_SCHEMA = {
  type: 'object',
  properties: {
    role: { type: 'string' },
    cells: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          purpose: { type: 'string' },
          issue: { type: 'string', description: '課題 What（番号付き縦対応・箇条書き）' },
          background: { type: 'string', description: '背景 Where-When-How（issueと同じ番号で対応）' },
          reason: { type: 'string', description: '理由 Why仮説（同番号で対応）' },
          to_explore: { type: 'string', description: '知りたいこと What-to-explore（同番号。ヒアリング質問化しない）' },
          sources: { type: 'array', items: { type: 'string' }, description: '当事者発信の一次情報URL' },
          gate_pass: { type: 'boolean', description: '採否ハードゲート7条件を満たすか' },
        },
        required: ['purpose', 'issue', 'background', 'reason', 'to_explore', 'sources', 'gate_pass'],
      },
    },
    gate_notes: { type: 'string', description: 'ゲート判定の補足（除外した隣接職種・会社単位判断の回避等）' },
  },
  required: ['role', 'cells', 'gate_notes'],
}

phase('MatrixA')
log(`Matrix A: ${SCALE.length}セグメント × ${PURPOSES.length}目的 を探索`)

const aRows = await parallel(SCALE.map(seg => () =>
  agent(`イベント「${EVENT}」の企画のため、企業規模セグメント「${seg}」の注力フェーズを判定する。本日: ${TODAY}。

目的軸（各セルの活動レベル ◎○△× を判定）:
${PURPOSES.map(p => `- ${p}`).join('\n')}

${GUARD_A}

ルール（厳守）:
- 出典は IR資料・適時開示・中期経営計画・公式ニュースリリースに限定。技術ブログ・登壇スライド・個人記事は不可（失敗1ガード）。
- 各セルに活動レベル（◎=注力/○=取組/△=限定/×=なし）と判定根拠・URLを付す。
- 一次情報が弱く推測が混じる場合は crosscheck_needed=true（claude.ai裏取り推奨）。
- 実在しないURL・記述の創作は重大違反。確認できないセルは level=× とし evidence に「一次情報なし」と書く。
- 必ず WebFetch で本文を開いてから判定する。
返答は StructuredOutput で返す。`, { label: `A:${seg}`, phase: 'MatrixA', schema: A_ROW_SCHEMA })
    .then(r => r ? ({ ...r, segment: seg }) : null)
))

const matrixA = {}
const aSources = []
for (const r of aRows.filter(Boolean)) {
  matrixA[r.segment] = { cells: r.cells || [], sources: r.sources || [] }
  aSources.push(...(r.sources || []))
}
const aDropped = SCALE.filter(s => !matrixA[s])
if (aDropped.length) log('Matrix A 欠落（探索失敗）: ' + aDropped.join('、'))
log('Matrix A 完了: ' + Object.keys(matrixA).length + 'セグメント')

phase('MatrixB')
log(`Matrix B: ${ROLES.length}職種 × ${PURPOSES.length}目的 を充填`)

const GATE_RULES = `
採否ハードゲート7条件（methodology/conference-planning-framework.md 4.6 / 公開版の方法論。全条件充足のみ gate_pass=true）:
- G1 執筆者の職種が特定可能 / G2 所属プロダクト（事業ユニット粒度）のフェーズ特定可能
- G3 「自社プロダクトでの」アーキ判断・実装を含む（業界トレンド解説・他社事例まとめ・概念紹介は不可）
- G4 著者の権威性・記事実在・対象期間（${SINCE}以降） / G5 職種カテゴリ厳密適合（隣接職種は当該行に入れない）
- G6 タイトル・サービス名と内容の一致 / G7 検索の深さ（キーワード表層一致での採用禁止）
4セクション規律: 課題/背景/理由/知りたいこと を番号付きで縦対応させる（失敗2/6ガード）。
「知りたいこと」はヒアリング質問にしない（失敗3）。特定企業の事例名で書かない（失敗4）。`

const bRows = await parallel(ROLES.map(role => () =>
  agent(`イベント「${EVENT}」の Matrix B「${role} × P1-P6」を充填する。本日: ${TODAY}。

目的軸: ${PURPOSES.join(' / ')}

各セル（職種×目的）を4セクション構造で書く:
1. 課題 What（その職種がそのフェーズで直面する技術課題。番号付き箇条書き）
2. 背景 Where-When-How（課題が生じる状況。課題と同じ番号で対応）
3. 理由 Why仮説（なぜ課題になるかの仮説。同番号で対応）
4. 知りたいこと What-to-explore（セッションで掘りたい論点。同番号。＝セッションテーマ素材）

${GATE_RULES}

ルール（厳守）:
- 根拠は当該職種の当事者（${role}本人）が自社プロダクトについて書いた一次情報に限る。
- WebFetch で本文を確認し、URLを sources に入れる。実在しないURLの創作は重大違反。
- ゲート7条件を満たさないセルは gate_pass=false とし、知りたいことのみ仮説で残す。
- 除外した隣接職種・会社単位判断の回避を gate_notes に記す。
返答は StructuredOutput で返す。`, { label: `B:${role}`, phase: 'MatrixB', schema: B_ROW_SCHEMA })
    .then(r => r ? ({ ...r, role }) : null)
))

const matrixB = {}
const bSources = []
for (const r of bRows.filter(Boolean)) {
  matrixB[r.role] = { cells: r.cells || [], gate_notes: r.gate_notes || '' }
  bSources.push(...(r.cells || []).flatMap(c => c.sources || []))
}
const bDropped = ROLES.filter(rl => !matrixB[rl])
if (bDropped.length) log('Matrix B 欠落（探索失敗）: ' + bDropped.join('、'))
log('Matrix B 完了: ' + Object.keys(matrixB).length + '職種')

return { matrixA, matrixB, searched_sources: [...aSources, ...bSources] }
