import logging

logger = logging.getLogger(__name__)

MAX_LINES_PER_FILE = 200


def format_diff_for_review(files: list, pr_context: dict = None) -> str:
    """
    Convert raw diff data into clean structured text for Claude.
    
    Takes the output of fetch_pr_diff() and formats it into
    a readable string the agent can reason over effectively.
    
    Args:
        files: list of {filename, patch, additions, deletions, status}
        pr_context: optional dict with {repo, pr_number, author, title}
    
    Returns:
        Clean formatted string ready for the LLM prompt
    """
    if not files:
        logger.warning("No files to format")
        return "No changes found in this pull request."

    sections = []

    if pr_context:
        header = (
            f"Pull Request: #{pr_context.get('pr_number', 'unknown')}\n"
            f"Repository: {pr_context.get('repo', 'unknown')}\n"
            f"Author: {pr_context.get('author', 'unknown')}\n"
            f"Title: {pr_context.get('title', 'unknown')}\n"
            f"Files changed: {len(files)}\n"
        )
        sections.append(header)

    for f in files:
        filename = f.get("filename", "unknown")
        patch = f.get("patch", "")
        additions = f.get("additions", 0)
        deletions = f.get("deletions", 0)
        status = f.get("status", "modified")

        file_header = (
            f"{'='*60}\n"
            f"File: {filename}\n"
            f"Status: {status} | +{additions} additions | -{deletions} deletions\n"
            f"{'='*60}\n"
        )

        if not patch:
            file_section = file_header + "(Binary file or no diff available)\n"
        else:
            patch_lines = patch.split("\n")
            truncated = False

            if len(patch_lines) > MAX_LINES_PER_FILE:
                patch_lines = patch_lines[:MAX_LINES_PER_FILE]
                truncated = True

            patch_text = "\n".join(patch_lines)
            if truncated:
                patch_text += f"\n... (truncated — showing first {MAX_LINES_PER_FILE} lines)"

            file_section = file_header + patch_text + "\n"

        sections.append(file_section)

    formatted = "\n".join(sections)
    token_estimate = len(formatted.split()) * 1.3
    logger.info(f"Formatted diff: {len(files)} files, ~{int(token_estimate)} tokens estimated")

    return formatted


def get_file_extension(filename: str) -> str:
    """Extract file extension for language-aware review hints."""
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return "unknown"


def is_reviewable(filename: str) -> bool:
    """
    Check if a file should be reviewed.
    Skip binary files, lock files, and auto-generated files.
    """
    skip_extensions = {
        "png", "jpg", "jpeg", "gif", "svg", "ico", "pdf",
        "lock", "sum", "min.js", "min.css"
    }
    skip_patterns = [
        "package-lock.json", "yarn.lock", "poetry.lock",
        "requirements.txt", "Pipfile.lock", ".gitignore",
        "Dockerfile", "docker-compose"
    ]

    ext = get_file_extension(filename)
    if ext in skip_extensions:
        return False

    for pattern in skip_patterns:
        if pattern in filename:
            return False

    return True
