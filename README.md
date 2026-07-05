# calibre-mcp

A minimal, **read-only** [Model Context Protocol](https://modelcontextprotocol.io)
server for a local [Calibre](https://calibre-ebook.com/) e-book library on
Windows. It wraps the `calibredb` CLI (`--for-machine` JSON output), so it needs
no content server and cannot modify your library — no write tools exist.

## Tools

| Tool | Description |
|------|-------------|
| `search_books(query, limit=20)` | Search using Calibre's search syntax (e.g. `author:Erikson`, `tag:Fantasy`). |
| `list_books(limit=50, sort_by="timestamp", ascending=False)` | List/browse the library, sorted. |
| `get_book(book_id)` | Full metadata for one book by its Calibre ID. |
| `list_recent(limit=10)` | Most recently added books. |

## Requirements

- [Calibre](https://calibre-ebook.com/) installed (provides `calibredb`).
- [`uv`](https://docs.astral.sh/uv/) to manage the environment.

## Configuration

Set via environment variables (Windows defaults shown):

| Variable | Default |
|----------|---------|
| `CALIBRE_LIBRARY_PATH` | `D:\Documents\Calibre Library` |
| `CALIBREDB_PATH` | `C:\Program Files\Calibre2\calibredb.exe` |

## Run

```bash
uv sync
uv run calibre-mcp     # or: uv run python calibre_mcp.py
```

## Register with Claude Code

```bash
claude mcp add calibre --scope user -- \
  uv run --directory "D:\projects\calibre-mcp" python calibre_mcp.py
```

## License

MIT
