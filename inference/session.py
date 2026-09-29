"""Wraps the OCR engine used for the local demo.

IMPORTANT: this runs the EasyOCR Python package locally on CPU/GPU for
the functional demo, since the dev machine has no Snapdragon NPU. The
NPU-accelerated execution path (detector INT8 + recognizer float, 
Hexagon NPU) is proven separately in BENCHMARKS.md via Qualcomm AI Hub,  
with per-stage latency in single-digit-to-low-double-digit milliseconds 
— roughly 60x faster than what this local CPU/GPU demo shows. That gap    
IS the pitch: this script proves the logic works, the benchmarks prove 
why it needs to ship on Snapdragon."""

import time
import numpy as np
from PIL import Image
import easyocr


class OCRSession:
    def __init__(self, languages=("en",), max_width: int = 1200):
        print("Loading OCR model (first run downloads weights)...")
        self.reader = easyocr.Reader(list(languages), gpu=True)
        self.max_width = max_width

    def _resize(self, image: np.ndarray):
        h, w = image.shape[:2]
        if w <= self.max_width:
            return image, 1.0
        scale = self.max_width / w
        new_size = (self.max_width, int(h * scale))
        resized = np.array(Image.fromarray(image).resize(new_size))
        return resized, scale

    def read(self, image):
        """Returns a list of (bbox, text, confidence). Downscales first
        for speed, then rescales bbox coords back to original size."""
        small_image, scale = self._resize(image)
        start = time.time()
        results = self.reader.readtext(
            small_image,
            canvas_size=1200,
            mag_ratio=1.0,
            batch_size=8,
            paragraph=False,
        )
        elapsed = time.time() - start
        print(f"  (OCR pass took {elapsed:.1f}s on {small_image.shape[1]}x{small_image.shape[0]}, "
              f"{len(results)} text regions found)")

        if scale != 1.0:
            rescaled = []
            for bbox, text, conf in results:
                bbox = [[x / scale, y / scale] for x, y in bbox]
                rescaled.append((bbox, text, conf))
            return rescaled
        return results


# --- Snapdragon NPU deployment path (for reference / final packaging) ---
#
# import onnxruntime as ort
#
# class NPUSession:
#     def __init__(self, detector_path, recognizer_path):
#         providers = ["QNNExecutionProvider", "CPUExecutionProvider"]
#         provider_options = [{"backend_path": "QnnHtp.dll"}, {}]
#         self.detector = ort.InferenceSession(
#             detector_path, providers=providers, provider_options=provider_options)
#         self.recognizer = ort.InferenceSession(
#             recognizer_path, providers=providers, provider_options=provider_options)
#     # ... run() would replicate EasyOCR's own pre/post-processing
#     # (CRAFT heatmap decode -> boxes -> crop -> recognizer -> CTC decode)
#     # using the exported models from export_assets/.
