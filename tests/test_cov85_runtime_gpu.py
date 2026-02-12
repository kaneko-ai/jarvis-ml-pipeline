from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from jarvis_core.runtime.gpu import GPUAccelerator, GPUInfo


def test_gpu_accelerator_cpu_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(GPUAccelerator, "_check_cuda", lambda self: False)
    acc = GPUAccelerator(prefer_gpu=True)

    assert acc.is_gpu_available is False
    assert acc.get_device() == "cpu"
    assert acc.list_gpus() == []
    assert acc.select_best_gpu() is None
    assert acc.optimize_batch_size(1.0, 100.0) == 32


def test_gpu_accelerator_gpu_listing_selection_and_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Props:
        def __init__(self, name: str, total_mb: int) -> None:
            self.name = name
            self.total_memory = total_mb * 1024 * 1024

    class _Cuda:
        @staticmethod
        def is_available() -> bool:
            return True

        @staticmethod
        def device_count() -> int:
            return 2

        @staticmethod
        def get_device_properties(i: int) -> _Props:
            return _Props(name=f"gpu-{i}", total_mb=1000 + i * 500)

        @staticmethod
        def memory_allocated(i: int) -> int:
            # gpu-0 uses more memory than gpu-1
            return (700 if i == 0 else 100) * 1024 * 1024

    fake_torch = SimpleNamespace(cuda=_Cuda())
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setattr(GPUAccelerator, "_check_cuda", lambda self: True)

    acc = GPUAccelerator(prefer_gpu=True, device_id=1)
    assert acc.get_device() == "cuda:1"

    gpus = acc.list_gpus()
    assert len(gpus) == 2
    assert isinstance(gpus[0], GPUInfo)

    best = acc.select_best_gpu()
    assert best == 1

    batch = acc.optimize_batch_size(item_size_mb=10, model_memory_mb=100)
    assert 1 <= batch <= 512


def test_gpu_embedder_and_embed_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(GPUAccelerator, "_check_cuda", lambda self: False)
    acc = GPUAccelerator()

    # ImportError path
    monkeypatch.delitem(sys.modules, "sentence_transformers", raising=False)
    assert acc.create_embedder() is None

    class _SentenceTransformer:
        def __init__(self, model_name: str, device: str) -> None:
            self.model_name = model_name
            self.device = device

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=_SentenceTransformer),
    )
    embedder = acc.create_embedder(model_name="m")
    assert embedder is not None
    assert embedder.model_name == "m"

    class _Array:
        def __init__(self, values):  # noqa: ANN001
            self._values = values

        def tolist(self):
            return self._values

    class _Embedder:
        def encode(self, texts, batch_size, show_progress_bar, convert_to_numpy):  # noqa: ANN001
            assert batch_size == 4
            assert show_progress_bar is False
            assert convert_to_numpy is True
            return [_Array([float(len(t))]) for t in texts]

    out = acc.embed_batch(["a", "bbb"], _Embedder(), batch_size=4)
    assert out == [[1.0], [3.0]]


def test_list_gpus_exception_path(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Cuda:
        @staticmethod
        def is_available() -> bool:
            return True

        @staticmethod
        def device_count() -> int:
            raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=_Cuda()))
    monkeypatch.setattr(GPUAccelerator, "_check_cuda", lambda self: True)

    acc = GPUAccelerator()
    assert acc.list_gpus() == []
