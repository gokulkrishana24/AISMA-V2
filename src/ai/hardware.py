from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class HardwareSnapshot:
    cpu_count: int
    ram_total_mb: int
    ram_available_mb: int
    gpu_name: str | None
    vram_total_mb: int | None
    vram_free_mb: int | None
    nvidia_smi_available: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_count": self.cpu_count,
            "ram_total_mb": self.ram_total_mb,
            "ram_available_mb": self.ram_available_mb,
            "gpu_name": self.gpu_name,
            "vram_total_mb": self.vram_total_mb,
            "vram_free_mb": self.vram_free_mb,
            "nvidia_smi_available": self.nvidia_smi_available,
        }


def _query_nvidia_smi() -> tuple[str | None, int | None, int | None, bool]:
    if not shutil.which("nvidia-smi"):
        return None, None, None, False
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None, None, None, True
        line = proc.stdout.strip().splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        name = parts[0] if parts else None
        total = int(float(parts[1])) if len(parts) > 1 else None
        free = int(float(parts[2])) if len(parts) > 2 else None
        return name, total, free, True
    except Exception:
        return None, None, None, True


def detect_hardware() -> HardwareSnapshot:
    import os
    if os.getenv("AISMA_TEST_MODE") == "true":
        return HardwareSnapshot(
            cpu_count=16,
            ram_total_mb=15709,
            ram_available_mb=8192,
            gpu_name="NVIDIA GeForce RTX 3050 Laptop GPU",
            vram_total_mb=4096,
            vram_free_mb=3962,
            nvidia_smi_available=True,
        )
    try:
        import psutil  # type: ignore

        cpu_count = psutil.cpu_count(logical=True) or 1
        vm = psutil.virtual_memory()
        ram_total = int(vm.total / (1024 * 1024))
        ram_avail = int(vm.available / (1024 * 1024))
    except Exception:
        cpu_count = 1
        ram_total = 0
        ram_avail = 0
    gpu_name, vram_total, vram_free, smi = _query_nvidia_smi()
    return HardwareSnapshot(
        cpu_count=cpu_count,
        ram_total_mb=ram_total,
        ram_available_mb=ram_avail,
        gpu_name=gpu_name,
        vram_total_mb=vram_total,
        vram_free_mb=vram_free,
        nvidia_smi_available=smi,
    )


def recommend_runtime_options(
    *,
    gpu_preference: str,
    gpu_memory_budget_mb: int,
    context_length: int,
    num_predict: int,
) -> dict[str, Any]:
    """Return Ollama runtime options with hardware-aware, conservative defaults.

    Ollama/llama.cpp handles actual offloading; we constrain context/prediction
    and expose GPU preference. Do not assume full model fits in 4GB VRAM.
    """
    hw = detect_hardware()
    options: dict[str, Any] = {
        "num_ctx": max(512, min(context_length, 32768)),
        "num_predict": max(1, num_predict),
    }
    # If VRAM is constrained, keep generation/context conservative.
    vram = hw.vram_free_mb or hw.vram_total_mb
    if vram is not None and vram <= 4096:
        options["num_ctx"] = min(options["num_ctx"], 8192)
        options["num_predict"] = min(options["num_predict"], 1024)
    if gpu_preference == "cpu_only":
        options["num_gpu"] = 0
    elif gpu_preference == "prefer_gpu" and (vram or 0) > 0:
        # Leave default GPU behavior; explicit num_gpu tuning depends on model/layers.
        pass
    # auto: let runtime decide but keep our request sizes bounded.
    options["_hardware_snapshot"] = hw.to_dict()
    options["_gpu_memory_budget_mb"] = gpu_memory_budget_mb
    return options
