class RagBrainsException(Exception):
    """Base exception for RAG pipeline."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class UnsupportedVectorstoreError(RagBrainsException):
    """Raised when an unsupported vectorstore is specified."""
    pass
