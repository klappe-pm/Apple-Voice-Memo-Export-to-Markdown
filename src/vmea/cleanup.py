"""VMEA Cleanup – Local transcript cleanup via Ollama."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib import error, request

from vmea.ollama import is_ollama_running


DEFAULT_CLEANUP_INSTRUCTIONS = """You are revising a raw voice memo transcript.

Return only the revised transcript text.
Preserve the speaker's meaning, order, tone, and first-person perspective.
Fix obvious speech-to-text mistakes, punctuation, capitalization, and paragraph breaks.
Do not summarize. Do not omit details. Do not add facts that are not present.
If a phrase is unclear, keep it close to the original wording instead of guessing.
"""

# Instruction file fallback order (after explicit path)
INSTRUCTION_FILE_FALLBACKS = ["CLAUDE.md", "GEMINI.md", "README.md"]


@dataclass
class CleanupResult:
    """Result of transcript cleanup with provenance."""

    revised_transcript: str
    instruction_source: str  # file path or "default"
    model: str


def resolve_instruction_file(
    explicit_path: Optional[Path],
    search_dir: Optional[Path] = None,
    fail_on_missing: bool = False,
) -> tuple[str, str]:
    """Resolve instruction file using priority order.

    Priority:
    1. Explicit configured path
    2. CLAUDE.md in search_dir or cwd
    3. GEMINI.md in search_dir or cwd
    4. README.md in search_dir or cwd
    5. Built-in default

    Args:
        explicit_path: Explicitly configured instruction file path.
        search_dir: Directory to search for fallback files. Defaults to cwd.
        fail_on_missing: If True, raise error when no file found.

    Returns:
        Tuple of (instructions_content, source_path_or_"default").

    Raises:
        FileNotFoundError: If fail_on_missing and no file found.
    """
    search_dir = search_dir or Path.cwd()

    # Try explicit path first
    if explicit_path:
        resolved = explicit_path.expanduser()
        if resolved.exists():
            content = resolved.read_text(encoding="utf-8").strip()
            if content:
                return content, str(resolved)
        if fail_on_missing:
            raise FileNotFoundError(f"Instruction file not found: {explicit_path}")

    # Try fallback files
    for filename in INSTRUCTION_FILE_FALLBACKS:
        candidate = search_dir / filename
        if candidate.exists():
            content = candidate.read_text(encoding="utf-8").strip()
            if content:
                return content, str(candidate)

    if fail_on_missing:
        raise FileNotFoundError(
            f"No instruction file found. Searched: {explicit_path}, "
            f"{', '.join(INSTRUCTION_FILE_FALLBACKS)} in {search_dir}"
        )

    return DEFAULT_CLEANUP_INSTRUCTIONS, "default"


def _call_ollama(
    prompt: str,
    system: str,
    model: str,
    host: str,
    timeout: int,
) -> str:
    """Make a request to Ollama API and return the response text."""
    if not is_ollama_running(host):
        raise RuntimeError(
            f"Ollama server is not running at {host}. "
            "Start with 'vmea ollama start' or 'ollama serve'"
        )

    payload = {
        "model": model,
        "stream": False,
        "system": system,
        "prompt": prompt,
    }
    body = json.dumps(payload).encode("utf-8")
    endpoint = host.rstrip("/") + "/api/generate"
    req = request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except error.URLError as exc:
        raise RuntimeError(f"Failed to reach Ollama at {endpoint}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama returned invalid JSON") from exc

    return str(response_data.get("response", "")).strip()


def cleanup_transcript(
    transcript: str,
    model: str,
    host: str = "http://localhost:11434",
    timeout: int = 120,
    instructions_path: Optional[Path] = None,
    search_dir: Optional[Path] = None,
    fail_on_missing_instruction: bool = False,
) -> CleanupResult:
    """Send a transcript to Ollama for cleanup and return revised text with provenance."""
    instructions, instruction_source = resolve_instruction_file(
        instructions_path,
        search_dir=search_dir,
        fail_on_missing=fail_on_missing_instruction,
    )

    revised = _call_ollama(transcript, instructions, model, host, timeout)
    if not revised:
        raise RuntimeError("Ollama returned an empty transcript")

    return CleanupResult(
        revised_transcript=revised,
        instruction_source=instruction_source,
        model=model,
    )


KEY_TAKEAWAYS_PROMPT = """You are analyzing a voice memo transcript.

Return exactly 5 key takeaways from this transcript.
Format each takeaway as a single concise sentence.
Number them 1 through 5.
Do not include any other text, just the 5 numbered takeaways.

Example format:
1. First key point from the memo.
2. Second key point from the memo.
3. Third key point from the memo.
4. Fourth key point from the memo.
5. Fifth key point from the memo.
"""


DOMAINS_PROMPT = """You are categorizing a voice memo transcript.

Analyze the transcript and determine the primary knowledge domain and sub-domain.

Return exactly 2 lines:
1. domain: [primary topic area, e.g., "Technology", "Business", "Personal", "Health", "Creative"]
2. sub-domain: [more specific topic, e.g., "Software Development", "Project Management", "Journal Entry"]

Be concise. Use title case. Do not include any other text.

Example output:
domain: Technology
sub-domain: Software Development
"""


def generate_key_takeaways(
    transcript: str,
    model: str,
    host: str = "http://localhost:11434",
    timeout: int = 120,
) -> list[str]:
    """Generate 5 key takeaways from a transcript using Ollama.

    Args:
        transcript: The transcript text to analyze.
        model: Ollama model name.
        host: Ollama server URL.
        timeout: Request timeout in seconds.

    Returns:
        List of 5 key takeaway strings.
    """
    response = _call_ollama(transcript, KEY_TAKEAWAYS_PROMPT, model, host, timeout)

    # Parse the numbered list from response
    takeaways = []
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove leading number and punctuation (e.g., "1. ", "1) ", "1: ")
        if line[0].isdigit():
            # Find where the actual content starts
            for i, char in enumerate(line):
                if char.isalpha():
                    takeaways.append(line[i:].strip())
                    break
        else:
            takeaways.append(line)

    # Ensure we have exactly 5 (pad or truncate)
    while len(takeaways) < 5:
        takeaways.append("No additional takeaway available.")

    return takeaways[:5]


@dataclass
class DomainResult:
    """Result of domain categorization."""

    domain: str
    sub_domain: str


def generate_domains(
    transcript: str,
    model: str,
    host: str = "http://localhost:11434",
    timeout: int = 60,
) -> DomainResult:
    """Generate domain and sub-domain categorization from a transcript.

    Args:
        transcript: The transcript text to analyze.
        model: Ollama model name.
        host: Ollama server URL.
        timeout: Request timeout in seconds.

    Returns:
        DomainResult with domain and sub_domain fields.
    """
    response = _call_ollama(transcript, DOMAINS_PROMPT, model, host, timeout)

    domain = ""
    sub_domain = ""

    for line in response.strip().split("\n"):
        line = line.strip().lower()
        if line.startswith("domain:"):
            domain = line.replace("domain:", "").strip().title()
        elif line.startswith("sub-domain:") or line.startswith("subdomain:"):
            sub_domain = line.replace("sub-domain:", "").replace("subdomain:", "").strip().title()

    return DomainResult(domain=domain, sub_domain=sub_domain)
