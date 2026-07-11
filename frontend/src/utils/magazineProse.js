/**
 * Magazine-style chat prose formatter.
 * Turns plain assistant text into highly readable blocks with real itemized lists.
 */

export function escapeHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Normalize href for app navigation vs external */
export function normalizeHref(raw) {
  let href = String(raw || '').trim().replace(/[.,;:)]+$/, '');
  if (!href) return '';
  if (/^www\./i.test(href)) href = `https://${href}`;
  // API routes open in Resources browser (usable UI, not raw JSON)
  if (href.startsWith('/api/sba/')) {
    const title = href.split('/').filter(Boolean).pop() || 'SBA';
    return `/browse#r=${encodeURIComponent(href)}&t=${encodeURIComponent(title)}`;
  }
  return href;
}

function anchorHtml(label, href) {
  const h = normalizeHref(href);
  if (!h) return escapeHtml(label);
  const external = /^https?:\/\//i.test(h);
  const attrs = external
    ? ' target="_blank" rel="noopener noreferrer"'
    : '';
  const cls = external ? 'mag-link mag-link-ext' : 'mag-link mag-link-app';
  return `<a href="${escapeHtml(h)}" class="${cls}"${attrs}>${escapeHtml(label)}</a>`;
}

/** Inline: **bold**, *italic*, `code`, [label](url), bare URLs, API routes */
export function formatInline(text) {
  const raw = String(text ?? '');
  const tokens = [];
  const hold = (html) => {
    tokens.push(html);
    return `\u0000${tokens.length - 1}\u0000`;
  };

  let s = raw;

  // Markdown [label](url) — http(s), /, /browse#, /sba, /api/...
  s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_, label, href) =>
    hold(anchorHtml(label, href))
  );

  // Official URL: https://...
  s = s.replace(
    /(^|[\s])((?:Official\s*URL|URL|Source\s*URL|Link)\s*:\s*)(https?:\/\/[^\s]+)/gi,
    (_, pre, label, url) =>
      `${pre}${hold(escapeHtml(label) + anchorHtml(url.replace(/[.,;:)]+$/, ''), url))}`
  );

  // API route: /api/sba/...
  s = s.replace(
    /(^|[\s])((?:API\s*route|Route|Path)\s*:\s*)(\/api\/sba\/[^\s]+)/gi,
    (_, pre, label, path) =>
      `${pre}${hold(escapeHtml(label) + anchorHtml(path.replace(/[.,;:)]+$/, ''), path))}`
  );

  // bare https
  s = s.replace(/(^|[^"'=\w/])(https?:\/\/[^\s<]+)/g, (match, pre, url) => {
    const clean = url.replace(/[.,;:)]+$/, '');
    return `${pre}${hold(anchorHtml(clean, clean))}`;
  });

  // bare www.
  s = s.replace(/(^|[^"'=/])(www\.[^\s<]+)/gi, (match, pre, url) => {
    const clean = url.replace(/[.,;:)]+$/, '');
    return `${pre}${hold(anchorHtml(clean, clean))}`;
  });

  // Escape remaining text, then restore anchors
  s = escapeHtml(s);
  s = s.replace(/\u0000(\d+)\u0000/g, (_, i) => tokens[Number(i)] || '');

  // **bold** / __bold__ on escaped text
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong class="mag-strong">$1</strong>');
  s = s.replace(/__([^_]+)__/g, '<strong class="mag-strong">$1</strong>');
  s = s.replace(/(^|[^\w*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');
  s = s.replace(/`([^`]+)`/g, '<code class="mag-code">$1</code>');

  return s;
}

function isBullet(line) {
  return /^([-*•▪◦●]|\u2022|\u25CF)\s+/.test(line) || /^·\s+/.test(line);
}

function isNumbered(line) {
  return /^\d+[.)]\s+/.test(line);
}

function bulletBody(line) {
  return line.replace(/^([-*•▪◦●·]|\u2022|\u25CF)\s+/, '');
}

function numberedBody(line) {
  return line.replace(/^\d+[.)]\s+/, '');
}

function isHeading(line) {
  return /^(#{1,4})\s+/.test(line) || /^(#{1,4})[^#\s]/.test(line);
}

/**
 * Convert plain / light-markdown text into magazine HTML.
 * @param {string} raw
 * @returns {string} HTML
 */
export function formatMagazineHtml(raw) {
  if (raw == null || raw === '') {
    return '<div class="magazine-prose"><p class="mag-p mag-muted">No message content.</p></div>';
  }
  if (typeof raw !== 'string') {
    return `<div class="magazine-prose"><p class="mag-p">${formatInline(String(raw))}</p></div>`;
  }

  const lines = raw.replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  let listType = null; // 'ul' | 'ol'
  let listItems = [];
  let paraBuf = [];

  const flushPara = () => {
    if (!paraBuf.length) return;
    const text = paraBuf.join(' ').trim();
    paraBuf = [];
    if (!text) return;
    blocks.push(`<p class="mag-p">${formatInline(text)}</p>`);
  };

  const flushList = () => {
    if (!listItems.length) return;
    const tag = listType === 'ol' ? 'ol' : 'ul';
    const cls = listType === 'ol' ? 'mag-list mag-list-ol' : 'mag-list mag-list-ul';
    const items = listItems
      .map((item) => `<li class="mag-li"><span class="mag-li-text">${formatInline(item)}</span></li>`)
      .join('');
    blocks.push(`<${tag} class="${cls}">${items}</${tag}>`);
    listItems = [];
    listType = null;
  };

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      flushPara();
      flushList();
      continue;
    }

    // Horizontal rule
    if (/^(-{3,}|_{3,}|\*{3,})$/.test(trimmed)) {
      flushPara();
      flushList();
      blocks.push('<hr class="mag-hr" />');
      continue;
    }

    // Blockquote
    if (/^>\s?/.test(trimmed)) {
      flushPara();
      flushList();
      const quote = trimmed.replace(/^>\s?/, '');
      blocks.push(`<blockquote class="mag-quote">${formatInline(quote)}</blockquote>`);
      continue;
    }

    // Markdown headings
    const hMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (hMatch) {
      flushPara();
      flushList();
      const level = Math.min(hMatch[1].length + 1, 4); // h2–h5 visually
      const tag = `h${level}`;
      blocks.push(
        `<${tag} class="mag-h mag-h${level}">${formatInline(hMatch[2].trim())}</${tag}>`
      );
      continue;
    }

    // Title-style line ending with colon alone as subhead (short)
    if (
      trimmed.length < 90 &&
      /:$/.test(trimmed) &&
      !isBullet(trimmed) &&
      !isNumbered(trimmed) &&
      !/https?:\/\//.test(trimmed)
    ) {
      flushPara();
      flushList();
      blocks.push(`<h3 class="mag-h mag-h3">${formatInline(trimmed.replace(/:$/, ''))}</h3>`);
      continue;
    }

    // Bullet list
    if (isBullet(trimmed)) {
      flushPara();
      if (listType && listType !== 'ul') flushList();
      listType = 'ul';
      listItems.push(bulletBody(trimmed));
      continue;
    }

    // Numbered list
    if (isNumbered(trimmed)) {
      flushPara();
      if (listType && listType !== 'ol') flushList();
      listType = 'ol';
      listItems.push(numberedBody(trimmed));
      continue;
    }

    // Continuation of list item (indented)
    if (listType && /^\s{2,}\S/.test(line)) {
      listItems[listItems.length - 1] =
        `${listItems[listItems.length - 1]} ${trimmed}`;
      continue;
    }

    // Normal paragraph line
    flushList();
    paraBuf.push(trimmed);
  }

  flushPara();
  flushList();

  if (!blocks.length) {
    blocks.push(`<p class="mag-p">${formatInline(raw.trim())}</p>`);
  }

  return `<div class="magazine-prose">${blocks.join('\n')}</div>`;
}

/**
 * Detect whether a node still needs magazine formatting (plain text only).
 */
export function needsMagazineFormat(el) {
  if (!el || el.dataset?.magazine === '1') return false;
  if (el.querySelector?.('.magazine-prose')) return false;
  // loading spinners etc.
  if (el.querySelector?.('.spinner-border, .spinner-grow, [class*="typing"]')) return false;
  const text = (el.textContent || '').trim();
  return text.length > 0;
}

export default formatMagazineHtml;
