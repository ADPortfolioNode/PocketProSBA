(function (global) {
  "use strict";
  var PHOTO = {
    "loan-advice": "css/assets/chat-bg/loan-advice.jpg",
    eligibility: "css/assets/chat-bg/eligibility.jpg",
    "real-estate-504": "css/assets/chat-bg/real-estate-504.jpg",
    documents: "css/assets/chat-bg/documents.jpg",
    general: "css/assets/chat-bg/general.jpg"
  };
  var photoCache = {};
  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&").replace(/</g, "<").replace(/>/g, ">").replace(/"/g, """);
  }
  function normalizeQueryResponse(raw) {
    var source = raw && typeof raw === "object" ? raw : {};
    var citations = Array.isArray(source.citations) ? source.citations : [];
    return {
      answerHtml: source.answerHtml || source.answer || "",
      citations: citations.map(function (item) {
        if (typeof item === "string") return { url: item, title: item, snippet: "" };
        return { url: item.url || "", title: item.title || item.url || "Source", snippet: item.snippet || "" };
      }),
      imageHint: PHOTO[source.imageHint] ? source.imageHint : "general",
      conversationId: source.conversationId || "anon"
    };
  }
  function applyStagePhoto(imageHint, conversationId) {
    var key = String(conversationId || "anon") + ":" + imageHint;
    if (!photoCache[key]) photoCache[key] = PHOTO[imageHint] || PHOTO.general;
    var img = document.querySelector(".content-stage__photo");
    if (img) { img.src = photoCache[key]; img.alt = ""; img.setAttribute("aria-hidden", "true"); }
    return photoCache[key];
  }
  function renderCitations(citations) {
    if (!citations.length) return "";
    var items = citations.map(function (cite) {
      return "<li><span><span class=\"ref-title\">" + escapeHtml(cite.title) +
        "</span><a href=\"" + escapeHtml(cite.url) + "\" target=\"_blank\" rel=\"noopener\">" +
        escapeHtml(cite.url) + "</a></span></li>";
    }).join("");
    return '<section class="chat-meta" aria-label="References"><h3>References</h3><ol class="chat-meta-links">' + items + "</ol></section>";
  }
  function renderQueryResult(root, payload, question) {
    var data = normalizeQueryResponse(payload);
    applyStagePhoto(data.imageHint, data.conversationId);
    var questionHtml = question ? '<p class="user-turn"><strong>You asked</strong> — ' + escapeHtml(question) + "</p>" : "";
    root.innerHTML = questionHtml + '<article class="chat-magazine">' + data.answerHtml + "</article>" + renderCitations(data.citations);
    return data;
  }
  var LIBRARY = {
    "Which SBA loan fits a retail startup?": {
      conversationId: "demo-retail", imageHint: "loan-advice",
      answerHtml: "<p>For a retail startup, begin with the flagship <a href=\"https://www.sba.gov/funding-programs/loans/7a-loans\" target=\"_blank\" rel=\"noopener\">SBA 7(a) loan</a>. It is the most flexible working-capital path for inventory, payroll, and leasehold improvements.</p><p>If you need less than $50,000, the <a href=\"https://www.sba.gov/funding-programs/loans/microloans\" target=\"_blank\" rel=\"noopener\">Microloan program</a> is often faster. Use <a href=\"https://www.sba.gov/funding-programs/loans/lender-match\" target=\"_blank\" rel=\"noopener\">Lender Match</a> to find a participating lender.</p>",
      citations: [
        { url: "https://www.sba.gov/funding-programs/loans/7a-loans", title: "SBA 7(a) loans", snippet: "Flagship working-capital program." },
        { url: "https://www.sba.gov/funding-programs/loans/microloans", title: "SBA Microloans", snippet: "Smaller amounts, counseling-friendly." },
        { url: "https://www.sba.gov/funding-programs/loans/lender-match", title: "Lender Match", snippet: "Connect with participating lenders." }
      ]
    },
    "How do I prepare for a 7(a) application?": {
      conversationId: "demo-7a-prep", imageHint: "documents",
      answerHtml: "<p>Treat the file as a lender package, not a form. Assemble a business plan, tax returns or projections, a personal financial statement, and a uses-of-proceeds memo. The <a href=\"https://www.sba.gov/funding-programs/loans/7a-loans\" target=\"_blank\" rel=\"noopener\">7(a) loan page</a> lists current terms.</p><p>Walk the checklist on the SBA <a href=\"https://www.sba.gov/funding-programs/loans\" target=\"_blank\" rel=\"noopener\">loans overview</a> before you request a term sheet.</p>",
      citations: [
        { url: "https://www.sba.gov/funding-programs/loans/7a-loans", title: "SBA 7(a) loans", snippet: "Terms, uses, and structure." },
        { url: "https://www.sba.gov/funding-programs/loans", title: "SBA-backed loans", snippet: "Program overview and next steps." }
      ]
    },
    "Compare 7(a) and 504 at a glance.": {
      conversationId: "demo-7a-504", imageHint: "real-estate-504",
      answerHtml: "<p><a href=\"https://www.sba.gov/funding-programs/loans/7a-loans\" target=\"_blank\" rel=\"noopener\">7(a)</a> is the generalist: working capital, equipment, acquisition. <a href=\"https://www.sba.gov/funding-programs/loans/504-loans\" target=\"_blank\" rel=\"noopener\">504</a> is the specialist for owner-occupied real estate and heavy equipment.</p><p>If the core need is a building, start at 504. If the need is cash to run the shop, start at 7(a).</p>",
      citations: [
        { url: "https://www.sba.gov/funding-programs/loans/7a-loans", title: "SBA 7(a) loans", snippet: "Flexible working capital." },
        { url: "https://www.sba.gov/funding-programs/loans/504-loans", title: "SBA 504 loans", snippet: "Owner-occupied real estate and equipment." }
      ]
    },
    "What are the basic SBA eligibility rules?": {
      conversationId: "demo-eligibility", imageHint: "eligibility",
      answerHtml: "<p>Most programs require a for-profit business operating in the United States, meeting SBA size standards, and showing conventional credit is not available on reasonable terms.</p><p>Confirm current rules on the official <a href=\"https://www.sba.gov/funding-programs/loans\" target=\"_blank\" rel=\"noopener\">loans page</a>. PocketProSBA retrieves this — it does not replace a lender decision.</p>",
      citations: [
        { url: "https://www.sba.gov/funding-programs/loans", title: "SBA-backed loans", snippet: "Eligibility and program list." },
        { url: "https://www.sba.gov/funding-programs/loans/lender-match", title: "Lender Match", snippet: "Find a participating lender." }
      ]
    }
  };
  function lookupSample(question) {
    return LIBRARY[question] || {
      conversationId: "demo-general", imageHint: "general",
      answerHtml: "<p>Ask about loan fit, eligibility, 7(a) prep, or 504 real estate and I will answer from SBA program guidance with inline sources.</p><p>Official program pages live on <a href=\"https://www.sba.gov/funding-programs/loans\" target=\"_blank\" rel=\"noopener\">sba.gov funding programs</a>.</p>",
      citations: [{ url: "https://www.sba.gov/funding-programs/loans", title: "SBA-backed loans", snippet: "Official program hub." }]
    };
  }
  global.PocketProQuery = {
    normalizeQueryResponse: normalizeQueryResponse,
    applyStagePhoto: applyStagePhoto,
    renderQueryResult: renderQueryResult,
    lookupSample: lookupSample
  };
})(window);
