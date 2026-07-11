import React, { useState, useEffect, useCallback } from 'react';
import { businessLifecycleStages, localResourceTypes, sbaPrograms } from '../sbaResources';
import apiClient from '../api/apiClient';
import {
  Card,
  Nav,
  Row,
  Col,
  Container,
  Badge,
  Spinner,
  Alert,
  Button,
  Modal,
  ListGroup,
} from 'react-bootstrap';

/**
 * SBA Programs | Business Lifecycle | Local Resources
 *
 * Data: GET /api/sba/resources → sbaPrograms, businessLifecycleStages, localResourceTypes
 * Details: click a CARD (not the tab headers) → detail modal with full info + related links.
 * Tab headers only switch which card list is visible.
 */
const SBAContent = ({ onProgramSelect, onResourceSelect }) => {
  const [activeTab, setActiveTab] = useState('programs');
  const [programs, setPrograms] = useState([]);
  const [lifecycle, setLifecycle] = useState([]);
  const [local, setLocal] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [related, setRelated] = useState([]);
  const [relatedLoading, setRelatedLoading] = useState(false);

  const normalizeCard = (raw, index, fallbackIcon = '📁') => {
    if (!raw || typeof raw !== 'object') return null;
    const name = String(raw.name || raw.title || '').trim();
    const description = String(
      raw.description || raw.detailedDescription || raw.summary || ''
    ).trim();
    if (!name && !description) return null;
    return {
      id: raw.id || raw.name || `card-${index}`,
      name: name || `SBA resource ${index + 1}`,
      title: raw.title || name,
      description: description || name,
      icon: raw.icon || fallbackIcon,
      url: raw.url || raw.link || '',
      path: raw.path || '',
      phase: raw.phase,
      resources: Array.isArray(raw.resources) ? raw.resources : [],
      is_current: raw.is_current,
      source: raw.source,
      group: raw.group,
    };
  };

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/api/sba/resources', { timeout: 60000 }, { quiet: true });
      const data = res?.data || res || {};

      let prog = data.sbaPrograms || data.programs || [];
      let life = data.businessLifecycleStages || data.lifecycle || [];
      let loc = data.localResourceTypes || data.local || [];

      if (!Array.isArray(prog) || !prog.length) {
        try {
          const p = await apiClient.get('/api/sba/programs', { timeout: 30000 }, { quiet: true });
          const pd = p?.data || p || {};
          prog = pd.items || pd.programs || (Array.isArray(pd) ? pd : []);
        } catch (_) {
          /* soft */
        }
      }
      if (!Array.isArray(life) || !life.length) {
        try {
          const p = await apiClient.get('/api/sba/lifecycle', { timeout: 30000 }, { quiet: true });
          const pd = p?.data || p || {};
          life = pd.items || pd.lifecycle || (Array.isArray(pd) ? pd : []);
        } catch (_) {
          /* soft */
        }
      }
      if (!Array.isArray(loc) || !loc.length) {
        try {
          const p = await apiClient.get('/api/sba/local-resources', { timeout: 30000 }, { quiet: true });
          const pd = p?.data || p || {};
          loc = pd.items || pd.local || (Array.isArray(pd) ? pd : []);
        } catch (_) {
          /* soft */
        }
      }

      if (!Array.isArray(prog) || !prog.length) prog = sbaPrograms || [];
      if (!Array.isArray(life) || !life.length) life = businessLifecycleStages || [];
      if (!Array.isArray(loc) || !loc.length) loc = localResourceTypes || [];

      setPrograms(prog.map((c, i) => normalizeCard(c, i, '💼')).filter(Boolean));
      setLifecycle(life.map((c, i) => normalizeCard(c, i, '📌')).filter(Boolean));
      setLocal(loc.map((c, i) => normalizeCard(c, i, '📍')).filter(Boolean));
    } catch (err) {
      setError(err.message || 'Failed to load SBA program cards');
      setPrograms((sbaPrograms || []).map((c, i) => normalizeCard(c, i, '💼')).filter(Boolean));
      setLifecycle(
        (businessLifecycleStages || []).map((c, i) => normalizeCard(c, i, '📌')).filter(Boolean)
      );
      setLocal((localResourceTypes || []).map((c, i) => normalizeCard(c, i, '📍')).filter(Boolean));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const childHasChildren = (row) => {
    if (!row) return false;
    if (row.has_children || row.drillable) return true;
    if (row.path && String(row.path).startsWith('/api/')) return true;
    if (Array.isArray(row.resources) && row.resources.length) return true;
    const t = String(row.type || '').toLowerCase();
    return ['loan_program', 'loan', 'related_loan', 'tool', 'program', 'lifecycle'].includes(t);
  };

  const openDetail = async (card, kind) => {
    setSelected({ ...card, _kind: kind });
    setRelated([]);
    // Optional parent hooks (chat prefill, etc.)
    if (kind === 'program' && onProgramSelect) onProgramSelect(card.id);
    if (kind !== 'program' && onResourceSelect) onResourceSelect(`${card.id} ${kind}`);

    if (card.path && String(card.path).startsWith('/api/')) {
      setRelatedLoading(true);
      try {
        const res = await apiClient.get(
          card.path,
          { params: { page: 1 }, timeout: 60000 },
          { quiet: true }
        );
        const data = res?.data || res || {};
        const list = data.items || data.results || data.available_loan_types || [];
        const parentPath = card.path;
        setRelated(
          (Array.isArray(list) ? list : []).map((row, i) => {
            let path = String(row.path || '').trim();
            const id = row.id != null ? String(row.id) : String(i);
            if (!path.startsWith('/api/') && parentPath.startsWith('/api/') && id && !String(id).startsWith('item-')) {
              const leaf = ['overview', 'link', 'notice', 'loan_section'].includes(
                String(row.type || '').toLowerCase()
              );
              if (!leaf) path = `${parentPath.replace(/\/$/, '')}/${encodeURIComponent(id)}`;
            }
            return {
              id: row.id || i,
              title: row.title || row.name || row.type || 'Item',
              description: row.description || row.summary || '',
              url: row.url || row.link || '',
              path,
              type: row.type || 'content',
              has_children: childHasChildren({ ...row, path }),
              drillable: path.startsWith('/api/'),
            };
          })
        );
      } catch (_) {
        setRelated([]);
      } finally {
        setRelatedLoading(false);
      }
    }
  };

  /** Child with children → load its API path into the same expanded card/modal */
  const openRelatedChild = async (row) => {
    if (!row) return;
    if (childHasChildren(row) && row.path && String(row.path).startsWith('/api/')) {
      await openDetail(
        {
          id: row.id,
          name: row.title,
          title: row.title,
          description: row.description,
          path: row.path,
          url: row.url,
          icon: '📂',
          resources: [],
        },
        selected?._kind || 'program'
      );
      return;
    }
    if (row.url) window.open(row.url, '_blank', 'noopener,noreferrer');
  };

  const renderCards = (items, kind) => {
    if (!items.length) {
      return (
        <Alert variant="info" className="mb-0">
          No {kind} cards returned from the API yet. Try Refresh.
        </Alert>
      );
    }
    return (
      <Row xs={1} md={2} lg={3} className="g-3">
        {items.map((card) => (
          <Col key={card.id}>
            <Card
              className={`${kind}-card h-100 svc-result-card`}
              style={{ cursor: 'pointer' }}
              onClick={() => openDetail(card, kind)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  openDetail(card, kind);
                }
              }}
            >
              <Card.Body className="d-flex flex-column">
                <div className="d-flex">
                  <div className={`${kind}-icon me-3`} style={{ fontSize: '1.6rem' }}>
                    {card.icon}
                  </div>
                  <div className={`${kind}-content flex-grow-1`}>
                    <Card.Title as="h5">{card.name}</Card.Title>
                    <Card.Text className="small text-muted">
                      {(card.description || '').slice(0, 160)}
                      {(card.description || '').length > 160 ? '…' : ''}
                    </Card.Text>
                    {card.phase && (
                      <Badge bg="info" pill className="me-1">
                        {card.phase}
                      </Badge>
                    )}
                    {card.group && (
                      <Badge bg="light" text="dark" pill className="me-1">
                        {card.group}
                      </Badge>
                    )}
                  </div>
                </div>
                {card.path && (
                  <div className="small font-monospace text-muted mb-1 text-break">{card.path}</div>
                )}
                <div className="mt-auto pt-2 text-primary small fw-semibold">
                  {card.path ? 'Expand card · load API children →' : 'View details →'}
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>
    );
  };

  return (
    <Card className="sba-content-explorer sba-navigation">
      <Card.Header>
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-2">
          <span className="small text-muted">
            From <code>/api/sba/resources</code>
            {programs.length || lifecycle.length || local.length
              ? ` · ${programs.length} programs · ${lifecycle.length} lifecycle · ${local.length} local`
              : ''}
            . <strong>Click a card</strong> to expand and load that API endpoint&apos;s children.
            Children with children are links that render the next result.
          </span>
          <div className="d-flex gap-2">
            <Button size="sm" variant="outline-primary" onClick={loadAll} disabled={loading}>
              {loading ? 'Loading…' : 'Refresh'}
            </Button>
            <a href="/sba" className="btn btn-sm btn-outline-secondary">
              Programs expand UI
            </a>
            <a href="/browse" className="btn btn-sm btn-primary">
              Full Resources browser →
            </a>
          </div>
        </div>
        <Nav variant="tabs" className="navigation-tabs">
          <Nav.Item>
            <Nav.Link active={activeTab === 'programs'} onClick={() => setActiveTab('programs')}>
              SBA Programs
              {programs.length > 0 && (
                <Badge bg="primary" pill className="ms-2">
                  {programs.length}
                </Badge>
              )}
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link active={activeTab === 'lifecycle'} onClick={() => setActiveTab('lifecycle')}>
              Business Lifecycle
              {lifecycle.length > 0 && (
                <Badge bg="primary" pill className="ms-2">
                  {lifecycle.length}
                </Badge>
              )}
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link active={activeTab === 'local'} onClick={() => setActiveTab('local')}>
              Local Resources
              {local.length > 0 && (
                <Badge bg="primary" pill className="ms-2">
                  {local.length}
                </Badge>
              )}
            </Nav.Link>
          </Nav.Item>
        </Nav>
      </Card.Header>

      <Card.Body className="content-explorer-body navigation-content">
        {loading && (
          <div className="text-center py-5">
            <Spinner animation="border" variant="primary" />
            <div className="mt-2 text-muted">Loading SBA resources…</div>
          </div>
        )}
        {!loading && error && (
          <Alert variant="warning" className="mb-3">
            {error} — showing best available cards.
          </Alert>
        )}
        {!loading && activeTab === 'programs' && (
          <Container fluid>{renderCards(programs, 'program')}</Container>
        )}
        {!loading && activeTab === 'lifecycle' && (
          <Container fluid>{renderCards(lifecycle, 'lifecycle')}</Container>
        )}
        {!loading && activeTab === 'local' && (
          <Container fluid>{renderCards(local, 'resource')}</Container>
        )}
      </Card.Body>

      <Modal show={!!selected} onHide={() => setSelected(null)} size="lg" centered scrollable>
        <Modal.Header closeButton>
          <Modal.Title>
            {selected?.icon ? `${selected.icon} ` : ''}
            {selected?.name || 'Details'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selected && (
            <>
              <div className="d-flex flex-wrap gap-2 mb-3">
                {selected.phase && <Badge bg="info">{selected.phase}</Badge>}
                {selected.group && (
                  <Badge bg="light" text="dark">
                    {selected.group}
                  </Badge>
                )}
                {selected.is_current === true && <Badge bg="success">Current</Badge>}
                {selected.source && (
                  <Badge bg="secondary">{selected.source}</Badge>
                )}
              </div>
              <p className="text-muted" style={{ whiteSpace: 'pre-wrap' }}>
                {selected.description}
              </p>
              {selected.path && (
                <p className="small mb-2">
                  <strong>API path:</strong> <code>{selected.path}</code>
                </p>
              )}
              {Array.isArray(selected.resources) && selected.resources.length > 0 && (
                <>
                  <h6 className="mt-3">Related resources</h6>
                  <ListGroup variant="flush" className="mb-2">
                    {selected.resources.map((r) => {
                      const label = typeof r === 'string' ? r : r.name || r.title || 'Link';
                      const href = typeof r === 'object' ? r.url : null;
                      return (
                        <ListGroup.Item key={label} className="px-0">
                          {href ? (
                            <a href={href} target="_blank" rel="noopener noreferrer">
                              {label} →
                            </a>
                          ) : (
                            label
                          )}
                        </ListGroup.Item>
                      );
                    })}
                  </ListGroup>
                </>
              )}
              {relatedLoading && (
                <div className="text-muted small">
                  <Spinner animation="border" size="sm" className="me-2" />
                  Loading API endpoint results into this card…
                </div>
              )}
              {!relatedLoading && related.length > 0 && (
                <>
                  <h6 className="mt-3">API children ({related.length})</h6>
                  <p className="small text-muted mb-2">
                    Children with more children are links — click to render the next endpoint in this card.
                  </p>
                  <ListGroup>
                    {related.map((row) => {
                      const linkable = childHasChildren(row);
                      return (
                        <ListGroup.Item
                          key={String(row.id)}
                          action={linkable}
                          onClick={() => (linkable ? openRelatedChild(row) : null)}
                          style={{ cursor: linkable ? 'pointer' : 'default' }}
                        >
                          <div className="d-flex justify-content-between gap-2">
                            <div>
                              <strong>{row.title}</strong>
                              {row.type && (
                                <Badge bg="light" text="dark" pill className="ms-2">
                                  {row.type}
                                </Badge>
                              )}
                              {linkable && (
                                <Badge bg="primary" pill className="ms-1">
                                  Link · has children
                                </Badge>
                              )}
                              {row.description && (
                                <div className="small text-muted mt-1">
                                  {String(row.description).slice(0, 180)}
                                </div>
                              )}
                              {row.path && (
                                <div className="small font-monospace text-muted mt-1">
                                  {row.path}
                                </div>
                              )}
                            </div>
                            <span className="text-primary small fw-semibold text-nowrap">
                              {linkable ? 'Render →' : row.url ? 'Official' : ''}
                            </span>
                          </div>
                          {!linkable && row.url && (
                            <a
                              href={row.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="small"
                              onClick={(e) => e.stopPropagation()}
                            >
                              Official source →
                            </a>
                          )}
                        </ListGroup.Item>
                      );
                    })}
                  </ListGroup>
                </>
              )}
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="outline-secondary" onClick={() => setSelected(null)}>
            Close
          </Button>
          {selected?.path?.includes('/api/sba/content') && (
            <Button variant="outline-primary" href="/browse">
              Open Resources browser
            </Button>
          )}
          {selected?.url && (
            <Button variant="primary" href={selected.url} target="_blank" rel="noopener noreferrer">
              Official SBA page
            </Button>
          )}
        </Modal.Footer>
      </Modal>
    </Card>
  );
};

export default SBAContent;
