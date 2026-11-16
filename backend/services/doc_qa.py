"""Answer questions about the owner's uploaded documents, citing them.

Flow: retrieve the best sections from the built-in document index
(services/doc_index.py) -> if GEMINI_API_KEY is set, ask Gemini to answer
*only* from those sections -> otherwise (or if Gemini fails or is slow) give
an extractive answer: the most relevant passages, quoted, with the file and
page/section they came from. Either way every answer names its source.

The LLM call is one function (``generate``) so tests can stub it.
"""
from __future__ import annotations

import concurrent.futures
import logging
import os
import re

from backend.services import doc_index

logger = logging.getLogger(__name__)

PERSONA = (
    "You are PocketPro, a friendly, plain-English business concierge for busy small business owners "
    "who are experts at their own trade, not at paperwork. Be warm and concise, avoid jargon, and give "
    "practical next steps."
)
DOC_PROMPT = (
    PERSONA
    + "\n\nAnswer the owner's question using ONLY the document excerpts below. If the excerpts don't "
    "contain the answer, say so plainly and suggest what to look for. Keep it under 150 words. Cite the "
    "source after each fact like (lease.pdf, p. 2).\n\nExcerpts:\n{context}\n\nQuestion: {question}\n\nAnswer:"
)
GEMINI_TIMEOUT_SECONDS = float(os.environ.get("GEMINI_TIMEOUT_SECONDS", "20"))
MIN_SCORE = 0.5

DOC_WORDS = re.compile(
    r"\b(my|the|this|that|our|uploaded|attached)\s+(document|doc|file|pdf|upload|lease|contract|agreement|"
    r"business plan|plan|policy|proposal|report|statement|invoice|quote|docx)\b"
    r"|\b(in|from|according to|based on)\s+(my|the)\s+(document|doc|file|upload|lease|contract|plan)\b",
    re.I,
)


def gemini_configured() -> bool:
    return bool((os.environ.get("GEMINI_API_KEY") or "").strip())


def generate(prompt: str) -> str:
    """Call Gemini (google-generativeai). Raises on any failure."""
    import google.generativeai as genai

    genai.configure(api_key=os.environ["GEMINI_API_KEY"].strip())
    model = genai.GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"))
    resp = model.generate_content(prompt)
    text = (getattr(resp, "text", "") or "").strip()
    if not text:
        raise RuntimeError("empty Gemini response")
    return text


def _generate_with_timeout(prompt: str):
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        return pool.submit(generate, prompt).result(timeout=GEMINI_TIMEOUT_SECONDS)
    finally:
        pool.shutdown(wait=False)


def mentioned_document(message: str, docs) -> str | None:
    """A filename (or its stem) the message names, if any."""
    low = (message or "").lower()
    for name in sorted(docs, key=len, reverse=True):
        stem = name.rsplit(".", 1)[0].lower()
        if name.lower() in low or (len(stem) >= 4 and stem.replace("_", " ").replace("-", " ") in low.replace("_", " ").replace("-", " ")):
            return name
    return None


def wants_documents(message: str, workflow: str | None = None, document: str | None = None) -> bool:
    if document or workflow == "doc_qa":
        return True
    return bool(DOC_WORDS.search(message or ""))


def _cite(hit) -> str:
    where = f"p. {hit['page']}" if hit.get("page") else f"section {hit['n']}"
    return f"{hit['doc']}, {where}"


def _clean(text: str) -> str:
    text = re.sub(r"\[Page \d+\]\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _best_sentences(question: str, text: str, limit: int = 3) -> str:
    q = set(doc_index.tokenize(question))
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", _clean(text)) if len(s.strip()) > 20]
    if not sentences:
        return _clean(text)[:400]
    ranked = sorted(enumerate(sentences), key=lambda p: (-len(q & set(doc_index.tokenize(p[1]))), p[0]))
    keep = sorted(i for i, _ in ranked[:limit])
    out = " ".join(sentences[i] for i in keep)
    return out[:600]


def answer(question: str, document: str | None = None, k: int = 4):
    """Grounded answer dict, or None when there are no documents / no relevant section.

    {"text", "sources": [{"title", "filename", "page", "section", "snippet"}], "grounded": True,
     "document": <filename or None>, "mode": "gemini" | "extractive"}
    """
    idx = doc_index.index()
    docs = idx.documents()
    if not docs:
        return None
    target = document if document in docs else mentioned_document(question, docs)
    hits = idx.search(question, k=k, filename=target)
    hits = [h for h in hits if h["score"] >= MIN_SCORE]
    if not hits:
        name = target or (next(iter(docs)) if len(docs) == 1 else None)
        if name:
            return {
                "text": (f"I looked through **{name}** but couldn't find anything about that. "
                         "Could you put it another way, or tell me which part of the document it's in?"),
                "sources": [{"title": name, "filename": name}],
                "grounded": True,
                "document": name,
                "mode": "no_match",
            }
        return None

    sources = []
    for h in hits:
        sources.append({
            "title": h["doc"],
            "filename": h["doc"],
            "page": h.get("page"),
            "section": h["n"],
            "snippet": _clean(h["text"])[:240],
        })

    text = None
    mode = "extractive"
    if gemini_configured():
        context = "\n\n".join(f"[{_cite(h)}]\n{_clean(h['text'])}" for h in hits)
        try:
            text = _generate_with_timeout(DOC_PROMPT.format(context=context, question=question))
            mode = "gemini"
        except Exception as err:
            logger.warning("Gemini document answer failed, using extractive answer: %s", err)
            text = None
    if not text:
        top = hits[:2]
        lines = [f"Here's what {'your document says' if len({h['doc'] for h in top}) == 1 else 'your documents say'}:"]
        for h in top:
            lines.append(f"> {_best_sentences(question, h['text'])}\n>\n> — *{_cite(h)}*")
        text = "\n\n".join(lines)
    names = sorted({h["doc"] for h in hits})
    cited = "; ".join(_cite(h) for h in hits[:3])
    text = f"{text.rstrip()}\n\n**Source:** {cited}"
    return {
        "text": text,
        "sources": sources,
        "grounded": True,
        "document": target or (names[0] if len(names) == 1 else None),
        "mode": mode,
    }
