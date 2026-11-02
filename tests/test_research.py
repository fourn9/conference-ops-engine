import copy
from datetime import date
import json
from pathlib import Path
import unittest

from demo.research import evaluate, run


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((Path(__file__).parents[1] / "demo/fixture.json").read_text())
        self.candidate = copy.deepcopy(self.fixture["research_batches"][0]["candidates"][0])

    def check_candidate(self, candidate=None, excluded=()):
        return evaluate(candidate or self.candidate, "demo", {"interview-demo-01"},
                        set(excluded), date(2030, 4, 15))

    def test_demo_outcomes(self):
        report = run(self.fixture)
        self.assertEqual(report["counts"], {"ready_for_review": 1, "pending": 2, "rejected": 1})
        self.assertFalse(report["live_sources_checked"])
        self.assertTrue(all(r["final_selection"] == "requires human approval" for r in report["candidates"]))

    def test_missing_evidence_never_passes(self):
        self.candidate["evidence"] = {}
        self.assertEqual(self.check_candidate()["status"], "pending")

    def test_strings_do_not_count_as_boolean_checks(self):
        self.candidate["evidence"]["author_matches"] = "true"
        self.assertEqual(self.check_candidate()["status"], "pending")

    def test_exclusions_override_complete_evidence(self):
        self.assertEqual(self.check_candidate(excluded=["candidate-a"])["status"], "rejected")

    def test_missing_interview_never_passes(self):
        self.candidate["insight_ref"] = "unknown"
        self.assertEqual(self.check_candidate()["status"], "pending")

    def test_stale_future_and_bad_dates(self):
        for value in ("2029-01-01", "2031-01-01", "bad", None):
            with self.subTest(value=value):
                self.candidate["evidence"]["checked_at"] = value
                self.assertEqual(self.check_candidate()["status"], "pending")

    def test_url_boundary(self):
        for url in ("file:///etc/passwd", "https://example.org.evil.test/a",
                    "https://user:password@example.org/a", "https://[broken", "https://example.org:bad/a"):
            with self.subTest(url=url):
                self.candidate["evidence"]["url"] = url
                self.assertEqual(self.check_candidate()["status"], "pending")

    def test_duplicate_evidence_is_preserved_and_held(self):
        second = copy.deepcopy(self.candidate)
        second["evidence"]["author_matches"] = False
        self.fixture["research_batches"][0]["candidates"].append(second)
        results = [r for r in run(self.fixture)["candidates"] if r["id"] == "candidate-a"]
        self.assertEqual([r["status"] for r in results], ["pending", "rejected"])

    def test_invalid_fixtures(self):
        for value in ({}, [], {"synthetic": False}, {"synthetic": True}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                run(value)


if __name__ == "__main__":
    unittest.main()
