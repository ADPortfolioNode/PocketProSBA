import React from 'react';
import { Card, ListGroup, Alert, Badge } from 'react-bootstrap';
import { normalizeHref } from '../utils/magazineProse';

// RAG process display (process panel, NOT chat-bubble text).
//
// The chat API is a single POST, not a stream, so the panel tracks the
// stages around that request honestly: the query is shown the moment it is
// sent, "retrieving" shows while the request runs, and the retrieved
// sources are listed once the concierge answers. It never invents a
// chunk count the API did not return — the count is the number of
// deduplicated sources the answer actually used.

export const PROCESS_STAGES = ['received', 'retrieving', 'retrieved', 'answered'];

export function sourceLabel(source) {
  if (!source) return '';
  if (typeof source === 'string') return source;
  return source.title || source.name || source.path || source.url || '';
}

export function sourceHref(source) {
  if (!source || typeof source === 'string') return null;
  const raw = source.path || source.url;
  if (!raw) return null;
  // Reuse the chat panel's rule: never link a raw API route — /api/sba/*
  // opens in /browse, everything else passes through as an in-app path
  // or an external link.
  try {
    return normalizeHref(raw);
  } catch (_) {
    return raw;
  }
}

export function dedupeSources(sources) {
  const seen = new Set();
  const out = [];
  (Array.isArray(sources) ? sources : []).forEach((source) => {
    const label = sourceLabel(source);
    const href = sourceHref(source);
    const key = href || label;
    if (!key || seen.has(key)) return;
    seen.add(key);
    out.push({ label, href });
  });
  return out;
}

// Markdown links inside a bubble that are NOT already in the sources list.
// Those — and only those — appear under "More links", so a link already
// shown in the panel is never listed again.
export function extraLinksFromContent(content, shown) {
  if (typeof content !== 'string' || !content) return [];
  const shownHrefs = new Set((shown || []).map((s) => s.href).filter(Boolean));
  const seen = new Set();
  const out = [];
  const matches = content.matchAll(/\[([^\]]+)\]\(([^)]+)\)/g);
  [...matches].forEach((m) => {
    let href = null;
    try {
      href = normalizeHref(m[2]);
    } catch (_) {
      href = m[2];
    }
    if (!href || shownHrefs.has(href) || seen.has(href)) return;
    seen.add(href);
    out.push({ label: m[1], href });
  });
  return out;
}

const RagProcessPanel = ({ query, stage = 'idle', sources = [], error = null }) => {
  const shown = dedupeSources(sources);
  const stageIndex = PROCESS_STAGES.indexOf(stage);
  const steps = [
    {
      key: 'received',
      label: query ? `Query received: “${query}”` : 'Query received',
    },
    { key: 'retrieving', label: 'Retrieving from your documents and SBA resources…' },
    {
      key: 'retrieved',
      label:
        stageIndex >= PROCESS_STAGES.indexOf('retrieved') && shown.length > 0
          ? `Retrieved ${shown.length} source${shown.length === 1 ? '' : 's'}`
          : 'Retrieved sources',
    },
    { key: 'answered', label: 'Answer ready — sources used are listed below' },
  ];

  return (
    <Card className="mb-3" data-testid="rag-process-panel">
      <Card.Header>
        <h5 className="mb-0">
          RAG process{' '}
          {stage === 'retrieving' && <Badge bg="info">Retrieving…</Badge>}
          {stage === 'answered' && <Badge bg="success">Done</Badge>}
          {stage === 'failed' && <Badge bg="danger">Failed</Badge>}
        </h5>
      </Card.Header>
      <Card.Body>
        {stage === 'idle' && (
          <p className="text-muted mb-0">
            Ask a question in the chat above to see the retrieval steps here.
          </p>
        )}
        {stage !== 'idle' && (
          <ListGroup aria-live="polite" className="mb-3">
            {steps.map((step, idx) => {
              const done = stage === 'answered' || stageIndex > idx;
              const active = stage === step.key;
              return (
                <ListGroup.Item key={step.key}>
                  {done ? '✓ ' : active ? '… ' : '○ '}
                  {step.label}
                </ListGroup.Item>
              );
            })}
          </ListGroup>
        )}
        {stage === 'failed' && error && (
          <Alert variant="danger" role="alert">
            {error}
          </Alert>
        )}
        {shown.length > 0 && (
          <div>
            <h6>Sources used for this answer</h6>
            <ListGroup>
              {shown.map((source) => (
                <ListGroup.Item key={source.href || source.label}>
                  {source.href ? <a href={source.href}>{source.label}</a> : source.label}
                </ListGroup.Item>
              ))}
            </ListGroup>
          </div>
        )}
        {stage === 'answered' && shown.length === 0 && (
          <p className="text-muted mb-0">
            No retrieved documents were returned for this answer.
          </p>
        )}
      </Card.Body>
    </Card>
  );
};

export default RagProcessPanel;
