import os
import logging
import anthropic
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)


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
        model="claude-sonnet-4-6",
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
