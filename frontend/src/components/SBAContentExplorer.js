import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Card,
  Form,
  Button,
  InputGroup,
  Spinner,
  Alert,
  Badge,
  Row,
  Col,
  Pagination,
  Container,
  Nav,
  Modal,
} from 'react-bootstrap';
import apiClient from '../api/apiClient';

/**
 * Resources page
 * --------------
 * 1. GET /api/sba/resources  → build left navigation (and mobile select)
 * 2. Click a nav item       → query that resource.path once
 * 3. Click a result item    → open a detail card/modal with full information
 */

const ICONS = {
  loans: '💰',
  loan_types: '📋',
  articles: '📰',
  blogs: '✍️',
  courses: '🎓',
  documents: '📄',
  events: '📅',
  offices: '🏢',
  sbir: '🔬',
  lenders: '🏦',
  sources: '🛰️',
};

function normalizeItem(raw, index = 0) {
  if (!raw || typeof raw !== 'object') {
    const text = String(raw || '').trim();
    if (!text) return null;
    return {
      id: `item-${index}`,
      title: text.slice(0, 120),
      description: text,
      url: '',
      type: 'content',
      meta: {},
    };
  }

  let title = String(
    raw.title || raw.name || raw.label || raw.award_title || raw.firm || raw.type || ''
  ).trim();
  let description = String(
    raw.description ||
      raw.summary ||
      raw.teaser ||
      raw.body ||
      raw.abstract ||
      raw.message ||
      ''
  ).trim();
  const url = String(
    raw.url || raw.link || raw.href || raw.award_link || raw.source_page || ''
  ).trim();

  if (!title && url) {
    title = decodeURIComponent(url.split('/').filter(Boolean).pop() || 'SBA resource')
      .replace(/[-_]/g, ' ')
      .replace(/\.\w+$/, '');
  }
  if (!title && description) {
    title = description.slice(0, 80) + (description.length > 80 ? '…' : '');
  }
  if (!description && title) {
    description = url ? `${title} — ${url}` : `SBA resource: ${title}`;
  }
  if (!title && !description && !url) return null;

  const meta = { ...(raw.meta || {}) };
  [
    'agency',
    'firm',
    'phase',
    'program',
    'award_amount',
    'award_year',
    'phone',
    'email',
    'address',
    'location',
    'source_page',
    'retrieved_at',
    'is_current',
    'freshness',
    'source',
    'max_amount',
    'terms',
    'rates',
    'use_cases',
  ].forEach((key) => {
    if (raw[key] !== undefined && raw[key] !== null && raw[key] !== '') {
      meta[key] = raw[key];
    }
  });

  return {
    ...raw,
    id: raw.id ?? raw.nid ?? `item-${index}`,
    title,
    name: raw.name || title,
    description,
    summary: raw.summary || description,
    url,
    type: raw.type || 'content',
    meta,
  };
}

/** Turn /api/sba/sources object into displayable cards */
function sourcesToItems(data) {
  if (!data || typeof data !== 'object') return [];
  return Object.entries(data).map(([key, value], i) => {
    if (value && typeof value === 'object') {
      const ok = value.ok === true;
      const desc = [
        value.base ? `Base: ${value.base}` : null,
        value.status_code != null ? `HTTP ${value.status_code}` : null,
        value.error ? `Error: ${value.error}` : null,
        value.ok === false ? 'Unavailable' : value.ok === true ? 'Healthy' : null,
      ]
        .filter(Boolean)
        .join(' · ');
      return normalizeItem(
        {
          id: key,
          title: key.replace(/_/g, ' '),
          description: desc || JSON.stringify(value),
          type: 'source_status',
          is_current: ok,
          url: value.base || '',
          meta: value,
        },
        i
      );
    }
    return normalizeItem(
      {
        id: key,
        title: key.replace(/_/g, ' '),
        description: String(value),
        type: 'source_status',
      },
      i
    );
  }).filter(Boolean);
}

function overviewToItems(data) {
  const types = data?.available_loan_types;
  if (!Array.isArray(types)) return [];
  return types
    .map((t, i) =>
      normalizeItem(
        {
          id: `loan-type-${i}`,
          title: t.type || t.name || t.title || `Loan type ${i + 1}`,
          description: [
            t.description,
            t.max_amount ? `Max: ${t.max_amount}` : null,
            t.terms ? `Terms: ${t.terms}` : null,
            t.rates ? `Rates: ${t.rates}` : null,
            Array.isArray(t.use_cases) ? `Uses: ${t.use_cases.join(', ')}` : null,
          ]
            .filter(Boolean)
            .join(' · '),
          url: t.url || '',
          type: 'loan_type',
          is_current: t.is_current,
          retrieved_at: t.retrieved_at,
          max_amount: t.max_amount,
          terms: t.terms,
          rates: t.rates,
          use_cases: t.use_cases,
        },
        i
      )
    )
    .filter(Boolean);
}

