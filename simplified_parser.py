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
        lines = text.split("\n")[:3]  # First 3 lines typically contain contact info
        
        # Regex patterns for common contact fields
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        phone_pattern = r"[\+]?[\d\s\-\(\)]{10,}"
        linkedin_pattern = r"linkedin\.com/in/[\w\-]+"

        email = next((re.findall(email_pattern, line) for line in lines if re.search(email_pattern, line)), [None])[0] if any(re.search(email_pattern, line) for line in lines) else None
        phone = next((re.findall(phone_pattern, line) for line in lines if re.search(phone_pattern, line)), [None])[0] if any(re.search(phone_pattern, line) for line in lines) else None
        linkedin = next((re.findall(linkedin_pattern, line) for line in lines if re.search(linkedin_pattern, line)), [None])[0] if any(re.search(linkedin_pattern, line) for line in lines) else None

        # Use ML model to extract name from first line
        prompt = f"Extract the candidate's full name from: {lines[0] if lines else ''}"
        name = self._infer(prompt, max_length=50) if lines else None

        return {
            "name": name if name and name.lower() != "unknown" else None,
            "email": email,
            "phone": phone,
            "linkedin": linkedin,
            "location": None,  # Can be enhanced with additional logic
        }

    def extract_education(self, text: str) -> list:
        """Extract education entries (institution, degree, field, year)."""
        prompt = f"""Extract education information as JSON array with fields: institution, degree, field_of_study, graduation_year.
        Resume text: {text[:6000]}"""
        
        response = self._infer(prompt, max_length=512)
        try:
            # Try to parse JSON from response
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fallback: regex-based extraction
        education_entries = []
        year_pattern = r"\b(?:19|20)\d{2}\b"
        years = re.findall(year_pattern, text)
        if years:
            graduation_year = int(years[0]) if years else None
            education_entries.append({
                "institution": "Unknown",
                "degree": "Degree",
                "field_of_study": "Field",
                "graduation_year": graduation_year,
            })
        return education_entries

    def extract_experience(self, text: str) -> list:
        """Extract work experience entries."""
        prompt = f"""Extract work experience as JSON array with: company, position, duration, description.
        Resume text: {text[:10000]}"""
        
        response = self._infer(prompt, max_length=512)
        try:
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, TypeError):
            pass
        
        return []

    def extract_skills(self, text: str) -> dict:
        """Extract technical and soft skills."""
        prompt = f"Extract all skills from this resume. Separate technical (Python, AWS, etc) from soft skills (leadership, communication, etc): {text[:8000]}"
        
        response = self._infer(prompt, max_length=256)
        
        # Simple heuristic to separate skills
        technical_keywords = {"python", "java", "aws", "kubernetes", "docker", "sql", "pytorch", "tensorflow", "git"}
        skills = [s.strip() for s in response.split(",")]
        
        technical = [s for s in skills if any(kw in s.lower() for kw in technical_keywords)]
        soft = [s for s in skills if s not in technical]
        
        return {
            "technical": technical if technical else skills[:5],  # First 5 as technical if none identified
            "soft": soft,
        }

    def extract_languages(self, text: str) -> list:
        """Extract languages mentioned in resume."""
        prompt = f"List all languages mentioned in this resume: {text}"
        response = self._infer(prompt, max_length=100)
        
        known_languages = {"English", "Spanish", "French", "German", "Mandarin", "Japanese", "Hindi", "Portuguese"}
        found = [lang for lang in known_languages if lang.lower() in response.lower()]
        return found if found else []

    def parse(self, text: str) -> dict:
        """Main parse method combining all extractors."""
        return {
            "contact": self.extract_contact(text),
            "education": self.extract_education(text),
            "experience": self.extract_experience(text),
            "skills": self.extract_skills(text),
            "languages": self.extract_languages(text),
        }
