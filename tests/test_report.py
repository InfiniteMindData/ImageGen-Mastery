import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from imagegen_mastery.reporting import make_report


class ReportTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.left, self.right = self.root / "blue.png", self.root / "changed.png"
        image = Image.new("RGB", (32, 32), "blue")
        image.save(self.left)
        image.paste("white", (0, 0, 16, 16))
        image.save(self.right)

    def test_localizes_known_difference_and_writes_review_bundle(self):
        out = self.root / "report"
        result = make_report(self.right, self.left, out, ssim=True, perceptual=True,
                             regions=[[0, 0, .5, .5], [.5, .5, 1, 1]])
        self.assertLess(result["regions"][0]["ssim"], 1)
        self.assertEqual(result["regions"][1]["ssim"], 1)
        self.assertGreater(result["frame"]["dhash_distance"], 0)
        self.assertEqual(result["visual_inspection"], "unassessed")
        for filename in ("preview.png", "changes.png", "report.html", "report.json"):
            self.assertTrue((out / filename).is_file())
        self.assertEqual(json.loads((out / "report.json").read_text()), result)

    def test_ocr_escapes_text_and_preserves_case(self):
        with patch("imagegen_mastery.reporting.recognize", return_value="OPEN\n<script>"):
            result = make_report(self.right, self.left, self.root / "out", required_text=["OPEN", "Open", "<script>"])
        self.assertEqual([x["found"] for x in result["frame"]["ocr"]["checks"]], [True, False, True])
        self.assertNotIn("<script>", (self.root / "out" / "report.html").read_text())

    def test_refuses_empty_region_and_existing_destination(self):
        with self.assertRaises(ValueError):
            make_report(self.left, self.right, self.root / "report", regions=[[0, 0, 0, 1]])
        with self.assertRaises(FileExistsError):
            make_report(self.left, self.right, self.root)

