#!/usr/bin/env python3
"""趣意書 Google Doc を テンプレからコピーして 5 空欄＋氏名/所属を埋める。

- ネットワークは curl 経由（gcloud token + Drive/Docs API）。Python 直 HTTPS は使わない。
- 本文の 5 空欄は見出しをアンカーに各セクション直後の `〇` を含む段落を特定し、段落本文を
  丸ごと置換（末尾 \\n は残す）。インデックスずれ回避のため末尾から適用。
- タイトル行 `株式会社〇〇 〇〇様` は replaceAllText で所属/氏名に差し替え（本文編集の後に実行）。
- content の「・」始まり行は apply_bullets で Google Docs ネイティブ箇条書きに自動変換する
  （「・」文字は削除）。content 側は従来どおり行頭「・」で書けばよい。

使い方:
  # テンプレからコピーして作成（推奨・自動コピー）
  python3 fill_prospectus.py --from-template <TEMPLATE_ID> \\
      --company "サンプル株式会社" --name "サンプル太郎" \\
      --content content.json [--apply]

  # 既存 Doc を直接埋める
  python3 fill_prospectus.py --doc <DOC_ID> \\
      --company "..." --name "..." --content content.json [--apply]

content.json のキー: participants / challenges / theme / background / points
"""
import argparse
import json
import subprocess
import sys

ANCHORS = [
    ("participants", "ご参加者について"),
    ("challenges", "ご参加者が直面している課題"),
    ("theme", "登壇テーマイメージ"),
    ("background", "ご登壇依頼とご依頼背景"),
    ("points", "具体的に伺いたい論点"),  # 冒頭「ご相談内容について」と衝突しない一意な文字列
]
PLACEHOLDER = "〇"
# テンプレのタイトル行トークン（順に置換。1つ目で「株式会社〇〇」の〇を消費）
TITLE_TOKENS = ["株式会社〇〇", "〇〇様"]


def sh(args, inp=None):
    return subprocess.run(args, capture_output=True, text=True, input=inp)


def token():
    r = sh(["gcloud", "auth", "print-access-token"])
    if r.returncode != 0:
        sys.exit("gcloud token error: " + r.stderr.strip())
    return r.stdout.strip()


def api_get(url, tok):
    r = sh(["curl", "-s", "-H", f"Authorization: Bearer {tok}", url])
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit("GET failed: " + r.stdout[:300])


def api_post(url, tok, body):
    r = sh(["curl", "-s", "-X", "POST", "-H", f"Authorization: Bearer {tok}",
            "-H", "Content-Type: application/json", "--data-binary", "@-", url], inp=body)
    try:
        resp = json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit("POST failed: " + r.stdout[:300])
    if "error" in resp:
        sys.exit("API error: " + json.dumps(resp["error"], ensure_ascii=False))
    return resp


def get_doc(doc_id, tok):
    return api_get(f"https://docs.googleapis.com/v1/documents/{doc_id}?fields=body", tok)


def copy_template(template_id, name, tok):
    # テンプレが共有ドライブにある場合に備え、supportsAllDrives を付け、
    # テンプレと同じ親フォルダ（共有ドライブ）へ複製する（未指定だと 404 / My Drive 直下に逃げる）。
    meta = api_get(
        f"https://www.googleapis.com/drive/v3/files/{template_id}?fields=parents&supportsAllDrives=true", tok)
    body = json.dumps({"name": name, "parents": meta.get("parents", [])}, ensure_ascii=False)
    resp = api_post(f"https://www.googleapis.com/drive/v3/files/{template_id}/copy?supportsAllDrives=true",
                    tok, body)
    return resp["id"]


def paragraphs(doc):
    out = []
    for e in doc.get("body", {}).get("content", []):
        p = e.get("paragraph")
        if not p:
            continue
        txt = "".join(r.get("textRun", {}).get("content", "")
                      for r in p.get("elements", []) if "textRun" in r)
        out.append((e["startIndex"], e["endIndex"], txt))
    return out


def find_targets(paras):
    targets = {}
    for key, anchor in ANCHORS:
        ai = next((i for i, (s, e, t) in enumerate(paras) if anchor in t), None)
        if ai is None:
            continue
        for j in range(ai + 1, len(paras)):
            s, e, t = paras[j]
            if any(next_anchor in t for _, next_anchor in ANCHORS):
                break
            if PLACEHOLDER in t:
                targets[key] = (s, e)
                break
    return targets


