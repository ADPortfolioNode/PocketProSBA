"""Read uploaded documents and keep a small built-in search index of them.

Why this exists: the Chroma path needs a running Chroma server *and* a
downloaded embedding model. When either is missing the upload used to be
saved but never searchable, so chat couldn't discuss it. This index is plain
Python (BM25 over ~900-character sections), persisted next to the uploads as
JSON, so upload -> index -> retrieve works on every deploy. Chroma ingest
still runs alongside it when available.

    text, pages = extract_text(path, "lease.pdf")
    index().add_document("lease.pdf", text, pages=pages)
    index().search("when does the lease end?", k=4, filename="lease.pdf")
"""
from __future__ import annotations

import html
import json
import logging
import math
import os
import re
import threading
import zipfile
from collections import Counter
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

CHUNK_CHARS = 900
INDEX_FILENAME = ".doc_index.json"
MAX_TEXT_CHARS = 2_000_000  # ~600 pages; more than that is cut

STOPWORDS = set(
    "a an and are as at be by for from has have how i if in into is it its my of on or our so that the "
    "their there these this to was we what when where which who why will with you your me do does did can "
    "could should would about any all also than then them they us".split()
)


# --- text extraction ------------------------------------------------------

def extract_text(path: str, filename: str):
    """(text, pages) for a saved upload. pages is an int for PDFs, else None.

    Raises ValueError with a friendly message when nothing readable is found.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    pages = None
    if ext == "pdf":
        from pypdf import PdfReader

        try:
            reader = PdfReader(path)
            pages = len(reader.pages)
            parts = []
            for i, page in enumerate(reader.pages, start=1):
                try:
                    parts.append(f"[Page {i}]\n{page.extract_text() or ''}")
                except Exception as err:  # one bad page shouldn't sink the file
                    logger.warning("PDF page %s of %s unreadable: %s", i, filename, err)
            text = "\n\n".join(parts)
        except Exception as err:
            raise ValueError("We couldn't open that PDF. Is it password-protected or damaged?") from err
    elif ext == "docx":
        text = _docx_text(path)
    elif ext == "doc":
        raise ValueError("Old .doc files can't be read. Please save it as .docx or PDF and upload again.")
    elif ext in ("html", "htm"):
        raw = _read_plain(path)
        raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
        text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    elif ext == "rtf":
        raw = _read_plain(path)
        text = re.sub(r"\\[a-z]+-?\d* ?|[{}]", " ", raw)
    else:
        text = _read_plain(path)
    text = re.sub(r"[ \t\r\f\v]+", " ", text or "")
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    if len(re.sub(r"\[Page \d+\]", "", text).strip()) < 20:
        raise ValueError(
            "We saved the file but couldn't find readable text in it. "
            "If it's a scanned PDF, try a text-based PDF, DOCX or TXT."
        )
    return text[:MAX_TEXT_CHARS], pages


def _read_plain(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _docx_text(path: str) -> str:
    try:
        import docx  # python-docx

        d = docx.Document(path)
        parts = [p.text for p in d.paragraphs]
        for table in d.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts)
    except ImportError:
        pass
    except Exception as err:
        logger.warning("python-docx failed on %s (%s); trying raw XML", path, err)
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    except Exception as err:
        raise ValueError("We couldn't open that Word file. Please check it isn't damaged.") from err
    xml = re.sub(r"</w:p>", "\n", xml)
    return html.unescape(re.sub(r"<[^>]+>", "", xml))


# --- chunking + search ----------------------------------------------------

def _stem(t: str) -> str:
    """Light suffix stemming so "end" matches "ending"/"ended"/"ends"."""
    if t.isdigit() or len(t) <= 3:
        return t
    for suf in ("ing", "ed", "es", "s"):
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            return t[: -len(suf)]
    return t


def tokenize(text: str):
    return [_stem(t) for t in re.findall(r"[a-z0-9]+(?:'[a-z]+)?", (text or "").lower()) if t not in STOPWORDS and len(t) > 1]


def chunk_text(text: str, size: int = CHUNK_CHARS):
    """Split on paragraph boundaries into ~size-character sections."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        while len(p) > size:  # very long paragraph: split at a sentence end or a space
            cut = p.rfind(". ", 0, size)
            if cut > size // 2:
                cut += 1
            else:
                cut = p.rfind(" ", 0, size)
                if cut <= 0:
                    cut = size
            piece, p = p[:cut].strip(), p[cut:].strip()
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(piece)
        if len(cur) + len(p) + 2 <= size:
            cur = f"{cur}\n\n{p}" if cur else p
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


