"""Interactive CLI manual testing tool for the Tenant Rights RAG system."""

import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
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

from src.rag_pipeline import answer


def print_banner():
    print("\n" + "=" * 80)
    print("      INDIAN TENANT RIGHTS - INTERACTIVE LEGAL RAG ASSISTANT (CLI)")
    print("=" * 80)
    print("Commands:")
    print("  * Type any question about tenant rights, rent, deposits, evictions, etc.")
    print("  * Type 'jurisdiction <name>' (e.g., 'jurisdiction Delhi' or 'jurisdiction Bengaluru')")
    print("  * Type 'exit', 'quit', or 'q' to close the session.")
    print("=" * 80 + "\n")


def run_interactive_session():
    current_jurisdiction: Optional[str] = "Bengaluru"
    print_banner()

    print(f"[Active Jurisdiction: {current_jurisdiction}]")

    while True:
        try:
            user_input = input("\n[Tenant Question] > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting session. Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Exiting session. Goodbye!")
            break

        # Command to switch jurisdiction
        if user_input.lower().startswith("jurisdiction "):
            parts = user_input.split(maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                new_jur = parts[1].strip()
                if new_jur.lower() == "none" or new_jur.lower() == "general":
                    current_jurisdiction = None
                    print(f"-> Jurisdiction set to: General (All India)")
                else:
                    current_jurisdiction = new_jur.capitalize()
                    print(f"-> Jurisdiction set to: {current_jurisdiction}")
            continue

        print("\nSearching legal database & generating guidance...")
        print("-" * 80)

        try:
            result = answer(
                query=user_input,
                jurisdiction=current_jurisdiction,
                return_details=True
            )

            assert isinstance(result, dict)

            # Display retrieved sources
            print("\n--- RETRIEVED LEGAL SOURCES ---")
            for idx, chunk in enumerate(result["retrieved_chunks"], start=1):
                raw_title = chunk.get("title", chunk.get("doc_id", "Unknown"))
                safe_title = raw_title.encode('ascii', errors='replace').decode('ascii')
                source_type = chunk.get("source_type", "DOC").upper()
                score = chunk.get("score", 0.0)
                jur = chunk.get("jurisdiction", "General")
                print(f"  [{idx}] {source_type} ({jur}) | Score: {score:.4f} | {safe_title[:60]}")

            # Display generated legal answer
            print("\n--- AI LEGAL GUIDANCE ---")
            safe_answer = result["answer"].encode('ascii', errors='replace').decode('ascii')
            print(safe_answer)
            print("-" * 80)

        except Exception as e:
            print(f"\n[Error generating response]: {e}")


if __name__ == "__main__":
    run_interactive_session()
