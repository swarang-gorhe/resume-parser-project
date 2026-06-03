"""
Parser Core Utilities - File I/O, sanitization, and logging
Consolidated utility functions for file reading, text cleaning, and logging.
"""
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Optional

import docx
import pdfplumber


class FileReader:
    """Simple file reader for PDF and DOCX formats."""

    @staticmethod
    def read(file_path: Path) -> str:
        """Read file content based on extension."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return FileReader._read_pdf(file_path)
        elif suffix == ".docx":
            return FileReader._read_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    @staticmethod
    def _read_pdf(file_path: Path) -> str:
        """Extract text from PDF using pdfplumber."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    @staticmethod
    def _read_docx(file_path: Path) -> str:
        """Extract text from DOCX using python-docx."""
        doc = docx.Document(file_path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text


class TextSanitizer:
    """Clean and sanitize resume text for ML processing."""

    @staticmethod
    def sanitize(text: str, max_length: int = 8000) -> str:
        """
        Clean text by:
        - Removing null bytes and control characters
        - Normalizing whitespace
        - Removing HTML tags
        - Truncating to max length
        """
        # Remove null bytes and control characters
        text = "".join(ch for ch in text if ord(ch) >= 32 or ch in "\n\t\r")

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Normalize multiple spaces
        text = re.sub(r"\s+", " ", text)

        # Truncate if needed
        if len(text) > max_length:
            text = text[:max_length]

        return text.strip()

    @staticmethod
    def hash_text(text: str) -> str:
        """Generate SHA-256 hash of text for integrity tracking."""
        return hashlib.sha256(text.encode()).hexdigest()


class JSONLogger:
    """Structured JSON logging for production use."""

    def __init__(self, name: str = "resume_parser"):
        """Initialize JSON logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Only add handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(self, event_name: str, **kwargs) -> None:
        """Log structured event as JSON."""
        log_data = {"event": event_name, **kwargs}
        self.logger.info(json.dumps(log_data))

    def log_error(self, error_msg: str, exc_info: Optional[str] = None) -> None:
        """Log error with optional exception info."""
        log_data = {"event": "error", "message": error_msg}
        if exc_info:
            log_data["exception"] = exc_info
        self.logger.error(json.dumps(log_data))
