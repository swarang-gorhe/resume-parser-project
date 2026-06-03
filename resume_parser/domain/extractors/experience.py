from __future__ import annotations

import re
from typing import Any, List

from resume_parser.domain.extractors.base import BaseExtractor


class ExperienceExtractor(BaseExtractor):
    PROMPT_TEMPLATE = (
        "Extract all work experiences. For each return exactly: Company | Position | Duration | Key responsibilities in one line. "
        "Separate entries with newline.\n\n{text}"
    )

    def extract(self, text: str) -> tuple[List[dict[str, Any]], float]:
        prompt = self.PROMPT_TEMPLATE.format(text=text)
        raw = self._run_inference(prompt)
        entries: list[dict[str, Any]] = []
        for line in raw.splitlines():
            parts = [part.strip() for part in line.split("|")]
            if not parts or len(parts) < 1:
                continue
            company = parts[0]
            position = parts[1] if len(parts) > 1 else None
            duration = parts[2] if len(parts) > 2 else None
            description = parts[3] if len(parts) > 3 else None
            entries.append(
                {
                    "company": company,
                    "position": position,
                    "duration": duration,
                    "description": description,
                }
            )
        confidence = self._compute_confidence(raw, required_pattern=r"\b(19|20)\d{2}\b")
        return entries, confidence
