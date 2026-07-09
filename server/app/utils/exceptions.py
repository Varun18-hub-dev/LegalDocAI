class LegalException(Exception):
    """Base exception class for all LegalDocAI system errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class DocumentNotFound(LegalException):
    def __init__(self, message: str = "Requested legal document was not found."):
        super().__init__(message, status_code=404)

class RetrievalError(LegalException):
    def __init__(self, message: str = "An error occurred during database/vector retrieval."):
        super().__init__(message, status_code=500)

class EmbeddingError(LegalException):
    def __init__(self, message: str = "Failed to generate vector embeddings."):
        super().__init__(message, status_code=500)

class LLMTimeout(LegalException):
    def __init__(self, message: str = "The LLM request timed out."):
        super().__init__(message, status_code=504)

class InvalidIntent(LegalException):
    def __init__(self, message: str = "Invalid query intent detected."):
        super().__init__(message, status_code=400)

class InvalidDocument(LegalException):
    def __init__(self, message: str = "The provided document is invalid or corrupted."):
        super().__init__(message, status_code=400)

class UnsupportedFileType(LegalException):
    def __init__(self, message: str = "Unsupported file type. Only PDF documents are allowed."):
        super().__init__(message, status_code=400)
