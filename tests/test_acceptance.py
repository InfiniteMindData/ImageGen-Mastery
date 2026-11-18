import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from imagegen_mastery.acceptance import EditPolicy, check_candidate


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base, self.new = (Path(tmp.name) / s for s in ("base.png", "new.png"))
        self.img = Image.new("RGBA", (12, 12), "red")
        self.img.save(self.base)

    def check(self, policy):
        self.img.save(self.new)
        return check_candidate(self.new, policy, baseline=self.base, previous=self.base, bounds=[0, 0, .5, .5])

    def test_rejects_alpha_only_change_outside_edit(self):
        self.img.putpixel((10, 10), (255, 0, 0, 240))
        self.assertFalse(self.check(EditPolicy())["checks"]["outside_edit_unchanged"])

    def test_protected_region_inside_edit(self):
        self.img.putpixel((0, 0), (255, 1, 1, 255))
        result = self.check(EditPolicy(protected=((0., 0., .25, .25),)))
        self.assertFalse(result["checks"]["protected_regions_unchanged"])
        self.assertTrue(result["checks"]["outside_edit_unchanged"])

    @patch("imagegen_mastery.acceptance.recognize", return_value="Open")
    def test_ocr_and_expected_dimensions_are_independent(self, recognize):
        checks = self.check(EditPolicy(required_text=("OPEN",), expected_size=(10, 10)))["checks"]
        self.assertFalse(checks["required_text"])
        self.assertFalse(checks["expected_dimensions"])
        recognize.assert_called_once()
