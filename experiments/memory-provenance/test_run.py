import copy
import json
import unittest

import run


class MemoryStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((run.HERE / "case_study.json").read_text())

    def test_fixed_design_and_annotations(self):
        run.validate(self.data)
        self.assertEqual(len(self.data["conversations"]), 12)
        self.assertEqual(len(self.data["queries"]), 8)
        self.assertEqual(sum(len(q["gold"]["eligible"]) for q in self.data["queries"]), 13)

    def test_duplicate_or_missing_labels_are_rejected(self):
        data = copy.deepcopy(self.data)
        data["queries"][0]["gold"]["eligible"].append("m01")
        with self.assertRaisesRegex(ValueError, "partition"):
            run.validate(data)
        data["queries"][0]["gold"]["eligible"].pop()
        data["queries"][0]["gold"]["superseded"].clear()
        with self.assertRaisesRegex(ValueError, "partition"):
            run.validate(data)

    def test_exact_cosine_and_tie_break(self):
        memories = [
            {"id": "b", "date": "2026-01-01", "source": "fish"},
            {"id": "a", "date": "2026-01-01", "source": "fish"},
            {"id": "c", "date": "2026-01-01", "source": "hotel"},
        ]
        result = run.rank(memories, {"text": "fish", "date": "2026-10-26"})
        self.assertEqual(result, [("a", 1.0), ("b", 1.0)])

    def test_future_and_zero_overlap_cues_are_not_ranked(self):
        memories = [{"id": "x", "date": "2027-01-01", "source": "fish"}]
        self.assertEqual(run.rank(memories, {"text": "fish", "date": "2026-10-26"}), [])
        self.assertEqual(run.rank(self.data["conversations"], {
            "text": "xyzzy", "date": "2026-10-26",
        }), [])

    def test_metadata_control_does_not_read_gold(self):
        by_id = {m["id"]: m for m in self.data["conversations"]}
        for query in self.data["queries"]:
            expected = set(query["gold"]["eligible"])
            without_gold = {key: value for key, value in query.items() if key != "gold"}
            actual = {key for key, value in by_id.items() if run.permitted(value, without_gold, by_id)}
            self.assertEqual(actual, expected)

    def test_update_only_applies_after_replacement_date(self):
        by_id = {m["id"]: m for m in self.data["conversations"]}
        query = dict(self.data["queries"][0], date="2026-02-01")
        self.assertTrue(run.permitted(by_id["m01"], query, by_id))
        self.assertFalse(run.permitted(by_id["m06"], query, by_id))
        query["date"] = "2026-10-26"
        self.assertFalse(run.permitted(by_id["m01"], query, by_id))
        self.assertTrue(run.permitted(by_id["m06"], query, by_id))

    def test_expected_nonuse_and_denominators(self):
        details, summary = run.evaluate(self.data)
        for row in summary:
            records = [r for r in details if
                       r["method"] == row["method"] and r["budget"] == row["budget"]]
            self.assertEqual(sum(row[c] for c in run.CATEGORIES), row["selected"])
            self.assertEqual(len(records), row["selected"])
            self.assertEqual(row["eligible_total"], 13)
            self.assertEqual(row["nonuse_queries"], 1)
            self.assertLessEqual(row["selected"], row["budget"] * 8)
            if row["method"] == "metadata_control":
                self.assertEqual(row["correct_nonuse"], 1)
                self.assertEqual(row["selected"], row["eligible"])
            else:
                self.assertEqual(row["correct_nonuse"], 0)

    def test_results_are_deterministic(self):
        self.assertEqual(run.evaluate(self.data), run.evaluate(self.data))

    def test_fixed_results_match_reported_counts(self):
        _, summary = run.evaluate(self.data)
        expected = {
            ("lexical", 1): (7, 0, 0, 1, 0),
            ("lexical", 2): (8, 0, 3, 4, 0),
            ("lexical", 4): (10, 1, 5, 7, 1),
            ("lexical", 8): (11, 3, 10, 9, 3),
            ("metadata_control", 1): (7, 0, 0, 0, 0),
            ("metadata_control", 2): (10, 0, 0, 0, 0),
            ("metadata_control", 4): (13, 0, 0, 0, 0),
            ("metadata_control", 8): (13, 0, 0, 0, 0),
        }
        for row in summary:
            self.assertEqual(
                tuple(row[category] for category in run.CATEGORIES),
                expected[(row["method"], row["budget"])],
            )

    def test_zero_selections_have_undefined_precision(self):
        data = copy.deepcopy(self.data)
        for query in data["queries"]:
            query["text"] = "xyzzy"
        details, summary = run.evaluate(data)
        self.assertEqual(details, [])
        for row in summary:
            self.assertIsNone(row["precision"])
            self.assertEqual(row["recall"], 0)
            self.assertEqual(row["correct_nonuse"], 1)


if __name__ == "__main__":
    unittest.main()
