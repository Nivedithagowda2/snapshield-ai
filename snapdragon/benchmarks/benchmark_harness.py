"""
Day 1 milestone script.

Exports the EasyOCR text-recognition model via Qualcomm AI Hub, compiles
it for a hosted Snapdragon X Elite device, profiles it on REAL Snapdragon
hardware, and prints a benchmark table.

NOTE: In practice this project used the officially supported export path:
    python -m qai_hub_models.models.easyocr.export --device "Snapdragon X Elite CRD" --target-runtime onnx
    python -m qai_hub_models.models.easyocr.export --device "Snapdragon X Elite CRD" --target-runtime onnx --precision w8a8
This script is kept as a reference for a hand-rolled version of the same flow.

Prereqs:
  pip install qai_hub_models easyocr torch
  qai-hub configure --api_token <your token>
  qai-hub list-devices   (confirms auth works)
"""

import qai_hub as hub
from qai_hub_models.models.easyocr.model import EasyOCR
from qai_hub_models.utils.printing import print_profile_metrics_from_job

DEVICE_NAME = "Snapdragon X Elite CRD"


def main():
    device = hub.Device(DEVICE_NAME)
    print(f"Using device: {device}\n")

    print("Loading EasyOCR model...")
    model = EasyOCR.from_pretrained()
    input_spec = model.get_input_spec()

    print("Submitting compile job to AI Hub (this runs in the cloud)...")
    compile_job = hub.submit_compile_job(
        model=model,
        device=device,
        input_specs=input_spec,
        options="--target_runtime onnx",
    )
    compile_job.wait()
    compiled_model = compile_job.get_target_model()
    print(f"Compile job done: {compile_job.job_id}\n")

    print("Submitting profile job to AI Hub (runs on a real hosted Snapdragon device)...")
    profile_job = hub.submit_profile_job(
        model=compiled_model,
        device=device,
    )
    profile_job.wait()
    print(f"Profile job done: {profile_job.job_id}\n")

    print("=" * 60)
    print("BENCHMARK RESULT — real Snapdragon NPU execution")
    print("=" * 60)
    print_profile_metrics_from_job(profile_job, profile_job.download_profile())
    print("\nView full profiling report at:")
    print(profile_job.url)


if __name__ == "__main__":
    main()
