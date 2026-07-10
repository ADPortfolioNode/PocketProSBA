import React, { useState, useEffect, useCallback } from 'react';
import { businessLifecycleStages, localResourceTypes, sbaPrograms } from '../sbaResources';
import apiClient from '../api/apiClient';
import { Card, Nav, Row, Col, Container, Badge, Spinner, Alert, Button } from 'react-bootstrap';

/**
 * SBA Programs | Business Lifecycle | Local Resources
 * --------------------------------------------------
 * Prebuilt SPA loads ALL three arrays from GET /api/sba/resources:
 *   sbaPrograms, businessLifecycleStages, localResourceTypes
 * This component mirrors that contract and also supports dedicated endpoints.
 */
const SBAContent = ({ onProgramSelect, onResourceSelect }) => {
  const [activeTab, setActiveTab] = useState('programs');
  const [programs, setPrograms] = useState([]);
  const [lifecycle, setLifecycle] = useState([]);
  const [local, setLocal] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
      // Primary: single API the prebuilt SPA already calls
      const res = await apiClient.get('/api/sba/resources', { timeout: 60000 }, { quiet: true });
      const data = res?.data || res || {};

      let prog =
        data.sbaPrograms ||
        data.programs ||
        [];
      let life =
        data.businessLifecycleStages ||
        data.lifecycle ||
        [];
      let loc =
        data.localResourceTypes ||
        data.local ||
        [];

      // Dedicated endpoints if bundled payload incomplete
      if (!Array.isArray(prog) || !prog.length) {
        try {
          const p = await apiClient.get('/api/sba/programs', { timeout: 30000 }, { quiet: true });
          const pd = p?.data || p || {};
          prog = pd.items || pd.programs || (Array.isArray(pd) ? pd : []);
        } catch (_) {
          /* fall through */
        }
      }
      if (!Array.isArray(life) || !life.length) {
        try {
          const p = await apiClient.get('/api/sba/lifecycle', { timeout: 30000 }, { quiet: true });
          const pd = p?.data || p || {};
          life = pd.items || pd.lifecycle || (Array.isArray(pd) ? pd : []);
        } catch (_) {
          /* fall through */
        }
      }
      if (!Array.isArray(loc) || !loc.length) {
        try {
          const p = await apiClient.get('/api/sba/local-resources', { timeout: 30000 }, { quiet: true });
          const pd = p?.data || p || {};
          loc = pd.items || pd.local || (Array.isArray(pd) ? pd : []);
        } catch (_) {
          /* fall through */
        }
      }

      // Soft local fallbacks so tabs never render empty if network fails
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
              onClick={() => {
                if (kind === 'program' && onProgramSelect) onProgramSelect(card.id);
                if (kind !== 'program' && onResourceSelect) {
                  onResourceSelect(`${card.id} ${kind}`);
                }
              }}
            >
              <Card.Body className="d-flex">
                <div className={`${kind}-icon me-3`} style={{ fontSize: '1.6rem' }}>
                  {card.icon}
                </div>
                <div className={`${kind}-content flex-grow-1`}>
                  <Card.Title as="h5">{card.name}</Card.Title>
                  <Card.Text className="small text-muted">{card.description}</Card.Text>
                  {card.phase && (
                    <Badge bg="info" pill className="me-1">
                      {card.phase}
                    </Badge>
                  )}
                  {card.is_current === true && (
                    <Badge bg="success" pill className="me-1">
                      Current
                    </Badge>
                  )}
                  {Array.isArray(card.resources) && card.resources.length > 0 && (
                    <ul className="small mt-2 mb-0 ps-3">
                      {card.resources.slice(0, 4).map((r) => {
                        const label = typeof r === 'string' ? r : r.name || r.title;
                        const href = typeof r === 'object' ? r.url : null;
                        return (
                          <li key={label}>
                            {href ? (
                              <a href={href} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                                {label}
                              </a>
                            ) : (
                              label
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  )}
                  {card.url && (
                    <div className="mt-2">
                      <a
                        href={card.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="small"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Official source →
                      </a>
                    </div>
                  )}
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
            Populated from <code>/api/sba/resources</code>
            {programs.length || lifecycle.length || local.length
              ? ` · ${programs.length} programs · ${lifecycle.length} lifecycle · ${local.length} local`
              : ''}
          </span>
          <div className="d-flex gap-2">
            <Button size="sm" variant="outline-primary" onClick={loadAll} disabled={loading}>
              {loading ? 'Loading…' : 'Refresh'}
            </Button>
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
    </Card>
  );
};

export default SBAContent;
