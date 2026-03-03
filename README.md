# Voice Memo Export Automation (VMEA)

VMEA exports Apple Voice Memos into a markdown-based notes folder as:

- one markdown file per memo
- one copied audio file per memo
- one durable state record per memo

It is designed for local use on macOS and supports optional local transcript cleanup through Ollama.

## Core Behavior

VMEA:

- scans the synced Voice Memos source directory for `.m4a` and `.composition` pairs
- waits for both files to be stable
- parses metadata and native transcript data from the plist
- optionally cleans and formats transcripts using a local Ollama model
- writes a markdown note with required YAML frontmatter
- copies the `.m4a` audio into an `audio/` subfolder
- records durable state so rescans do not create duplicates

## First Run

On first run, VMEA must prompt the user to select an output folder before any export occurs.

Rules:

- this selection is mandatory
- the selected folder is persisted to `config.toml`
- markdown files are written into the selected output folder
- audio files are written into `output_folder/audio/`
- after first-run setup is complete, VMEA can run unattended

## Installation

```bash
git clone https://github.com/klappe-pm/vmea.git
cd vmea
pip install -e .
```

### Requirements

- macOS 13+ (Ventura or later)
- Python 3.11+
- Full Disk Access permission (for Voice Memos folder)

## Quick Start

```bash
# First run – select output folder
vmea init

# Export all memos
vmea export

# Check system health
vmea doctor

# Retry previously failed exports
vmea retry-failed

# Watch for new memos (foreground)
vmea watch

# Install as background daemon
vmea daemon install
```

## Optional Local LLM Cleanup

Ollama-based transcript cleanup is optional.

If `llm_cleanup_enabled = false`, VMEA:

- does not require Ollama
- does not load transcript instruction files
- exports using the raw transcript produced by native extraction

If `llm_cleanup_enabled = true`, VMEA will:

1. check if Ollama is running (start if needed)
2. verify the configured model is available
3. preload the model into memory
4. run transcript cleanup using local instructions

### Ollama Commands

```bash
# Check Ollama status
vmea ollama status

# Start Ollama server
vmea ollama start
vmea ollama start --terminal  # Opens in Terminal.app

# List available models
vmea ollama models

# Interactively select and configure a model
vmea ollama select

# Pull a new model
vmea ollama pull llama3.2:3b
```

Transcript cleanup is post-processing only. It may:

- fix punctuation
- fix obvious transcript artifacts
- improve paragraphing
- apply formatting rules

It must not:

- summarize
- invent content
- add interpretation

## Transcript Instruction Files

When LLM cleanup is enabled, transcript formatting instructions are resolved in this order:

1. explicit `transcript_instruction_path`
2. `CLAUDE.md`
3. `GEMINI.md`
4. `README.md`

## Required Frontmatter

Every markdown note must include:

- `domain`
- `subdomain`
- `date-created`
- `date-revised`
- `aliases`
- `tags`

Date rules:

- format must be `YYYY-MM-DD`
- on note creation, `date-created` and `date-revised` are identical
- on note update, `date-created` remains unchanged and `date-revised` updates

## Example Frontmatter

```yaml
---
domain: ""
subdomain: ""
date-created: 2026-01-14
date-revised: 2026-01-14
aliases:
  - "My Meeting Notes"
tags:
  - "voice-memo"
memo_id: "vm-123456789"
source: "voice-memos"
transcript_source: "native"
transcript_status: "present"
transcript_cleanup: ""
transcript_cleanup_model: ""
transcript_instruction_source: ""
audio_relpath: "audio/2026-01-14-my-meeting-notes.m4a"
---
```

## Configuration

VMEA uses a TOML config file at `~/.config/vmea/config.toml`.

See `config.example.toml` for all options.

## Commands

| Command | Description |
|---------|-------------|
| `vmea init` | First-run setup with folder picker |
| `vmea export` | Full export/reconciliation pass |
| `vmea export --memo-id <id>` | Export single memo |
| `vmea watch` | Foreground filesystem watcher |
| `vmea daemon install` | Install launchd daemon |
| `vmea daemon uninstall` | Remove launchd daemon |
| `vmea doctor` | System health check |
| `vmea retry-failed` | Retry previously failed exports |
| `vmea list` | List discovered memos |
| `vmea config` | Show current configuration |
| `vmea ollama status` | Check Ollama server status |
| `vmea ollama start` | Start Ollama server |
| `vmea ollama models` | List available models |
| `vmea ollama select` | Interactively select a model |
| `vmea ollama pull <model>` | Pull a model from registry |

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,ollama]
pytest
```

## License

MIT – see [LICENSE](LICENSE)
