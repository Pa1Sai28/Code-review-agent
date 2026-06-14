import logging
import time
from flask import Flask
from app.webhooks.github import github_bp
from app.webhooks.gitlab import gitlab_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)
app.register_blueprint(github_bp)
app.register_blueprint(gitlab_bp)

stats = {
    "start_time": time.time(),
    "requests_total": 0,
    "reviews_completed": 0,
    "last_review_time": None
}


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


@app.route("/", methods=["GET"])
def index():
    return {
        "service": "Code Review Agent",
        "status": "running",
        "version": "2.0.0",
        "description": "Autonomous AI code review agent powered by Anthropic Claude",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "github_webhook": "/webhook/github",
            "gitlab_webhook": "/webhook/gitlab"
        },
        "repository": "github.com/Pa1Sai28/Code-review-agent"
    }, 200


@app.route("/metrics", methods=["GET"])
def metrics():
    uptime_seconds = int(time.time() - stats["start_time"])
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60

    return {
        "service": "Code Review Agent",
        "uptime": f"{uptime_hours}h {uptime_minutes}m",
        "uptime_seconds": uptime_seconds,
        "requests_total": stats["requests_total"],
        "reviews_completed": stats["reviews_completed"],
        "last_review_time": stats["last_review_time"],
        "platform": "GCP Cloud Run"
    }, 200


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")