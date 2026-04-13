# Code Review Agent 🤖

An autonomous AI agent that reviews Pull Requests and Merge Requests on **GitHub** and **GitLab** — automatically. When a PR is opened, the agent receives the event via webhook, fetches the code diff, analyzes it using **Anthropic Claude**, and posts inline review comments covering bugs, security issues, code style, performance, and industry best practices.

![CI](https://github.com/Pa1Sai28/Code-review-agent/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Flask](https://img.shields.io/badge/flask-3.x-lightgrey)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Tests](https://img.shields.io/badge/tests-51%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

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
├── infra/                           # Terraform IaC (Sprint 3)
├── docs/                            # Architecture diagrams
├── .github/workflows/ci.yml         # GitHub Actions CI
├── Dockerfile
└── docker-compose.yml
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.11 | Primary development language |
| Web Framework | Flask | Lightweight webhook receiver |
| AI / LLM | Anthropic Claude (Sonnet 4.6) | Code analysis and review generation |
| Platform APIs | GitHub REST API, GitLab REST API | Diff retrieval and comment posting |
| Security | HMAC-SHA256, python-dotenv | Webhook verification and secrets management |
| Async Processing | Python threading | Non-blocking webhook handling |
| Containerization | Docker | Consistent runtime environment |
| CI/CD | GitHub Actions | Automated testing on every push |
| Infrastructure | Terraform | Infrastructure as Code (Sprint 3) |
| Cloud | GCP Cloud Run | Serverless deployment (Sprint 3) |

---

## Features

### Sprint 1 — Webhook Infrastructure
- **Dual platform support** — handles both GitHub Pull Requests and GitLab Merge Requests
- **Cryptographic security** — HMAC-SHA256 signature verification on every GitHub request
- **Async processing** — returns 200 instantly, processes in background thread
- **Graceful error handling** — malformed payloads, API failures, and timeouts handled cleanly
- **Dockerized** — runs identically in any environment
- **CI/CD** — full test suite runs on every push via GitHub Actions

### Sprint 2 — AI Agent Core
- **Anthropic Claude integration** — Sonnet 4.6 via official Python SDK
- **Structured prompt engineering** — carefully crafted system prompt covering 5 review dimensions
- **Smart diff formatting** — cleans raw diffs into token-efficient LLM context with truncation
- **File filtering** — skips binary files, lock files, and auto-generated files automatically
- **Structured JSON output** — Claude returns typed comments with filename, line, severity, dimension
- **Inline comment posting** — comments appear on the exact changed lines in the PR diff view
- **Single review per PR** — posts one consolidated review, not N individual comments
- **Retry logic** — exponential backoff handles Claude API rate limits gracefully
- **51 automated tests** — unit, integration, and end-to-end pipeline coverage

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
= > SECURITY
SQL injection vulnerability. User input is concatenated directly into the query.
Use parameterized queries: cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

= > SECURITY  
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
# 51 tests — all should pass
```

### Webhook Setup (Local Development)

```bash
# Terminal 1 — start the server
python -m app.main

# Terminal 2 — expose locally via ngrok
ngrok http 5000 --request-header-add "ngrok-skip-browser-warning:true"

# Register the ngrok URL in your GitHub repo:
# Settings → Webhooks → Add webhook
# Payload URL: https://your-ngrok-url/webhook/github
# Content type: application/json
# Secret: your GITHUB_WEBHOOK_SECRET value
# Events: Pull requests only
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check — returns `{"status": "ok"}` |
| `/webhook/github` | POST | GitHub PR event receiver |
| `/webhook/gitlab` | POST | GitLab MR event receiver |

---

## Sprint Roadmap

| Sprint | Focus | Deliverable | Status |
|---|---|---|---|
| Sprint 1 | Webhook & Integration | Secure Flask receiver, GitHub + GitLab dual platform, Docker, GitHub Actions CI | ✅ Complete |
| Sprint 2 | AI Agent Core | Anthropic Claude integration, structured prompt engineering, inline comment posting, 51 tests | ✅ Complete |
| Sprint 3 | Production Deployment | GCP Cloud Run, Terraform IaC, full CI/CD pipeline, live public demo | 🔄 In Progress |

---

## Security

- All webhook requests are cryptographically verified before processing
- GitHub uses HMAC-SHA256 — timing-safe comparison via `hmac.compare_digest`
- GitLab uses token verification — same timing-safe approach
- Secrets stored in `.env` — never committed to version control
- `.env.example` provides a safe onboarding template for new contributors
- API keys loaded from environment at runtime — never hardcoded

---

## Project Stats

| Metric | Value |
|---|---|
| Automated tests | 51 |
| Review dimensions | 5 |
| Platforms supported | 2 (GitHub + GitLab) |
| Lines of application code | ~600 |
| Average review latency | < 30 seconds |
| Webhook response time | < 200ms |

---

## Contributing

This project is part of an active portfolio build following industry-standard Agile methodology — daily tickets, acceptance criteria, conventional commits, and CI on every push. Sprint 3 (GCP Cloud Run deployment) is currently in progress. Feel free to open an issue or star the repo to follow along.

---

## Author

**Naga Pavansai Kumar Varikuti**
Software Engineer | Cloud & DevOps | MLOps & Agentic AI | Chicago, IL

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/naga-pavan-sai-kumar-varikuti)
[![GitHub](https://img.shields.io/badge/GitHub-Pa1Sai28-black)](https://github.com/Pa1Sai28)