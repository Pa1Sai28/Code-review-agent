# Code Review Agent 🤖

An autonomous AI agent that reviews Pull Requests and Merge Requests on **GitHub** and **GitLab** — automatically. When a PR is opened, the agent receives the event via webhook, fetches the code diff, analyzes it using **Anthropic Claude**, and posts inline review comments covering bugs, security issues, code style, performance, and industry best practices.

[![CI](https://github.com/Pa1Sai28/Code-review-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Pa1Sai28/Code-review-agent/actions/workflows/ci.yml)
[![Deploy](https://github.com/Pa1Sai28/Code-review-agent/actions/workflows/deploy.yml/badge.svg)](https://github.com/Pa1Sai28/Code-review-agent/actions/workflows/deploy.yml)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/flask-3.x-lightgrey)](https://flask.palletsprojects.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://docker.com)
[![Tests](https://img.shields.io/badge/tests-51%20passing-brightgreen)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#)

---

## 🌐 Live Demo

The agent is deployed and running on **GCP Cloud Run**:

```
https://code-review-agent-3eiibjyvxq-uc.a.run.app
```

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Returns `{"status": "ok"}` |
| `/` | GET | Service info and available endpoints |
| `/webhook/github` | POST | GitHub PR event receiver |
| `/webhook/gitlab` | POST | GitLab MR event receiver |

To verify it's live:
```bash
curl https://code-review-agent-3eiibjyvxq-uc.a.run.app/health
# {"status": "ok"}
```

---

## What It Does

When a developer opens a Pull Request or Merge Request, the agent:

1. Receives the webhook event and cryptographically verifies it came from GitHub/GitLab
2. Fetches the code diff via REST API — asynchronously, so the server responds in under 200ms
3. Formats the diff into clean, structured context for the LLM
4. Sends it to **Anthropic Claude** with a carefully engineered system prompt
5. Parses Claude's structured JSON response into actionable review comments
6. Posts inline comments directly on the changed lines of the PR — exactly like a human reviewer

---

## How It Works

```
Developer opens PR / MR
         ↓
GitHub / GitLab fires webhook → Flask verifies HMAC-SHA256 signature
         ↓
Returns 200 immediately → spawns background thread (async)
         ↓
Fetches code diff via GitHub / GitLab REST API
         ↓
Diff formatter cleans and structures the changes for the LLM
         ↓
Anthropic Claude analyzes across 5 dimensions:
bugs · security · style · performance · best practices
         ↓
Structured JSON comments parsed and posted inline on the PR
```

---

## Architecture

```
code-review-agent/
├── app/
│   ├── main.py                      # Flask entry point — registers blueprints
│   ├── webhooks/
│   │   ├── github.py                # GitHub webhook handler + full pipeline
│   │   └── gitlab.py                # GitLab webhook handler + full pipeline
│   ├── utils/
│   │   ├── security.py              # HMAC-SHA256 + GitLab token verification
│   │   ├── github_api.py            # GitHub REST API — payload parsing + diff fetch
│   │   └── gitlab_api.py            # GitLab REST API — payload parsing + diff fetch
│   └── agent/
│       ├── reviewer.py              # Anthropic Claude client + review agent
│       ├── diff_formatter.py        # Converts raw diffs to LLM-ready context
│       └── comment_poster.py        # Posts inline comments to GitHub + GitLab
├── tests/                           # 51 automated tests
│   ├── test_security.py             # HMAC + token verification tests
│   ├── test_github_api.py           # Payload parsing tests
│   ├── test_webhooks.py             # Webhook endpoint integration tests
│   ├── test_diff_formatter.py       # Diff formatting tests
│   ├── test_reviewer.py             # Claude client tests
│   ├── test_review_agent.py         # Review pipeline tests
│   ├── test_comment_poster.py       # Comment posting tests
│   └── test_integration.py          # Full end-to-end pipeline tests
├── infra/                           # Terraform IaC
│   ├── main.tf                      # Provider + backend config
│   ├── cloud_run.tf                 # Cloud Run service + IAM
│   ├── artifact_registry.tf         # Docker registry + cleanup policies
│   ├── secrets.tf                   # Secret Manager references
│   ├── monitoring.tf                # 5xx alert policy + email notifications
│   ├── variables.tf                 # Input variables
│   └── outputs.tf                   # Service URL + registry URL outputs
├── .github/workflows/
│   ├── ci.yml                       # Run tests on every push
│   └── deploy.yml                   # Build → push → Cloud Run deploy on main
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.11 | Primary development language |
| Web Framework | Flask 3.x | Lightweight webhook receiver |
| AI / LLM | Anthropic Claude Sonnet 4.6 | Code analysis and review generation |
| Platform APIs | GitHub REST API, GitLab REST API | Diff retrieval and comment posting |
| Security | HMAC-SHA256, python-dotenv | Webhook verification and secrets management |
| Async Processing | Python threading | Non-blocking webhook handling |
| Containerization | Docker | Consistent runtime environment |
| CI/CD | GitHub Actions | Test + deploy on every push to main |
| Secrets | GCP Secret Manager | Secure runtime secret injection |
| Infrastructure | Terraform | Full IaC — Cloud Run, Artifact Registry, Monitoring |
| Cloud | GCP Cloud Run | Serverless deployment — scales to zero |

---

## Features

### Sprint 1 — Webhook Infrastructure ✅

- **Dual platform support** — handles both GitHub Pull Requests and GitLab Merge Requests
- **Cryptographic security** — HMAC-SHA256 signature verification on every GitHub request
- **Async processing** — returns 200 instantly, processes in background thread
- **Graceful error handling** — malformed payloads, API failures, and timeouts handled cleanly
- **Dockerized** — runs identically in any environment
- **CI** — full test suite runs on every push via GitHub Actions

### Sprint 2 — AI Agent Core ✅

- **Anthropic Claude integration** — Sonnet 4.6 via official Python SDK
- **Structured prompt engineering** — carefully crafted system prompt covering 5 review dimensions
- **Smart diff formatting** — cleans raw diffs into token-efficient LLM context with truncation
- **File filtering** — skips binary files, lock files, and auto-generated files automatically
- **Structured JSON output** — Claude returns typed comments with filename, line, severity, dimension
- **Inline comment posting** — comments appear on the exact changed lines in the PR diff view
- **Single review per PR** — posts one consolidated review, not N individual comments
- **Retry logic** — exponential backoff handles Claude API rate limits gracefully
- **51 automated tests** — unit, integration, and end-to-end pipeline coverage

### Sprint 3 — Production Deployment ✅

- **GCP Cloud Run** — serverless, scales to zero when idle, auto-scales to 3 instances under load
- **Artifact Registry** — Docker image storage with cleanup policy (keeps latest only)
- **GCP Secret Manager** — all secrets injected at runtime, never in environment files or source
- **Terraform IaC** — full infrastructure as code: Cloud Run, Artifact Registry, Monitoring, IAM
- **GitHub Actions CD** — every push to `main` builds, pushes, and deploys automatically in ~70s
- **Cloud Monitoring** — 5xx error alert policy with email notification
- **Live public endpoint** — `https://code-review-agent-3eiibjyvxq-uc.a.run.app`

---

## Review Dimensions

Claude analyzes every PR across five dimensions:

| Dimension | What Claude Looks For |
|---|---|
| **Bugs** | Logic errors, null pointer risks, off-by-one errors, incorrect conditions |
| **Security** | SQL injection, hardcoded secrets, insecure dependencies, input validation gaps |
| **Style** | Naming conventions, readability, unnecessary complexity, dead code |
| **Performance** | Inefficient algorithms, N+1 queries, unnecessary loops, memory leaks |
| **Best Practices** | Missing error handling, lack of tests, SOLID violations, missing docstrings |

---

## Real-World Demo

Opening a PR with this code:

```python
def authenticate_user(username, password):
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    api_key = "sk-prod-1234567890abcdef"
    db.execute(query)
```

Claude posts inline comments like:

```
⚠ SECURITY
SQL injection vulnerability. User input is concatenated directly into the query.
Use parameterized queries: cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

⚠ SECURITY
Hardcoded API key detected. Store secrets in environment variables via os.getenv().
Never commit credentials to version control.
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Docker
- ngrok (for local webhook testing)

### Installation

```bash
# Clone the repo
git clone https://github.com/Pa1Sai28/Code-review-agent.git
cd Code-review-agent

# Create and activate virtual environment
python -m venv cragent
source cragent/bin/activate  # Mac/Linux
# cragent\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Fill in your secrets in .env
```

### Environment Variables

```bash
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret
GITHUB_PAT=your_github_personal_access_token
GITLAB_WEBHOOK_TOKEN=your_gitlab_webhook_token
GITLAB_PAT=your_gitlab_personal_access_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Run Locally

```bash
python -m app.main
```

### Run with Docker

```bash
docker build -t code-review-agent .
docker run -p 5000:5000 --env-file .env code-review-agent
```

### Run Tests

```bash
pytest tests/ -v
# 51 tests — all pass in under 1s
```

### Webhook Setup (Local Development)

```bash
# Terminal 1 — start the server
python -m app.main

# Terminal 2 — expose locally via ngrok
ngrok http 5000

# Register the ngrok URL in your GitHub repo:
# Settings → Webhooks → Add webhook
# Payload URL: https://your-ngrok-url/webhook/github
# Content type: application/json
# Secret: your GITHUB_WEBHOOK_SECRET value
# Events: Pull requests only
```

---

## Infrastructure (Terraform)

All GCP infrastructure is managed as code in `infra/`. To inspect or re-apply:

```bash
cd infra
terraform init
terraform plan    # should show no changes — everything is deployed
terraform output  # prints live service URL and registry URL
```

Outputs:
```
cloud_run_url         = "https://code-review-agent-3eiibjyvxq-uc.a.run.app"
artifact_registry_url = "us-central1-docker.pkg.dev/pa1-cloud-project/code-review-agent"
service_name          = "code-review-agent"
```

---

## CI/CD Pipeline

Every push to `main` triggers two parallel workflows:

```
git push origin main
        ↓
┌─────────────────────┐    ┌──────────────────────────────────────────┐
│   CI (ci.yml)       │    │   Deploy to Cloud Run (deploy.yml)       │
│                     │    │                                          │
│  pip install        │    │  docker build                            │
│  pytest (51 tests)  │    │  docker push → Artifact Registry         │
│  ~17s               │    │  gcloud run deploy → Cloud Run           │
│                     │    │  ~70s                                    │
└─────────────────────┘    └──────────────────────────────────────────┘
```

---

## Sprint Roadmap

| Sprint | Focus | Status |
|---|---|---|
| Sprint 1 | Webhook Infrastructure — Flask, GitHub + GitLab dual platform, Docker, GitHub Actions CI | ✅ Complete |
| Sprint 2 | AI Agent Core — Claude integration, structured prompt engineering, inline comment posting, 51 tests | ✅ Complete |
| Sprint 3 | Production Deployment — GCP Cloud Run, Terraform IaC, automated CD pipeline, Cloud Monitoring, live demo | ✅ Complete |

---

## Security

- All webhook requests are cryptographically verified before processing
- GitHub uses HMAC-SHA256 — timing-safe comparison via `hmac.compare_digest`
- GitLab uses token verification — same timing-safe approach
- Secrets stored in GCP Secret Manager — injected at runtime, never in source or `.env`
- `.env.example` provides a safe onboarding template — no real values committed
- API keys loaded from environment at runtime — never hardcoded
- `terraform-sa-key.json` is gitignored — never committed to version control

---

## Project Stats

| Metric | Value |
|---|---|
| Automated tests | 51 |
| Test runtime | < 1s |
| Review dimensions | 5 |
| Platforms supported | 2 (GitHub + GitLab) |
| Lines of application code | ~600 |
| Average review latency | < 30 seconds |
| Webhook response time | < 200ms |
| CD pipeline duration | ~70 seconds |
| Cloud Run min instances | 0 (scales to zero) |
| Cloud Run max instances | 3 |

---

## Author

**Naga Pavansai Kumar Varikuti**
Software Engineer | Cloud & DevOps | MLOps & Agentic AI | Chicago, IL

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/naga-pavan-sai-kumar-varikuti)
[![GitHub](https://img.shields.io/badge/GitHub-Pa1Sai28-black)](https://github.com/Pa1Sai28)