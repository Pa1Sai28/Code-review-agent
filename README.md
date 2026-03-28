# Code Review Agent 🤖

An autonomous AI agent that reviews Pull Requests and Merge Requests on **GitHub** and **GitLab** — automatically. When a PR is opened, the agent receives the event via webhook, fetches the code diff, analyzes it using **Anthropic Claude**, and posts inline review comments covering bugs, security issues, code style, performance, and industry best practices.

![CI](https://github.com/Pa1Sai28/Code-review-agent/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Flask](https://img.shields.io/badge/flask-3.x-lightgrey)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## How It Works

```
Developer opens PR
       ↓
GitHub / GitLab fires webhook → Flask receiver validates signature
       ↓
Agent fetches code diff via REST API (background thread)
       ↓
Anthropic Claude analyzes: bugs · security · style · performance · best practices
       ↓
Agent posts inline review comments on the PR
```

---

## Architecture

```
code-review-agent/
├── app/
│   ├── main.py                  # Flask entry point
│   ├── webhooks/
│   │   ├── github.py            # GitHub webhook handler
│   │   └── gitlab.py            # GitLab webhook handler
│   └── utils/
│       ├── security.py          # HMAC-SHA256 signature verification
│       ├── github_api.py        # GitHub REST API — diff fetching
│       └── gitlab_api.py        # GitLab REST API — diff fetching
├── tests/                       # 18 automated tests
├── infra/                       # Terraform IaC (Sprint 3)
├── .github/workflows/ci.yml     # GitHub Actions CI
├── Dockerfile
└── docker-compose.yml
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Web Framework | Flask |
| AI / LLM | Anthropic Claude (Sonnet 4.6) |
| Agent Framework | LangChain + MCP |
| Platform APIs | GitHub REST API, GitLab REST API |
| Security | HMAC-SHA256, python-dotenv |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Infrastructure | Terraform |
| Cloud | GCP Cloud Run |

---

## Features

- **Dual platform support** — handles both GitHub Pull Requests and GitLab Merge Requests
- **Cryptographic security** — HMAC-SHA256 signature verification on every webhook request
- **Async processing** — returns 200 instantly, processes diff in background thread
- **Graceful error handling** — malformed payloads, API failures, and timeouts handled cleanly
- **18 automated tests** — unit tests, integration tests, and edge case coverage
- **Dockerized** — runs identically in any environment
- **CI/CD** — full test suite runs on every push via GitHub Actions

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

### Test

```bash
pytest tests/ -v
```

### Webhook Setup (Local Development)

```bash
# Start ngrok tunnel
ngrok http 5000 --request-header-add "ngrok-skip-browser-warning:true"

# Register the ngrok URL in your GitHub repo:
# Settings → Webhooks → Add webhook
# Payload URL: https://your-ngrok-url/webhook/github
# Content type: application/json
# Secret: your GITHUB_WEBHOOK_SECRET value
# Events: Pull requests
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/webhook/github` | POST | GitHub PR event receiver |
| `/webhook/gitlab` | POST | GitLab MR event receiver |

---

## Sprint Roadmap

| Sprint | Focus | Status |
|---|---|---|
| Sprint 1 | Webhook receiver, GitHub + GitLab integration, Docker, CI | ✅ Complete |
| Sprint 2 | Anthropic Claude agent, MCP tools, inline comment posting | 🔄 In Progress |
| Sprint 3 | GCP Cloud Run, Terraform IaC, production deployment | ⬜ Planned |

---

## Security

- All webhook requests are cryptographically verified before processing
- Secrets are stored in `.env` — never committed to version control
- `.env.example` provides a safe onboarding template
- Timing-safe comparison (`hmac.compare_digest`) prevents timing attacks

---

## Contributing

This project is part of an active portfolio build. Sprints 2 and 3 are in progress. Feel free to open an issue or star the repo to follow along.

---

## Author

**Naga Pavansai Kumar Varikuti**
Software Engineer | Cloud & DevOps | MLOps & Agentic AI | Chicago, IL

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/naga-pavan-sai-kumar-varikuti)
[![GitHub](https://img.shields.io/badge/GitHub-Pa1Sai28-black)](https://github.com/Pa1Sai28)
