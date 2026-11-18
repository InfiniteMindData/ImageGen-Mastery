"""A local ComfyUI IMAGE node. Install imagegen-mastery in ComfyUI's Python."""

from PIL import Image

from imagegen_mastery.enhancement import enhance_image, output_size


class ImageGenMasteryEnhance:
    CATEGORY = "image/postprocessing"
    FUNCTION = "enhance"
    RETURN_TYPES = ("IMAGE",)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image": ("IMAGE",),
            "scale": ("INT", {"default": 1, "min": 1, "max": 4}),
            "denoise": ("BOOLEAN", {"default": False}),
            "sharpen": ("INT", {"default": 0, "min": 0, "max": 200}),
        }}

    def enhance(self, image, scale, denoise, sharpen):
        import numpy as np
        import torch

        if image.ndim != 4 or image.shape[-1] != 3 or image.shape[0] < 1 or not image.is_floating_point():
            raise ValueError("Expected a floating-point ComfyUI IMAGE batch shaped [B,H,W,3].")
        width, height = output_size((image.shape[2], image.shape[1]), scale)
        if not torch.isfinite(image).all():
            raise ValueError("The IMAGE batch contains non-finite values.")
        if scale == 1 and not denoise and sharpen == 0:
            return (image,)
        result = image.new_empty((image.shape[0], height, width, 3))
        for i, frame in enumerate(image):
            pixels = frame.detach().clamp(0, 1).mul(255).round().to(device="cpu", dtype=torch.uint8).numpy()
            enhanced = enhance_image(Image.fromarray(pixels), scale=scale, denoise=denoise, sharpen=sharpen)
            samples = np.asarray(enhanced, dtype=np.float32) / 255
            result[i].copy_(torch.from_numpy(samples))
        return (result,)


NODE_CLASS_MAPPINGS = {"ImageGenMasteryEnhance": ImageGenMasteryEnhance}
NODE_DISPLAY_NAME_MAPPINGS = {"ImageGenMasteryEnhance": "ImageGen Mastery Enhance"}