def fill_sections(doc_id, content, tok):
    """5 空欄を index ベースで丸ごと置換（末尾から適用）"""
    paras = paragraphs(get_doc(doc_id, tok))
    targets = find_targets(paras)
    missing = [k for k, _ in ANCHORS if k not in targets]
    if missing:
        sys.exit("placeholder 未検出: " + ", ".join(missing)
                 + "\n（テンプレに 〇〇 が残っているか、見出し文言を確認）")
    reqs = []
    for key, (s, e) in sorted(targets.items(), key=lambda kv: -kv[1][0]):
        txt = content.get(key)
        if txt is None:
            print(f"  [skip] {key}: content に無し")
            continue
        reqs.append({"deleteContentRange": {"range": {"startIndex": s, "endIndex": e - 1}}})
        reqs.append({"insertText": {"location": {"index": s}, "text": txt}})
    resp = api_post(f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
                    tok, json.dumps({"requests": reqs}, ensure_ascii=False))
    print(f"  本文: {len(resp.get('replies', []))} replies")


def apply_bullets(doc_id, tok, preset="BULLET_DISC_CIRCLE_SQUARE"):
    """本文中の「・」始まり段落を Google Docs ネイティブ箇条書きに変換する。
    ①連続する「・」段落を run にまとめ createParagraphBullets（テキスト長は不変）
    ②再取得して各段落先頭の「・」1文字を末尾から削除（インデックスずれ回避）。"""
    paras = paragraphs(get_doc(doc_id, tok))
    runs, cur = [], []
    for s, e, t in paras:
        if t.startswith("・"):
            cur.append((s, e))
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    if not runs:
        return
    reqs = [{"createParagraphBullets": {
        "range": {"startIndex": r[0][0], "endIndex": r[-1][1] - 1},
        "bulletPreset": preset}} for r in runs]
    api_post(f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
             tok, json.dumps({"requests": reqs}, ensure_ascii=False))
    paras = paragraphs(get_doc(doc_id, tok))
    dels = [{"deleteContentRange": {"range": {"startIndex": s, "endIndex": s + 1}}}
            for s, e, t in sorted(paras, key=lambda x: -x[0]) if t.startswith("・")]
    api_post(f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
             tok, json.dumps({"requests": dels}, ensure_ascii=False))
    print(f"  箇条書き: {sum(len(r) for r in runs)} 段落 / {len(runs)} run をネイティブ化")


def fill_title(doc_id, company, name, tok):
    """タイトル行の所属/氏名トークンを replaceAllText（本文編集の後に呼ぶこと）"""
    repls = [(TITLE_TOKENS[0], company), (TITLE_TOKENS[1], name + "様")]
    reqs = [{"replaceAllText": {"containsText": {"text": old, "matchCase": True},
                                "replaceText": new}} for old, new in repls]
    resp = api_post(f"https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate",
                    tok, json.dumps({"requests": reqs}, ensure_ascii=False))
    changed = sum(r.get("replaceAllText", {}).get("occurrencesChanged", 0) for r in resp.get("replies", []))
    print(f"  タイトル: {changed} occurrences changed")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--from-template", help="テンプレ Doc ID（コピーして新規作成）")
    g.add_argument("--doc", help="既存 Doc ID（直接編集）")
    ap.add_argument("--content", required=True, help="content JSON のパス")
    ap.add_argument("--company", required=True, help="所属（正式名。例 サンプル株式会社）")
    ap.add_argument("--name", required=True, help="氏名（様は付けない）")
    ap.add_argument("--title", help="新規 Doc のファイル名（省略時 '<company> <name>様＿特別ご登壇依頼'）")
    ap.add_argument("--apply", action="store_true", help="付けると実書き込み")
    a = ap.parse_args()

    with open(a.content, encoding="utf-8") as source:
        content = json.load(source)
    doc_name = a.title or f"{a.company} {a.name}様＿特別ご登壇依頼"

    if not a.apply:
        print("DRY-RUN（書き込みなし）")
        if a.from_template:
            print(f"  テンプレ {a.from_template} を複製 → '{doc_name}'")
        else:
            print(f"  既存 Doc {a.doc} を編集")
        print(f"  所属='{a.company}' 氏名='{a.name}様'")
        for key, _ in ANCHORS:
            print(f"  section {key:12s} content={'有' if content.get(key) else '無'}")
        print("--apply で実行。")
        return

    tok = token()
    doc_id = copy_template(a.from_template, doc_name, tok) if a.from_template else a.doc
    if a.from_template:
        print(f"複製作成: {doc_id}")
    fill_sections(doc_id, content, tok)   # 先に本文（index ベース）
    apply_bullets(doc_id, tok)            # 「・」をネイティブ箇条書きに変換（タイトル編集前）
    fill_title(doc_id, a.company, a.name, tok)  # 後にタイトル（text ベース）

    # 検証
    full = "".join(t for _, _, t in paragraphs(get_doc(doc_id, tok)))
    remaining = full.count(PLACEHOLDER)
    print(f"残存 〇: {remaining}")
    print(f"URL: https://docs.google.com/document/d/{doc_id}/edit")
    sys.exit(0 if remaining == 0 else 2)


if __name__ == "__main__":
    main()
