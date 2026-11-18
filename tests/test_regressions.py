import io
import json
import os
import random
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from imagegen_mastery.cli import main
from imagegen_mastery.evaluation import load_image
from imagegen_mastery.metrics import measure_pair
from imagegen_mastery.references import bind_references


class ReliabilityTests(unittest.TestCase):
    def test_identity_at_high_frequency_and_large_size(self):
        image = Image.frombytes("RGB", (1024, 1024), random.Random(19).randbytes(3*1024*1024))
        metrics, diff = measure_pair(image, image, ssim=True, perceptual=True)
        self.assertIsNone(diff.getbbox())
        self.assertAlmostEqual(metrics["ssim"], 1)
        self.assertEqual((metrics["rgb_mae"], metrics["dhash_distance"]), (0, 0))

    def test_corrupt_png_crc(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.png"
            Image.new("RGB", (4, 4)).save(path)
            data = bytearray(path.read_bytes())
            start = data.index(b"IDAT")
            data[start+4+int.from_bytes(data[start-4:start], "big")] ^= 1
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                load_image(path)

    def test_named_references_must_be_unambiguous_in_loop(self):
        brief = {"references": [{"image": "sample"}]}
        with self.assertRaises(ValueError):
            bind_references(brief, [Path("wrong")], [], require_all=True)
        with self.assertRaises(ValueError):
            bind_references(brief, [], [], require_all=True)
        paths, labels = bind_references(brief, [], [("sample", Path("right"))], require_all=True)
        self.assertEqual(list(zip(labels, paths)), [("sample", Path("right"))])

    def test_inspect_honors_brief_locks_and_named_pixel_bindings(self):
        root = Path(__file__).resolve().parents[1] / "examples"
        body = {"defects": [], "uncertainties": [], "locks": [
            {"status": "met", "evidence": "OPEN in capitals."}, {"status": "met", "evidence": "Cream field."}]}
        response = {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(body)}}]}
        with patch.dict(os.environ, {"OPENAI_API_KEY": "mock"}), patch(
                "urllib.request.OpenerDirector.open", return_value=io.BytesIO(json.dumps(response).encode())), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(main(["inspect", str(root/"fixtures/candidate.png"), "--brief", str(root/"sign-brief.json"),
                                   "--named-reference", "Palette", str(root/"fixtures/reference.png"), "--authorize-paid"]), 0)
        result = json.loads(out.getvalue())
        self.assertEqual(len(result["locked_attributes"]), 2)
        self.assertEqual(result["inputs"][1]["role"], "reference: Palette")
