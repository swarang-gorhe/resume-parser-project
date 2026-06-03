# Resume Parser

A production-grade resume parser system designed for structured data extraction from PDF, DOCX, and DOC files. Built with clean layered architecture, enterprise-grade security, Pydantic schema validation, and scalable NLP model orchestration.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                        │
│            CLI (main.py) | FastAPI (/api/routes.py)         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 Application Layer                           │
│          ResumeParserService (orchestration)                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Domain Layer                             │
│   Extractors | SectionDetector | Schema Models              │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│               Infrastructure Layer                          │
│  FileReader | ModelLoader | Sanitizer | Logging             │
└─────────────────────────────────────────────────────────────┘
```

### Layers Explained

- **Presentation**: CLI for batch processing, FastAPI for HTTP endpoints
- **Application**: Orchestrates sanitization, reading, detection, extraction, validation
- **Domain**: Business logic—extractors, section detection, strict output schema
- **Infrastructure**: I/O, model management, security, observability

## 🔒 Security Features

- **File Validation**: MIME type detection (PDF/DOCX/DOC), file size limits, path traversal prevention
- **Text Sanitization**: Null byte stripping, control character removal, Unicode normalization, HTML tag removal
- **PII Redaction**: Automatic detection and redaction of SSN, passport numbers, phone patterns
- **Structured Logging**: JSON logs with hashed file identifiers—never raw text or paths
- **Input Truncation**: Automatic token truncation to prevent model overload (max 8000 tokens)

## 📋 Supported Output Schema

```json
{
  "parser_version": "1.0.0",
  "parsed_at": "2026-06-03T12:00:00Z",
  "source_file": "resume.pdf",
  "raw_text_hash": "sha256_hash_of_resume",
  "confidence_scores": {
    "contact": 0.95,
    "education": 0.88,
    "experience": 0.85,
    "skills": 0.92,
    "misc": 0.75,
    "overall": 0.87
  },
  "candidate": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567",
    "linkedin": "https://linkedin.com/in/johndoe",
    "location": "San Francisco, CA"
  },
  "education": [
    {
      "institution": "University of California",
      "degree": "MSc",
      "field_of_study": "Computer Science",
      "graduation_year": 2020
    }
  ],
  "work_experience": [
    {
      "company": "Tech Corp",
      "position": "Senior Software Engineer",
      "duration": "2020-2024",
      "description": "Led ML infrastructure and model deployment"
    }
  ],
  "skills": {
    "technical": ["Python", "PyTorch", "SQL", "Kubernetes"],
    "soft": ["Leadership", "Communication", "Problem Solving"]
  },
  "certifications": ["AWS Certified Solutions Architect"],
  "projects": [
    {
      "name": "Project Alpha",
      "description": "Built a recommendation engine"
    }
  ],
  "languages": ["English", "Spanish"],
  "summary": "Experienced ML engineer with 5+ years building production systems"
}
```

## 🚀 Quick Start

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/swarang-gorhe/resume-parsing-test.git
   cd resume-parsing-test
   ```

2. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy and configure environment:
   ```bash
   cp .env.example .env
   ```

### CLI Usage

Parse a single resume and output JSON:

```bash
python main.py --file resume.pdf --output result.json --log-level INFO
```

**Options:**
- `--file` — Path to resume file (PDF, DOCX, or DOC)
- `--output` — Optional output JSON file path (default: stdout)
- `--log-level` — Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
- `--version` — Show parser version

**Exit Codes:**
- `0` — Success
- `1` — File error
- `2` — Model error
- `3` — Parse error

### FastAPI Server

Start the API server for HTTP requests:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level info
```

**Endpoint:** `POST /parse-resume`

**Request:**
```bash
curl -X POST http://localhost:8000/parse-resume \
  -F "file=@resume.pdf"
