import os
import re


def load_prompt_from_file(filename):
    """Load prompt from a text file in the local prompts/ directory."""
    path = os.path.join("prompts", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"⚠️  Prompt file {filename} not found, using default prompt")
        return "You are an AI agent. Please help the user with their request."


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _extract_last_content(resp):
    content = None
    try:
        messages = resp.get("messages", []) if isinstance(resp, dict) else []
        for m in reversed(messages):
            c = getattr(m, "content", None)
            if c:
                content = c
                break
        if content is None and hasattr(resp, "content"):
            content = resp.content
    except Exception:
        content = None
    return content or ""


def _print_last_url_or_content(resp) -> None:
    content = _extract_last_content(resp)
    if not content:
        print("")
        return
    match = re.search(r"https?://\S+", str(content))
    if match:
        print(match.group(0))
    else:
        print(str(content))