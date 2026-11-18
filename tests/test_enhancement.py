import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from imagegen_mastery.enhancement import enhance_image, enhance_file, output_size


class EnhancementTests(unittest.TestCase):
    def test_denoise_removes_isolated_speck(self):
        image = Image.new("RGB", (11, 11), "gray")
        image.putpixel((5, 5), (255, 255, 255))
        clean = enhance_image(image, denoise=True)
        self.assertEqual(clean.getpixel((5, 5)), (128, 128, 128))
        self.assertEqual(image.getpixel((5, 5)), (255, 255, 255))

    def test_sharpen_contrast_preserves_alpha(self):
        image = Image.new("RGBA", (13, 13), (80, 80, 80, 255))
        image.paste((160, 160, 160, 255), (7, 0, 13, 13))
        image.putpixel((0, 0), (255, 0, 0, 32))
        result = enhance_image(image, sharpen=100)
        self.assertGreater(result.getpixel((7, 6))[0], 160)
        self.assertEqual(result.getchannel("A").tobytes(), image.getchannel("A").tobytes())
        self.assertEqual(result.getpixel((0, 0)), image.getpixel((0, 0)))

    def test_cli_orients_and_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            source, output = (Path(temp) / f"{name}.png" for name in ("source", "output"))
            exif = Image.Exif()
            exif[274] = 6
            Image.new("RGB", (8, 4), "blue").save(source, exif=exif)
            result = subprocess.run([sys.executable, "-m", "imagegen_mastery", "enhance", str(source),
                                     "--output", str(output), "--scale", "2"], check=True, capture_output=True)
            self.assertEqual(json.loads(result.stdout)["output"]["height"], 16)
            with Image.open(output) as restored:
                self.assertEqual(restored.size, (8, 16))
                self.assertFalse(restored.getexif())
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                enhance_file(source, output, sharpen=100)
            self.assertEqual(before, output.read_bytes())

    def test_scale_limits(self):
        for size, scale in [((2000, 2000), 4), ((1, 1), 0), ((1, 1), True)]:
            with self.assertRaises(ValueError):
                output_size(size, scale)

    def test_comfy_node_registration(self):
        from custom_nodes.imagegen_mastery_enhance import NODE_CLASS_MAPPINGS
        node = NODE_CLASS_MAPPINGS["ImageGenMasteryEnhance"]
        self.assertEqual(node.RETURN_TYPES, ("IMAGE",))
        self.assertEqual(node.INPUT_TYPES()["required"]["image"], ("IMAGE",))
        self.assertTrue(callable(getattr(node(), node.FUNCTION)))

    @unittest.skipUnless(importlib.util.find_spec("torch"), "optional ComfyUI tensor runtime")
    def test_comfy_batch_execution(self):
        import torch
        from custom_nodes.imagegen_mastery_enhance import ImageGenMasteryEnhance
        image = torch.rand((2, 8, 9, 3))
        result, = ImageGenMasteryEnhance().enhance(image, 2, True, 40)
        self.assertEqual(tuple(result.shape), (2, 16, 18, 3))
        self.assertTrue(torch.isfinite(result).all())
