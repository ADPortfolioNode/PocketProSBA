"""
FileAgent — list, read, and search local uploaded documents.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import BaseAssistant

logger = logging.getLogger(__name__)

# Prefer project uploads/; fall back to common paths used in Docker
UPLOAD_CANDIDATES = [
    os.environ.get("UPLOAD_FOLDER", ""),
    "uploads",
    "/app/uploads",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"),
    "frontend/uploads",
]


def _resolve_upload_dir() -> str:
    for path in UPLOAD_CANDIDATES:
        if path and os.path.isdir(path):
            return os.path.abspath(path)
    # Default create under cwd
    default = os.path.abspath("uploads")
    os.makedirs(default, exist_ok=True)
    return default


class FileAgent(BaseAssistant):
    """Works with files on disk in the uploads directory."""

    ALLOWED_EXT = {".txt", ".md", ".markdown", ".csv", ".json", ".log", ".pdf", ".doc", ".docx"}

    def __init__(self, upload_folder: Optional[str] = None):
        super().__init__("FileAgent")
        self.upload_folder = upload_folder or _resolve_upload_dir()

    def handle_message(self, message, session_id=None, metadata=None):
        try:
            self._update_status("processing", 15, "Interpreting file request…")
            text = (message or "").strip()
            low = text.lower()

            if not text:
                return self.report_failure("No file instruction provided.")

            if any(k in low for k in ("list", "show files", "what files", "documents available")):
                return self._list_response()
            if any(k in low for k in ("search", "find", "look for", "contains")):
                query = self._extract_query(text)
                return self._search_response(query)
            if any(k in low for k in ("read", "open", "show content", "display")):
                name = self._extract_filename(text)
                if name:
                    return self._read_response(name)
                return self._list_response()
            if any(k in low for k in ("upload", "save")):
                return self.report_success(
                    text=(
                        "To upload a document, use **POST /api/documents/upload** "
                        "(multipart form field `file`) or the Documents UI. "
                        f"Files are stored in `{self.upload_folder}`."
                    ),
                    additional_data={"upload_folder": self.upload_folder},
                )

            # Default: search message terms in files
            return self._search_response(text)

        except Exception as e:
            logger.exception("FileAgent failed")
            return self.report_failure(f"FileAgent error: {e}")

    def list_files(self) -> Dict[str, Any]:
        files = []
        folder = self.upload_folder
        if not os.path.isdir(folder):
            return {"files": [], "folder": folder}
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if not os.path.isfile(path):
                continue
            ext = os.path.splitext(name)[1].lower()
            files.append({
                "filename": name,
                "size": os.path.getsize(path),
                "modified": os.path.getmtime(path),
                "extension": ext,
                "readable": ext in {".txt", ".md", ".markdown", ".csv", ".json", ".log"},
            })
        return {"files": files, "folder": folder, "count": len(files)}

    def upload_file(self, file) -> Dict[str, Any]:
        """Save a Werkzeug FileStorage-like object into uploads."""
        from werkzeug.utils import secure_filename

        os.makedirs(self.upload_folder, exist_ok=True)
        filename = secure_filename(getattr(file, "filename", None) or "upload.bin")
        if not filename:
            return {"success": False, "error": "Invalid filename"}
        dest = os.path.join(self.upload_folder, filename)
        file.save(dest)
        return {
            "success": True,
            "filename": filename,
            "path": dest,
            "size": os.path.getsize(dest),
        }

    def read_file(self, filename: str, max_chars: int = 8000) -> Dict[str, Any]:
        safe = os.path.basename(filename)
        path = os.path.join(self.upload_folder, safe)
        if not os.path.isfile(path):
            return {"success": False, "error": f"File not found: {safe}"}
        ext = os.path.splitext(safe)[1].lower()
        if ext == ".pdf":
            return {
                "success": True,
                "filename": safe,
                "content": (
                    f"[PDF] {safe} ({os.path.getsize(path)} bytes). "
                    "Binary PDF text extraction is limited in this agent; "
                    "use the Documents/RAG pipeline for full indexing."
                ),
                "truncated": True,
            }
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(max_chars + 1)
            truncated = len(content) > max_chars
            if truncated:
                content = content[:max_chars]
            return {
                "success": True,
                "filename": safe,
                "content": content,
                "truncated": truncated,
                "size": os.path.getsize(path),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, query: str, max_hits: int = 20) -> List[Dict[str, Any]]:
        hits = []
        terms = [t for t in re.split(r"\s+", (query or "").lower()) if len(t) > 2]
        listing = self.list_files().get("files", [])
        for info in listing:
            if not info.get("readable"):
                # still match filename
                if any(t in info["filename"].lower() for t in terms):
                    hits.append({
                        "filename": info["filename"],
                        "snippet": f"Filename match for: {query}",
                        "score": 1,
                    })
                continue
            data = self.read_file(info["filename"], max_chars=20000)
            if not data.get("success"):
                continue
            content = data.get("content", "")
            low = content.lower()
            score = sum(low.count(t) for t in terms) if terms else 0
            if score <= 0 and terms:
                continue
            # snippet around first term
            snippet = content[:240].replace("\n", " ")
            for t in terms:
                idx = low.find(t)
                if idx >= 0:
                    start = max(0, idx - 60)
                    snippet = content[start:start + 200].replace("\n", " ")
                    break
            hits.append({"filename": info["filename"], "snippet": snippet, "score": score})
            if len(hits) >= max_hits:
                break
        hits.sort(key=lambda h: h["score"], reverse=True)
        return hits

    def _list_response(self):
        data = self.list_files()
        files = data.get("files", [])
        if not files:
            return self.report_success(
                text=f"No files found in `{data.get('folder')}`. Upload via `/api/documents/upload`.",
                additional_data=data,
            )
        lines = [f"**{len(files)} file(s)** in `{data['folder']}`:\n"]
        for f in files:
            lines.append(f"- `{f['filename']}` ({f['size']} bytes)")
        return self.report_success(text="\n".join(lines), additional_data=data)

    def _read_response(self, filename: str):
        data = self.read_file(filename)
        if not data.get("success"):
            return self.report_failure(data.get("error", "Read failed"))
        note = "\n\n_(truncated)_" if data.get("truncated") else ""
        return self.report_success(
            text=f"**{data['filename']}**\n\n```\n{data['content']}\n```{note}",
            additional_data=data,
        )

    def _search_response(self, query: str):
        self._update_status("searching", 50, f"Searching files for “{query[:40]}”…")
        hits = self.search_files(query)
        if not hits:
            return self.report_success(
                text=f"No matches for “{query}” in uploaded files.",
                additional_data={"query": query, "hits": []},
            )
        lines = [f"**Search results for** “{query}” ({len(hits)} hits):\n"]
        for h in hits[:10]:
            lines.append(f"- **{h['filename']}** (score {h['score']}): {h['snippet'][:160]}…")
        return self.report_success(
            text="\n".join(lines),
            sources=[{"title": h["filename"], "snippet": h["snippet"]} for h in hits[:10]],
            additional_data={"query": query, "hits": hits},
        )

    def _extract_filename(self, text: str) -> Optional[str]:
        # quoted name or known file from listing
        m = re.search(r"[\"']([^\"']+\.[A-Za-z0-9]+)[\"']", text)
        if m:
            return os.path.basename(m.group(1))
        m = re.search(r"([\w.\-]+\.(?:md|txt|pdf|csv|json|docx?))\b", text, re.I)
        if m:
            return os.path.basename(m.group(1))
        # fuzzy: any listed file name appearing in message
        for f in self.list_files().get("files", []):
            if f["filename"].lower() in text.lower():
                return f["filename"]
        return None

    def _extract_query(self, text: str) -> str:
        for prefix in ("search for", "find", "look for", "search", "contains"):
            if prefix in text.lower():
                idx = text.lower().find(prefix)
                return text[idx + len(prefix):].strip(" :\"'") or text
        return text
