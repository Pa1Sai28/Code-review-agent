from app.agent.diff_formatter import (
    format_diff_for_review,
    get_file_extension,
    is_reviewable
)

SAMPLE_FILES = [
    {
        "filename": "app/main.py",
        "patch": "@@ -1,5 +1,6 @@\n def hello():\n-    return 'world'\n+    return 'hello world'\n+    print('done')\n",
        "additions": 2,
        "deletions": 1,
        "status": "modified"
    },
    {
        "filename": "tests/test_main.py",
        "patch": "@@ -0,0 +1,3 @@\n+def test_hello():\n+    assert hello() == 'hello world'\n",
        "additions": 3,
        "deletions": 0,
        "status": "added"
    }
]

SAMPLE_CONTEXT = {
    "repo": "Pa1Sai28/crates",
    "pr_number": 1,
    "author": "Pa1Sai28",
    "title": "feat: update hello function"
}


def test_format_returns_string():
    result = format_diff_for_review(SAMPLE_FILES)
    assert isinstance(result, str)
    assert len(result) > 0


def test_format_includes_filenames():
    result = format_diff_for_review(SAMPLE_FILES)
    assert "app/main.py" in result
    assert "tests/test_main.py" in result


def test_format_includes_pr_context():
    result = format_diff_for_review(SAMPLE_FILES, SAMPLE_CONTEXT)
    assert "Pa1Sai28/crates" in result
    assert "Pa1Sai28" in result
    assert "feat: update hello function" in result


def test_format_includes_patch_content():
    result = format_diff_for_review(SAMPLE_FILES)
    assert "hello world" in result


def test_empty_files_returns_message():
    result = format_diff_for_review([])
    assert "No changes found" in result


def test_truncation_on_large_diff():
    large_patch = "\n".join([f"+line {i}" for i in range(300)])
    large_file = [{
        "filename": "big_file.py",
        "patch": large_patch,
        "additions": 300,
        "deletions": 0,
        "status": "added"
    }]
    result = format_diff_for_review(large_file)
    assert "truncated" in result


def test_binary_file_handled():
    binary_file = [{
        "filename": "image.png",
        "patch": "",
        "additions": 0,
        "deletions": 0,
        "status": "added"
    }]
    result = format_diff_for_review(binary_file)
    assert "Binary file" in result


def test_get_file_extension():
    assert get_file_extension("app/main.py") == "py"
    assert get_file_extension("Dockerfile") == "unknown"
    assert get_file_extension("style.min.css") == "css"


def test_is_reviewable_python():
    assert is_reviewable("app/main.py") is True


def test_is_reviewable_image():
    assert is_reviewable("logo.png") is False


def test_is_reviewable_lock_file():
    assert is_reviewable("package-lock.json") is False
