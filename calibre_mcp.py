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

import os
import sys

# --- Windows MCP stdio fix (must run BEFORE importing fastmcp) --------------
# The MCP SDK frames messages with TextIOWrapper(sys.stdout.buffer) using the
# default newline=None, which on Windows rewrites every '\n' as '\r\n'. That
# stray '\r' corrupts the newline-delimited JSON-RPC stream and hangs clients
# (os.linesep and fd binary-mode do NOT help — the CRLF is baked into
# TextIOWrapper). Interpose a binary writer on sys.stdout.buffer that strips the
# '\r' back out, so the SDK's wrapper ends up emitting clean LF.
if sys.platform == "win32":

    class _LFBuffer:
        """Binary writer proxy that rewrites b'\\r\\n' -> b'\\n'."""

        def __init__(self, raw):
            self._raw = raw

        def write(self, data):
            # Strip all raw CR bytes. A literal 0x0D never appears in MCP's
            # UTF-8 JSON (a CR inside a string is escaped as \r), so the only
            # source is Windows newline translation — safe to remove wholesale,
            # and robust to '\r'/'\n' landing in separate write() calls.
            return self._raw.write(data.replace(b"\r", b""))

        def __getattr__(self, name):
            return getattr(self._raw, name)

    class _StdoutProxy:
        """sys.stdout stand-in whose .buffer is the LF-stripping writer."""

        def __init__(self, real):
            self._real = real
            self.buffer = _LFBuffer(real.buffer)

        def __getattr__(self, name):
            return getattr(self._real, name)

    sys.stdout = _StdoutProxy(sys.stdout)
# ---------------------------------------------------------------------------

import json
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
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            # CRITICAL: this server talks MCP over stdio. Without redirecting
            # stdin, calibredb inherits that pipe and blocks on it forever,
            # hanging every tool call. Give it an empty stdin instead.
            stdin=subprocess.DEVNULL,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "calibredb timed out after 60s. If the Calibre app is open, close it "
            "(it blocks direct library access) and try again."
        )
    if proc.returncode != 0:
        err = proc.stderr.strip()
        if "Another calibre program" in err or "is running" in err:
            raise RuntimeError(
                "Calibre appears to be open. calibredb cannot read the library "
                "directly while the Calibre desktop app is running. Please close "
                "Calibre and try again (or run Calibre's Content Server)."
            )
        raise RuntimeError(
            f"calibredb failed ({proc.returncode}): {err or 'unknown error'}"
        )
    return proc.stdout


def _list(*extra: str) -> list[dict]:
    """Run `calibredb list --for-machine` with the core fields plus extra args."""
    out = _calibredb("list", "--for-machine", "--fields", FIELDS, *extra)
    return json.loads(out or "[]")


@mcp.tool()
def search_books(query: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """Search the Calibre library using Calibre's search syntax.

    Examples: ``author:Erikson``, ``title:Malazan``, ``tag:Fantasy``,
    ``series:"Malazan Book of the Fallen"``, or plain free text. Use ``offset``
    to page through matches. Read-only.
    """
    return _list("--search", query, "--limit", str(offset + limit))[offset:]


@mcp.tool()
def list_books(
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "timestamp",
    ascending: bool = False,
) -> list[dict]:
    """List books in the library, sorted. Read-only.

    Use ``offset`` to page through the whole library. (calibredb has no native
    offset, so this fetches offset+limit rows and drops the first ``offset``.)
    For a small library, just pass a large ``limit`` to get everything at once.
    ``sort_by`` accepts any Calibre column, e.g. ``title``, ``authors``,
    ``pubdate``, ``timestamp``, ``rating``.
    """
    extra = ["--limit", str(offset + limit), "--sort-by", sort_by]
    if ascending:
        extra.append("--ascending")
    return _list(*extra)[offset:]


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


@mcp.tool()
def count_books() -> int:
    """Return the total number of books in the library. Read-only.

    Call this first to know how many books exist, then fetch them all with
    ``list_books(limit=<count>)`` or page with ``offset``.
    """
    out = _calibredb("list", "--for-machine", "--fields", "id", "--limit", "1000000000")
    return len(json.loads(out or "[]"))


def main() -> None:
    """Entry point: run the MCP server over stdio.

    Windows stdio is normalized to LF-only at module import (see top of file).
    The FastMCP banner is disabled: it prints to stderr, and a client that does
    not promptly drain stderr can stall the server at startup.
    """
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
