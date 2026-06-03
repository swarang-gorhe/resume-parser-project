class ResumeParserError(Exception):
    """Base exception for parser errors."""


class UnsupportedFileTypeError(ResumeParserError):
    pass


class FileSizeLimitExceededError(ResumeParserError):
    pass


class FileCorruptedError(ResumeParserError):
    pass


class MIMETypeMismatchError(ResumeParserError):
    pass


class ModelInferenceError(ResumeParserError):
    pass


class SanitizationError(ResumeParserError):
    pass


class ConversionError(ResumeParserError):
    pass
