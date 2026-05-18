"""Domain exceptions."""


class EvalRAGError(Exception):
    """Base error."""


class DocumentNotFound(EvalRAGError):
    pass


class DuplicateDocument(EvalRAGError):
    """Same content_hash already ingested for this tenant."""


class IngestionError(EvalRAGError):
    pass


class EmbeddingError(EvalRAGError):
    pass