class DocIndex:
    def __init__(self, folder: str):
        self.folder = folder
        self.path = os.path.join(folder, INDEX_FILENAME)
        self._lock = threading.Lock()
        self._data = None
        self._mtime = None

    # persistence
    def _load(self):
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            self._data, self._mtime = {"documents": {}, "chunks": []}, None
            return self._data
        if self._data is None or mtime != self._mtime:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                self._mtime = mtime
            except Exception as err:
                logger.error("Document index unreadable (%s); starting fresh", err)
                self._data, self._mtime = {"documents": {}, "chunks": []}, None
        return self._data

    def _save(self, data):
        os.makedirs(self.folder, exist_ok=True)
        tmp = f"{self.path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, self.path)  # atomic: a crash never leaves half a file
        self._data, self._mtime = data, os.path.getmtime(self.path)

    # api
    def add_document(self, filename: str, text: str, pages=None):
        chunks = chunk_text(text)
        with self._lock:
            data = self._load()
            data = {"documents": dict(data["documents"]),
                    "chunks": [c for c in data["chunks"] if c["doc"] != filename]}
            for i, body in enumerate(chunks):
                page = None
                m = re.findall(r"\[Page (\d+)\]", body)
                if m:
                    page = int(m[0])
                data["chunks"].append({"doc": filename, "n": i + 1, "page": page, "text": body})
            data["documents"][filename] = {
                "filename": filename,
                "chunks": len(chunks),
                "pages": pages,
                "chars": len(text),
                "indexed_at": datetime.now(timezone.utc).isoformat(),
            }
            self._save(data)
        return data["documents"][filename]

    def remove_document(self, filename: str) -> bool:
        with self._lock:
            data = self._load()
            if filename not in data["documents"]:
                return False
            data = {"documents": {k: v for k, v in data["documents"].items() if k != filename},
                    "chunks": [c for c in data["chunks"] if c["doc"] != filename]}
            self._save(data)
            return True

    def documents(self):
        with self._lock:
            return dict(self._load()["documents"])

    def has(self, filename: str) -> bool:
        return filename in self.documents()

    def search(self, query: str, k: int = 4, filename: str | None = None):
        """Top-k sections by BM25: [{doc, n, page, text, score}] (score > 0 only)."""
        q = tokenize(query)
        with self._lock:
            chunks = list(self._load()["chunks"])
        if filename:
            chunks = [c for c in chunks if c["doc"] == filename]
        if not chunks or not q:
            return []
        toks = [tokenize(c["text"]) for c in chunks]
        n = len(chunks)
        avg = sum(len(t) for t in toks) / n or 1
        df = Counter()
        for t in toks:
            df.update(set(t))
        k1, b = 1.5, 0.75
        scored = []
        for c, t in zip(chunks, toks):
            tf = Counter(t)
            s = 0.0
            for term in set(q):
                if term not in tf:
                    continue
                idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
                s += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * len(t) / avg))
            if s > 0:
                scored.append({**c, "score": round(s, 4)})
        scored.sort(key=lambda x: (-x["score"], x["doc"], x["n"]))
        return scored[:k]


_indexes = {}
_indexes_lock = threading.Lock()


def upload_folder() -> str:
    try:
        from backend.routes import files as files_routes
        return files_routes.UPLOAD_FOLDER
    except Exception:  # pragma: no cover
        return os.environ.get("UPLOAD_FOLDER", "uploads")


def index(folder: str | None = None) -> DocIndex:
    folder = os.path.abspath(folder or upload_folder())
    with _indexes_lock:
        if folder not in _indexes:
            _indexes[folder] = DocIndex(folder)
        return _indexes[folder]
