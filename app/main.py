import logging
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

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)