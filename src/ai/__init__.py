"""Local AI infrastructure (Phase 2): Ollama client, LLM providers, model manager.

All inference uses locally hosted/open-weight models via configured runtimes.
No paid/proprietary AI APIs.
"""

from .config import AIConfig, load_ai_config
from .model_manager import ModelManager
from .ollama_provider import OllamaProvider
from .provider import LLMProvider

__all__ = [
    "AIConfig",
    "LLMProvider",
    "ModelManager",
    "OllamaProvider",
    "load_ai_config",
]
