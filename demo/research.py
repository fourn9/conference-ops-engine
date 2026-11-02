#!/usr/bin/env python3
"""Offline, synthetic demonstration of evidence-gated conference research."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import json
from pathlib import Path
import sys
from urllib.parse import urlparse


def evaluate(candidate, topic, insights, excluded, as_of):
    """Evaluate recorded evidence; this function does not verify live sources."""
    candidate_id = candidate.get("id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("Every candidate needs a non-empty string id")
    evidence = candidate.get("evidence", {})
    if not isinstance(evidence, dict):
        raise ValueError("Candidate evidence must be an object")
    rejected, pending = [], []
    if candidate_id in excluded:
        rejected.append("excluded by the event owner")
    for key, label in (("author_matches", "authorship"), ("first_hand", "first-hand experience")):
        value = evidence.get(key)
        if value is False:
            rejected.append(label + " check failed")
        elif value is not True:
            pending.append(label + " not checked")
    if candidate.get("topic_fit") is False:
        rejected.append("outside the topic")
    elif candidate.get("topic_fit") is not True:
        pending.append("topic fit not checked")

    url = evidence.get("url", "")
    try:
        parsed = urlparse(url) if isinstance(url, str) else None
        valid_url = (parsed is not None and parsed.scheme == "https"
                     and parsed.hostname == "example.org" and not parsed.username
                     and not parsed.password and parsed.port in (None, 443))
    except ValueError:
        valid_url = False
    if not valid_url:
        pending.append("missing or invalid synthetic source URL")
    if evidence.get("body_reviewed") is not True:
        pending.append("source body not reviewed")
    try:
        checked = date.fromisoformat(evidence.get("checked_at", ""))
        age = (as_of - checked).days
        if age < 0 or age > 30:
            pending.append("source check is future-dated or older than 30 days")
    except (TypeError, ValueError):
        pending.append("source check date missing or invalid")
    insight = candidate.get("insight_ref")
    if not isinstance(insight, str) or insight not in insights:
        pending.append("no link to a recorded audience interview")

    status = "rejected" if rejected else "pending" if pending else "ready_for_review"
    return {"id": candidate_id, "name": candidate.get("name", candidate_id),
            "topic": topic, "status": status, "reasons": rejected + pending,
            "source": url if valid_url else None, "insight_ref": insight,
            "final_selection": "requires human approval"}


def run(data):
    if not isinstance(data, dict) or data.get("synthetic") is not True:
        raise ValueError("This public demo accepts explicitly synthetic fixtures only")
    try:
        as_of = date.fromisoformat(data["as_of"])
        interviews = data["interviews"]
        batches = data["research_batches"]
        if not isinstance(interviews, list) or not isinstance(batches, list):
            raise ValueError("interviews and research_batches must be arrays")
        insights = {entry["id"] for entry in interviews if entry.get("summary", "").strip()}
        excluded = set(data.get("excluded_ids", []))
        for batch in batches:
            if not isinstance(batch.get("topic"), str) or not batch["topic"].strip():
                raise ValueError("Every research batch needs a topic")
            if not isinstance(batch.get("candidates"), list):
                raise ValueError("Every research batch needs a candidates array")
            if not all(isinstance(c, dict) for c in batch["candidates"]):
                raise ValueError("Each candidate must be an object")
    except (KeyError, TypeError, AttributeError) as error:
        raise ValueError("Malformed research fixture") from error

    def process(batch):
        return [evaluate(c, batch["topic"], insights, excluded, as_of)
                for c in batch["candidates"]]

    # Independent topic batches can run concurrently. No model or network calls.
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(process, batches))
    rows = [row for batch in results for row in batch]
    # Preserve conflicting evidence: repeated records remain visible for review.
    counts = {}
    for row in rows:
        key = (row["id"], row["topic"])
        counts[key] = counts.get(key, 0) + 1
    for row in rows:
        if counts[(row["id"], row["topic"])] > 1:
            row["reasons"].append("duplicate candidate/topic: reconcile evidence")
            if row["status"] == "ready_for_review":
                row["status"] = "pending"
    statuses = ("ready_for_review", "pending", "rejected")
    return {"synthetic": True, "as_of": data["as_of"], "live_sources_checked": False,
            "counts": {s: sum(r["status"] == s for r in rows) for s in statuses},
            "candidates": rows}


def markdown(report):
    lines = ["# Synthetic research review", "",
             "Offline fixture; no live research or invitations were performed.", ""]
    for status, count in report["counts"].items():
        lines.append("- {}: {}".format(status, count))
    for row in report["candidates"]:
        lines += ["", "## {} / {}".format(row["name"], row["topic"]), "",
                  "Status: **{}**".format(row["status"]), "",
                  "- Source: {}".format(row["source"] or "not available"),
                  "- Interview: {}".format(row["insight_ref"] or "not available")]
        lines += ["- " + reason for reason in row["reasons"]]
        lines += ["", "Final selection: requires human approval."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", type=Path,
                        default=Path(__file__).parent / "fixture.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = run(json.loads(args.fixture.read_text(encoding="utf-8")))
    except (OSError, ValueError) as error:
        parser.exit(2, "Error: {}\n".format(error))
    sys.stdout.write(json.dumps(report, indent=2) + "\n" if args.json else markdown(report))


if __name__ == "__main__":
    main()
