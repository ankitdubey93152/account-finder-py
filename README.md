# OSINT Account & Digital Footprint Analyzer

An ethical, high-confidence OSINT tool designed strictly for querying **publicly available digital footprints**.

---

## 🔒 Ethical & Operational Constraints

This application operates under strict ethical rules:

1. **Public Data Only**: Never bypasses login walls, CAPTCHAs, paywalls, or authentication flows.

2. **No Intrusion**: Never attempts brute-forcing, credential stuffing, or password recovery flows.
3. **No Private Scraping**: Content gated behind authentication is never scraped.
4. **Rate Limit Respect**: Enforces strict per-host rate limits, exponential backoff on HTTP 429, and respects platform limits.
5. **No Identity Inference**: Username lookups confirm **public existence and profile fields only**.
6. **Phone Metadata Limits**: Returns carrier, line type, and region metadata only—never attempts to find accounts or real-name identities tied to a phone number.
7. **Explicit Ownership Requirement for Email**: Email checks only run against self-confirmed owner emails for DNS and technical breach metadata.

---

## 🚀 Phase 1 Features

- **Pydantic Configuration Management**: Safe `.env` loading and settings validation.
- **Structured Logging**: `structlog` setup with JSON or formatted output.
- **Custom Exception Hierarchy**: Standardized error management across API and CLI boundaries.
- **Resilient Async HTTP Client**: Built on `httpx` with timeout management, automatic retries, exponential backoff, and HTTP 429 rate limit handling.
- **Host Rate Limiting**: Async token-bucket / semaphore concurrency control per host.
- **Database Engine & ORM**: SQLAlchemy 2.0 async engine with SQLite (`aiosqlite`) and Alembic migration scripts.
- **FastAPI Web Engine**: Clean application bootstrap serving `/health`.
- **Typer CLI**: Command-line interface root.

---

## 🛠️ Getting Started

### Installation

```bash
# Clone or navigate to directory
cd "ACCOUNT FINDER"

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in editable mode with development dependencies
pip install -e ".[dev]"
```

### Environment Configuration

Copy `.env.example` to `.env` and adjust settings as required:

```bash
cp .env.example .env
```

### Running the API

```bash
uvicorn api.main:app --reload
```

Check health endpoint:

```bash
curl http://127.0.0.1:8000/health
```


### Running CLI

```bash
osint version
osint health
```

### Running Tests

```bash
pytest
```
