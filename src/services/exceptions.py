class DocumentImportError(ValueError):
    """A document could not be safely imported."""


class DuplicateDocumentError(DocumentImportError):
    """The same PDF has already been imported."""
