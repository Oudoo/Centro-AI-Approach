"""
Aura (by Centro) — One-shot document ingestion CLI.

Walks a folder of text/markdown files, chunks + embeds them, and upserts into
the metadata-sandboxed vector store so RAG returns real answers immediately.

Metadata is derived per-file (so you can mix scopes in one run):
  * Convention:  <name>.<account_scope>.<min_role>.md   e.g. payroll.coastline.manager.md
  * Or pass global defaults via flags.

Usage:
    python -m scripts.ingest_docs --path ./sample_docs
    python -m scripts.ingest_docs --path ./docs --department hr \\
        --account-scope coastline --min-role agent

Run this from the `backend/` directory with your .env pointing at a live
embedding endpoint (Msty / Ollama) and Qdrant.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow `python scripts/ingest_docs.py` as well as `-m scripts.ingest_docs`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import ROLE_RANK, AccountScope  # noqa: E402
from core.ingest import ingest_document  # noqa: E402
from core.vector_db import get_vector_sandbox  # noqa: E402

TEXT_SUFFIXES = (".md", ".markdown", ".txt")


def derive_metadata(path: Path, args: argparse.Namespace) -> dict:
    """Infer scope/role from filename convention, falling back to CLI defaults."""
    account_scope = args.account_scope
    min_role = args.min_role
    parts = path.stem.split(".")
    if len(parts) >= 2 and parts[-1] in ROLE_RANK and parts[-2] in {s.value for s in AccountScope}:
        account_scope, min_role = parts[-2], parts[-1]
    elif len(parts) >= 2 and parts[-1] in {s.value for s in AccountScope}:
        account_scope = parts[-1]
    return {
        "department": args.department,
        "account_scope": account_scope,
        "min_role_required": min_role,
        "source": path.name,
        "doc_id": path.stem,
    }


async def run(args: argparse.Namespace) -> None:
    root = Path(args.path)
    if not root.exists():
        raise SystemExit(f"Path not found: {root}")

    files = [p for p in sorted(root.rglob("*")) if p.suffix.lower() in TEXT_SUFFIXES]
    if not files:
        raise SystemExit(f"No .md/.txt files under {root}")

    sandbox = await get_vector_sandbox()
    total_chunks = 0
    for path in files:
        meta = derive_metadata(path, args)
        n = await ingest_document(path.name, path.read_text(encoding="utf-8"), meta)
        total_chunks += n
        print(
            f"  ✓ {path.name:<40} {n:>3} chunks "
            f"[scope={meta['account_scope']}, min_role={meta['min_role_required']}]"
        )

    print(f"\nIngested {len(files)} file(s), {total_chunks} chunks into the vector store.")
    print(f"Collection now holds {await sandbox.count()} chunks total.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Aura one-shot RAG ingestion")
    ap.add_argument("--path", default="./sample_docs", help="Folder of documents")
    ap.add_argument("--department", default="general")
    ap.add_argument("--account-scope", default="global",
                    choices=[s.value for s in AccountScope])
    ap.add_argument("--min-role", default="agent", choices=list(ROLE_RANK))
    asyncio.run(run(ap.parse_args()))


if __name__ == "__main__":
    main()
