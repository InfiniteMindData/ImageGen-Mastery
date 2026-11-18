import base64
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from PIL import Image

from imagegen_mastery.cli import main
from imagegen_mastery.providers import ProviderError
from imagegen_mastery.workflow import run_loop


class LoopTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.start = self.root / "input.png"
        Image.new("RGB", (16, 16), "red").save(self.start)
        self.issue = {"observation": "Red top-left corner", "requirement": 0,
                      "bounds": [0, 0, .5, .5], "confidence": .95, "uncertainty": ""}
        self.brief = {"intent": "Blue top left.", "locked_attributes": ["Red bottom half."]}
        self.ok = {"defects": [], "uncertainties": [], "locks": [{"status": "met", "evidence": "Red bottom."}]}
        self.corrected = {**self.ok, "resolution": {"status": "corrected", "before": "Red corner", "after": "Blue corner"}}
        env = patch.dict(os.environ, {"OPENAI_API_KEY": "test-vision", "GEMINI_API_KEY": "test-image"}, clear=True)
        env.start()
        self.addCleanup(env.stop)
        transport = patch("urllib.request.OpenerDirector.open")
        self.http = transport.start()
        self.addCleanup(transport.stop)
        self.http.side_effect = AssertionError("Unexpected HTTP call")

    def run_case(self, **kwargs):
        opts = {"start": self.start, "budget": "8", "max_revisions": 2, "authorized": True}
        return run_loop(self.brief, self.root / "run", **{**opts, **kwargs})

    @staticmethod
    def vision(review):
        body = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(review)}}]}
        return io.BytesIO(json.dumps(body).encode())

    @staticmethod
    def pixels(color, size=(16, 16)):
        out = io.BytesIO()
        Image.new("RGB", size, color).save(out, format="PNG")
        image = {"inlineData": {"mimeType": "image/png", "data": base64.b64encode(out.getvalue()).decode()}}
        return io.BytesIO(json.dumps({"candidates": [{"content": {"parts": [image]}}]}).encode())

    def revisions(self, final, *, first=None):
        self.http.side_effect = [self.vision({**self.ok, "defects": first or [self.issue]}),
                                 self.pixels("blue"), self.vision(final)]

    def test_only_local_change_promoted_after_reinspection(self):
        self.revisions(self.corrected)
        result = self.run_case()
        self.assertEqual(result["status"], "no_observed_defects")
        self.assertEqual(result["accepted"], "v001.png")
        with Image.open(self.root / "run" / result["accepted"]) as out:
            self.assertEqual(out.getpixel((0, 0))[:3], (0, 0, 255))
            self.assertEqual(out.getpixel((15, 15))[:3], (255, 0, 0))
        self.assertTrue((self.root / "run" / "v001-provider.png").is_file())
        self.assertEqual(len(result["requests"]), 3)
        self.assertEqual(result["reserved_usd"], "2.48")
        self.assertNotIn("test-vision", json.dumps(result))
        self.assertIn("Blue top left.", result["requests"][1]["prompt"])

    def test_cli_generate_inspect_edit_inspect(self):
        self.http.side_effect = [self.pixels("red"), self.vision({**self.ok, "defects": [self.issue]}),
                                 self.pixels("blue"), self.vision(self.corrected)]
        brief = self.root / "brief.json"
        brief.write_text(json.dumps(self.brief))
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["revise", str(brief), "--run-dir", str(self.root / "run"),
                                   "--max-revisions", "1", "--budget-usd", "4.52", "--authorize-paid"]), 0)
        manifest = json.loads(output.getvalue())
        self.assertEqual([x["operation"] for x in manifest["requests"]], ["generate", "inspect", "edit", "inspect"])
        self.assertEqual(manifest["reserved_usd"], "4.52")
        self.assertEqual(manifest["accepted"], "v001.png")

    def test_lock_regression_keeps_baseline(self):
        self.revisions({**self.corrected, "locks": [{"status": "uncertain", "evidence": "Hidden."}]})
        result = self.run_case()
        self.assertEqual(result["accepted"], "v000.png")
        self.assertEqual(result["status"], "lock_review_required")

    def test_new_region_on_same_requirement_rejects_revision(self):
        other = {**self.issue, "bounds": [.5, 0, 1, .5]}
        new_issue = {**self.issue, "bounds": [0, .5, .5, 1]}
        self.revisions({**self.corrected, "defects": [new_issue]}, first=[self.issue, other])
        self.assertEqual(self.run_case()["status"], "revision_unverified")

    def test_distinct_outstanding_defect_can_remain(self):
        other = {**self.issue, "bounds": [.5, 0, 1, .5]}
        self.revisions({**self.corrected, "defects": [other]}, first=[self.issue, other])
        result = self.run_case(max_revisions=1)
        self.assertEqual((result["status"], result["accepted"]), ("iteration_limit", "v001.png"))

    def test_uncertain_finding_blocks_promotion_even_at_limit(self):
        self.revisions({**self.corrected, "defects": [{**self.issue, "confidence": .5}]})
        result = self.run_case(max_revisions=1)
        self.assertEqual((result["status"], result["accepted"]), ("uncertain", "v000.png"))

    def test_unchanged_patch_does_not_trigger_paid_reinspection(self):
        self.http.side_effect = [self.vision({**self.ok, "defects": [self.issue]}), self.pixels("red")]
        self.assertEqual(self.run_case()["status"], "unchanged_region")
        self.assertEqual(self.http.call_count, 2)

    def test_no_budget_or_authorization_never_calls(self):
        with self.assertRaises(ValueError):
            self.run_case(authorized=False)
        result = self.run_case(budget="0.01", start=None)
        self.assertEqual(result["status"], "budget_limit")
        self.http.assert_not_called()

    def test_budget_includes_next_inspection(self):
        self.http.side_effect = [self.vision({**self.ok, "defects": [self.issue]})]
        result = self.run_case(budget="2.47")
        self.assertEqual(result["status"], "budget_limit")
        self.assertEqual(self.http.call_count, 1)

    def test_iteration_limit(self):
        self.http.side_effect = [self.vision({**self.ok, "defects": [self.issue]})]
        result = self.run_case(max_revisions=0)
        self.assertEqual(result["status"], "iteration_limit")
        self.assertEqual(self.http.call_count, 1)

    def test_missing_key_does_not_reserve_or_generate(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}), self.assertRaises(ProviderError):
            self.run_case(start=None)
        manifest = json.loads((self.root / "run" / "manifest.json").read_text())
        self.assertEqual((manifest["reserved_usd"], manifest["status"]), ("0", "local_failure"))
        self.http.assert_not_called()

    def test_failure_keeps_reservation_and_never_replays(self):
        self.http.side_effect = URLError("test-vision")
        with self.assertRaises(ProviderError):
            self.run_case()
        journal = (self.root / "run" / "manifest.json").read_text()
        self.assertNotIn("test-vision", journal)
        self.assertEqual(json.loads(journal)["requests"][-1]["status"], "unconfirmed")
        with self.assertRaises(FileExistsError):
            self.run_case()
        self.http.assert_called_once()
