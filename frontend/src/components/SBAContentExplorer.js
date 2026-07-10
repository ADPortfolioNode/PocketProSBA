import React, { useState, useEffect, useCallback } from 'react';
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
} from 'react-bootstrap';
import apiClient from '../api/apiClient';

/**
 * Browse flow:
 *  1) Load /api/sba/resources once (catalog cards — no content query yet)
 *  2) User clicks a resource → query that endpoint once
 *  3) Render result cards with full title/description/url/meta (never empty)
 */
const RESOURCE_ICONS = {
  loans: '💰',
  articles: '📰',
  blogs: '✍️',
  courses: '🎓',
  documents: '📄',
  events: '📅',
  offices: '🏢',
  sbir: '🔬',
  lenders: '🏦',
  loan_types: '📋',
  sources: '🛰️',
};

const SBAContentExplorer = () => {
  const [resources, setResources] = useState([]);
  const [activeResource, setActiveResource] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [loadingItems, setLoadingItems] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [resultMeta, setResultMeta] = useState(null);
  const [queriedOnce, setQueriedOnce] = useState(false);

  const normalizeItem = useCallback((raw, index = 0) => {
    if (!raw || typeof raw !== 'object') {
      const text = String(raw || '').trim();
      if (!text) return null;
      return {
        id: `item-${index}`,
        title: text.slice(0, 120),
        description: text,
        url: '',
        type: 'content',
      };
    }
    const title = String(
      raw.title || raw.name || raw.label || raw.award_title || raw.firm || ''
    ).trim();
    const description = String(
      raw.description || raw.summary || raw.teaser || raw.body || raw.abstract || ''
    ).trim();
    const url = String(raw.url || raw.link || raw.href || raw.award_link || '').trim();
    if (!title && !description && !url) return null;

    let finalTitle = title;
    let finalDescription = description;
    if (!finalTitle && url) {
      finalTitle = url.split('/').filter(Boolean).pop()?.replace(/-/g, ' ') || 'SBA resource';
    }
    if (!finalTitle && finalDescription) {
      finalTitle = finalDescription.slice(0, 80) + (finalDescription.length > 80 ? '…' : '');
    }
    if (!finalDescription && finalTitle) {
      finalDescription = url
        ? `${finalTitle}. Official source: ${url}`
        : `SBA resource: ${finalTitle}`;
    }

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
    ].forEach((key) => {
      if (raw[key] !== undefined && raw[key] !== null && raw[key] !== '') {
        meta[key] = raw[key];
      }
    });

    return {
      ...raw,
      id: raw.id ?? `item-${index}`,
      title: finalTitle,
      name: raw.name || finalTitle,
      description: finalDescription,
      summary: raw.summary || finalDescription,
      url,
      type: raw.type || 'content',
      meta,
    };
  }, []);

  const loadCatalog = useCallback(async () => {
    setLoadingCatalog(true);
    setError(null);
    try {
      const res = await apiClient.get('/api/sba/resources', {}, { quiet: true });
      const list = res?.data?.resources || res?.resources || [];
      // Keep only queryable content resources (skip status-only endpoints as primary cards optional)
      const cards = (Array.isArray(list) ? list : [])
        .filter((r) => r && r.path && r.id !== 'sources')
        .map((r) => ({
          id: r.id,
          name: r.name || r.id,
          description: r.description || `Browse ${r.name || r.id}`,
          path: r.path,
          icon: RESOURCE_ICONS[r.id] || '📁',
        }));
      setResources(cards);
      if (!cards.length) {
        setError('No SBA resource categories available from the API.');
      }
    } catch (err) {
      setError(`Failed to load SBA resources: ${err.message}`);
      setResources([]);
    } finally {
      setLoadingCatalog(false);
    }
  }, []);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  const queryResource = useCallback(
    async (resource, pageNum = 1, query = searchQuery) => {
      if (!resource?.path) return;
      setLoadingItems(true);
      setError(null);
      setSelectedItem(null);
      setQueriedOnce(true);
      setActiveResource(resource);

      try {
        const isOverview = resource.path.includes('/rag/');
        const response = await apiClient.get(
          resource.path,
          {
            params: isOverview
              ? { fresh: 1 }
              : { query: query || undefined, page: pageNum, fresh: 1 },
          },
          { quiet: true }
        );
        const data = response?.data || response || {};

        // Support both item lists and overview-style payloads
        let rawItems = Array.isArray(data.items)
          ? data.items
          : Array.isArray(data.available_loan_types)
            ? data.available_loan_types.map((t, i) => ({
                id: `loan-type-${i}`,
                title: t.type || t.name || t.title,
                description: [
                  t.description,
                  t.max_amount ? `Max: ${t.max_amount}` : null,
                  t.terms ? `Terms: ${t.terms}` : null,
                  t.rates ? `Rates: ${t.rates}` : null,
                  Array.isArray(t.use_cases) ? `Uses: ${t.use_cases.join(', ')}` : null,
                  t.url,
                ]
                  .filter(Boolean)
                  .join(' · '),
                url: t.url || '',
                type: 'loan_type',
                is_current: t.is_current,
                retrieved_at: t.retrieved_at,
              }))
            : [];

        const items = rawItems
          .map((item, i) => normalizeItem(item, i))
          .filter(Boolean);

        setResults(items);
        setPage(data.currentPage || pageNum);
        setTotalPages(data.totalPages || 1);
        setResultMeta({
          is_current: data.is_current,
          freshness: data.freshness,
          retrieved_at: data.retrieved_at,
          source: data.source || data.mode,
          message: data.message,
          resource: resource.name,
        });

        if (!items.length) {
          setError(
            data.message ||
              `No items returned for ${resource.name}. Try another category or refine search.`
          );
        }
      } catch (err) {
        console.error(err);
        setResults([]);
        setError(`Query failed for ${resource.name}: ${err.message}`);
        setResultMeta(null);
      } finally {
        setLoadingItems(false);
      }
    },
    [normalizeItem, searchQuery]
  );

  const handleResourceClick = (resource) => {
    setSearchQuery('');
    queryResource(resource, 1, '');
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!activeResource) {
      setError('Select a resource category first, then search.');
      return;
    }
    queryResource(activeResource, 1, searchQuery);
  };

  const handlePageChange = (nextPage) => {
    if (!activeResource) return;
    queryResource(activeResource, nextPage, searchQuery);
  };

  const openItem = (item) => {
    setSelectedItem(item);
  };

  const renderMetaRows = (item) => {
    const meta = item.meta || {};
    const rows = Object.entries(meta).filter(
      ([k, v]) => v !== undefined && v !== null && v !== '' && k !== 'raw'
    );
    if (!rows.length) return null;
    return (
      <dl className="svc-meta-grid mb-0 mt-3">
        {rows.map(([key, value]) => (
          <div key={key} className="svc-meta-row">
            <dt>{key.replace(/_/g, ' ')}</dt>
            <dd>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</dd>
          </div>
        ))}
      </dl>
    );
  };

  const renderSelectedItem = () => {
    if (!selectedItem) return null;
    const item = selectedItem;
    return (
      <Card className="svc-detail-card mt-4 border-0 shadow">
        <Card.Header className="d-flex justify-content-between align-items-center">
          <div>
            <h4 className="mb-1">{item.title}</h4>
            <div className="d-flex flex-wrap gap-2">
              {item.type && <Badge bg="primary">{item.type}</Badge>}
              {item.is_current === true && <Badge bg="success">Current</Badge>}
              {item.is_current === false && <Badge bg="secondary">Not current</Badge>}
              {item.source && (
                <Badge bg="light" text="dark">
                  {item.source}
                </Badge>
              )}
            </div>
          </div>
          <Button variant="outline-secondary" size="sm" onClick={() => setSelectedItem(null)}>
            Back to results
          </Button>
        </Card.Header>
        <Card.Body>
          {(item.description || item.summary) && (
            <p className="lead text-muted">{item.description || item.summary}</p>
          )}
          {renderMetaRows(item)}
          {item.url && (
            <Button
              variant="primary"
              className="mt-3"
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Open official source
            </Button>
          )}
        </Card.Body>
      </Card>
    );
  };

  return (
    <Container fluid className="sba-content-explorer svc-browse py-4">
      <div className="text-center mb-4 svc-browse-hero">
        <h1 className="display-5 fw-bold mb-2 svc-browse-title">SBA Resources</h1>
        <p className="lead text-muted mb-0">
          Choose a category to load live data once — cards always show the data they reference.
        </p>
      </div>

      {error && (
        <Alert
          variant={results.length ? 'warning' : 'info'}
          dismissible
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}

      {/* Step 1: resource catalog — click to query */}
      <Card className="border-0 shadow-sm mb-4">
        <Card.Header className="bg-white">
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <strong>Resource categories</strong>
            <Button
              size="sm"
              variant="outline-primary"
              onClick={loadCatalog}
              disabled={loadingCatalog}
            >
              {loadingCatalog ? 'Loading…' : 'Refresh catalog'}
            </Button>
          </div>
        </Card.Header>
        <Card.Body>
          {loadingCatalog ? (
            <div className="text-center py-4">
              <Spinner animation="border" variant="primary" />
              <div className="text-muted mt-2">Loading SBA resources…</div>
            </div>
          ) : (
            <Row xs={1} sm={2} lg={3} className="g-3">
              {resources.map((resource) => {
                const active = activeResource?.id === resource.id;
                return (
                  <Col key={resource.id}>
                    <Card
                      className={`h-100 svc-resource-card ${active ? 'is-active' : ''}`}
                      role="button"
                      tabIndex={0}
                      onClick={() => handleResourceClick(resource)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handleResourceClick(resource);
                        }
                      }}
                    >
                      <Card.Body>
                        <div className="d-flex gap-3 align-items-start">
                          <span className="svc-resource-icon" aria-hidden="true">
                            {resource.icon}
                          </span>
                          <div>
                            <Card.Title as="h3" className="h6 mb-1">
                              {resource.name}
                            </Card.Title>
                            <Card.Text className="small text-muted mb-2">
                              {resource.description}
                            </Card.Text>
                            <span className="svc-link small">
                              {active && loadingItems ? 'Loading…' : 'Load resources →'}
                            </span>
                          </div>
                        </div>
                      </Card.Body>
                    </Card>
                  </Col>
                );
              })}
            </Row>
          )}
        </Card.Body>
      </Card>

      {/* Step 2: query results after click */}
      {activeResource && (
        <Card className="border-0 shadow-sm mb-3">
          <Card.Header className="bg-white">
            <div className="d-flex flex-wrap justify-content-between align-items-center gap-2">
              <div>
                <strong>{activeResource.name}</strong>
                {resultMeta && (
                  <div className="d-flex flex-wrap gap-2 mt-1">
                    <Badge bg={resultMeta.is_current ? 'success' : 'secondary'}>
                      {resultMeta.is_current ? 'Current' : 'Not current'}
                    </Badge>
                    {resultMeta.source && (
                      <Badge bg="light" text="dark">
                        {resultMeta.source}
                      </Badge>
                    )}
                    {resultMeta.retrieved_at && (
                      <span className="small text-muted">
                        {new Date(resultMeta.retrieved_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <Form onSubmit={handleSearch} className="d-flex gap-2" style={{ minWidth: 260 }}>
                <InputGroup size="sm">
                  <Form.Control
                    placeholder={`Filter ${activeResource.name}…`}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
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
                <div className="text-muted mt-2">Querying {activeResource.name}…</div>
              </div>
            ) : selectedItem ? (
              renderSelectedItem()
            ) : (
              <>
                {!queriedOnce && (
                  <Alert variant="light" className="border">
                    Click a category above to load its resources.
                  </Alert>
                )}
                {queriedOnce && results.length === 0 && !error && (
                  <Alert variant="info">No items to display for this resource.</Alert>
                )}
                <Row xs={1} md={2} className="g-3">
                  {results.map((item) => (
                    <Col key={String(item.id)}>
                      <Card className="h-100 svc-result-card">
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
                            {item.description}
                          </Card.Text>
                          {item.meta && Object.keys(item.meta).length > 0 && (
                            <div className="small text-muted mb-2">
                              {Object.entries(item.meta)
                                .slice(0, 4)
                                .map(([k, v]) => (
                                  <div key={k}>
                                    <strong>{k.replace(/_/g, ' ')}:</strong>{' '}
                                    {String(v).slice(0, 80)}
                                  </div>
                                ))}
                            </div>
                          )}
                          <div className="d-flex gap-2 mt-auto">
                            <Button
                              size="sm"
                              variant="outline-primary"
                              onClick={() => openItem(item)}
                            >
                              View details
                            </Button>
                            {item.url && (
                              <Button
                                size="sm"
                                variant="primary"
                                href={item.url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                Open source
                              </Button>
                            )}
                          </div>
                        </Card.Body>
                      </Card>
                    </Col>
                  ))}
                </Row>

                {totalPages > 1 && (
                  <Pagination className="justify-content-center mt-4 mb-0">
                    <Pagination.Prev
                      disabled={page <= 1 || loadingItems}
                      onClick={() => handlePageChange(page - 1)}
                    />
                    <Pagination.Item active>{page}</Pagination.Item>
                    <Pagination.Next
                      disabled={page >= totalPages || loadingItems}
                      onClick={() => handlePageChange(page + 1)}
                    />
                  </Pagination>
                )}
              </>
            )}
          </Card.Body>
        </Card>
      )}
    </Container>
  );
};

export default SBAContentExplorer;
