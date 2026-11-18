import io
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from imagegen_mastery.workflow import run_loop


class LoopTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.start = self.root / "input.png"
        Image.new("RGB", (16, 16), "red").save(self.start)
        buf = io.BytesIO()
        Image.new("RGB", (16, 16), "blue").save(buf, format="PNG")
        self.edited = buf.getvalue()
        self.issue = {"observation": "Red top-left corner", "requirement": 0,
                      "bounds": [0, 0, .5, .5], "confidence": .95, "uncertainty": ""}
        self.brief = {"intent": "Blue top left.", "locked_attributes": ["Red bottom half."]}
        self.ok = {"defects": [], "uncertainties": [], "locks": [{"status": "met", "evidence": "Red bottom."}]}

    def run_case(self, **kwargs):
        opts = {"start": self.start, "budget": Decimal("8"), "max_revisions": 2, "authorized": True}
        return run_loop(self.brief, self.root / "run", **{**opts, **kwargs})

    @patch("imagegen_mastery.workflow.render")
    @patch("imagegen_mastery.workflow.inspect_image")
    def test_only_local_change_promoted_after_reinspection(self, inspect, render):
        inspect.side_effect = [{**self.ok, "defects": [self.issue]}, self.ok]
        render.return_value = self.edited
        result = self.run_case()
        self.assertEqual(result["status"], "no_observed_defects")
        self.assertEqual(result["accepted"], "v001.png")
        with Image.open(self.root / "run" / result["accepted"]) as out:
            self.assertEqual(out.getpixel((0, 0))[:3], (0, 0, 255))
            self.assertEqual(out.getpixel((15, 15))[:3], (255, 0, 0))
        self.assertEqual(inspect.call_count, 2)
        self.assertTrue((self.root / "run" / "v001-provider.png").is_file())
        self.assertEqual(len(result["requests"]), 3)

    @patch("imagegen_mastery.workflow.render")
    @patch("imagegen_mastery.workflow.inspect_image")
    def test_lock_regression_keeps_baseline(self, inspect, render):
        inspect.side_effect = [{**self.ok, "defects": [self.issue]},
                               {**self.ok, "locks": [{"status": "uncertain", "evidence": "Hidden."}]}]
        render.return_value = self.edited
        result = self.run_case()
        self.assertEqual(result["accepted"], "v000.png")
        self.assertEqual(result["status"], "lock_review_required")

    @patch("imagegen_mastery.workflow.render")
    @patch("imagegen_mastery.workflow.inspect_image")
    def test_no_budget_or_authorization_never_calls(self, inspect, render):
        with self.assertRaises(ValueError):
            self.run_case(authorized=False)
        result = self.run_case(budget=Decimal("0.01"), start=None)
        self.assertEqual(result["status"], "budget_limit")
        render.assert_not_called()
        inspect.assert_not_called()

    @patch("imagegen_mastery.workflow.render")
    @patch("imagegen_mastery.workflow.inspect_image")
    def test_uncertainty_and_iteration_limit(self, inspect, render):
        inspect.return_value = {**self.ok, "defects": [self.issue]}
        result = self.run_case(max_revisions=0)
        self.assertEqual(result["status"], "iteration_limit")
        render.assert_not_called()

    @patch("imagegen_mastery.workflow.inspect_image", side_effect=RuntimeError("secret error"))
    def test_failure_keeps_reservation_and_never_replays(self, inspect):
        with self.assertRaises(RuntimeError):
            self.run_case()
        journal = (self.root / "run" / "manifest.json").read_text()
        self.assertNotIn("secret error", journal)
        self.assertEqual(json.loads(journal)["requests"][-1]["status"], "unconfirmed")
        with self.assertRaises(FileExistsError):
            self.run_case()
        inspect.assert_called_once()