const SBAContentExplorer = () => {
  const [resources, setResources] = useState([]);
  const [activeResource, setActiveResource] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [loadingItems, setLoadingItems] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetail, setShowDetail] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [resultMeta, setResultMeta] = useState(null);

  const navGroups = useMemo(() => {
    const groups = {};
    resources.forEach((r) => {
      const g = r.group || 'Resources';
      if (!groups[g]) groups[g] = [];
      groups[g].push(r);
    });
    return groups;
  }, [resources]);

  const loadCatalog = useCallback(async () => {
    setLoadingCatalog(true);
    setError(null);
    try {
      const res = await apiClient.get('/api/sba/resources', {}, { quiet: true });
      const list = res?.data?.resources || [];
      const cards = (Array.isArray(list) ? list : [])
        .filter((r) => r && r.id && r.path)
        .map((r) => ({
          id: r.id,
          name: r.name || r.id,
          description: r.description || `Browse ${r.name || r.id}`,
          path: r.path,
          group: r.group || 'Resources',
          icon: ICONS[r.icon || r.id] || '📁',
          queryable: r.queryable !== false,
        }));
      setResources(cards);
      if (!cards.length) {
        setError('No resources returned from /api/sba/resources');
      }
    } catch (err) {
      setError(`Failed to load resource navigation: ${err.message}`);
      setResources([]);
    } finally {
      setLoadingCatalog(false);
    }
  }, []);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  // After catalog headers exist, load the preferred tab so the panel is never blank
  useEffect(() => {
    if (loadingCatalog || !resources.length || activeResource) return;
    const preferred = resources.find((r) => r.id === 'loans') || resources[0];
    if (preferred) queryResource(preferred, 1, '');
  }, [loadingCatalog, resources, activeResource, queryResource]);

  const queryResource = useCallback(
    async (resource, pageNum = 1, query = '') => {
      if (!resource?.path) return;
      setLoadingItems(true);
      setError(null);
      setSelectedItem(null);
      setShowDetail(false);
      setActiveResource(resource);

      try {
        const isOverview = resource.path.includes('/sba-overview');
        const isSources = resource.path.includes('/sources');
        // Prefer cached API payload (no fresh=1). Re-scrape only when user searches or explicitly needs it.
        // fresh=1 forces live sba.gov HTML pulls and often empties the UI on 10s axios timeout.
        const response = await apiClient.get(
          resource.path,
          {
            params:
              isOverview || isSources
                ? {}
                : { query: query || undefined, page: pageNum },
            timeout: 60000,
          },
          { quiet: true }
        );
        const data = response?.data || response || {};

        let items = [];
        if (isSources) {
          items = sourcesToItems(data);
        } else if (isOverview || Array.isArray(data.available_loan_types)) {
          items = overviewToItems(data);
        } else if (Array.isArray(data.items)) {
          items = data.items.map((item, i) => normalizeItem(item, i)).filter(Boolean);
        } else if (Array.isArray(data.results)) {
          items = data.results.map((item, i) => normalizeItem(item, i)).filter(Boolean);
        }

        // Never leave a selected tab visually empty if the envelope is valid
        if (!items.length) {
          items = [
            normalizeItem(
              {
                id: `${resource.id}-empty`,
                title: `${resource.name} — no rows yet`,
                description:
                  data.message ||
                  `The API at ${resource.path} returned no items. Try again shortly.`,
                type: 'notice',
                is_current: false,
                source: data.source || 'api',
              },
              0
            ),
          ].filter(Boolean);
        }

        setResults(items);
        setPage(Number(data.currentPage) || pageNum);
        setTotalPages(Number(data.totalPages) || 1);
        setResultMeta({
          is_current: data.is_current,
          freshness: data.freshness,
          retrieved_at: data.retrieved_at,
          source: data.source || data.mode,
          message: data.message,
          count: items.length,
        });

        if (!items.length) {
          setError(
            data.message ||
              `No items for “${resource.name}”. Try another category or search.`
          );
        }
      } catch (err) {
        setResults([]);
        setResultMeta(null);
        setError(`Could not load ${resource.name}: ${err.message}`);
      } finally {
        setLoadingItems(false);
      }
    },
    []
  );

  const handleNavClick = (resource) => {
    setSearchQuery('');
    queryResource(resource, 1, '');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!activeResource) {
      setError('Select a resource in the navigation first.');
      return;
    }
    queryResource(activeResource, 1, searchQuery.trim());
  };

  const openItemCard = (item) => {
    setSelectedItem(item);
    setShowDetail(true);
  };

  const closeItemCard = () => {
    setShowDetail(false);
    setSelectedItem(null);
  };

  const renderDetailBody = (item) => {
    if (!item) return null;
    const metaEntries = Object.entries(item.meta || {}).filter(
      ([k, v]) => v !== undefined && v !== null && v !== '' && k !== 'raw'
    );
    return (
      <>
        <div className="d-flex flex-wrap gap-2 mb-3">
          {item.type && <Badge bg="primary">{item.type}</Badge>}
          {item.is_current === true && <Badge bg="success">Current</Badge>}
          {item.is_current === false && <Badge bg="secondary">Not current</Badge>}
          {(item.source || item.meta?.source) && (
            <Badge bg="light" text="dark">
              {item.source || item.meta.source}
            </Badge>
          )}
        </div>
        <p className="text-muted" style={{ whiteSpace: 'pre-wrap' }}>
          {item.description || item.summary}
        </p>
        {metaEntries.length > 0 && (
          <dl className="svc-meta-grid">
            {metaEntries.map(([key, value]) => (
              <div key={key} className="svc-meta-row">
                <dt>{key.replace(/_/g, ' ')}</dt>
                <dd>
                  {Array.isArray(value)
                    ? value.join(', ')
                    : typeof value === 'object'
                      ? JSON.stringify(value)
                      : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        )}
        {item.url && (
          <Button
            variant="primary"
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3"
          >
            Open official source
          </Button>
        )}
      </>
    );
  };

  return (
    <Container fluid className="sba-content-explorer svc-browse py-3">
      <div className="mb-4 svc-browse-hero text-center text-md-start">
        <h1 className="display-6 fw-bold mb-2 svc-browse-title">SBA Resources</h1>
        <p className="text-muted mb-0">
          Navigation is built from <code>/api/sba/resources</code>. Click a category to load
          items, then open any card for more detail.
        </p>
      </div>

      {error && (
        <Alert
          variant={results.length ? 'warning' : 'info'}
          dismissible
          onClose={() => setError(null)}
          className="mb-3"
        >
          {error}
        </Alert>
      )}

      <Row className="g-3">
        {/* —— API-driven navigation —— */}
        <Col lg={3} md={4}>
          <Card className="border-0 shadow-sm svc-res-nav sticky-lg-top" style={{ top: '4.5rem' }}>
            <Card.Header className="bg-white d-flex justify-content-between align-items-center">
              <strong>Browse</strong>
              <Button
                size="sm"
                variant="outline-primary"
                onClick={loadCatalog}
                disabled={loadingCatalog}
              >
                {loadingCatalog ? '…' : 'Refresh'}
              </Button>
            </Card.Header>
            <Card.Body className="p-2">
              {loadingCatalog ? (
                <div className="text-center py-4">
                  <Spinner animation="border" size="sm" variant="primary" />
                </div>
              ) : (
                Object.entries(navGroups).map(([group, items]) => (
                  <div key={group} className="mb-3">
                    <div className="px-2 pb-1 small text-uppercase text-muted fw-semibold">
                      {group}
                    </div>
                    <Nav className="flex-column gap-1">
                      {items.map((resource) => {
                        const active = activeResource?.id === resource.id;
                        return (
                          <Nav.Link
                            key={resource.id}
                            active={active}
                            className={`svc-res-nav-link ${active ? 'is-active' : ''}`}
                            onClick={() => handleNavClick(resource)}
                            title={resource.description}
                          >
                            <span className="me-2" aria-hidden="true">
                              {resource.icon}
                            </span>
                            <span>
                              <span className="d-block">{resource.name}</span>
                              <span className="d-block small text-muted text-truncate">
                                {resource.description}
                              </span>
                            </span>
                          </Nav.Link>
                        );
                      })}
                    </Nav>
                  </div>
                ))
              )}
            </Card.Body>
          </Card>
        </Col>

        {/* —— Results + detail —— */}
        <Col lg={9} md={8}>
          {!activeResource && !loadingCatalog && (
            <Card className="border-0 shadow-sm">
              <Card.Body className="text-center py-5 text-muted">
                <div className="display-6 mb-2">📂</div>
                <p className="mb-0">
                  Select a resource from the navigation to load its items from the API.
                </p>
              </Card.Body>
            </Card>
          )}

          {activeResource && (
            <Card className="border-0 shadow-sm">
              <Card.Header className="bg-white">
                <div className="d-flex flex-wrap justify-content-between align-items-start gap-3">
                  <div>
                    <h2 className="h5 mb-1">
                      <span className="me-2">{activeResource.icon}</span>
                      {activeResource.name}
                    </h2>
                    <p className="small text-muted mb-2">{activeResource.description}</p>
                    {resultMeta && (
                      <div className="d-flex flex-wrap gap-2 align-items-center">
                        {resultMeta.is_current != null && (
                          <Badge bg={resultMeta.is_current ? 'success' : 'secondary'}>
                            {resultMeta.is_current ? 'Current' : 'Not current'}
                          </Badge>
                        )}
                        {resultMeta.source && (
                          <Badge bg="light" text="dark">
                            {resultMeta.source}
                          </Badge>
                        )}
                        <span className="small text-muted">
                          {resultMeta.count ?? results.length} item
                          {(resultMeta.count ?? results.length) === 1 ? '' : 's'}
                        </span>
                        {resultMeta.retrieved_at && (
                          <span className="small text-muted">
                            · {new Date(resultMeta.retrieved_at).toLocaleString()}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                  <Form onSubmit={handleSearch} style={{ minWidth: 240, maxWidth: 360, flex: 1 }}>
                    <InputGroup size="sm">
                      <Form.Control
                        placeholder={`Search ${activeResource.name}…`}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        disabled={loadingItems}
                      />
                      <Button type="submit" variant="primary" disabled={loadingItems}>
                        Search
                      </Button>
                    </InputGroup>
                  </Form>
                </div>
              </Card.Header>

              <Card.Body>
                {loadingItems ? (
                  <div className="text-center py-5">
                    <Spinner animation="border" variant="primary" />
                    <div className="text-muted mt-2">
                      Loading {activeResource.name} from API…
                    </div>
                  </div>
                ) : (
                  <>
                    {results.length === 0 ? (
                      <Alert variant="light" className="border mb-0">
                        No items to display. Try another category or clear the search.
                      </Alert>
                    ) : (
                      <Row xs={1} lg={2} className="g-3">
                        {results.map((item) => (
                          <Col key={String(item.id)}>
                            <Card
                              className="h-100 svc-result-card svc-clickable-card"
                              role="button"
                              tabIndex={0}
                              onClick={() => openItemCard(item)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                  e.preventDefault();
                                  openItemCard(item);
                                }
                              }}
                            >
                              <Card.Body className="d-flex flex-column">
                                <div className="d-flex justify-content-between gap-2 mb-2">
                                  <Card.Title as="h3" className="h6 mb-0">
                                    {item.title}
                                  </Card.Title>
                                  <div className="d-flex flex-column align-items-end gap-1">
                                    {item.is_current === true && (
                                      <Badge bg="success">Current</Badge>
                                    )}
                                    {item.is_current === false && (
                                      <Badge bg="secondary">Not current</Badge>
                                    )}
                                    {item.type && (
                                      <Badge bg="light" text="dark">
                                        {item.type}
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                                <Card.Text className="small text-muted flex-grow-1">
                                  {(item.description || '').slice(0, 220)}
                                  {(item.description || '').length > 220 ? '…' : ''}
                                </Card.Text>
                                {item.meta && Object.keys(item.meta).length > 0 && (
                                  <div className="small text-muted mb-2 border-top pt-2">
                                    {Object.entries(item.meta)
                                      .slice(0, 3)
                                      .map(([k, v]) => (
                                        <div key={k}>
                                          <strong>{k.replace(/_/g, ' ')}:</strong>{' '}
                                          {Array.isArray(v)
                                            ? v.join(', ')
                                            : String(v).slice(0, 90)}
                                        </div>
                                      ))}
                                  </div>
                                )}
                                <div className="mt-auto small text-primary fw-semibold">
                                  Open details →
                                </div>
                              </Card.Body>
                            </Card>
                          </Col>
                        ))}
                      </Row>
                    )}

                    {totalPages > 1 && (
                      <Pagination className="justify-content-center mt-4 mb-0">
                        <Pagination.Prev
                          disabled={page <= 1 || loadingItems}
                          onClick={() =>
                            queryResource(activeResource, page - 1, searchQuery)
                          }
                        />
                        <Pagination.Item active>
                          {page} / {totalPages}
                        </Pagination.Item>
                        <Pagination.Next
                          disabled={page >= totalPages || loadingItems}
                          onClick={() =>
                            queryResource(activeResource, page + 1, searchQuery)
                          }
                        />
                      </Pagination>
                    )}
                  </>
                )}
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>

      {/* Detail card for a clicked item */}
      <Modal show={showDetail && !!selectedItem} onHide={closeItemCard} size="lg" centered>
        <Modal.Header closeButton className="border-0 pb-0">
          <Modal.Title className="h5 pe-3">{selectedItem?.title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>{renderDetailBody(selectedItem)}</Modal.Body>
        <Modal.Footer className="border-0 pt-0">
          <Button variant="outline-secondary" onClick={closeItemCard}>
            Close
          </Button>
          {selectedItem?.url && (
            <Button
              variant="primary"
              href={selectedItem.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Official source
            </Button>
          )}
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default SBAContentExplorer;
