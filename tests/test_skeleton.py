from pathlib import Path

def test_repo_structure():
    """Verify that all core folders in the repo skeleton exist."""
    required_dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/chunks"),
        Path("data/embeddings"),
        Path("data/eval"),
        Path("src"),
        Path("notebooks"),
        Path("frontend"),
        Path("tests"),
        Path("configs"),
    ]
    for d in required_dirs:
        assert d.exists() and d.is_dir(), f"Expected directory '{d}' to exist."
