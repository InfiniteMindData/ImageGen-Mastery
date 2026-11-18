import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from imagegen_mastery.evaluation import evaluate


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def save(self, name, image, **options):
        path = self.root / name
        image.save(path, **options)
        return path

    def test_reports_visible_pixels_and_leaves_visual_judgments_open(self):
        path = self.save("clear.png", Image.new("RGBA", (3, 2), (255, 0, 0, 0)))
        report = evaluate(path)
        json.dumps(report, allow_nan=False)
        self.assertEqual(report["image"]["mean_rgb"], [255, 255, 255])
        self.assertEqual(report["image"]["luma_stddev"], 0)
        self.assertIsNone(report["comparison"])
        for name in ("anatomy", "artifacts", "composition", "consistency"):
            criterion = report["rubric"][name]
            self.assertEqual(criterion["status"], "unassessed")
            self.assertEqual(criterion["evidence"], [])
            self.assertTrue(criterion["inspect"])

    def test_comparison_detects_spatial_changes_with_identical_palettes(self):
        split = Image.new("RGB", (64, 64))
        split.paste("white", (32, 0, 64, 64))
        left = self.save("left.png", split)
        right = self.save("right.png", split.transpose(Image.Transpose.FLIP_LEFT_RIGHT))
        same = evaluate(left, left)["comparison"]
        report = evaluate(left, right)
        flipped = report["comparison"]
        self.assertEqual(report["image"]["sha256"], hashlib.sha256(left.read_bytes()).hexdigest())
        self.assertEqual(flipped["reference"]["sha256"], hashlib.sha256(right.read_bytes()).hexdigest())
        self.assertEqual(same["normalized_mean_absolute_rgb_difference"], 0)
        self.assertEqual(same["most_changed_regions"], [])
        self.assertEqual(flipped["normalized_mean_absolute_rgb_difference"], 1)
        self.assertTrue(flipped["aspect_ratio_match"])

    def test_smallest_sampled_change_remains_distinguishable_from_equality(self):
        canvas = Image.new("RGB", (64, 64))
        black = self.save("black.png", canvas)
        canvas.putpixel((5, 5), (0, 0, 1))
        changed = self.save("changed.png", canvas)
        result = evaluate(changed, black)["comparison"]
        self.assertGreater(result["normalized_mean_absolute_rgb_difference"], 0)
        self.assertEqual(len(result["most_changed_regions"]), 1)

    def test_ranks_three_local_changes_and_breaks_ties_in_reading_order(self):
        canvas = Image.new("RGB", (64, 64), "black")
        original = self.save("original.png", canvas)
        canvas.paste("red", (32, 0, 48, 16))
        canvas.paste("green", (0, 16, 16, 32))
        canvas.paste("blue", (48, 32, 64, 48))
        canvas.paste("white", (16, 48, 32, 64))
        changed = self.save("changed.png", canvas)
        regions = evaluate(changed, original)["comparison"]["most_changed_regions"]
        self.assertEqual([cell["bounds"] for cell in regions], [
            [0.25, 0.75, 0.5, 1.0],
            [0.5, 0, 0.75, 0.25],
            [0.75, 0.5, 1.0, 0.75],
        ])
        self.assertEqual([cell["normalized_mean_absolute_rgb_difference"] for cell in regions],
                         [1, 1 / 3, 1 / 3])

    def test_compares_as_displayed_and_reports_aspect_ratio_separately(self):
        portrait = Image.new("RGB", (300, 900), "blue")
        exif = Image.Exif()
        exif[274] = 6
        rotated = self.save("oriented.png", portrait, exif=exif)
        square = self.save("square.png", Image.new("RGB", (64, 64), "blue"))
        report = evaluate(rotated, square)
        self.assertEqual((report["image"]["width"], report["image"]["height"]), (900, 300))
        self.assertLess(max(report["image"]["sample_size"]), 900)
        self.assertFalse(report["comparison"]["aspect_ratio_match"])
        self.assertEqual(report["comparison"]["normalized_mean_absolute_rgb_difference"], 0)

    def test_rejects_corrupt_candidate_or_reference(self):
        valid = self.save("ok.png", Image.new("L", (1, 1)))
        corrupt = self.root / "corrupt.png"
        corrupt.write_bytes(b"truncated")
        for candidate, reference in ((valid, corrupt), (corrupt, None)):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                evaluate(candidate, reference)

    def test_rejects_oversize_header_before_decoding(self):
        # PPM declares dimensions in its header. The missing body must never be decoded.
        path = self.root / "oversize.ppm"
        path.write_bytes(b"P6\n6000 6000\n255\n")
        with self.assertRaisesRegex(ValueError, "pixel"):
            evaluate(path)

    def test_rejects_animation_instead_of_scoring_one_frame(self):
        path = self.save("animated.gif", Image.new("RGB", (6, 6), "red"),
                         save_all=True, append_images=[Image.new("RGB", (6, 6), "blue")])
        with self.assertRaisesRegex(ValueError, "animated"):
            evaluate(path)

    def test_rejects_oversize_file_before_image_identification(self):
        path = self.root / "large.bin"
        with path.open("wb") as file:
            file.truncate(65 * 1024 * 1024)
        with self.assertRaisesRegex(ValueError, "byte"):
            evaluate(path)
