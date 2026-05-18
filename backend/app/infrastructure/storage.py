"""Local filesystem storage for uploaded documents."""
from __future__ import annotations

import hashlib
from pathlib import Path


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_bytes(storage_dir: str, tenant_id: str, document_id: str, data: bytes) -> str:
    tenant_dir = Path(storage_dir) / tenant_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    path = tenant_dir / f"{document_id}.pdf"
    path.write_bytes(data)
    return str(path)
