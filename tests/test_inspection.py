import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from imagegen_mastery.inspection import inspect_image
from imagegen_mastery.providers import ProviderError


class InspectionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "tile.png"
        Image.new("RGB", (20, 10), "red").save(self.path)
        self.response = {"defects": [{"requirement": 0, "observation": "Blue mark at left",
                         "bounds": [0, 0, .3, 1], "confidence": .9,
                         "uncertainty": ""}], "uncertainties": [], "locks": []}

    def inspect(self, **kwargs):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test"}), patch(
            "imagegen_mastery.inspection._post") as post:
            post.return_value = {"choices": [{"finish_reason": "stop", "message":
                                 {"content": json.dumps(self.response)}}]}
            result = inspect_image(self.path, ["Red rectangle"], **kwargs)
            return result, post.call_args.args[2]

    def test_sends_decodable_candidate_and_reference_pixels(self):
        result, payload = self.inspect(references=(self.path,), authorized=True)
        parts = payload["messages"][1]["content"]
        urls = [p["image_url"]["url"] for p in parts if p["type"] == "image_url"]
        self.assertEqual(len(urls), 2)
        for url in urls:
            with Image.open(io.BytesIO(base64.b64decode(url.split(",")[1]))) as image:
                self.assertEqual(image.getpixel((0, 0)), (255, 0, 0))
        self.assertEqual(result["defects"], self.response["defects"])
        self.assertEqual(result["inputs"][0]["role"], "candidate")
        self.assertEqual(result["status"], "inspected")

    def test_no_consent_never_posts(self):
        with patch("imagegen_mastery.inspection._post") as post, self.assertRaises(ValueError):
            inspect_image(self.path, ["Red rectangle"])
        post.assert_not_called()

    def test_invalid_evidence_is_rejected(self):
        for key, value in [("bounds", [1, 0, .2, 1]), ("confidence", float("nan")),
                           ("confidence", True), ("observation", ""), ("requirement", 10)]:
            with self.subTest(key=key), patch.dict(self.response["defects"][0], {key: value}):
                with self.assertRaises(ProviderError):
                    self.inspect(authorized=True)

    def test_missing_lock_check_cannot_pass(self):
        with self.assertRaises(ProviderError):
            self.inspect(locks=["Red background"], authorized=True)

