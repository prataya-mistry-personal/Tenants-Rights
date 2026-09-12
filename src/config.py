"""Central configuration management for Tenant Rights RAG system."""

from pathlib import Path
from typing import List, Optional, Any, Dict
import yaml
from pydantic import BaseModel, Field


class ChunkingConfig(BaseModel):
    chunk_size: int = 512
    chunk_overlap: int = 64


class EmbeddingConfig(BaseModel):
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    dimension: int = 384
    faiss_index_path: str = "data/embeddings/faiss.index"
    chunk_ids_path: str = "data/embeddings/chunk_ids.jsonl"


class LLMConfig(BaseModel):
    provider: str = "groq"
    model_name: str = "openai/gpt-oss-120b"
    temperature: float = 0.1
    max_new_tokens: int = 1024


class RetrievalConfig(BaseModel):
    top_k: int = 4
    similarity_threshold: float = 0.6


class PathsConfig(BaseModel):
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    chunks_dir: str = "data/chunks"
    embeddings_dir: str = "data/embeddings"
    eval_dir: str = "data/eval"


class AppConfig(BaseModel):
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    jurisdictions: List[str] = Field(default_factory=lambda: ["Bengaluru", "Delhi", "Other"])
    paths: PathsConfig = Field(default_factory=PathsConfig)

    # Convenience shortcuts
    @property
    def chunk_size(self) -> int:
        return self.chunking.chunk_size

    @property
    def chunk_overlap(self) -> int:
        return self.chunking.chunk_overlap

    @property
    def embedding_model(self) -> str:
        return self.embeddings.model_name

    @property
    def faiss_index_path(self) -> str:
        return self.embeddings.faiss_index_path

    @property
    def llm_model(self) -> str:
        return self.llm.model_name


def _find_config_file(config_path: Optional[str] = None) -> Path:
    """Resolve config file path relative to current working directory or repo root."""
    if config_path:
        path = Path(config_path)
        if path.exists():
            return path

    candidates = [
        Path("configs/config.yaml"),
        Path(__file__).resolve().parent.parent / "configs" / "config.yaml",
        Path("config.yaml"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return Path("configs/config.yaml")


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from YAML file with fallback to defaults.
    
    Args:
        config_path: Optional file path to config YAML file.

    Returns:
        AppConfig: Validated application configuration instance.
    """
    resolved_path = _find_config_file(config_path)

    if resolved_path.exists():
        with open(resolved_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f) or {}
        return AppConfig(**raw_data)
    
    return AppConfig()


if __name__ == "__main__":
    cfg = load_config()
    print("Configuration loaded successfully:")
    print(cfg.model_dump_json(indent=2))
