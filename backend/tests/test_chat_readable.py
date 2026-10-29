"""Chat answers must read like plain conversation, not a document dump.

Regression for the 2026-10-26 readability fix: a RAG answer used to stack
a bold intro, one "### N. Title" heading per hit, a per-item
"Official page / Open in Resources" line, a full "## Links" list, a
"### More links" list, and a "## Use this information" section — with the
same links a third time in the Resources panel.

2026-10-27 message-only rule (screenshot report): the bubble carries
ONLY the conversational message — no resource titles, no per-resource
paragraphs, no "Current link on sba.gov" pointer lines. Every resource
and its link lives in the Resources panel via the returned sources,
deduplicated there, so a link already shown is never listed again.
"""

from backend.assistants.concierge import Concierge, META_ANSWER
from backend.services.chat_answer_format import format_hits_as_answer


def _hits():
    return [
        {
            "id": "1",
            "title": "SBA 7(a) loans",
            "body": "7(a) loans help small businesses with working capital and equipment. "
            "They are guaranteed by the SBA and made by approved lenders.",
            "path": "/api/sba/content/loans/7a",
            "url": "https://www.sba.gov/funding-programs/loans/7a-loans",
            "type": "loan program",
            "metadata": {},
        },
        {
            "id": "2",
            "title": "SBA Microloans",
            "body": "Microloans of up to $50,000 help small businesses start up and expand.",
            "path": "/api/sba/content/loans/microloans",
            "url": "https://www.sba.gov/funding-programs/loans/microloans",
            "type": "loan program",
            "metadata": {},
        },
    ]


def test_rag_answer_is_plain_text_without_link_sections():
    text, sources = format_hits_as_answer("7(a) loans", _hits())
    # Message only: no resource titles, no per-resource paragraphs, no
    # link-pointer lines, no headings, no markdown links, no URLs.
    assert "SBA 7(a) loans" not in text
    assert "SBA Microloans" not in text
    assert "working capital" not in text
    assert "Current link" not in text
    assert "sba.gov" not in text
    assert "## Links" not in text
    assert "###" not in text
    assert "##" not in text
    assert "](" not in text
    assert "→" not in text
    assert "Official page" not in text
    assert "Use this information" not in text
    # But the message still says resources were found and where to open them.
    assert "2 SBA resources" in text
    assert "Links & resources panel" in text


def test_rag_answer_bubble_never_repeats_screenshot_link_lines():
    # Body text exactly like the SBA API snapshots in the reported
    # screenshot: a "Current link on sba.gov" pointer line must not leak
    # into the bubble even when it is the resource's whole paragraph.
    hits = [
        {
            "id": "9",
            "title": "Write your business plan",
            "body": "Current link on sba.gov — open source for full official details.",
            "path": "/api/sba/content/articles/123",
            "url": "https://www.sba.gov/business-guide/plan-your-business/write-your-business-plan",
            "type": "article",
            "metadata": {},
        },
    ]
    text, sources = format_hits_as_answer("business plan", hits)
    assert "Current link" not in text
    assert "Write your business plan" not in text
    assert sources[0]["title"] == "Write your business plan"
    assert sources[0]["url"].startswith("https://www.sba.gov/")


def test_rag_answer_sources_still_carry_links_for_resources_panel():
    _text, sources = format_hits_as_answer("7(a) loans", _hits())
    assert len(sources) == 2
    assert sources[0]["url"] == "https://www.sba.gov/funding-programs/loans/7a-loans"
    assert sources[0]["path"] == "/api/sba/content/loans/7a"
    assert sources[1]["title"] == "SBA Microloans"


def test_rag_answer_empty_hits_is_plain_too():
    text, sources = format_hits_as_answer("nothing here", [])
    assert sources == []
    assert "## Links" not in text
    assert "couldn't find" in text


def test_meta_question_about_instructions_is_not_a_document_search():
    concierge = Concierge()
    assert concierge._classify_intent("what are your instructions?", {}) == "meta"
    assert concierge._classify_intent("what can you do?", {}) == "meta"
    assert concierge._classify_intent("how do you work?", {}) == "meta"
    # Real SBA questions are unaffected.
    assert concierge._classify_intent("what is SBA", {}) == "document_search"
    assert concierge._classify_intent("help me create a business plan", {}) == "task_request"


def test_meta_answer_is_short_plain_text_without_task_lead_or_dump():
    concierge = Concierge()
    result = concierge.handle_message("what are your instructions?", "test-chat-readable-meta")
    text = result.get("text", "")
    assert text == META_ANSWER
    assert "Got it" not in text
    assert "###" not in text
    assert "##" not in text
    assert "loan approval" in text or "eligibility" in text
