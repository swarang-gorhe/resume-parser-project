import re
from typing import Dict, List

SECTION_HEADERS = [
    "contact",
    "experience",
    "work experience",
    "professional experience",
    "education",
    "skills",
    "certifications",
    "projects",
    "languages",
    "summary",
    "objective",
]


class SectionDetector:
    def __init__(self) -> None:
        header_pattern = r"^(?P<header>{})\s*$".format("|".join(re.escape(h) for h in SECTION_HEADERS))
        self._section_regex = re.compile(header_pattern, flags=re.MULTILINE | re.IGNORECASE)

    def detect_sections(self, text: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        if not text:
            return sections

        splitter = list(self._section_regex.finditer(text))
        if not splitter:
            sections["summary"] = text.strip()
            return sections

        boundaries: List[tuple[int, str]] = []
        for match in splitter:
            header = match.group("header").strip().lower()
            boundaries.append((match.start(), header))

        for index, (start, header) in enumerate(boundaries):
            end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text)
            sections[header] = text[start:end].strip()

        return sections
