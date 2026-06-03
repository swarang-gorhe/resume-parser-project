from __future__ import annotations

import re
from typing import Any

from resume_parser.domain.extractors.base import BaseExtractor


class ContactExtractor(BaseExtractor):
    PROMPT_TEMPLATE = (
        "Extract the candidate's full name, email address, phone number, LinkedIn profile URL, and location from this resume. "
        "Return only JSON with keys name, email, phone, linkedin, location.\n\nResume:\n{text}"
    )

    def extract(self, text: str) -> tuple[dict[str, Any], float]:
        prompt = self.PROMPT_TEMPLATE.format(text=text)
        raw = self._run_inference(prompt)
        result: dict[str, Any] = {}
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", raw)
        phone_match = re.search(r"(\+?\d[\d\s\-().]{7,}\d)", raw)
        linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", raw, re.IGNORECASE)
        result["email"] = email_match.group(0) if email_match else None
        result["phone"] = phone_match.group(0) if phone_match else None
        result["linkedin"] = (
            f"https://{linkedin_match.group(0)}" if linkedin_match else None
        )
        name_line = raw.splitlines()[0].strip() if raw else None
        result["name"] = name_line if name_line and (result["email"] is None or result["email"] not in name_line) else None
        result["location"] = None
        confidence = self._compute_confidence(raw, required_pattern=r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
        return result, confidence
