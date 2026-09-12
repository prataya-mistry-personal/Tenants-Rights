from src.config import load_config, AppConfig

def test_load_config():
    """Test loading configuration from default configs/config.yaml."""
    cfg = load_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.chunking.chunk_size == 512
    assert cfg.chunking.chunk_overlap == 64
    assert cfg.embeddings.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert cfg.embeddings.faiss_index_path == "data/embeddings/faiss.index"
    assert cfg.llm.model_name == "openai/gpt-oss-120b"
    assert cfg.llm.provider == "groq"
    assert "Bengaluru" in cfg.jurisdictions
    assert "Delhi" in cfg.jurisdictions
    assert "Other" in cfg.jurisdictions
    assert cfg.chunk_size == 512
    assert cfg.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
