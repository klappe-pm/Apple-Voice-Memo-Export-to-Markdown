# Apple Voice Memo Export to Markdown

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/macOS-13%2B-brightgreen.svg)](https://www.apple.com/macos/)

Export Apple Voice Memos to markdown notes with AI-powered transcription and organization.

## How It Works

1. **Discovers** Voice Memos from your iCloud sync folder
2. **Extracts** native iOS transcripts (or generates them with Whisper)
3. **Enhances** content using a local LLM via Ollama -- cleans transcripts, generates titles and summaries
4. **Writes** markdown notes with YAML frontmatter: `YYYY-MM-DD-XX-title.md`
5. **Tracks** state for incremental updates without duplicates

## Quick Start

```bash
# Install
git clone https://github.com/klappe-pm/Apple-Voice-Memo-Export-to-Markdown.git
cd Apple-Voice-Memo-Export-to-Markdown
pip install -e .

# Setup
vmea init

# Export all memos
vmea export

# Check system health
vmea doctor
```

### Requirements

- **macOS 13+** (Ventura or later)
- **Python 3.11+**
- **Full Disk Access** permission (System Settings > Privacy & Security)
- **Ollama** (optional, for LLM features)

### Optional Extras

```bash
pip install -e ".[transcribe]"   # Whisper transcription
pip install -e ".[llm]"          # LLM dependencies
pip install -e ".[dev]"          # Development tools
```

## Output Example

```
2024-03-15-00-project-kickoff-meeting.md
```

```yaml
---
domains: Technology
sub-domains: Software Development
llm-model: llama3.2:3b
date-created: 2024-03-15
date-revised: 2024-03-15
aliases:
tags:
---

# 2024-03-15-00-project-kickoff-meeting

## Voice Memo
![[Audio/2024-03-15-00-project-kickoff-meeting.m4a]]

## Key Takeaways
1. First key point from the memo.
2. Second key point from the memo.
...

### Revised Transcript
Cleaned up transcript text...

### Original Transcript
Raw transcript from iOS/Whisper...
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](docs/GETTING_STARTED.md) | Full setup walkthrough |
| [Commands Reference](docs/COMMANDS.md) | All CLI commands and flags |
| [Configuration](docs/CONFIGURATION.md) | Config options, cascade mode, audio modes |
| [Use Cases & LLM Processing](docs/USE_CASES.md) | Transcription sources, LLM pipeline, workflows |
| [Customizing LLM Instructions](docs/CUSTOMIZING_LLM_INSTRUCTIONS.md) | Tailor transcript cleanup prompts |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common errors and fixes |
| [Development](docs/DEVELOPMENT.md) | Contributing, project structure, testing |
| [Architecture Diagrams](docs/diagrams/README.md) | Mermaid.js system diagrams |

## License

MIT -- see [LICENSE](LICENSE)
