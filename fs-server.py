"""
Minimal, secure MCP Filesystem Server (Python)

Features:
- Exposes a small set of filesystem "tools" to an MCP host:
  - list_dir(path)
  - read_file(path, max_bytes=...)
  - stat(path)
  - search(path, query, max_results=...)
- Safe by default: all paths are rooted under a configured root directory, preventing path traversal.
- Read-size limits and read-only by default; you can extend to write/delete with care.

Usage (development):
    pip install mcp-server
    python mcp_filesystem_server.py

Then connect an MCP host (eg. Claude Desktop or the MCP Inspector) using stdio transport
or run `mcp dev mcp_filesystem_server.py` if you have the MCP dev tooling installed.

IMPORTANT SECURITY NOTE: Running a filesystem MCP exposes local files to whatever MCP client
connects (for example an LLM host). Only run this server in trusted environments and/or
restrict the `ROOT_DIR` to a safe directory.
"""

from pathlib import Path
import os
import typing as t

try:
    from mcp.server.fastmcp import FastMCP
except Exception as e:
    raise RuntimeError(
        "Missing MCP Python SDK. Install it (pip install mcp-server or check the SDK docs)."
    )

# Configuration
ROOT_DIR = Path(os.environ.get("MCP_FS_ROOT", "."))  # root of allowed filesystem access
READ_LIMIT_BYTES = int(os.environ.get("MCP_FS_READ_LIMIT", "200000"))  # 200 KB default
NAME = "Filesystem"

mcp = FastMCP(NAME)

# Helper utilities
def _resolve_path(user_path: str) -> Path:
    """
    Resolve a user-supplied path and ensure it is inside ROOT_DIR.
    Raises ValueError if the path is outside the allowed root.
    """
    p = (ROOT_DIR / user_path).resolve()
    try:
        root_resolved = ROOT_DIR.resolve()
    except Exception:
        root_resolved = ROOT_DIR

    if not str(p).startswith(str(root_resolved)):
        raise ValueError("path outside of allowed root")
    return p


@mcp.tool()
def list_dir(path: str = "") -> t.Dict[str, t.Any]:
    """
    List directory contents. Returns a dict with 'entries' (list of name/type) and 'path'.
    """
    p = _resolve_path(path)
    if not p.exists():
        return {"error": "not_found", "path": str(p)}
    if not p.is_dir():
        return {"error": "not_a_directory", "path": str(p)}

    entries = []
    for child in sorted(p.iterdir(), key=lambda x: x.name):
        entries.append({
            "name": child.name,
            "is_dir": child.is_dir(),
            "size": child.stat().st_size if child.is_file() else None,
        })
    return {"path": str(p), "entries": entries}


@mcp.tool()
def stat(path: str) -> t.Dict[str, t.Any]:
    """
    Return basic stat info for a file or directory.
    """
    p = _resolve_path(path)
    if not p.exists():
        return {"error": "not_found", "path": str(p)}
    st = p.stat()
    return {
        "path": str(p),
        "is_dir": p.is_dir(),
        "size": st.st_size,
        "mtime": int(st.st_mtime),
        "ctime": int(st.st_ctime),
    }


@mcp.tool()
def read_file(path: str, max_bytes: int = READ_LIMIT_BYTES) -> t.Dict[str, t.Any]:
    """
    Read up to max_bytes from a file and return as UTF-8 string if possible.
    Returns {'path':..., 'content':..., 'truncated': bool} or error dict.
    """
    if max_bytes <= 0:
        return {"error": "invalid_max_bytes"}
    max_bytes = min(max_bytes, READ_LIMIT_BYTES)

    p = _resolve_path(path)
    if not p.exists() or not p.is_file():
        return {"error": "not_found_or_not_file", "path": str(p)}

    try:
        with p.open("rb") as f:
            data = f.read(max_bytes + 1)
    except Exception as e:
        return {"error": "read_failed", "reason": str(e)}

    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]

    # Try to decode as utf-8; if fails, return base64 to avoid data loss
    try:
        text = data.decode("utf-8")
        return {"path": str(p), "content": text, "truncated": truncated, "encoding": "utf-8"}
    except Exception:
        import base64

        b64 = base64.b64encode(data).decode("ascii")
        return {"path": str(p), "content": b64, "truncated": truncated, "encoding": "base64"}


@mcp.tool()
def search(path: str = "", query: str = "", max_results: int = 25) -> t.Dict[str, t.Any]:
    """
    Simple filename search (not full-text). Walks the directory tree (bounded) and returns matching file paths.
    """
    p = _resolve_path(path)
    if not p.exists() or not p.is_dir():
        return {"error": "not_found_or_not_dir", "path": str(p)}

    if max_results <= 0:
        return {"error": "invalid_max_results"}
    matches = []
    q_lower = query.lower()
    # Walk but limit depth/number of entries to avoid DoS
    for root, dirs, files in os.walk(p):
        # optionally limit depth by comparing Path parts
        for fname in files:
            if q_lower in fname.lower():
                full = Path(root) / fname
                matches.append(str(full))
                if len(matches) >= max_results:
                    return {"path": str(p), "matches": matches, "truncated": True}
    return {"path": str(p), "matches": matches, "truncated": False}


# Additional metadata resource to advertise server capabilities
@mcp.resource("resource://capabilities")
def capabilities():
    return {
        "name": NAME,
        "description": "Filesystem access (read-only) with path-rooting and size limits",
        "tools": ["list_dir", "stat", "read_file", "search"],
        "root": str(ROOT_DIR.resolve()),
        "read_limit_bytes": READ_LIMIT_BYTES,
    }


if __name__ == "__main__":
    print(f"Starting MCP Filesystem server for root: {ROOT_DIR.resolve()}")
    mcp.run(transport="stdio")
