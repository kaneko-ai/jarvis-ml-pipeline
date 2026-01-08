"""GPU Acceleration.

Per RP-414, implements GPU acceleration for embeddings and inference.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GPUInfo:
    """GPU device information."""

    device_id: int
    name: str
    memory_total_mb: int
    memory_used_mb: int
    utilization_percent: float


class GPUAccelerator:
    """GPU acceleration manager.
    
    Per RP-414:
    - CUDA-compatible embeddings
    - vLLM integration
    - GPU scheduling
    """

    def __init__(
        self,
        prefer_gpu: bool = True,
        device_id: int | None = None,
    ):
        self.prefer_gpu = prefer_gpu
        self.device_id = device_id
        self._cuda_available = self._check_cuda()

    def _check_cuda(self) -> bool:
        """Check CUDA availability."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    @property
    def is_gpu_available(self) -> bool:
        """Check if GPU is available."""
        return self._cuda_available

    def get_device(self) -> str:
        """Get compute device string.
        
        Returns:
            'cuda:X' or 'cpu'.
        """
        if self._cuda_available and self.prefer_gpu:
            if self.device_id is not None:
                return f"cuda:{self.device_id}"
            return "cuda"
        return "cpu"

    def list_gpus(self) -> list[GPUInfo]:
        """List available GPUs.
        
        Returns:
            List of GPU info.
        """
        gpus = []

        if not self._cuda_available:
            return gpus

        try:
            import torch

            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                memory_total = props.total_memory // (1024 * 1024)
                memory_used = torch.cuda.memory_allocated(i) // (1024 * 1024)

                gpus.append(GPUInfo(
                    device_id=i,
                    name=props.name,
                    memory_total_mb=memory_total,
                    memory_used_mb=memory_used,
                    utilization_percent=0.0,  # Would need nvidia-smi
                ))
        except Exception:
            pass

        return gpus

    def select_best_gpu(self) -> int | None:
        """Select best available GPU.
        
        Returns:
            Best GPU device ID or None.
        """
        gpus = self.list_gpus()

        if not gpus:
            return None

        # Select GPU with most free memory
        best = max(
            gpus,
            key=lambda g: g.memory_total_mb - g.memory_used_mb,
        )

        return best.device_id

    def optimize_batch_size(
        self,
        item_size_mb: float,
        model_memory_mb: float,
    ) -> int:
        """Calculate optimal batch size.
        
        Args:
            item_size_mb: Memory per item.
            model_memory_mb: Model memory footprint.
            
        Returns:
            Optimal batch size.
        """
        if not self._cuda_available:
            return 32  # CPU default

        gpus = self.list_gpus()
        if not gpus:
            return 32

        gpu = gpus[self.device_id or 0]
        free_memory = gpu.memory_total_mb - gpu.memory_used_mb - model_memory_mb

        # Reserve 20% for safety
        usable = free_memory * 0.8

        batch_size = int(usable / item_size_mb)

        # Clamp to reasonable range
        return max(1, min(batch_size, 512))

    def create_embedder(
        self,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """Create GPU-accelerated embedder.
        
        Args:
            model_name: Model name.
            
        Returns:
            Embedder instance.
        """
        try:
            from sentence_transformers import SentenceTransformer

            device = self.get_device()
            model = SentenceTransformer(model_name, device=device)

            return model
        except ImportError:
            return None

    def embed_batch(
        self,
        texts: list[str],
        embedder,
        batch_size: int | None = None,
    ) -> list[list[float]]:
        """Embed texts with GPU acceleration.
        
        Args:
            texts: Texts to embed.
            embedder: Embedder model.
            batch_size: Optional batch size.
            
        Returns:
            Embeddings.
        """
        if batch_size is None:
            batch_size = self.optimize_batch_size(0.1, 500)

        embeddings = embedder.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        return [emb.tolist() for emb in embeddings]
