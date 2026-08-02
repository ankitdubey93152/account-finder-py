# 🔍 OSINT Account & Digital Footprint Analyzer (`account-finder-py`)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An ethical, high-confidence, asynchronous OSINT (Open Source Intelligence) tool designed strictly for querying **publicly available digital footprints** across online platforms. 

Built with modern Python (3.11+), **`account-finder-py`** provides dual interfaces—a high-performance **FastAPI REST API** and an interactive **Typer CLI**—backed by an async token-bucket rate limiter, resilient HTTP client (`httpx`), and SQLAlchemy 2.0 async database persistence.

---

## 📋 Table of Contents

- [🔒 Ethical & Operational Constraints](#-ethical--operational-constraints)
- [🚀 Key Features](#-key-features)
- [🏗️ Architecture & Project Structure](#️-architecture--project-structure)
- [🌐 Supported Platforms](#-supported-platforms)
- [⚙️ Configuration Reference](#️-configuration-reference)
- [🛠️ Installation & Setup](#️-installation--setup)
- [💻 How to Run the Application](#-how-to-run-the-application)
  - [1. Running the CLI Interface](#1-running-the-cli-interface)
  - [2. Running the FastAPI Web Server](#2-running-the-fastapi-web-server)
  - [3. Running the Automated Test Suite](#3-running-the-automated-test-suite)
- [📊 Execution Results & Explanation](#-execution-results--explanation)
  - [CLI Output Examples](#cli-output-examples)
  - [REST API JSON Response Example](#rest-api-json-response-example)
  - [Field Explanation Matrix](#field-explanation-matrix)
  - [Test Suite Pass Results](#test-suite-pass-results)
- [🛠️ Extending Platform Support](#️-extending-platform-support)
- [📄 License](#-license)

---

## 🔒 Ethical & Operational Constraints

This application strictly enforces ethical OSINT standards:

1. **Public Data Only**: Queries only endpoints with public data contracts. Never bypasses login walls, CAPTCHAs, paywalls, or authentication flows.
2. **No Intrusion**: Zero attempt at credential testing, password guessing, brute-forcing, or account recovery probing.
3. **No Private Scraping**: Gated content is never accessed or scraped.
4. **Rate Limit Respect**: Enforces strict per-host rate limits, concurrency semaphores, and exponential backoff on HTTP 429.
5. **No Identity Inference**: Confirms public profile existence and metadata only—never correlates identities automatically without explicit data.

---

## 🚀 Key Features

- **⚡ Asynchronous Concurrency**: High-performance parallel scanning built on `asyncio` and `httpx.AsyncClient`.
- **🛡️ Resilient HTTP Engine**: Automatic retries, configurable timeouts, custom headers, and rate-limit backoff handling.
- **🎯 Multi-Strategy Detection**: Flexible evaluation logic supporting status codes, JSON field extraction, string presence, and string absence.
- **💾 Async Database Storage**: Automatic scan history and platform result recording into SQLite (`aiosqlite`) via SQLAlchemy 2.0 ORM with Alembic migrations.
- **🖥️ Dual Interface Support**:
  - **FastAPI Web Server**: Interactive OpenAPI/Swagger documentation, JSON REST API endpoints, and lifespan management.
  - **Rich Typer CLI**: Formatted terminal output with interactive tables, raw JSON dumping, CSV exporting, and file saving (`--output`).
- **🔧 Production-Grade Foundation**: Pydantic v2 settings management, structured logging (`structlog`), and comprehensive exception hierarchy.

---

## 🏗️ Architecture & Project Structure

```
ACCOUNT FINDER/
├── api/                        # FastAPI Web Layer
│   ├── routes/
│   │   ├── health.py           # Health check endpoint (/health)
│   │   └── username.py         # Username scan endpoint (/scan/username)
│   ├── __init__.py
│   └── main.py                 # FastAPI application entrypoint & lifespan
├── cli/                        # Command Line Interface Layer
│   ├── __init__.py
│   └── main.py                 # Typer CLI application (version, health, username commands)
├── core/                       # Core Infrastructure & Cross-Cutting Concerns
│   ├── config.py               # Pydantic BaseSettings management (.env loader)
│   ├── exceptions.py           # Custom exception hierarchy (OSINTError, etc.)
│   ├── http_client.py          # Resilient async httpx client with retry & rate limiting
│   ├── logging.py              # Structured logging configuration (structlog)
│   └── rate_limiter.py         # Per-host token bucket & concurrency limiter
├── database/                   # Database & Persistence Layer
│   ├── migrations/             # Alembic migration environment & revision scripts
│   ├── models.py               # SQLAlchemy 2.0 Async ORM models (ScanHistory, ScanResult)
│   └── session.py              # Async engine initialization & session generator
├── modules/                    # OSINT Scan Modules
│   └── username_search/
│       ├── detector.py         # Platform detection evaluator logic
│       ├── models.py           # Pydantic scan result schemas (ScanSummary, PlatformResult)
│       ├── platforms.py        # Declarative platform specification registry
│       └── scanner.py          # Async orchestrator scanning all target platforms
├── tests/                      # Automated Unit & Integration Tests
│   ├── integration/            # API & Scanner integration tests
│   ├── unit/                   # Config, Detector & HTTP Client unit tests
│   └── conftest.py             # Pytest async fixtures
├── .env.example                # Template for environment configuration
├── .gitignore                  # Git ignore rules for .venv, .env, *.db, etc.
├── alembic.ini                 # Alembic database migration config
├── pyproject.toml              # Project metadata & dependency definitions
└── README.md                   # Project documentation
```

### Database Schema

- **`scan_histories`**: Stores top-level metadata for each scan operation.
  - `id`: Primary key (Integer)
  - `scan_type`: Type of query (`username`, `email`, `phone`)
  - `target_query`: The target string queried
  - `created_at`: UTC timestamp of the scan execution
  - `status`: Execution status (`completed`, `failed`)
- **`scan_results`**: Individual platform check result tied to a scan history.
  - `id`: Primary key (Integer)
  - `scan_id`: Foreign Key referencing `scan_histories.id`
  - `platform_or_provider`: Platform name (e.g., `GitHub`, `GitLab`)
  - `target_url`: Evaluated profile URL
  - `exists`: Boolean outcome (`true`, `false`, or `null` if inconclusive)
  - `confidence`: Result confidence level (`high`, `low`)
  - `details`: JSON field storing platform metadata (bio, response time, etc.)
  - `error`: Error string if HTTP/network failure occurred

---

## 🌐 Supported Platforms

The username scanner evaluates public profile availability against platforms with explicit public endpoints:

| Platform | Endpoint Template | Detection Method | Existence Indicator |
| :--- | :--- | :--- | :--- |
| **GitHub** | `https://api.github.com/users/{username}` | `json_field` | JSON key `login` is present |
| **Reddit** | `https://www.reddit.com/user/{username}/about.json` | `json_field` | JSON key `data.name` is present |
| **GitLab** | `https://gitlab.com/{username}` | `text_absence` | HTML does **not** contain `"Page Not Found"` |
| **Docker Hub** | `https://hub.docker.com/v2/users/{username}/` | `status_code` | HTTP Status `200` |
| **Keybase** | `https://keybase.io/{username}` | `status_code` | HTTP Status `200` |

---

## ⚙️ Configuration Reference

All settings can be customized via environment variables or a local `.env` file:

| Setting | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `"OSINT Digital Footprint Analyzer"` | Application name string |
| `ENV` | `"development"` | Environment mode (`development`, `production`, `testing`) |
| `DEBUG` | `true` | Debug flag |
| `LOG_LEVEL` | `"INFO"` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `HOST` | `"127.0.0.1"` | Server host binding |
| `PORT` | `8000` | Server HTTP port |
| `DATABASE_URL` | `"sqlite+aiosqlite:///./osint.db"` | Async database connection URI |
| `DEFAULT_TIMEOUT_SECONDS` | `8.0` | HTTP request timeout in seconds |
| `GLOBAL_SCAN_TIMEOUT_SECONDS` | `60.0` | Maximum allowed duration for a complete scan batch |
| `MAX_CONCURRENT_REQUESTS` | `10` | Default concurrency limit for requests |
| `USER_AGENT` | `"OSINT-Analyzer/1.0 ..."` | HTTP User-Agent string sent in requests |

---

## 🛠️ Installation & Setup

### 1. Prerequisites
- **Python 3.11** or higher
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/ankitdubey93152/account-finder-py.git
cd account-finder-py
```

### 3. Create and Activate a Virtual Environment

**On Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
Install the package in editable mode with development tools:
```bash
pip install -e ".[dev]"
```

### 5. Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```

---

## 💻 How to Run the Application

### 1. Running the CLI Interface

The Typer CLI offers fast terminal-based footprint lookup.

#### Check Application Version:
```bash
python -m cli.main version
```

#### Check System Health:
```bash
python -m cli.main health
```

#### Run Username Scan (Default Table Output):
```bash
python -m cli.main username torvalds
```

#### Export Username Scan as JSON:
```bash
python -m cli.main username torvalds --format json
```

#### Export Username Scan to CSV File:
```bash
python -m cli.main username torvalds --format csv --output results.csv
```

---

### 2. Running the FastAPI Web Server

Start the asynchronous Uvicorn server:
```bash
uvicorn api.main:app --reload
```
or run `main.py` directly:
```bash
python -m api.main
```

Once running, access:
- **Interactive OpenAPI (Swagger) Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

#### API Endpoint Usage Example (`POST /scan/username`):

**cURL Request:**
```bash
curl -X POST "http://127.0.0.1:8000/scan/username" \
     -H "Content-Type: application/json" \
     -d '{"username": "torvalds", "concurrency": 15}'
```

---

### 3. Running the Automated Test Suite

Run unit and integration tests using `pytest`:
```bash
pytest
```
or via python:
```bash
python -m pytest
```

---

## 📊 Execution Results & Explanation

### CLI Output Examples

#### 1. Formatted Terminal Table Output (`--format table`):
```text
            Username scan: torvalds            
+---------------------------------------------+
| Platform   | Exists | Confidence | Response |
|------------+--------+------------+----------|
| GitHub     | yes    | high       | 750 ms   |
| Reddit     | no     | high       | 375 ms   |
| GitLab     | yes    | high       | 655 ms   |
| Docker Hub | yes    | high       | 280 ms   |
| Keybase    | yes    | high       | 1046 ms  |
+---------------------------------------------+
```

#### 2. Raw JSON Output (`--format json`):
```json
{
  "username": "torvalds",
  "total_platforms": 5,
  "found": 4,
  "not_found": 1,
  "errored": 0,
  "duration_ms": 1672,
  "results": [
    {
      "platform": "GitHub",
      "url": "https://api.github.com/users/torvalds",
      "exists": true,
      "confidence": "high",
      "bio": null,
      "avatar_url": null,
      "follower_count": null,
      "location": null,
      "website": null,
      "created_at": null,
      "error": null,
      "response_time_ms": 750,
      "checked_at": "2026-08-02T04:50:37.779675Z"
    },
    {
      "platform": "Reddit",
      "url": "https://www.reddit.com/user/torvalds/about.json",
      "exists": false,
      "confidence": "high",
      "error": null,
      "response_time_ms": 375,
      "checked_at": "2026-08-02T04:50:37.724081Z"
    },
    {
      "platform": "GitLab",
      "url": "https://gitlab.com/torvalds",
      "exists": true,
      "confidence": "high",
      "error": null,
      "response_time_ms": 655,
      "checked_at": "2026-08-02T04:50:37.874187Z"
    },
    {
      "platform": "Docker Hub",
      "url": "https://hub.docker.com/v2/users/torvalds/",
      "exists": true,
      "confidence": "high",
      "error": null,
      "response_time_ms": 280,
      "checked_at": "2026-08-02T04:50:37.601374Z"
    },
    {
      "platform": "Keybase",
      "url": "https://keybase.io/torvalds",
      "exists": true,
      "confidence": "high",
      "error": null,
      "response_time_ms": 1046,
      "checked_at": "2026-08-02T04:50:38.378659Z"
    }
  ]
}
```

---

### REST API JSON Response Example

When sending a `POST` request to `/scan/username`:

```json
{
  "username": "torvalds",
  "total_platforms": 5,
  "found": 4,
  "not_found": 1,
  "errored": 0,
  "duration_ms": 1420,
  "results": [
    {
      "platform": "GitHub",
      "url": "https://api.github.com/users/torvalds",
      "exists": true,
      "confidence": "high",
      "bio": null,
      "avatar_url": null,
      "follower_count": null,
      "location": null,
      "website": null,
      "created_at": null,
      "error": null,
      "response_time_ms": 620,
      "checked_at": "2026-08-02T10:20:37.779Z"
    }
  ]
}
```

---

### Field Explanation Matrix

| Field | Type | Description |
| :--- | :--- | :--- |
| `username` | `string` | Target account username passed in the scan request |
| `total_platforms` | `integer` | Count of platforms evaluated in this batch |
| `found` | `integer` | Count of platforms where profile existence was confirmed (`exists: true`) |
| `not_found` | `integer` | Count of platforms where profile does not exist (`exists: false`) |
| `errored` | `integer` | Count of platforms where request timed out or returned server error |
| `duration_ms` | `integer` | Total execution time in milliseconds for the scan batch |
| `platform` | `string` | Public target service name (e.g., `GitHub`, `GitLab`, `Docker Hub`) |
| `url` | `string` | Target endpoint URL requested |
| `exists` | `boolean \| null` | `true` if profile exists, `false` if not found, `null` if inconclusive |
| `confidence` | `string` | Evaluation confidence (`high` for exact indicator matches, `low` for 5xx/timeouts) |
| `response_time_ms` | `integer` | Platform-specific HTTP response latency in milliseconds |
| `checked_at` | `string` | ISO-8601 UTC timestamp of execution |

---

### Test Suite Pass Results

The repository includes comprehensive unit and integration tests covering the API endpoints, scanner engine, platform detector, HTTP client retry logic, and configuration loader:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1
rootdir: C:\Users\Ankit\Desktop\ACCOUNT FINDER
plugins: anyio-4.14.2, asyncio-1.4.0, respx-0.23.1
collected 12 items

tests\integration\test_health_api.py .                                   [  8%]
tests\integration\test_scanner.py .                                      [ 16%]
tests\unit\test_config.py .                                              [ 25%]
tests\unit\test_detector.py ......                                       [ 75%]
tests\unit\test_http_client.py ...                                       [100%]

============================= 12 passed in 6.60s ==============================
```

---

## 🛠️ Extending Platform Support

To add support for a new public platform, declare a new `PlatformSpec` entry in [`modules/username_search/platforms.py`](file:///c:/Users/Ankit/Desktop/ACCOUNT%20FINDER/modules/username_search/platforms.py):

```python
PlatformSpec(
    name="Dev.to",
    url_template="https://dev.to/api/users/by_username?url={username}",
    check_method="json_field",
    json_exists_path="username",
    enabled=True
)
```

No changes to scanner loops or database schemas are needed; the system automatically discovers and queries registered specs.

---

## 📄 License

This project is released under the **MIT License**. Refer to the [LICENSE](LICENSE) file for details.
