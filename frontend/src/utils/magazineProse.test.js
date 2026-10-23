import { normalizeHref, isSafeHref, formatInline, formatMagazineHtml } from './magazineProse';

const hrefsIn = (html) => {
  const div = document.createElement('div');
  div.innerHTML = html;
  return Array.from(div.querySelectorAll('a')).map((a) => a.getAttribute('href'));
};

const DANGEROUS = [
  'javascript:alert(document.domain)',
  'JavaScript:alert(1)',
  'JAVASCRIPT:alert(1)',
  '  javascript:alert(1)',
  'java\tscript:alert(1)',
  'java\nscript:alert(1)',
  'java\u0000script:alert(1)',
  '\u0001javascript:alert(1)',
  'javascript://%0aalert(1)',
  'data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==',
  'DATA:text/html,<script>alert(1)</script>',
  'data:image/svg+xml,<svg onload=alert(1)>',
  'vbscript:msgbox("x")',
  'VBScript:msgbox(1)',
  'vb\tscript:msgbox(1)',
  'file:///etc/passwd',
  '//evil.example.com/x',
  '/\\evil.example.com',
  '\\\\evil.example.com',
];

describe('magazineProse link safety', () => {
  test.each(DANGEROUS)('normalizeHref rejects %p', (href) => {
    expect(isSafeHref(href)).toBe(false);
    expect(normalizeHref(href)).toBe('');
  });

  test.each([
    ['https://www.sba.gov/funding', 'https://www.sba.gov/funding'],
    ['http://example.com', 'http://example.com'],
    ['HTTPS://SBA.GOV', 'HTTPS://SBA.GOV'],
    ['mailto:help@sba.gov', 'mailto:help@sba.gov'],
    ['/browse', '/browse'],
    ['#section-2', '#section-2'],
    ['?q=loans', '?q=loans'],
    ['./docs/guide', './docs/guide'],
    ['../up', '../up'],
    ['sba/loans', 'sba/loans'],
  ])('normalizeHref keeps safe link %p', (href, expected) => {
    expect(normalizeHref(href)).toBe(expected);
  });

  test('www. links become https and /api/sba routes still map to the Resources browser', () => {
    expect(normalizeHref('www.sba.gov')).toBe('https://www.sba.gov');
    expect(normalizeHref('/api/sba/loans')).toBe('/browse#r=%2Fapi%2Fsba%2Floans&t=loans');
  });

  test('markdown javascript: link renders as plain text, not an anchor', () => {
    const html = formatMagazineHtml('see [click](javascript:alert(document.domain))');
    expect(hrefsIn(html)).toEqual([]);
    expect(html).not.toMatch(/href="\s*javascript/i);
    expect(html).toContain('click');
  });

  test.each([
    '[x](data:text/html;base64,PHNjcmlwdD4=)',
    '[x](vbscript:msgbox(1))',
    '[x](JaVaScRiPt:alert(1))',
    '[x](//evil.example.com)',
  ])('formatInline drops unsafe markdown link %p', (md) => {
    const html = formatInline(md);
    expect(hrefsIn(html)).toEqual([]);
    expect(html).not.toMatch(/<a\s/i);
  });

  test('safe links still render, external ones open in a new tab safely', () => {
    const html = formatInline('[SBA](https://www.sba.gov) and [mail](mailto:a@b.co) and [home](/browse)');
    expect(hrefsIn(html)).toEqual(['https://www.sba.gov', 'mailto:a@b.co', '/browse']);
    expect(html).toContain('rel="noopener noreferrer"');
  });

  test('attribute breakout via quotes is escaped', () => {
    const html = formatInline('[x](https://a.co/"onmouseover="alert(1))');
    const div = document.createElement('div');
    div.innerHTML = html;
    const a = div.querySelector('a');
    if (a) expect(a.getAttribute('onmouseover')).toBeNull();
  });
});
