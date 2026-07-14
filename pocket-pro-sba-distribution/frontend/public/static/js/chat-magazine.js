/**
 * Live magazine formatter for the prebuilt chat UI.
 * Turns plain assistant text into readable paragraphs + itemized lists
 * with REAL clickable hyperlinks (markdown, https, official URLs, /api/sba routes).
 */
(function () {
  'use strict';

  function escapeHtml(str) {
    return String(str == null ? '' : str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function normalizeHref(raw) {
    var href = String(raw || '').trim().replace(/[.,;:)]+$/, '');
    if (!href) return '';
    if (/^www\./i.test(href)) href = 'https://' + href;
    // Raw API routes → Resources browser deep-link (usable, not JSON)
    if (href.indexOf('/api/sba/') === 0) {
      var title = href.split('/').filter(Boolean).pop() || 'SBA';
      return (
        '/browse#r=' +
        encodeURIComponent(href) +
        '&t=' +
        encodeURIComponent(title)
      );
    }
    return href;
  }

  function anchorHtml(label, href) {
    var h = normalizeHref(href);
    if (!h) return escapeHtml(label);
    var external = /^https?:\/\//i.test(h);
    var attrs = external ? ' target="_blank" rel="noopener noreferrer"' : '';
    var cls = external ? 'mag-link mag-link-ext' : 'mag-link mag-link-app';
    return (
      '<a href="' +
      escapeHtml(h) +
      '" class="' +
      cls +
      '"' +
      attrs +
      '>' +
      escapeHtml(label) +
      '</a>'
    );
  }

  function formatInline(text) {
    var raw = String(text == null ? '' : text);
    var tokens = [];
    function hold(html) {
      tokens.push(html);
      return '\u0000' + (tokens.length - 1) + '\u0000';
    }

    var s = raw;

    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (_, label, href) {
      return hold(anchorHtml(label, href));
    });

    s = s.replace(
      /(^|[\s])((?:Official\s*URL|URL|Source\s*URL|Link)\s*:\s*)(https?:\/\/[^\s]+)/gi,
      function (_, pre, label, url) {
        return (
          pre +
          hold(escapeHtml(label) + anchorHtml(url.replace(/[.,;:)]+$/, ''), url))
        );
      }
    );

    s = s.replace(
      /(^|[\s])((?:API\s*route|Route|Path)\s*:\s*)(\/api\/sba\/[^\s]+)/gi,
      function (_, pre, label, path) {
        return (
          pre +
          hold(escapeHtml(label) + anchorHtml(path.replace(/[.,;:)]+$/, ''), path))
        );
      }
    );

    s = s.replace(/(^|[^"'=\w/])(https?:\/\/[^\s<]+)/g, function (match, pre, url) {
      var clean = url.replace(/[.,;:)]+$/, '');
      return pre + hold(anchorHtml(clean, clean));
    });

    s = s.replace(/(^|[^"'=/])(www\.[^\s<]+)/gi, function (match, pre, url) {
      var clean = url.replace(/[.,;:)]+$/, '');
      return pre + hold(anchorHtml(clean, clean));
    });

    // Useful program phrases → official SBA pages (when not already linked)
    var programLinks = [
      [/SBA\s*7\s*[\(\-]?\s*a(?:\s*loans?)?/gi, 'https://www.sba.gov/funding-programs/loans/7a-loans'],
      [/SBA\s*504(?:\s*loans?)?/gi, 'https://www.sba.gov/funding-programs/loans/504-loans'],
      [/SBA\s*Microloans?/gi, 'https://www.sba.gov/funding-programs/loans/microloans'],
      [/Lender\s*Match/gi, 'https://www.sba.gov/funding-programs/loans/lender-match'],
      [/SBA-backed loans?/gi, 'https://www.sba.gov/funding-programs/loans'],
    ];
    programLinks.forEach(function (pair) {
      s = s.replace(pair[0], function (m) {
        // Skip if this looks like it sits inside a held token (rare) or already markdown
        return hold(anchorHtml(m, pair[1]));
      });
    });

    s = escapeHtml(s);
    s = s.replace(/\u0000(\d+)\u0000/g, function (_, i) {
      return tokens[Number(i)] || '';
    });

    s = s.replace(/\*\*([^*]+)\*\*/g, '<strong class="mag-strong">$1</strong>');
    s = s.replace(/__([^_]+)__/g, '<strong class="mag-strong">$1</strong>');
    s = s.replace(/(^|[^\w*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
    s = s.replace(/`([^`]+)`/g, '<code class="mag-code">$1</code>');
    return s;
  }

  function isBullet(line) {
    return /^([-*•▪◦●·]|\u2022|\u25CF)\s+/.test(line);
  }

  function isNumbered(line) {
    return /^\d+[.)]\s+/.test(line);
  }

  function formatMagazineHtml(raw) {
    if (raw == null || raw === '') {
      return '<div class="magazine-prose"><p class="mag-p mag-muted">No message content.</p></div>';
    }
    var lines = String(raw).replace(/\r\n/g, '\n').split('\n');
    var blocks = [];
    var listType = null;
    var listItems = [];
    var paraBuf = [];

    function flushPara() {
      if (!paraBuf.length) return;
      var text = paraBuf.join(' ').trim();
      paraBuf = [];
      if (!text) return;
      blocks.push('<p class="mag-p">' + formatInline(text) + '</p>');
    }

    function flushList() {
      if (!listItems.length) return;
      var tag = listType === 'ol' ? 'ol' : 'ul';
      var cls = listType === 'ol' ? 'mag-list mag-list-ol' : 'mag-list mag-list-ul';
      var items = listItems
        .map(function (item) {
          return (
            '<li class="mag-li"><span class="mag-li-text">' +
            formatInline(item) +
            '</span></li>'
          );
        })
        .join('');
      blocks.push('<' + tag + ' class="' + cls + '">' + items + '</' + tag + '>');
      listItems = [];
      listType = null;
    }

    for (var i = 0; i < lines.length; i++) {
      var line = lines[i];
      var trimmed = line.trim();

      if (!trimmed) {
        flushPara();
        flushList();
        continue;
      }

      if (/^(-{3,}|_{3,}|\*{3,})$/.test(trimmed)) {
        flushPara();
        flushList();
        blocks.push('<hr class="mag-hr" />');
        continue;
      }

      if (/^>\s?/.test(trimmed)) {
        flushPara();
        flushList();
        blocks.push(
          '<blockquote class="mag-quote">' +
            formatInline(trimmed.replace(/^>\s?/, '')) +
            '</blockquote>'
        );
        continue;
      }

      var hMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
      if (hMatch) {
        flushPara();
        flushList();
        var level = Math.min(hMatch[1].length + 1, 4);
        blocks.push(
          '<h' +
            level +
            ' class="mag-h mag-h' +
            level +
            '">' +
            formatInline(hMatch[2].trim()) +
            '</h' +
            level +
            '>'
        );
        continue;
      }

      // "Links:" / "Use this information" as headings
      if (/^links:?$/i.test(trimmed) || /^##\s*links/i.test(trimmed)) {
        flushPara();
        flushList();
        blocks.push('<h3 class="mag-h mag-h3">Links</h3>');
        continue;
      }
      if (/^use this information:?$/i.test(trimmed) || /^##\s*use this information/i.test(trimmed)) {
        flushPara();
        flushList();
        blocks.push('<h3 class="mag-h mag-h3">Use this information</h3>');
        continue;
      }

      if (
        trimmed.length < 90 &&
        /:$/.test(trimmed) &&
        !isBullet(trimmed) &&
        !isNumbered(trimmed) &&
        !/https?:\/\//.test(trimmed) &&
        !/\[[^\]]+\]\(/.test(trimmed)
      ) {
        flushPara();
        flushList();
        blocks.push(
          '<h3 class="mag-h mag-h3">' +
            formatInline(trimmed.replace(/:$/, '')) +
            '</h3>'
        );
        continue;
      }

      if (isBullet(trimmed)) {
        flushPara();
        if (listType && listType !== 'ul') flushList();
        listType = 'ul';
        listItems.push(trimmed.replace(/^([-*•▪◦●·]|\u2022|\u25CF)\s+/, ''));
        continue;
      }

      if (isNumbered(trimmed)) {
        flushPara();
        if (listType && listType !== 'ol') flushList();
        listType = 'ol';
        listItems.push(trimmed.replace(/^\d+[.)]\s+/, ''));
        continue;
      }

      if (listType && /^\s{2,}\S/.test(line)) {
        listItems[listItems.length - 1] =
          listItems[listItems.length - 1] + ' ' + trimmed;
        continue;
      }

      flushList();
      paraBuf.push(trimmed);
    }

    flushPara();
    flushList();

    if (!blocks.length) {
      blocks.push('<p class="mag-p">' + formatInline(String(raw).trim()) + '</p>');
    }

    return '<div class="magazine-prose">' + blocks.join('\n') + '</div>';
  }

  function shouldSkip(el) {
    if (!el || el.dataset.magazine === '1') return true;
    if (el.querySelector && el.querySelector('.magazine-prose')) return true;
    if (
      el.querySelector &&
      el.querySelector(
        '.spinner-border, .spinner-grow, .typing-indicator, [role="status"]'
      )
    ) {
      return true;
    }
    var text = (el.textContent || '').trim();
    return !text || text === 'Thinking...';
  }

  function bindLinkClicks(el) {
    if (!el || !el.querySelectorAll) return;
    el.querySelectorAll('a.mag-link').forEach(function (a) {
      a.addEventListener('click', function (e) {
        // Let the browser follow the href; don't let parent message handlers eat it
        e.stopPropagation();
      });
    });
  }

  function enhanceNode(el) {
    if (shouldSkip(el)) return;
    var raw = el.textContent || '';
    if (el.children && el.children.length > 0) {
      var onlyBreaks = Array.prototype.every.call(el.childNodes, function (n) {
        return (
          n.nodeType === 3 ||
          (n.nodeType === 1 && (n.tagName === 'BR' || n.tagName === 'SPAN'))
        );
      });
      if (!onlyBreaks) {
        // Already HTML with anchors? still bind clicks
        if (el.querySelector('a[href]')) {
          el.dataset.magazine = '1';
          bindLinkClicks(el);
        }
        return;
      }
      raw = el.innerText || el.textContent || '';
    }
    el.innerHTML = formatMagazineHtml(raw);
    el.dataset.magazine = '1';
    el.classList.add('magazine-enhanced');
    bindLinkClicks(el);
  }

  function enhanceAll(root) {
    var scope = root || document;
    scope
      .querySelectorAll(
        [
          '.assistant-message .message-content',
          '.message.assistant-message .message-content',
          '.message-modern.assistant .message-bubble:not(.typing)',
          '.message-bubble.assistant',
          '.chat-messages .assistant-message .message-content',
        ].join(',')
      )
      .forEach(enhanceNode);
  }

  function boot() {
    document.documentElement.classList.add('mag-chat-ready');
    enhanceAll(document);

    var obs = new MutationObserver(function (mutations) {
      var needs = false;
      for (var i = 0; i < mutations.length; i++) {
        if (mutations[i].addedNodes && mutations[i].addedNodes.length) {
          needs = true;
          break;
        }
        if (mutations[i].type === 'characterData') {
          needs = true;
          break;
        }
      }
      if (!needs) return;
      clearTimeout(boot._t);
      boot._t = setTimeout(function () {
        // React re-render clears data-magazine; re-run
        document
          .querySelectorAll(
            '.assistant-message .message-content, .message.assistant-message .message-content'
          )
          .forEach(function (el) {
            // If React replaced content, allow re-format
            if (el.dataset.magazine === '1' && !el.querySelector('.magazine-prose')) {
              delete el.dataset.magazine;
            }
            if (el.dataset.magazine === '1' && el.querySelector('a.mag-link')) return;
            if (!el.querySelector('.magazine-prose')) {
              delete el.dataset.magazine;
            }
          });
        enhanceAll(document);
      }, 40);
    });

    obs.observe(document.body, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  window.PocketProMagazineChat = {
    format: formatMagazineHtml,
    enhanceAll: enhanceAll,
    normalizeHref: normalizeHref,
  };
})();
