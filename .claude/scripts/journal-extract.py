#!/usr/bin/env python3
"""transcript jsonl から対話テキストを抽出する（session-journal 用）。

Claude Code の transcript 形式は内部仕様で非保証。壊れたらこのスクリプトを直す。
確認済みの行構造（v2.1.198）: type / sessionId / cwd / gitBranch / isSidechain / message

出力: 1行目にメタヘッダ、以降 USER:/ASSISTANT: の対話ターン。
exit 3 = 実ユーザーターンが閾値未満（トリビアルセッション。要約せず INDEX 記録のみ）
"""
import json
import sys

TURN_CHAR_LIMIT = 2000
TOTAL_CHAR_LIMIT = 60000
MIN_USER_TURNS = 3


def text_of(message):
    """message.content から表示テキストのみを取り出す（tool_use/tool_result/thinking は捨てる）"""
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
    return "\n".join(p for p in parts if isinstance(p, str) and p)


def main():
    if len(sys.argv) < 2:
        print("usage: journal-extract.py <transcript.jsonl>", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]

    turns = []
    meta = {"session": "", "cwd": "", "branch": ""}
    user_turns = 0

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict) or obj.get("isSidechain"):
                continue
            t = obj.get("type")
            if t not in ("user", "assistant"):
                continue
            text = text_of(obj.get("message") or {}).strip()
            if not text:
                continue
            if t == "user":
                # フック注入・コマンド出力・system-reminder 等（<xxx> で始まる）は実ユーザー発話でない
                if text.lstrip().startswith("<"):
                    continue
                user_turns += 1
            meta["session"] = meta["session"] or obj.get("sessionId", "")
            meta["cwd"] = meta["cwd"] or obj.get("cwd", "")
            meta["branch"] = meta["branch"] or obj.get("gitBranch", "")
            if len(text) > TURN_CHAR_LIMIT:
                text = text[:TURN_CHAR_LIMIT] + "\n[...切詰め...]"
            turns.append(("USER" if t == "user" else "ASSISTANT", text))

    header = (
        f"# session={meta['session']} cwd={meta['cwd']} "
        f"branch={meta['branch']} user_turns={user_turns}"
    )
    body = "\n\n".join(f"{role}:\n{text}" for role, text in turns)
    if len(body) > TOTAL_CHAR_LIMIT:
        head_len = TOTAL_CHAR_LIMIT // 5
        tail_len = TOTAL_CHAR_LIMIT - head_len
        body = body[:head_len] + "\n\n[...中略...]\n\n" + body[-tail_len:]

    print(header)
    print()
    print(body)

    if user_turns < MIN_USER_TURNS:
        sys.exit(3)


if __name__ == "__main__":
    main()
