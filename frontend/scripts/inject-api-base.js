#!/usr/bin/env node
/**
 * Post-build step: write the configured API base into the static pages
 * (build/resources.html, build/programs.html). CRA only templates
 * public/index.html, so these pages carry a %REACT_APP_API_URL% placeholder in
 * <meta name="pp-api-base">. Empty when not configured -> same-origin /api.
 */
const fs = require('fs');
const path = require('path');

const PLACEHOLDER = '%REACT_APP_API_URL%';
const PAGES = ['resources.html', 'programs.html'];

function escapeAttr(value) {
  return String(value).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
}

function configuredBase(env) {
  const raw = (env.REACT_APP_API_URL || env.REACT_APP_BACKEND_URL || '').trim();
  // Only absolute http(s) URLs are meaningful here; anything else -> same origin.
  return /^https?:\/\//i.test(raw) ? raw.replace(/\/api\/?$/, '').replace(/\/+$/, '') : '';
}

function injectApiBase(html, base) {
  return html.split(PLACEHOLDER).join(escapeAttr(base || ''));
}

function run(buildDir, env) {
  const base = configuredBase(env);
  PAGES.forEach((page) => {
    const file = path.join(buildDir, page);
    if (!fs.existsSync(file)) return;
    fs.writeFileSync(file, injectApiBase(fs.readFileSync(file, 'utf8'), base));
  });
  return base;
}

if (require.main === module) {
  // Load .env / .env.production the same way react-scripts build does.
  process.env.NODE_ENV = process.env.NODE_ENV || 'production';
  try { require('react-scripts/config/env'); } catch (_) { /* plain env only */ }
  const base = run(path.resolve(__dirname, '..', 'build'), process.env);
  console.log(`Static pages API base: ${base || '(same origin)'}`);
}

module.exports = { injectApiBase, configuredBase, run, PLACEHOLDER };
