# calibre-mcp

A minimal, **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server for a local [Calibre](https://calibre-ebook.com/) e-book library. It
wraps the `calibredb` CLI (`--for-machine` JSON output), so it needs no content
server and **cannot modify your library** — no write tools exist.

Defaults target Windows, but it runs anywhere `calibredb` does (macOS/Linux) —
just set the two environment variables below.

## Tools

| Tool | Description |
|------|-------------|
| `search_books(query, limit=20, offset=0)` | Search using Calibre's search syntax (e.g. `author:Erikson`, `tag:Fantasy`, `series:"Malazan"`); page with `offset`. |
| `list_books(limit=50, offset=0, sort_by="timestamp", ascending=False)` | List/browse the library, sorted; page through it with `offset`. |
| `get_book(book_id)` | Full metadata for one book by its Calibre ID. |
| `list_recent(limit=10)` | Most recently added books. |
| `count_books()` | Total number of books in the library. |

## Requirements

- [Calibre](https://calibre-ebook.com/) installed (provides `calibredb`).
- [`uv`](https://docs.astral.sh/uv/) to manage the environment.

## Install

```bash
git clone https://github.com/mmccarthy404/calibre-mcp.git
cd calibre-mcp
uv sync
```

## Configuration

Set via environment variables (Windows defaults shown; change to your paths):

| Variable | Default | Notes |
|----------|---------|-------|
| `CALIBRE_LIBRARY_PATH` | `D:\Documents\Calibre Library` | Path to your Calibre library folder (contains `metadata.db`). |
| `CALIBREDB_PATH` | `C:\Program Files\Calibre2\calibredb.exe` | Path to `calibredb` (on macOS/Linux, usually just `calibredb`). |

## Run

```bash
uv run calibre-mcp        # or: uv run python calibre_mcp.py
```

## Register with Claude Code

```bash
claude mcp add calibre --scope user -- \
  uv run --directory "/path/to/calibre-mcp" python calibre_mcp.py
```

Then, in a new Claude session, ask things like *"search my Calibre library for
Erikson"* or *"what are my 5 most recently added books?"*.

## License

[MIT](LICENSE)
