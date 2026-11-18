import tempfile
import unittest
from pathlib import Path

from PIL import Image

from imagegen_mastery.localization import localize, pixel_box


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.source, self.proposed, self.target = (Path(tmp.name) / f"{name}.png"
                                                  for name in ("source", "proposed", "result"))
        self.base = Image.new("RGBA", (12, 12), "black")
        self.patch = Image.new("RGBA", (12, 12), "white")
        self.box = [.25, .25, .75, .75]

    def run_edit(self, **options):
        self.base.save(self.source)
        self.patch.save(self.proposed)
        return localize(self.source, self.proposed, self.box, self.target, **options)

    def test_hard_cut_and_feather_against_flat_background(self):
        self.assertEqual(self.run_edit(max_boundary_jump=.6), "boundary_discontinuity")
        self.assertEqual(self.run_edit(feather=1, max_boundary_jump=.6), "changed")
        with Image.open(self.target) as result:
            self.assertEqual(result.getpixel((3, 5)), (128, 128, 128, 255))
            self.assertEqual(result.getpixel((4, 5)), (255, 255, 255, 255))
            self.assertEqual(result.getpixel((2, 5)), (0, 0, 0, 255))

    def test_existing_edge_and_frame_boundary(self):
        self.box = [0, 0, .5, 1]
        self.base.paste("white", (0, 0, 6, 12))
        self.patch.paste("gray", (0, 0, 12, 12))
        self.assertEqual(self.run_edit(feather=2, max_boundary_jump=0), "changed")
        with Image.open(self.target) as result:
            self.assertEqual(result.getpixel((0, 0)), (128, 128, 128, 255))

    def test_protection_hole_and_its_seam(self):
        self.box = [0, 0, 1, 1]
        options = {"protected": ((.25, .25, .75, .75),), "max_boundary_jump": .6}
        self.assertEqual(self.run_edit(**options), "boundary_discontinuity")
        self.assertEqual(self.run_edit(feather=1, **options), "changed")
        with Image.open(self.target) as result:
            self.assertEqual(result.getpixel((3, 5)), (0, 0, 0, 255))
            self.assertEqual(result.getpixel((2, 5)), (128, 128, 128, 255))

    def test_no_hidden_color_halo_and_protected_exact_rgba(self):
        self.base.paste((0, 255, 0, 0), (0, 0, 12, 12))
        self.patch.paste((255, 0, 0, 255), (0, 0, 12, 12))
        self.assertEqual(self.run_edit(feather=1, protected=[[.5, .5, 1, 1]]), "changed")
        with Image.open(self.target) as result:
            self.assertEqual(result.getpixel((3, 3)), (255, 0, 0, 128))
            self.assertEqual(result.getpixel((6, 6)), (0, 255, 0, 0))
            self.assertEqual(result.getpixel((0, 0)), (0, 255, 0, 0))

    def test_hidden_only_change_and_alpha_only_change(self):
        self.base.paste((255, 255, 255, 0), (0, 0, 12, 12))
        self.patch.paste((0, 255, 0, 0), (0, 0, 12, 12))
        self.assertEqual(self.run_edit(), "unchanged_region")
        self.patch.paste("white", (0, 0, 12, 12))
        self.assertEqual(self.run_edit(max_boundary_jump=.9), "boundary_discontinuity")

    def test_provider_change_only_outside_the_edit(self):
        self.patch.paste("black", (3, 3, 9, 9))
        self.assertEqual(self.run_edit(feather=2), "unchanged_region")
        with Image.open(self.target) as result:
            self.assertEqual(result.tobytes(), self.base.tobytes())

    def test_low_alpha_channels_keep_precision_and_identical_transparent_pixels(self):
        self.base.paste((16, 101, 25, 1), (0, 0, 12, 12))
        self.patch.paste((64, 141, 125, 1), (0, 0, 12, 12))
        self.base.putpixel((3, 4), (7, 17, 27, 0))
        self.patch.putpixel((3, 4), (7, 17, 27, 0))
        self.run_edit(feather=1)
        with Image.open(self.target) as result:
            self.assertEqual(result.getpixel((3, 3)), (40, 121, 75, 1))
            self.assertEqual(result.getpixel((3, 4)), (7, 17, 27, 0))

    def test_full_protection_and_dimension_gate(self):
        self.assertEqual(self.run_edit(protected=[self.box]), "unchanged_region")
        self.target.unlink()
        self.patch = self.patch.resize((8, 12))
        self.assertEqual(self.run_edit(), "dimension_mismatch")
        self.assertFalse(self.target.exists())

    def test_options_reject_nonfinite_inverted_and_untyped_values(self):
        for bad in ({"max_boundary_jump": float("nan")}, {"feather": True}, {"feather": -1},
                    {"protected": [[1, 0, .5, 1]]}, {"protected": [[0, 0, float("inf"), 1]]}):
            with self.subTest(options=bad), self.assertRaises(ValueError):
                self.run_edit(**bad)
        self.assertEqual(pixel_box((13, 10), [.25, .25, .75, .75]), (3, 2, 10, 8))
