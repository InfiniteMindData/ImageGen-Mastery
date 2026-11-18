"""Optional one-request CLI checks against the selected provider's real API."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "examples" / "fixtures"
BRIEF = ROOT / "examples" / "sign-brief.json"


class ProviderCases:
    def setUp(self):
        if os.environ.get("IMAGEGEN_LIVE_AUTHORIZE_PAID") != "yes":
            self.skipTest("Live uploads and charges require IMAGEGEN_LIVE_AUTHORIZE_PAID=yes")
        if os.environ.get("IMAGEGEN_LIVE_PROVIDER") != self.provider:
            self.skipTest(f"Select this provider with IMAGEGEN_LIVE_PROVIDER={self.provider}")
        self.assertTrue(os.environ.get(self.key_variable, "").strip(),
                        f"Set {self.key_variable} for the selected provider")
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.output = Path(directory.name) / "output.png"

    def cli(self, *args):
        environment = os.environ.copy()
        for key in ("GEMINI_API_KEY", "OPENAI_API_KEY"):
            if key != self.key_variable:
                environment.pop(key, None)
        result = subprocess.run(
            [sys.executable, "-m", "imagegen_mastery", *args, "--authorize-paid"],
            cwd=ROOT, env=environment, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def image_request(self, *args):
        self.cli(*args, "--provider", self.provider, "--model", self.image_model,
                 *self.image_options, "--output", self.output)
        with Image.open(self.output) as image:
            self.assertEqual(image.format, "PNG")
            image.load()
            self.assertEqual(image.size, (1024, 1024))

    def test_generation(self):
        self.image_request("generate", BRIEF)

    def test_reference_edit(self):
        self.image_request("edit", FIXTURES / "candidate.png", BRIEF,
                           "--reference", FIXTURES / "reference.png")

    def test_vision(self):
        candidate = FIXTURES / "candidate.png"
        reference = FIXTURES / "reference.png"
        result = json.loads(self.cli("inspect", candidate, "--brief", BRIEF,
                                     "--reference", reference, "--provider", self.provider,
                                     "--model", self.vision_model))
        self.assertEqual(result["status"], "inspected")
        self.assertEqual(result["provider"], self.provider)
        self.assertEqual(result["model"], self.vision_model)
        expected_hashes = [hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in (candidate, reference)]
        self.assertEqual([entry["sha256"] for entry in result["inputs"]], expected_hashes)
        locks = json.loads(BRIEF.read_text(encoding="utf-8"))["locked_attributes"]
        self.assertEqual(result["locked_attributes"], locks)
        self.assertEqual(len(result["locks"]), len(locks))
        self.assertIsInstance(result["defects"], list)
        self.assertIsInstance(result["uncertainties"], list)


class OpenAILiveTests(ProviderCases, unittest.TestCase):
    provider = "openai"
    key_variable = "OPENAI_API_KEY"
    image_model = "gpt-image-2.5-flare"
    image_options = ("--size", "1024x1024", "--quality", "low")
    vision_model = "gpt-5.4-mini-2026-03-17"

    def test_native_mask(self):
        self.image_request("edit", FIXTURES / "candidate.png", BRIEF,
                           "--mask", FIXTURES / "mask.png")


class GeminiLiveTests(ProviderCases, unittest.TestCase):
    provider = "google"
    key_variable = "GEMINI_API_KEY"
    image_model = "gemini-3.1-flash-image"
    image_options = ("--aspect-ratio", "1:1", "--size", "1K")
    vision_model = "gemini-3.1-flash-lite"
