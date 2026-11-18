import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from imagegen_mastery.editing import ImageSettings, render


class EditingTests(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.source = Path(d.name) / "source.png"
        self.mask = Path(d.name) / "mask.png"
        Image.new("RGB", (16, 12), "blue").save(self.source)
        Image.new("RGBA", (16, 12)).save(self.mask)
        self.b64 = base64.b64encode(self.source.read_bytes()).decode()
        transport = patch("urllib.request.OpenerDirector.open")
        self.http = transport.start()
        self.addCleanup(transport.stop)
        env = patch.dict("os.environ", {"OPENAI_API_KEY": "test", "GEMINI_API_KEY": "test"})
        env.start()
        self.addCleanup(env.stop)

    def call(self, provider="openai", model="gpt-image-2.5-flare", **options):
        return render(provider, model, "Repair the missing dot.", ImageSettings(**options), authorized=True)

    def respond(self, body):
        self.http.return_value = io.BytesIO(json.dumps(body).encode())

    def test_openai_mask_first_image_and_settings(self):
        self.respond({"data": [{"b64_json": self.b64}]})
        result = self.call(source=self.source, references=(self.source,), mask=self.mask,
                           aspect_ratio="3:2", quality="high")
        self.assertEqual(result, self.source.read_bytes())
        req = self.http.call_args.args[0]
        self.assertTrue(req.full_url.endswith("/images/edits"))
        body = json.loads(req.data)
        self.assertEqual((body["size"], body["quality"]), ("1536x1024", "high"))
        self.assertEqual(len(body["images"]), 2)
        self.assertTrue(body["mask"]["image_url"].startswith("data:image/png;base64,"))

    def test_google_reference_and_options(self):
        self.respond({"candidates": [{"content": {"parts": [{"inlineData": {"data": self.b64}}]}}]})
        self.call("google", "gemini-3.1-flash-image", references=(self.source,), size="2K", aspect_ratio="16:9")
        body = json.loads(self.http.call_args.args[0].data)
        self.assertEqual(body["generationConfig"]["imageConfig"], {"aspectRatio": "16:9", "imageSize": "2K"})
        self.assertEqual(body["contents"][0]["parts"][-1]["inlineData"]["mimeType"], "image/png")

    def test_invalid_combinations_never_send(self):
        for provider, model, options in [
            ("google", "gemini-3.1-flash-image", {"mask": self.mask, "source": self.source}),
            ("google", "unknown", {"references": (self.source,)}),
            ("google", "gemini-3.1-flash-lite-image", {"size": "4K"}),
            ("openai", "gpt-image-2.5-flare", {"size": "1024x1024", "aspect_ratio": "3:2"}),
            ("openai", "gpt-image-2.5-flare", {"mask": self.mask}),
            ("openai", "gpt-image-2.5-flare", {"source": self.source, "mask": self.source}),
        ]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.call(provider, model, **options)
        self.http.assert_not_called()

