"""Minimal read-only Calibre MCP server (Windows).

Wraps the ``calibredb`` CLI (``--for-machine`` JSON output) to expose a small
set of read-only tools over the Model Context Protocol. No write tools exist,
so this server cannot modify your library.

Configuration via environment variables (with sensible Windows defaults):
  CALIBRE_LIBRARY_PATH  path to your Calibre library
                        (default: D:\\Documents\\Calibre Library)
  CALIBREDB_PATH        path to calibredb(.exe)
                        (default: C:\\Program Files\\Calibre2\\calibredb.exe)
"""

from __future__ import annotations

import json
import os
import subprocess

from fastmcp import FastMCP

CALIBREDB = os.environ.get(
    "CALIBREDB_PATH", r"C:\Program Files\Calibre2\calibredb.exe"
)
LIBRARY = os.environ.get(
    "CALIBRE_LIBRARY_PATH", r"D:\Documents\Calibre Library"
)

# Core metadata fields returned for list/search results.
FIELDS = (
    "id,title,authors,series,series_index,tags,rating,"
    "publisher,pubdate,timestamp,languages,formats"
)

mcp = FastMCP("calibre-mcp")


def _calibredb(*args: str) -> str:
    """Run calibredb against the configured library and return stdout."""
    cmd = [CALIBREDB, *args, "--with-library", LIBRARY]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"calibredb failed ({proc.returncode}): "
            f"{proc.stderr.strip() or 'unknown error'}"
        )
    return proc.stdout


def _list(*extra: str) -> list[dict]:
    """Run `calibredb list --for-machine` with the core fields plus extra args."""
    out = _calibredb("list", "--for-machine", "--fields", FIELDS, *extra)
    return json.loads(out or "[]")


@mcp.tool()
def search_books(query: str, limit: int = 20) -> list[dict]:
    """Search the Calibre library using Calibre's search syntax.

    Examples: ``author:Erikson``, ``title:Malazan``, ``tag:Fantasy``,
    ``series:"Malazan Book of the Fallen"``, or plain free text. Returns
    matching books with their core metadata. Read-only.
    """
    return _list("--search", query, "--limit", str(limit))


@mcp.tool()
def list_books(
    limit: int = 50, sort_by: str = "timestamp", ascending: bool = False
) -> list[dict]:
    """List books in the library, sorted (default: newest first). Read-only.

    ``sort_by`` accepts any Calibre column, e.g. ``title``, ``authors``,
    ``pubdate``, ``timestamp``, ``rating``.
    """
    extra = ["--limit", str(limit), "--sort-by", sort_by]
    if ascending:
        extra.append("--ascending")
    return _list(*extra)


@mcp.tool()
def get_book(book_id: int) -> dict:
    """Get the full metadata for one book by its Calibre ID. Read-only."""
    out = _calibredb(
        "list", "--for-machine", "--fields", "all", "--search", f"id:{book_id}"
    )
    rows = json.loads(out or "[]")
    if not rows:
        raise ValueError(f"No book found with id {book_id}")
    return rows[0]


@mcp.tool()
def list_recent(limit: int = 10) -> list[dict]:
    """List the most recently added books (newest first). Read-only."""
    return _list("--sort-by", "timestamp", "--limit", str(limit))


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
