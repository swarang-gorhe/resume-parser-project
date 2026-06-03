from __future__ import annotations

import re
from typing import Any

from resume_parser.domain.extractors.base import BaseExtractor


class SkillsExtractor(BaseExtractor):
    PROMPT_TEMPLATE = (
        "List all technical skills, tools, and technologies mentioned. Return as comma-separated values.\n\n" "{text}"
    )

    def extract(self, text: str) -> tuple[dict[str, Any], float]:
        prompt = self.PROMPT_TEMPLATE.format(text=text)
        raw = self._run_inference(prompt)
        skills = [skill.strip() for skill in re.split(r",|;", raw) if skill.strip()]
        technical = [skill for skill in skills if skill.lower() not in {"communication", "leadership", "teamwork", "problem solving"}]
        soft = [skill for skill in skills if skill.lower() in {"communication", "leadership", "teamwork", "problem solving", "collaboration"}]
        confidence = self._compute_confidence(raw, required_pattern=r"\w+")
        return {"technical": technical, "soft": soft}, confidence
