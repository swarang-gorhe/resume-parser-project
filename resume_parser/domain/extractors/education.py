from __future__ import annotations

import re
from typing import Any, List

from resume_parser.domain.extractors.base import BaseExtractor


class EducationExtractor(BaseExtractor):
    PROMPT_TEMPLATE = (
        "Extract all education entries from this resume. For each entry return exactly: "
        "Institution | Degree | Field | Year. Separate entries with newline.\n\n{text}"
    )

    def extract(self, text: str) -> tuple[List[dict[str, Any]], float]:
        prompt = self.PROMPT_TEMPLATE.format(text=text)
        raw = self._run_inference(prompt)
        entries: list[dict[str, Any]] = []
        for line in raw.splitlines():
            parts = [part.strip() for part in line.split("|")]
            if not parts or len(parts) < 1:
                continue
            institution = parts[0]
            degree = parts[1] if len(parts) > 1 else None
            field = parts[2] if len(parts) > 2 else None
            year = None
            if len(parts) > 3:
                year_match = re.search(r"\b(19|20)\d{2}\b", parts[3])
                year = int(year_match.group(0)) if year_match else None
            entries.append(
                {
                    "institution": institution,
                    "degree": degree,
                    "field_of_study": field,
                    "graduation_year": year,
                }
            )
        confidence = self._compute_confidence(raw, required_pattern=r"\b(19|20)\d{2}\b")
        return entries, confidence
