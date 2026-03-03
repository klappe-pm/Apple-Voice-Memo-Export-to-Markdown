"""VMEA Writer – Generate Markdown notes for Voice Memos."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from vmea.parser import MemoMetadata


def generate_filename(
    metadata: MemoMetadata,
    has_transcript: bool,
    date_format: str = "%Y-%m-%d",
) -> str:
    """Generate a filename for a memo.

    Format: {date}-transcript.md or {date}-audio.md

    Args:
        metadata: Parsed memo metadata.
        has_transcript: Whether the memo has a transcript.
        date_format: strftime format for date.

    Returns:
        Generated filename (without path).
    """
    if metadata.created:
        date_str = metadata.created.strftime(date_format)
    else:
        date_str = datetime.now().strftime(date_format)

    suffix = "transcript" if has_transcript else "audio"
    return f"{date_str}-{suffix}.md"


def format_duration(seconds: Optional[float]) -> str:
    """Format duration in human-readable form."""
    if seconds is None:
        return "Unknown"

    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def generate_note_content(
    metadata: MemoMetadata,
    audio_filename: str,
    note_title: str,
    date_created: str,
    date_revised: str,
    llm_model: str = "",
    domains: str = "",
    sub_domains: str = "",
    key_takeaways: Optional[list[str]] = None,
) -> str:
    """Generate Markdown note content with YAML frontmatter.

    Args:
        metadata: Parsed memo metadata.
        audio_filename: Filename of the audio file (for embed link).
        note_title: Title for the note (e.g., "2025-01-01-transcript").
        date_created: Date created in YYYY-MM-DD format.
        date_revised: Date revised in YYYY-MM-DD format.
        llm_model: Name of the LLM model used.
        domains: Domain value from LLM.
        sub_domains: Sub-domain value from LLM.
        key_takeaways: List of 5 key takeaways from LLM.

    Returns:
        Complete Markdown content with YAML frontmatter.
    """
    parts = []

    # YAML Frontmatter
    parts.append("---")
    parts.append(f"domains: {domains}")
    parts.append(f"sub-domains: {sub_domains}")
    parts.append(f"llm-model: {llm_model}")
    parts.append(f"date-created: {date_created}")
    parts.append(f"date-revised: {date_revised}")
    parts.append("aliases:")
    parts.append("tags:")
    parts.append("---")
    parts.append("")

    # Title (filename without .md)
    parts.append(f"# {note_title}")

    # Voice Memo section with audio link
    parts.append("## Voice Memo")
    parts.append(f"![[{audio_filename}]]")
    parts.append("")

    # Key Takeaways section
    parts.append("## Key Takeaways")
    if key_takeaways and len(key_takeaways) > 0:
        for i, takeaway in enumerate(key_takeaways[:5], 1):
            parts.append(f"{i}. {takeaway}")
    else:
        parts.append("*No key takeaways available*")
    parts.append("")

    # Revised Transcript section (in code block)
    parts.append("### Revised Transcript")
    parts.append("```markdown")
    if metadata.revised_transcript:
        parts.append(metadata.revised_transcript)
    else:
        parts.append("No LLM Transcript")
    parts.append("```")
    parts.append("")

    # Original Transcript section (in code block)
    parts.append("### Original Transcript")
    parts.append("```markdown")
    if metadata.transcript:
        parts.append(metadata.transcript)
    else:
        parts.append("No iOS Transcription Available")
    parts.append("```")
    parts.append("")

    return "\n".join(parts)


def copy_audio_file(audio_source: Path, audio_dest: Path) -> None:
    """Copy an audio file to the destination with atomic write."""
    audio_dest.parent.mkdir(parents=True, exist_ok=True)
    temp_audio = audio_dest.with_suffix(".m4a.tmp")
    try:
        shutil.copy2(audio_source, temp_audio)
        temp_audio.replace(audio_dest)
    except Exception:
        temp_audio.unlink(missing_ok=True)
        raise


def write_note(
    metadata: MemoMetadata,
    output_folder: Path,
    audio_source: Path,
    key_takeaways: Optional[list[str]] = None,
    llm_model: str = "",
    domains: str = "",
    sub_domains: str = "",
    date_format: str = "%Y-%m-%d",
    dry_run: bool = False,
) -> tuple[Path, Path]:
    """Write a Markdown note and copy the audio file.

    Args:
        metadata: Parsed memo metadata.
        output_folder: Destination folder for Markdown notes.
        audio_source: Source .m4a file.
        key_takeaways: List of 5 key takeaways from LLM.
        llm_model: Name of the LLM model used.
        domains: Domain value from LLM.
        sub_domains: Sub-domain value from LLM.
        date_format: Date format for filenames.
        dry_run: If True, don't actually write files.

    Returns:
        Tuple of (note_path, audio_path) for the written files.
    """
    output_folder.mkdir(parents=True, exist_ok=True)

    # Audio folder is always output_folder/Audio/
    audio_folder = output_folder / "Audio"
    audio_folder.mkdir(parents=True, exist_ok=True)

    # Generate filename based on whether transcript exists
    has_transcript = bool(metadata.transcript)
    note_filename = generate_filename(metadata, has_transcript, date_format)
    note_path = output_folder / note_filename

    # Handle filename collision by appending counter
    if note_path.exists() and not dry_run:
        base = note_filename.removesuffix(".md")
        counter = 1
        while note_path.exists():
            counter += 1
            note_filename = f"{base}-{counter}.md"
            note_path = output_folder / note_filename

    # Audio filename matches note filename
    audio_filename = note_filename.replace(".md", ".m4a")
    audio_path = audio_folder / audio_filename

    if dry_run:
        return note_path, audio_path

    # Copy audio file
    copy_audio_file(audio_source, audio_path)

    # Date values
    if metadata.created:
        date_created = metadata.created.strftime(date_format)
    else:
        date_created = datetime.now().strftime(date_format)
    date_revised = datetime.now().strftime(date_format)

    # Note title is filename without .md
    note_title = note_filename.removesuffix(".md")

    # Generate and write note content
    temp_note = note_path.with_suffix(".md.tmp")
    try:
        content = generate_note_content(
            metadata=metadata,
            audio_filename=f"Audio/{audio_filename}",
            note_title=note_title,
            date_created=date_created,
            date_revised=date_revised,
            llm_model=llm_model,
            domains=domains,
            sub_domains=sub_domains,
            key_takeaways=key_takeaways,
        )
        temp_note.write_text(content, encoding="utf-8")
        temp_note.replace(note_path)
    except Exception:
        temp_note.unlink(missing_ok=True)
        # Clean up audio if note write failed
        audio_path.unlink(missing_ok=True)
        raise

    return note_path, audio_path
