from __future__ import annotations

import hashlib
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import bleach

try:
    import magic
except ImportError:  # pragma: no cover
    magic = None

from resume_parser.core.config import Settings
from resume_parser.core.exceptions import (
    FileSizeLimitExceededError,
    MIMETypeMismatchError,
    SanitizationError,
)
from resume_parser.core.logging import get_logger
from resume_parser.domain.schema import ResumeOutput


PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b[A-Z]{1}[0-9]{7}\b"),
    re.compile(r"\b[0-9]{9}\b"),
]


class Sanitizer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)

    def validate_file(self, file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            raise SanitizationError("Input file does not exist or is not a file.")
        if file_path.stat().st_size > self.settings.MAX_FILE_SIZE_BYTES:
            raise FileSizeLimitExceededError("File exceeds maximum allowed size.")
        if ".." in file_path.name or file_path.name.startswith("/"):
            raise SanitizationError("Filename contains prohibited path traversal or absolute path.")
        mime_type = self._detect_mime_type(file_path)
        extension = file_path.suffix.lower()
        if extension == ".pdf" and mime_type != "application/pdf":
            raise MIMETypeMismatchError("PDF file MIME type mismatch.")
        if extension == ".docx" and (mime_type is None or "wordprocessingml" not in mime_type):
            raise MIMETypeMismatchError("DOCX file MIME type mismatch.")
        if extension == ".doc" and mime_type not in {"application/msword", "application/vnd.ms-office"}:
            raise MIMETypeMismatchError("DOC file MIME type mismatch.")

    def _detect_mime_type(self, file_path: Path) -> str | None:
        if magic is not None:
            try:
                return magic.from_file(str(file_path), mime=True)
            except Exception:
                pass
        raw_bytes = file_path.read_bytes()[:8]
        if raw_bytes.startswith(b"%PDF-"):
            return "application/pdf"
        if raw_bytes.startswith(b"PK"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if raw_bytes.startswith(b"\xd0\xcf\x11\xe0"):
            return "application/msword"
        return None

    def sanitize_text(self, text: str) -> str:
        cleaned = text.replace("\x00", "")
        cleaned = re.sub(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]", "", cleaned)
        cleaned = unicodedata.normalize("NFKC", cleaned)
        cleaned = bleach.clean(cleaned, tags=[], strip=True)
        cleaned = self.truncate_text(cleaned)
        return cleaned

    def truncate_text(self, text: str, max_tokens: int = 8000) -> str:
        tokens = text.split()
        if len(tokens) <= max_tokens:
            return text
        return " ".join(tokens[:max_tokens])

    def sanitize_output(self, data: dict[str, Any]) -> ResumeOutput:
        sanitized = self._redact_pii(data)
        try:
            resume_output = ResumeOutput(**sanitized)
        except Exception as exc:  # noqa: BLE001
            raise SanitizationError("Output validation failed") from exc
        return resume_output

    def _redact_pii(self, payload: dict[str, Any]) -> dict[str, Any]:
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, str):
                redacted[key] = self._redact_text(value)
            elif isinstance(value, list):
                redacted[key] = [self._redact_text(item) if isinstance(item, str) else item for item in value]
            elif isinstance(value, dict):
                redacted[key] = self._redact_pii(value)
            else:
                redacted[key] = value
        return redacted

    def _redact_text(self, text: str) -> str:
        for pattern in PII_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text

    def hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
