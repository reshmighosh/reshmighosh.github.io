import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

import run


class RetrievalPlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((run.HERE / "case_study.json").read_text())
        _, cls.summary = run.evaluate(data)

    def test_seaborn_bar_segments_match_every_measured_count(self):
        from matplotlib.colors import to_hex

        figure = run.retrieval_figure(self.summary)
        try:
            self.assertEqual(len(figure.axes), 2)
            self.assertEqual(figure.axes[0].get_ylim(), figure.axes[1].get_ylim())
            for ax, method in zip(figure.axes, ("lexical", "metadata_control")):
                rows = [row for row in self.summary if row["method"] == method]
                actual = {}
                for bar in ax.patches:
                    center = round(bar.get_x() + bar.get_width() / 2)
                    category = next(
                        key for key in run.CATEGORIES
                        if run.COLORS[key] == to_hex(bar.get_facecolor())
                    )
                    actual[(center, category)] = (bar.get_y(), bar.get_height())
                for index, row in enumerate(rows):
                    bottom = 0
                    for category in run.CATEGORIES:
                        y, height = actual[(index, category)]
                        self.assertAlmostEqual(height, row[category])
                        self.assertAlmostEqual(y, bottom)
                        bottom += row[category]
                    self.assertEqual(bottom, row["selected"])
                self.assertEqual(
                    [label.get_text().splitlines()[0] for label in ax.get_xticklabels()],
                    ["k=1", "k=2", "k=4", "k=8"],
                )
        finally:
            figure.clear()

    def test_svg_is_accessible_and_byte_reproducible(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(run, "FIGURES", output):
                run.retrieval_chart(self.summary)
                svg = output / "02_retrieval_budget.svg"
                first = svg.read_bytes()
                run.retrieval_chart(self.summary)
                self.assertEqual(first, svg.read_bytes())
            root = ElementTree.fromstring(first)
            namespace = {"svg": "http://www.w3.org/2000/svg"}
            self.assertEqual(root.attrib["role"], "img")
            for reference in root.attrib["aria-labelledby"].split():
                self.assertIsNotNone(root.find(f".//*[@id='{reference}']"))
            self.assertIn("Seaborn", root.find("svg:desc", namespace).text)
            self.assertIn("max-width:100%", root.attrib["style"])
            self.assertNotIn(b"<script", first)


if __name__ == "__main__":
    unittest.main()
