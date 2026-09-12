"""Groq Cloud LLM inference client for legal answer generation."""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Ensure project root is in sys.path and load .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import io

# Ensure UTF-8 output on Windows consoles
for _stream in (sys.stdout, sys.stderr):
    if isinstance(_stream, io.TextIOWrapper):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

load_dotenv(PROJECT_ROOT / ".env")

from groq import Groq
from groq.types.chat import ChatCompletionMessageParam
from src.config import load_config


# System Prompt tailored for Indian Tenancy RAG Assistant
DEFAULT_LEGAL_SYSTEM_PROMPT = (
    "You are an expert AI legal information assistant specializing in Indian Tenant and Rental Law.\n"
    "Your objective is to provide accurate, grounded, and structured legal guidance to tenants in Indian metro cities (e.g., Bengaluru, Delhi NCR).\n\n"
    "Guidelines:\n"
    "1. Ground your answer strictly in the provided legal context (Statutes, Acts, and Court Judgments).\n"
    "2. Cite specific sections (e.g., Section 44 of the Karnataka Rent Act 1999, Section 11/20 of Model Tenancy Act 2021, Section 106/108 of Transfer of Property Act 1882) and case precedents where relevant.\n"
    "3. Provide practical, step-by-step next actions the tenant can take (e.g., preserving proof, issuing written notice, approaching Rent Authority or Consumer Forum).\n"
    "4. Maintain an objective, supportive, and professional legal tone.\n"
    "5. Always conclude with a concise legal disclaimer: 'Disclaimer: This information is for educational guidance and does not constitute formal legal advice.'"
)


class LLMClient:
    """Client for Groq Cloud LLM inference."""

    def __init__(self, api_key: Optional[str] = None):
        self.cfg = load_config()
        self.model_name = self.cfg.llm.model_name
        self.default_temperature = self.cfg.llm.temperature
        self.default_max_new_tokens = self.cfg.llm.max_new_tokens

        resolved_api_key = api_key or os.getenv("GROQ_API_KEY")
        if not resolved_api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Please add GROQ_API_KEY='your_key' to your .env file."
            )
        self.client = Groq(api_key=resolved_api_key)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        # Ensure sufficient token headroom for reasoning models
        requested_tokens = max_new_tokens or self.default_max_new_tokens
        max_tokens = max(requested_tokens, 512)
        temp = temperature if temperature is not None else self.default_temperature
        sys_prompt = system_prompt or DEFAULT_LEGAL_SYSTEM_PROMPT

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens,
            )
            msg = completion.choices[0].message
            response_text = msg.content or getattr(msg, "reasoning", "") or ""
            return response_text.strip()

        except Exception as e:
            raise RuntimeError(f"Groq API Error during generation: {e}") from e


# Global singleton instance
_LLM_INSTANCE: Optional[LLMClient] = None


def generate(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_new_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> str:
    """Module-level generation wrapper."""
    global _LLM_INSTANCE
    if _LLM_INSTANCE is None:
        _LLM_INSTANCE = LLMClient()
    return _LLM_INSTANCE.generate(
        prompt,
        system_prompt=system_prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature
    )


if __name__ == "__main__":
    test_prompt = "Can my landlord in Bengaluru cut off my water supply if I have a dispute over rent?"
    print("\n--- Testing Groq LLM Client ---")
    print(f"User Prompt: {test_prompt}\n")
    try:
        response_text = generate(test_prompt, max_new_tokens=300)
        print("--- Model Response ---")
        print(response_text)
        print("----------------------")
    except Exception as err:
        print(f"Test failed: {err}")
