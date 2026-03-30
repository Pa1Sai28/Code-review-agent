import os
import json
import logging
import anthropic
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are an expert senior software engineer conducting a thorough code review.
Your job is to analyze code diffs and provide specific, actionable, and constructive feedback.

You review code across exactly five dimensions:
1. BUGS — Logic errors, null pointer risks, off-by-one errors, incorrect conditions
2. SECURITY — SQL injection, hardcoded secrets, insecure dependencies, input validation gaps
3. STYLE — Naming conventions, code readability, unnecessary complexity, dead code
4. PERFORMANCE — Inefficient algorithms, N+1 queries, unnecessary loops, memory leaks
5. BEST_PRACTICES — Missing error handling, lack of tests, violation of SOLID principles, missing docstrings

Rules you must follow:
- Only comment on lines that actually changed (lines starting with + in the diff)
- Be specific — reference the exact code that has the issue
- Be constructive — suggest how to fix it, not just what is wrong
- Skip trivial issues like minor formatting unless they are clearly wrong
- If a file looks good, do not force comments — quality over quantity

You must respond with ONLY a valid JSON array. No explanation, no markdown, no preamble.
Each item in the array must have exactly these fields:
- filename: the file where the issue was found
- line_content: the exact line of code with the issue (the + line from the diff)
- comment: your specific, actionable review comment
- severity: one of "error", "warning", or "info"
- dimension: one of "BUGS", "SECURITY", "STYLE", "PERFORMANCE", "BEST_PRACTICES"

If there are no issues found, return an empty array: []

Example response format:
[
  {
    "filename": "app/main.py",
    "line_content": "+    password = 'hardcoded123'",
    "comment": "Never hardcode credentials. Use environment variables via os.getenv() instead.",
    "severity": "error",
    "dimension": "SECURITY"
  }
]"""


def get_claude_client() -> anthropic.Anthropic:
    """
    Initialize and return the Anthropic client.
    Always loads the API key from environment — never hardcoded.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in .env")
    return anthropic.Anthropic(api_key=api_key)


def test_claude_connection() -> str:
    """
    Send a simple test prompt to Claude.
    Used to verify the API key and connection work.
    """
    client = get_claude_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=100,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: Claude connection successful."
            }
        ]
    )
    response = message.content[0].text
    logger.info(f"Claude test response: {response}")
    return response


def review_diff(formatted_diff: str, pr_context: dict = None) -> list:
    """
    Send a formatted diff to Claude for code review.

    Args:
        formatted_diff: clean diff string from diff_formatter.py
        pr_context: optional dict with PR metadata

    Returns:
        List of review comment dicts with filename, line_content,
        comment, severity, and dimension
    """
    client = get_claude_client()

    context_note = ""
    if pr_context:
        context_note = (
            f"You are reviewing PR #{pr_context.get('pr_number')} "
            f"titled '{pr_context.get('title')}' "
            f"by {pr_context.get('author')} "
            f"in {pr_context.get('repo')}.\n\n"
        )

    user_message = (
        f"{context_note}"
        f"Please review the following code changes:\n\n"
        f"{formatted_diff}"
    )

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Sending diff to Claude for review (attempt {attempt + 1})")

            message = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )

            response_text = message.content[0].text.strip()
            logger.info(f"Claude response received — {len(response_text)} chars")

            comments = parse_review_response(response_text)
            logger.info(f"Parsed {len(comments)} review comments")
            return comments

        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                import time
                wait = retry_delay * (2 ** attempt)
                logger.warning(f"Rate limited — retrying in {wait}s")
                time.sleep(wait)
            else:
                logger.error("Rate limit exceeded after all retries")
                return []

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return []

        except Exception as e:
            logger.error(f"Unexpected error during review: {type(e).__name__}: {e}")
            return []

    return []


def parse_review_response(response_text: str) -> list:
    """
    Parse Claude's JSON response into a list of review comments.
    Handles edge cases where Claude adds markdown or extra text.
    """
    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        comments = json.loads(response_text)

        if not isinstance(comments, list):
            logger.warning("Claude response was not a JSON array")
            return []

        valid_comments = []
        required_fields = {"filename", "line_content", "comment", "severity", "dimension"}

        for c in comments:
            if required_fields.issubset(c.keys()):
                valid_comments.append(c)
            else:
                logger.warning(f"Skipping comment missing required fields: {c}")

        return valid_comments

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response as JSON: {e}")
        logger.error(f"Raw response: {response_text[:200]}")
        return []