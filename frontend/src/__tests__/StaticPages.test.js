/**
 * The standalone /browse (resources.html) and /sba (programs.html) pages:
 * no dev-machine API fallback, the API base comes from same origin or the
 * build-time REACT_APP_API_URL, and their nav matches the React app's nav.
 */
import fs from 'fs';
import path from 'path';
import { NAV_ITEMS } from '../components/SBANavigation';

const PUBLIC_DIR = path.join(__dirname, '..', '..', 'public');
const read = (name) => fs.readFileSync(path.join(PUBLIC_DIR, name), 'utf8');
const PAGES = [
  { file: 'resources.html', active: '/browse' },
  { file: 'programs.html', active: '/sba' },
];

describe.each(PAGES)('$file', ({ file, active }) => {
  const html = read(file);

  test('has no hard-coded 127.0.0.1:5000 / localhost:5000 API fallback', () => {
    expect(html).not.toMatch(/127\.0\.0\.1:5000/);
    expect(html).not.toMatch(/localhost:5000/);
  });

  test('reads the API base from the shared helper and the build-time meta tag', () => {
    expect(html).toContain('<meta name="pp-api-base" content="%REACT_APP_API_URL%" />');
    expect(html).toContain('<script src="/pp-api-base.js"></script>');
    expect(html).toMatch(/window\.ppApiBase\s*\?\s*window\.ppApiBase\(\)/);
  });

  test('nav has the same links, labels and order as the React app nav', () => {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const links = [...doc.querySelectorAll('nav[aria-label="Primary"] a')];
    expect(links.map((a) => [a.getAttribute('href'), a.textContent.trim()])).toEqual(
      NAV_ITEMS.map((i) => [i.to, i.label])
    );
    const current = links.filter((a) => a.getAttribute('aria-current') === 'page');
    expect(current.map((a) => a.getAttribute('href'))).toEqual([active]);
  });
});

describe('pp-api-base.js', () => {
  const src = read('pp-api-base.js');
  const load = () => {
    const root = {};
    // eslint-disable-next-line no-new-func
    new Function('window', src)(root);
    return root;
  };
  const docWithMeta = (content) => {
    const doc = document.implementation.createHTMLDocument('x');
    if (content !== undefined) {
      const m = doc.createElement('meta');
      m.setAttribute('name', 'pp-api-base');
      m.setAttribute('content', content);
      doc.head.appendChild(m);
    }
    return doc;
  };
  const loc = { origin: 'https://pocketpro.example' };

  test('defaults to the page origin (same-origin /api)', () => {
    const { ppApiBase, ppApiUrl } = load();
    expect(ppApiBase(docWithMeta(undefined), loc)).toBe('https://pocketpro.example');
    expect(ppApiBase(docWithMeta(''), loc)).toBe('https://pocketpro.example');
    expect(ppApiUrl('/api/sba/resources', docWithMeta(''), loc)).toBe('https://pocketpro.example/api/sba/resources');
  });

  test('treats an unreplaced placeholder (dev server) as not configured', () => {
    const { ppApiBase } = load();
    expect(ppApiBase(docWithMeta('%REACT_APP_API_URL%'), loc)).toBe('https://pocketpro.example');
  });

  test('uses the configured REACT_APP_API_URL, normalised like apiClient', () => {
    const { ppApiBase, ppApiUrl } = load();
    expect(ppApiBase(docWithMeta('https://api.example.com/api/'), loc)).toBe('https://api.example.com');
    expect(ppApiUrl('/api/sba/programs', docWithMeta('https://api.example.com'), loc)).toBe('https://api.example.com/api/sba/programs');
  });

  test('ignores non-http values', () => {
    const { ppApiBase } = load();
    expect(ppApiBase(docWithMeta('javascript:alert(1)'), loc)).toBe('https://pocketpro.example');
  });
});

describe('scripts/inject-api-base.js', () => {
  // eslint-disable-next-line global-require
  const { injectApiBase, configuredBase, PLACEHOLDER } = require('../../scripts/inject-api-base');

  test('fills the placeholder with the configured base, or empties it', () => {
    const html = `<meta name="pp-api-base" content="${PLACEHOLDER}" />`;
    expect(injectApiBase(html, 'https://api.example.com')).toBe('<meta name="pp-api-base" content="https://api.example.com" />');
    expect(injectApiBase(html, '')).toBe('<meta name="pp-api-base" content="" />');
  });

  test('reads REACT_APP_API_URL then REACT_APP_BACKEND_URL, http(s) only', () => {
    expect(configuredBase({ REACT_APP_API_URL: 'https://a.example/api' })).toBe('https://a.example');
    expect(configuredBase({ REACT_APP_BACKEND_URL: 'http://b.example/' })).toBe('http://b.example');
    expect(configuredBase({ REACT_APP_API_URL: '/api' })).toBe('');
    expect(configuredBase({})).toBe('');
  });

  test('escapes quotes so a bad value cannot break out of the attribute', () => {
    expect(injectApiBase(`content="${PLACEHOLDER}"`, 'https://x.example/"><script>')).toBe(
      'content="https://x.example/&quot;>&lt;script>"'
    );
  });
});