```

**Response:**
```json
{
  "request_id": "uuid-string",
  "agent": {"name": "ResumeAgent", "mode": "AI parsing"},
  "data": {
    "parser_version": "1.0.0",
    "parsed_at": "2026-06-03T12:00:00Z",
    ...
  }
}
```

## 🤖 Model Strategy

### Primary Model: Google Flan-T5-Large
- Instruction-tuned, highly capable at structured extraction
- ~780M parameters, optimized for prompting
- Excellent reasoning and few-shot learning

### Fallback: Google Flan-T5-Base
- Automatically triggered if large model fails to load
- ~250M parameters, lower latency
- Maintains same API contract

### Device Selection
- **CUDA** (NVIDIA GPU) — fastest inference
- **MPS** (Apple Metal) — hardware acceleration on Mac
- **CPU** — fallback with INT8 quantization for reduced latency

### Inference Configuration
- Max tokens: 256 per completion
- Temperature: 0 (greedy decoding)
- Quantization: INT8 on CPU only
- Inference mode: Enabled to reduce memory footprint

## 📊 Confidence Scoring

Each section receives a confidence score (0.0–1.0) based on:
- Non-empty output (+0.7)
- Regex validation match (+0.2)
- All required fields present (+0.1)

**Overall score** is the weighted average of section scores.

## 📁 Project Structure

```
resume-parsing-test/
├── resume_parser/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # FastAPI endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings + environment config
│   │   ├── exceptions.py          # Custom exception hierarchy
│   │   └── logging.py             # Structured JSON logger
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── schema.py              # Pydantic output models
│   │   ├── section_detector.py    # Resume section splitter
│   │   └── extractors/
│   │       ├── __init__.py
│   │       ├── base.py            # Abstract BaseExtractor
│   │       ├── contact.py         # Contact info extraction
│   │       ├── education.py       # Education extraction
│   │       ├── experience.py      # Work experience extraction
│   │       ├── skills.py          # Skills extraction
│   │       └── misc.py            # Certifications, projects, languages
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── file_reader.py         # PDF/DOCX/DOC readers
│   │   ├── model_loader.py        # Thread-safe model singleton
│   │   └── sanitizer.py           # Input/output sanitization + PII redaction
│   └── services/
│       ├── __init__.py
│       └── parser_service.py      # Orchestration service
├── main.py                        # CLI entrypoint
├── requirements.txt               # Production dependencies
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
└── README.md                      # This file
```

## 🔧 Configuration

Create a `.env` file or set environment variables:

```env
MODEL_NAME=google/flan-t5-large
MAX_FILE_SIZE_BYTES=10485760
LOG_LEVEL=INFO
PARSER_VERSION=1.0.0
LIBREOFFICE_PATH=libreoffice
RATE_LIMIT=10/minute
```

## 📦 Dependencies

- **transformers** ≥4.40.0 — Hugging Face model loading
- **torch** ≥2.2.0 — Neural network inference
- **pdfplumber** ≥0.10.0 — PDF text extraction
- **python-docx** ≥1.1.0 — DOCX parsing
- **python-magic** ≥0.4.27 — MIME type detection
- **pydantic** ≥2.0.0 — Schema validation with strict typing
- **pydantic-settings** ≥2.0.0 — Environment-driven configuration
- **python-json-logger** ≥2.0.0 — Structured JSON logging
- **bleach** ≥6.0.0 — HTML sanitization
- **fastapi** ≥0.110.0 — HTTP API framework
- **uvicorn** ≥0.29.0 — ASGI server
- **slowapi** ≥0.1.9 — Rate limiting

## 📝 Example Workflow

### 1. Parse resume via CLI
```bash
python main.py --file sample_resume.pdf --output parsed_resume.json
```

### 2. Inspect JSON output
```bash
cat parsed_resume.json | jq '.confidence_scores'
```

### 3. Start API server
```bash
uvicorn resume_parser.api.routes:app --reload
```

### 4. Send resume via HTTP
```bash
curl -X POST http://localhost:8000/parse-resume \
  -F "file=@sample_resume.pdf" | jq '.data.candidate'
```

## 🛡️ Error Handling

The parser handles:
- **UnsupportedFileTypeError** — Non-PDF/DOCX/DOC files
- **FileSizeLimitExceededError** — Files exceeding 10MB
- **MIMETypeMismatchError** — MIME type doesn't match extension
- **ModelInferenceError** — Model loading or inference failure
- **SanitizationError** — Invalid file or text content
- **ConversionError** — DOC to DOCX conversion failure
- **FileCorruptedError** — Corrupted or unreadable file

All errors return structured JSON with error details and exit codes.

## 📈 Performance Considerations

- **Cold Start**: ~30s (first model load)
- **Warm Inference**: ~2-5s per resume (single GPU)
- **Memory**: ~3GB (Flan-T5-Large) / ~1GB (Base model)
- **Quantization**: INT8 on CPU reduces memory 4x

## 🔍 Observability

All operations logged as structured JSON with:
- `timestamp` — ISO 8601 datetime
- `level` — log level (INFO, DEBUG, ERROR, etc.)
- `event` — operation name (parser.start, model.inference, etc.)
- `duration_ms` — milliseconds for timed operations
- `file_hash` — SHA-256 hash of resume (never raw text)

Never includes:
- Raw resume text
- Full file paths
- PII (email, phone, SSN)

## 🚢 Deployment

### Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "resume_parser.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t resume-parser .
docker run -p 8000:8000 resume-parser
```

### Cloud Deployment

Compatible with:
- AWS Lambda + API Gateway (serverless)
- Google Cloud Run (containerized)
- Azure Container Instances (containerized)
- Kubernetes (horizontal scaling)

## 📞 Support

For issues or questions, refer to:
- [Pydantic v2 Migration Guide](https://docs.pydantic.dev/2.0/)
- [Transformers Documentation](https://huggingface.co/docs/transformers/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
