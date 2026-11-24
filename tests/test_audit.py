import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from imagegen_mastery.audit import DeliveryPolicy, audit_candidates
from imagegen_mastery.cli import main


class AuditTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def image(self, name, color, size=(16, 16)):
        path = self.root / name
        Image.new("RGBA", size, color).save(path)
        return path

    def test_rank_reference_and_exclude_failed_dimensions(self):
        ref = self.image("ref.png", "red")
        other = self.image("other.png", "blue")
        wrong = self.image("wrong.png", "red", (8, 8))
        result = audit_candidates([other, wrong, ref], self.root / "out", reference=ref,
                                  policy=DeliveryPolicy(expected_size=(16, 16)))
        self.assertEqual(result["reference_similarity_order"], [3, 1])
        self.assertEqual(result["candidates"][1]["status"], "failed")
        self.assertEqual(result["visual_review"], "unassessed")
        self.assertTrue((self.root / "out/contact-sheet.png").is_file())
        self.assertEqual(json.loads((self.root / "out/audit.json").read_text()), result)

    def test_alpha_and_hidden_rgb(self):
        first = self.image("a.png", (255, 0, 0, 0))
        second = self.image("b.png", (0, 0, 255, 0))
        result = audit_candidates([second], self.root / "out", reference=first,
                                  policy=DeliveryPolicy(require_transparency=True))
        row = result["candidates"][0]
        self.assertEqual(row["reference"]["dual_background_mae"], 0)
        self.assertEqual(row["status"], "failed")
        self.assertEqual(row["alpha"]["transparent_fraction"], 1)

    def test_partial_cutout_passes(self):
        path = self.image("cutout.png", (0, 0, 0, 0))
        with Image.open(path) as image:
            copy = image.copy()
        copy.paste((255, 0, 0, 255), (4, 4, 12, 12))
        copy.save(path)
        row = audit_candidates([path], self.root / "out",
                               policy=DeliveryPolicy(require_transparency=True))["candidates"][0]
        self.assertEqual(row["status"], "passed")
        self.assertEqual(row["alpha"]["opaque_fraction"], .25)

    def test_tile_seam_and_preview(self):
        path = self.image("tile.png", "white")
        with Image.open(path) as image:
            copy = image.copy()
        copy.paste((0, 0, 0, 255), (0, 0, 1, 16))
        copy.save(path)
        result = audit_candidates([path], self.root / "out", policy=DeliveryPolicy(max_tile_seam=.1))
        row = result["candidates"][0]
        self.assertEqual(row["tile_seams"], {"left_right": 1, "top_bottom": 0})
        self.assertEqual(row["status"], "failed")
        self.assertTrue((self.root / "out" / row["tile_preview"]).is_file())

    def test_aspect_mismatch_is_not_ranked(self):
        a = self.image("a.png", "red")
        b = self.image("b.png", "red", (16, 8))
        result = audit_candidates([b], self.root / "out", reference=a,
                                  policy=DeliveryPolicy(max_reference_mae=1))
        self.assertEqual(result["reference_similarity_order"], [])
        self.assertEqual(result["candidates"][0]["status"], "failed")

    def test_invalid_policy_and_no_overwrite(self):
        a = self.image("a.png", "red")
        out = self.root / "out"
        for policy in (DeliveryPolicy(max_tile_seam=float("nan")), DeliveryPolicy(max_reference_mae=.2)):
            with self.assertRaises(ValueError):
                audit_candidates([a], out, policy=policy)
            self.assertFalse(out.exists())
        audit_candidates([a], out)
        with self.assertRaises(FileExistsError):
            audit_candidates([a], out)

    def test_cli_failure_still_writes_evidence(self):
        a = self.image("a.png", "red")
        out = self.root / "out"
        self.assertEqual(main(["audit", str(a), "--output-dir", str(out), "--require-transparency"]), 2)
        self.assertTrue((out / "audit.json").is_file())
