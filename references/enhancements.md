# Local enhancement

Run `imagegen-mastery enhance INPUT --output NEW.png --scale 2 --denoise --sharpen 40`. Each operation is optional and runs locally. The input is decoded in display orientation. The CLI retains an embedded color profile and omits original EXIF metadata. The destination must be a new PNG in an existing directory on a filesystem supporting hard links.

The pipeline applies a 3×3 median filter, Lanczos resizing (integer scale 1–4), then a radius-one unsharp mask (0–200 percent). Filtering preserves the original alpha channel at the working resolution and skips neighborhoods with partially transparent pixels. Upscaling resamples alpha. Upscaling cannot recover missing source detail, median filtering can blur text, and strong sharpening can emphasize noise or introduce halos. Compare at the intended display size. Output is limited to 16,777,216 pixels and 16,384 pixels per side.

## ComfyUI node

Install this project into the Python environment running ComfyUI. Copy the checkout's `custom_nodes/imagegen_mastery_enhance` directory into ComfyUI's `custom_nodes` and restart ComfyUI. Add **ImageGen Mastery Enhance** from **image/postprocessing**, connect an IMAGE to the input and connect the output to Preview Image or Save Image. The node supports three-channel float IMAGE batches. Process masks separately. Filters use 8-bit channels on the CPU and return the output batch on the input device. A no-op passes the original tensor through.

[ComfyUI image tensors](https://docs.comfy.org/custom-nodes/backend/images_and_masks) · [Custom node properties](https://docs.comfy.org/custom-nodes/backend/server_overview)
