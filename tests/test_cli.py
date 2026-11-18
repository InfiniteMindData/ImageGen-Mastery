import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from imagegen_mastery.cli import main


EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "brief.json"


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "imagegen_mastery", *args],
            capture_output=True, text=True, check=False,
        )

    def test_example_compiles(self):
        result = self.run_cli("optimize", EXAMPLE)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(json.loads(EXAMPLE.read_text())["intent"], result.stdout)

    def test_image_report_is_json(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "square.png"
            Image.new("RGB", (10, 10), "red").save(source)
            result = self.run_cli("evaluate", source, "--reference", source)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIsInstance(json.loads(result.stdout), dict)

    def test_bad_json_exits_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            brief = Path(directory) / "bad.json"
            brief.write_text("{")
            result = self.run_cli("optimize", brief)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Error:", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    @patch("imagegen_mastery.cli.generate")
    def test_existing_output_prevents_billing(self, generate):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "keep.png"
            output.write_bytes(b"keep")
            args = ["generate", str(EXAMPLE), "--provider", "google",
                    "--model", "test", "--output", str(output)]
            self.assertEqual(main(args), 1)
            self.assertEqual(output.read_bytes(), b"keep")
            generate.assert_not_called()

    @patch("imagegen_mastery.cli.generate", side_effect=RuntimeError("offline"))
    def test_failed_generation_releases_destination(self, generate):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new.png"
            self.assertEqual(main(["generate", str(EXAMPLE), "--provider", "google",
                                   "--model", "test", "--output", str(output)]), 1)
            self.assertFalse(output.exists())
            generate.assert_called_once()
