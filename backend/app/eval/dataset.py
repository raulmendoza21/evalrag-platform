"""Eval dataset loader.

Format: JSONL, one item per line. Required keys:
- question (str)

Optional keys (enable extra metrics when present):
- expected_doc_filenames (list[str]) — enables recall@k / MRR by filename match
- reference_answer (str) — currently unused (reserved for future correctness judge)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class EvalItem:
    question: str
    expected_doc_filenames: tuple[str, ...] = field(default_factory=tuple)
    reference_answer: str | None = None

    @property
    def has_retrieval_label(self) -> bool:
        return len(self.expected_doc_filenames) > 0


def load_dataset(path: str | Path) -> list[EvalItem]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found: {p}")
    items: list[EvalItem] = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {i} of {p}: {exc}") from exc
        if "question" not in raw or not str(raw["question"]).strip():
            raise ValueError(f"Missing 'question' on line {i} of {p}")
        items.append(
            EvalItem(
                question=str(raw["question"]).strip(),
                expected_doc_filenames=tuple(raw.get("expected_doc_filenames") or ()),
                reference_answer=raw.get("reference_answer"),
            )
        )
    if not items:
        raise ValueError(f"Dataset {p} is empty")
    return items
