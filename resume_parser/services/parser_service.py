from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from resume_parser.core.config import Settings
from resume_parser.core.exceptions import ResumeParserError
from resume_parser.core.logging import get_logger
from resume_parser.domain.schema import ContactInfo, ResumeOutput
from resume_parser.domain.section_detector import SectionDetector
from resume_parser.domain.extractors.contact import ContactExtractor
from resume_parser.domain.extractors.education import EducationExtractor
from resume_parser.domain.extractors.experience import ExperienceExtractor
from resume_parser.domain.extractors.skills import SkillsExtractor
from resume_parser.domain.extractors.misc import MiscExtractor
from resume_parser.infrastructure.file_reader import FileReaderFactory
from resume_parser.infrastructure.model_loader import ModelLoader
from resume_parser.infrastructure.sanitizer import Sanitizer


class ResumeParserService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)
        self.sanitizer = Sanitizer(settings)
        self.section_detector = SectionDetector()
        self.model_loader = ModelLoader.get_instance(settings)
        self.model = self.model_loader.model
        self.tokenizer = self.model_loader.tokenizer

    def parse_resume(self, file_path: Path) -> ResumeOutput:
        self.logger.info("Starting resume parse.", extra={"event": "parser.start"})
        self.sanitizer.validate_file(file_path)
        reader = FileReaderFactory.get_reader(file_path)
        raw_text = reader.read_text()
        sanitized_text = self.sanitizer.sanitize_text(raw_text)
        sections = self.section_detector.detect_sections(sanitized_text)
        parse_results = self._extract_sections(sections, sanitized_text)
        data = self._assemble_output(parse_results, file_path.name, raw_text)
        resume_output = self.sanitizer.sanitize_output(data)
        self.logger.info("Resume parse completed.", extra={"event": "parser.completed"})
        return resume_output

    def _extract_sections(self, sections: dict[str, str], full_text: str) -> dict[str, dict]:
        contact_text = sections.get("contact", full_text)
        education_text = sections.get("education", full_text)
        experience_text = sections.get("experience", sections.get("work experience", full_text))
        skills_text = sections.get("skills", full_text)
        misc_text = "\n".join(
            sections.get(section, "")
            for section in ["certifications", "projects", "languages", "summary"]
            if sections.get(section)
        )

        contact, contact_conf = ContactExtractor(self.model, self.tokenizer, self.settings).extract(contact_text)
        education, education_conf = EducationExtractor(self.model, self.tokenizer, self.settings).extract(education_text)
        experience, experience_conf = ExperienceExtractor(self.model, self.tokenizer, self.settings).extract(experience_text)
        skills, skills_conf = SkillsExtractor(self.model, self.tokenizer, self.settings).extract(skills_text)
        misc, misc_conf = MiscExtractor(self.model, self.tokenizer, self.settings).extract(misc_text or full_text)

        return {
            "candidate": {"data": contact, "confidence": contact_conf},
            "education": {"data": education, "confidence": education_conf},
            "work_experience": {"data": experience, "confidence": experience_conf},
            "skills": {"data": skills, "confidence": skills_conf},
            "misc": {"data": misc, "confidence": misc_conf},
        }

    def _assemble_output(self, parse_results: dict[str, dict], source_file: str, raw_text: str) -> dict[str, object]:
        overall = sum(item["confidence"] for item in parse_results.values()) / len(parse_results)
        contact_data = parse_results["candidate"]["data"]
        return {
            "parser_version": self.settings.PARSER_VERSION,
            "parsed_at": datetime.now(timezone.utc),
            "source_file": source_file,
            "confidence_scores": {
                "contact": parse_results["candidate"]["confidence"],
                "education": parse_results["education"]["confidence"],
                "experience": parse_results["work_experience"]["confidence"],
                "skills": parse_results["skills"]["confidence"],
                "misc": parse_results["misc"]["confidence"],
                "overall": round(overall, 2),
            },
            "candidate": ContactInfo(**contact_data),
            "education": parse_results["education"]["data"],
            "work_experience": parse_results["work_experience"]["data"],
            "skills": parse_results["skills"]["data"],
            "certifications": parse_results["misc"]["data"].get("certifications", []),
            "projects": parse_results["misc"]["data"].get("projects", []),
            "languages": parse_results["misc"]["data"].get("languages", []),
            "summary": parse_results["misc"]["data"].get("summary"),
            "raw_text_hash": self.sanitizer.hash_text(raw_text),
        }
