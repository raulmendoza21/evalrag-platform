"""Documents API."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.config import Settings, get_settings
from app.core.exceptions import IngestionError
from app.dependencies import get_tenant_id
from app.schemas.document_schema import DocumentOut, DocumentUploadResponse
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_BYTES = 20 * 1024 * 1024  # 20 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    tenant_id: UUID = Depends(get_tenant_id),
) -> DocumentUploadResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF is supported; got {file.content_type}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {MAX_BYTES // 1024 // 1024} MB)",
        )

    try:
        doc, deduplicated = await document_service.upload_and_index(
            settings=settings,
            tenant_id=tenant_id,
            filename=file.filename or "upload.pdf",
            data=data,
        )
    except IngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return DocumentUploadResponse(
        document=DocumentOut.model_validate(doc),
        deduplicated=deduplicated,
    )


@router.get("", response_model=list[DocumentOut])
async def list_documents(tenant_id: UUID = Depends(get_tenant_id)) -> list[DocumentOut]:
    rows = await document_service.list_for_tenant(tenant_id)
    return [DocumentOut.model_validate(r) for r in rows]


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: UUID, tenant_id: UUID = Depends(get_tenant_id)
) -> DocumentOut:
    doc = await document_service.get_for_tenant(tenant_id, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(doc)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_document(
    document_id: UUID,
    settings: Settings = Depends(get_settings),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Response:
    ok = await document_service.delete_for_tenant(settings, tenant_id, document_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
