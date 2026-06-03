"""
Simplified Resume Parser - Core extraction logic with integrated ML inference
Consolidates all extraction logic in a single module for clarity and maintainability.
"""
import json
import re
from typing import Any

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class ResumeAgent:
    """AI-powered resume parsing agent using a Flan-T5 model to extract structured resume sections."""

    def __init__(self, model_name: str = "google/flan-t5-large"):
        """Initialize model and tokenizer once on class instantiation."""
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
        self.model.eval()

    def _infer(self, prompt: str, max_length: int = 256) -> str:
        """Run model inference in evaluation mode for memory efficiency."""
        with torch.inference_mode():
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True).to(self.device)
            outputs = self.model.generate(**inputs, max_new_tokens=max_length)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def extract_contact(self, text: str) -> dict:
        """Extract contact information: name, email, phone, LinkedIn, location."""
        lines = text.split("\n")[:10]  # First 10 lines to find contact info
        
        # Regex patterns for common contact fields
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        phone_pattern = r"[\+]?[\d\s\-\(\)]{10,}"
        linkedin_pattern = r"linkedin\.com/in/[\w\-]+"

        email = next((re.findall(email_pattern, line) for line in lines if re.search(email_pattern, line)), [None])[0] if any(re.search(email_pattern, line) for line in lines) else None
        phone = next((re.findall(phone_pattern, line) for line in lines if re.search(phone_pattern, line)), [None])[0] if any(re.search(phone_pattern, line) for line in lines) else None
        linkedin = next((re.findall(linkedin_pattern, line) for line in lines if re.search(linkedin_pattern, line)), [None])[0] if any(re.search(linkedin_pattern, line) for line in lines) else None

        # Extract name: look for capitalized words at the beginning, not from ML
        name = None
        for line in lines[:5]:
            line = line.strip()
            if line and not any(keyword in line.lower() for keyword in ['email', 'phone', 'linkedin', 'github', 'portfolio', 'education', 'experience', '(', '+']):
                # Extract just capitalized words
                words = line.split()
                name_words = []
                for word in words:
                    if word and word[0].isupper():
                        name_words.append(word)
                    elif name_words and len(name_words) >= 2:
                        break
                if name_words and len(name_words) <= 4:
                    name = " ".join(name_words)
                    break

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "location": None,
        }

    def extract_education(self, text: str) -> list:
        """Extract education entries (institution, degree, field, year)."""
        # Look for education section marker and extract more context
        education_section = self._extract_section(text, ["education", "academic", "qualification"], max_chars=6000)
        
        prompt = f"""Extract each education entry as a line with format: Institution | Degree | Field | Year
Education section: {education_section[:3000]}

Return only the education entries, one per line."""
        
        response = self._infer(prompt, max_length=512)
        entries = []
        
        # Parse line-by-line output
        if response and response.strip():
            for line in response.split("\n"):
                line = line.strip()
                if not line or "|" not in line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 1 and parts[0]:
                    year = None
                    if len(parts) > 3:
                        year_match = re.search(r"\b(?:19|20)\d{2}\b", parts[3])
                        year = int(year_match.group(0)) if year_match else None
                    entries.append({
                        "institution": parts[0],
                        "degree": parts[1] if len(parts) > 1 else None,
                        "field_of_study": parts[2] if len(parts) > 2 else None,
                        "graduation_year": year,
                    })
        
        # Fallback: regex-based extraction for years
        if not entries:
            year_pattern = r"\b(?:19|20)\d{2}\b"
            years = re.findall(year_pattern, education_section)
            for year in years[:3]:  # Max 3 entries
                entries.append({
                    "institution": "Unknown",
                    "degree": None,
                    "field_of_study": None,
                    "graduation_year": int(year),
                })
        
        return entries

    def extract_experience(self, text: str) -> list:
        """Extract work experience entries."""
        # Extract experience section
        experience_section = self._extract_section(text, ["experience", "employment", "work history", "professional"], max_chars=10000)
        
        prompt = f"""Extract each work experience entry as a line with format: Company | Position | Duration | Brief Description
Experience section: {experience_section[:4000]}

Return only the experience entries, one per line."""
        
        response = self._infer(prompt, max_length=512)
        entries = []
        
        if response and response.strip():
            for line in response.split("\n"):
                line = line.strip()
                if not line or "|" not in line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 1 and parts[0]:
                    entries.append({
                        "company": parts[0],
                        "position": parts[1] if len(parts) > 1 else None,
                        "duration": parts[2] if len(parts) > 2 else None,
                        "description": parts[3] if len(parts) > 3 else None,
                    })
        
        return entries

    def extract_skills(self, text: str) -> dict:
        """Extract technical and soft skills."""
        skills_section = self._extract_section(text, ["skills", "technical", "competencies"], max_chars=8000)
        
        prompt = f"""Extract all skills and list them separated by commas. Format: skill1, skill2, skill3, ...
Skills section: {skills_section[:2000]}

Return only the comma-separated list."""
        
        response = self._infer(prompt, max_length=256)
        
        # Parse comma-separated skills
        all_skills = [s.strip() for s in response.split(",") if s.strip()]
        
        # Categorize skills
        technical_keywords = {"python", "java", "c++", "javascript", "typescript", "go", "rust",
                            "aws", "azure", "gcp", "kubernetes", "docker", "sql", "nosql",
                            "pytorch", "tensorflow", "keras", "sklearn", "numpy", "pandas",
                            "git", "linux", "windows", "react", "vue", "angular",
                            "fastapi", "django", "flask", "nodejs", "rest", "graphql",
                            "machine learning", "deep learning", "nlp", "computer vision",
                            "ai", "ml", "cv", "llm", "transformers", "bert", "gpt"}
        
        technical = [s for s in all_skills if any(kw in s.lower() for kw in technical_keywords)]
        soft = [s for s in all_skills if s not in technical]
        
        return {
            "technical": technical if technical else all_skills[:5],
            "soft": soft if soft else all_skills[5:10] if len(all_skills) > 5 else [],
        }

    def extract_languages(self, text: str) -> list:
        """Extract languages mentioned in resume."""
        prompt = f"List only the language names mentioned in this resume (e.g., English, Spanish, French): {text[:1000]}"
        response = self._infer(prompt, max_length=100)
        
        known_languages = {"English", "Spanish", "French", "German", "Mandarin", "Chinese", "Japanese", "Hindi", "Portuguese", "Russian", "Arabic", "Korean"}
        found = [lang for lang in known_languages if lang.lower() in response.lower()]
        return found if found else []

    def _extract_section(self, text: str, section_keywords: list, max_chars: int = 5000) -> str:
        """Extract a specific section from resume based on keywords."""
        text_lower = text.lower()
        best_pos = -1
        matched_keyword = None
        
        # Find the first occurrence of any section keyword
        for keyword in section_keywords:
            pos = text_lower.find(keyword.lower())
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos
                matched_keyword = keyword
        
        if best_pos == -1:
            return text[:max_chars]  # Return beginning if no section found
        
        # Extract content from this section onwards
        section_start = best_pos
        # Find the next section (heuristic: all caps word followed by colon/newline)
        remaining_text = text[section_start:]
        next_section = re.search(r"\n[A-Z][A-Z\s]{3,}[:\n]", remaining_text)
        
        if next_section:
            section_end = section_start + next_section.start()
        else:
            section_end = section_start + max_chars
        
        return text[section_start:section_end].strip()

    def parse(self, text: str) -> dict:
        """Main parse method combining all extractors."""
        return {
            "contact": self.extract_contact(text),
            "education": self.extract_education(text),
            "experience": self.extract_experience(text),
            "skills": self.extract_skills(text),
            "languages": self.extract_languages(text),
        }
