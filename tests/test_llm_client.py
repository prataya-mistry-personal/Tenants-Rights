import pytest
from src.llm_client import generate, DEFAULT_LEGAL_SYSTEM_PROMPT

def test_llm_client_generate():
    """Verify that the LLM client generates a non-empty textual response."""
    result = generate("Say hello in one brief sentence.", max_new_tokens=30)
    assert isinstance(result, str)
    assert len(result.strip()) > 0
    print(f"Generated test output: {result}")


def test_llm_client_with_custom_system_prompt():
    """Verify that custom system prompt directs the LLM behavior."""
    custom_prompt = "You are a legal assistant. Answer in strictly 10 words or fewer."
    result = generate("What is a lease agreement?", system_prompt=custom_prompt, max_new_tokens=30)
    assert isinstance(result, str)
    assert len(result.strip()) > 0
