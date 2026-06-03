# Resume Parser - Simplified Architecture Guide

## 📁 Simplified Project Structure

```
resume-parsing-test/
├── app.py                    # FastAPI HTTP server (main API)
├── main_cli.py              # CLI interface for batch processing
├── simplified_parser.py      # ML-powered extraction logic (ResumeAgent)
├── parser_core.py           # Utilities: FileReader, TextSanitizer, JSONLogger
├── models.py                # Pydantic schemas for validation & serialization
├── requirements_simple.txt  # Production dependencies only
├── .env.example             # Configuration template
├── .gitignore              # Git ignore rules
└── README.md               # Original documentation
```

## 🎯 Why Simplified?

### Before: 4-Layer Enterprise Architecture
- `resume_parser/` (9 subdirectories)
- 23+ Python files
- Deep nesting (extractors/base.py, infrastructure/*, domain/*)
- High abstraction overhead

### After: 3-File Core Architecture
- **`models.py`** - All Pydantic schemas (Contact, Education, Skills, ParsedResume)
- **`parser_core.py`** - All utilities (FileReader, TextSanitizer, JSONLogger)
- **`simplified_parser.py`** - All extraction logic (`ResumeAgent` class)
- **`app.py`** - FastAPI server as AI resume parsing agent
- **`main_cli.py`** - CLI interface

**Benefits:**
- ✅ Easier to understand - all related code in one place
- ✅ Fewer files to maintain
- ✅ Clear separation of concerns
- ✅ Better for FastAPI-focused use case
- ✅ Faster to modify and debug

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_simple.txt
```

### 2. Run FastAPI Server
```bash
python app.py
# Or: uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test API Endpoint
```bash
curl -X POST http://localhost:8000/parse-resume \
  -F "file=@sample_resume.docx"
```

### 4. Use CLI
```bash
python main_cli.py --file sample_resume.docx --output result.json
```

---

## 📝 Code Comments - Key Components

### `simplified_parser.py` - ML Extraction Logic

```python
class ResumeAgent:
    """AI-powered resume parsing agent for extracting structured resume sections."""
    
    def __init__(self, model_name: str = "google/flan-t5-large"):
        """Initialize model once on class instantiation."""
        # Auto-detects: CUDA > MPS > CPU
        device = "cuda" if torch.cuda.is_available() else ...
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    
    def _infer(self, prompt: str, max_length: int = 256) -> str:
        """Run inference in torch.inference_mode() for memory efficiency."""
        with torch.inference_mode():  # No gradients, optimized memory
            outputs = self.model.generate(**inputs, max_new_tokens=max_length)
    
    def extract_contact(self, text: str) -> dict:
        """Extract: name (ML), email (regex), phone (regex), LinkedIn (regex)"""
        # Regex fallbacks are fast and reliable for structured data
        # ML model used only for name extraction
    
    def parse(self, text: str) -> dict:
        """Main parse orchestrator combining all extractors."""
```

### `parser_core.py` - Utilities

```python
class FileReader:
    """Handle PDF and DOCX file reading."""
    @staticmethod
    def read(file_path: Path) -> str:
        """Dispatches to _read_pdf() or _read_docx() based on extension."""

class TextSanitizer:
    """Clean text for ML processing."""
    @staticmethod
    def sanitize(text: str, max_length: int = 8000) -> str:
        """Remove null bytes, HTML, normalize whitespace, truncate."""
        # Security: prevents prompt injection and memory issues

class JSONLogger:
    """Structured JSON logging for production."""
    def log_event(self, event_name: str, **kwargs) -> None:
        """Never logs raw text - only event names and metadata."""
```

### `app.py` - FastAPI Server

```python
@app.post("/parse-resume")
@limiter.limit("10/minute")  # Rate limiting per IP
async def parse_resume(request: Request, file: UploadFile = File(...)):
    """
    1. Validate file (type, size)
    2. Read file content
    3. Sanitize text
    4. Run extraction
    5. Build Pydantic model (auto validation)
    6. Return JSON response
    """
    request_id = str(uuid4())  # Tracing ID
    
    # Lazy load model once per request
    parsed_data = extractor.parse(sanitized_text)
    
    # Pydantic handles serialization automatically
    return JSONResponse(
        content={
            "request_id": request_id,
            "data": resume.model_dump(mode="json"),
        }
    )
```

### `main_cli.py` - CLI Interface

```python
def main():
    """
    CLI flow:
    1. Parse arguments (--file, --output)
    2. Validate file exists & type
    3. Read & sanitize
    4. Initialize model (can take 30-60s first run)
    5. Extract resume data
    6. Build Pydantic model
    7. Output JSON to stdout + optional file
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--output", default=None)
```

---

## 🔄 Data Flow

### FastAPI Flow
```
HTTP Request
    ↓
[app.py] parse_resume()
    ↓
FileReader.read() → Load PDF/DOCX
    ↓
TextSanitizer.sanitize() → Clean text
    ↓
ResumeExtractor.parse() → Extract data using ML
    ↓
ParsedResume (Pydantic) → Validate & serialize
    ↓
JSON Response → HTTP 200 + request_id
```

### CLI Flow
```
CLI Arguments
    ↓
[main_cli.py] main()
    ↓
FileReader.read() → Load file
    ↓
TextSanitizer.sanitize() → Clean
    ↓
ResumeExtractor.parse() → Extract
    ↓
ParsedResume (Pydantic) → Validate
    ↓
JSON to stdout + file
```

---

## 📊 JSON Output Format

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "parser_version": "1.0.0",
    "parsed_at": "2026-06-03T12:34:56.789Z",
    "source_file": "resume.docx",
    "confidence_scores": {
      "contact": 0.8,
      "education": 0.95,
      "experience": 0.9,
      "skills": 0.85,
      "languages": 0.75,
      "overall": 0.85
    },
    "candidate": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1-555-0123",
      "linkedin": "linkedin.com/in/johndoe",
      "location": "San Francisco, CA"
    },
    "education": [
      {
        "institution": "Stanford University",
        "degree": "MS Computer Science",
        "field_of_study": "Machine Learning",
        "graduation_year": 2023
      }
    ],
    "experience": [
      {
        "company": "Tech Corp",
        "position": "Senior ML Engineer",
        "duration": "2023-Present",
        "description": "Led recommendation system team"
      }
    ],
    "skills": {
      "technical": ["Python", "PyTorch", "AWS", "Kubernetes"],
      "soft": ["Leadership", "Communication"]
    },
    "languages": ["English", "Spanish"],
    "raw_text_hash": "abc123def456..."
  }
}
```

---

## 🔧 Configuration

### `.env.example`
```
# Model Configuration
MODEL_NAME=google/flan-t5-large

# API Configuration
RATE_LIMIT=10/minute
MAX_FILE_SIZE_BYTES=10485760  # 10MB

# Logging
LOG_LEVEL=INFO
```

---

## ⚡ Performance Notes

| Task | Time | Notes |
|------|------|-------|
| Model load (first run) | 30-60s | Downloads ~3.1GB |
| Model load (cached) | 1-2s | From disk cache |
| Single resume parse | 3-8s | Depends on resume length |
| API response | 5-10s | Includes model load first time |

---

## 🛡️ Security Features

✅ **File Validation**
- Type check (PDF/DOCX only)
- Size limit (10MB default)
- No path traversal

✅ **Text Sanitization**
- Removes null bytes
- Strips HTML
- Normalizes whitespace
- No raw text in logs

✅ **API Rate Limiting**
- 10 requests/minute per IP
- Prevents DDoS

✅ **Structured Logging**
- Only hashes raw text (never logs resume content)
- Event-based tracking
- Request IDs for tracing

---

## 🚀 Deployment

### Docker Option
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements_simple.txt .
RUN pip install -r requirements_simple.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Run with Uvicorn
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📞 Support

For issues or questions about the simplified architecture, refer to the code comments in each module. Each class and method includes docstrings explaining its purpose.
