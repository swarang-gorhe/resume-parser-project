from __future__ import annotations

import re
from typing import Any

from resume_parser.domain.extractors.base import BaseExtractor


class MiscExtractor(BaseExtractor):
    PROMPT_TEMPLATE = (
        "Extract certifications, projects, languages, and a short professional summary from this resume. "
        "Provide JSON with keys certifications, projects, languages, summary.\n\n{text}"
    )

    def extract(self, text: str) -> tuple[dict[str, Any], float]:
        prompt = self.PROMPT_TEMPLATE.format(text=text)
        raw = self._run_inference(prompt)
        certifications = re.findall(r"(?i)(Certified[^,;\n]+|Certification[^,;\n]+|AWS Certified[^,;\n]+)", raw)
        languages = re.findall(r"\b(?:English|Spanish|French|German|Mandarin|Hindi|Portuguese)\b", raw)
        project_lines = [line.strip() for line in raw.splitlines() if "project" in line.lower()]
        projects = [{"name": line, "description": line} for line in project_lines]
        summary_match = re.search(r'(?i)summary\s*:\s*"([^"]+)"', raw)
        summary = summary_match.group(1) if summary_match else None
        confidence = self._compute_confidence(raw, required_pattern=r"\bproject\b")
        return {
            "certifications": certifications,
            "projects": projects,
            "languages": list(dict.fromkeys(languages)),
            "summary": summary,
        }, confidence
