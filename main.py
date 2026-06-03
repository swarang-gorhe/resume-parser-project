"""CLI entrypoint for the resume parser."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from resume_parser.core.config import Settings
from resume_parser.core.logging import configure_logging, get_logger
from resume_parser.services.parser_service import ResumeParserService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resume Parser CLI for structured resume extraction."
    )
    parser.add_argument("--file", required=True, help="Path to the resume file.")
    parser.add_argument("--output", help="Optional output JSON file path.")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="Log level override.",
    )
    parser.add_argument("--version", action="store_true", help="Show parser version.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.version:
        print("resume-parser 1.0.0")
        return 0

    settings = Settings()
    if args.log_level:
        settings.LOG_LEVEL = args.log_level
    configure_logging(settings)
    logger = get_logger(__name__)

    file_path = Path(args.file)
    if not file_path.exists() or not file_path.is_file():
        logger.error("File not found or not a file.", extra={"event": "cli.file_error"})
        print(json.dumps({"error": "File not found or not a file."}, indent=2))
        return 1

    parser_service = ResumeParserService(settings=settings)
    try:
        result = parser_service.parse_resume(file_path)
        output_json = result.model_dump_json(indent=2)
        print(output_json)
        if args.output:
            Path(args.output).write_text(output_json, encoding="utf-8")
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Parser execution failed.", exc_info=exc, extra={"event": "cli.execution_error"})
        print(json.dumps({"error": str(exc)}, indent=2))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
