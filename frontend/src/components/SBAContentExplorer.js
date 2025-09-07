import React, { useState, useEffect } from 'react';
import { Card, ListGroup, Form, Button, InputGroup, Spinner, Alert, Badge, Row, Col, Pagination, Container, Navbar, Nav, Dropdown } from 'react-bootstrap';
import apiClient from '../api/apiClient'; // Corrected import path

const SBAContentExplorer = ({ selectedResource, endpoints }) => {
  const [contentType, setContentType] = useState('articles');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]); // Top-level nodes
  const [nodeMap, setNodeMap] = useState({}); // id -> children
  const [expandedNodes, setExpandedNodes] = useState({}); // id -> bool
  const [error, setError] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Content type options
  const contentTypes = [
    { value: 'articles', label: 'Articles' },
    { value: 'blogs', label: 'Blog Posts' },
    { value: 'courses', label: 'Courses' },
    { value: 'events', label: 'Events' },
    { value: 'documents', label: 'Documents' },
    { value: 'offices', label: 'Offices' }
  ];

  // Endpoint registry for SBA content
  const endpointRegistry = {
    sba_content_articles: '/api/sba/content/articles',
    sba_content_blogs: '/api/sba/content/blogs',
    sba_content_courses: '/api/sba/content/courses',
    sba_content_events: '/api/sba/content/events',
    sba_content_documents: '/api/sba/content/documents',
    sba_content_offices: '/api/sba/content/offices',
    sba_content_details: '/api/sba/content/node'
  };

  // Resource status (chromadb, flask)
  const [resourceStatus, setResourceStatus] = useState({
    chromadb: { status: 'unknown', message: '' },
    flask: { status: 'unknown', message: '' }
  });

  // Fetch resource status from backend endpoints
  const fetchResourceStatus = async () => {
    try {
      // Flask health
      const flaskResp = await apiClient.get('/api/health');
      setResourceStatus(prev => ({
        ...prev,
        flask: { status: flaskResp.data.status === 'ok' ? 'online' : 'error', message: flaskResp.data.message || '' }
      }));
    } catch (err) {
      setResourceStatus(prev => ({ ...prev, flask: { status: 'error', message: err.message } }));
    }
    try {
      // ChromaDB health
      const chromaResp = await apiClient.get('/api/chromadb_health');
      setResourceStatus(prev => ({
        ...prev,
        chromadb: { status: chromaResp.data.status === 'ok' ? 'online' : 'error', message: chromaResp.data.message || '' }
      }));
    } catch (err) {
      setResourceStatus(prev => ({ ...prev, chromadb: { status: 'error', message: err.message } }));
    }
  };

  useEffect(() => {
    fetchResourceStatus();
  }, []);

  // Search SBA content using endpoint registry (node structure)
  const searchContent = async (pageNum = 1) => {
    if (!searchQuery.trim() && contentType !== 'offices') return;

    setLoading(true);
    setError(null);

    try {
      const endpointKey = `sba_content_${contentType}`;
      const endpoint = endpointRegistry[endpointKey];
      if (!endpoint) {
        setError('SBA content endpoint not found. Please check your backend configuration or registry.');
        setResults([]);
        return;
      }
      const response = await apiClient.get(endpoint, {
        params: { query: searchQuery, page: pageNum }
      });

      // Expect response.items to be an array of nodes, each with possible children
      if (response.data && response.data.items) {
        setResults(response.data.items);
        setTotalPages(response.data.totalPages || 1);
        setPage(pageNum);
        setNodeMap({}); // Reset node map on new search
      } else {
        setError('No SBA content found for your query.');
        setResults([]);
      }
    } catch (err) {
      console.error('Error searching SBA content:', err);
      setError(`Error fetching SBA content: ${err.message}`);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch children for a node (by id)
  const fetchNodeChildren = async (nodeId) => {
    setLoading(true);
    setError(null);
    try {
      const endpointKey = `sba_content_${contentType}_children`;
      if (!endpoints || !endpoints[endpointKey]) throw new Error('Children endpoint not found');
      const response = await apiClient.get(endpoints[endpointKey], {
        params: { id: nodeId }
      });
      setNodeMap(prev => ({ ...prev, [nodeId]: response.data.items || [] }));
    } catch (err) {
      setError(`Error fetching node children: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle search form submission
  const handleSearch = (e) => {
    e.preventDefault();
    searchContent(1); // Reset to first page on new search
  };

  // Load offices without a search query
  useEffect(() => {
    if (contentType === 'offices') {
      searchContent(page);
    }
  }, [contentType]);

  // View content details using endpoint registry
  const viewContentDetails = async (id) => {
    setLoading(true);
    setError(null);

    try {
      const endpoint = endpointRegistry.sba_content_details;
      if (!endpoint) throw new Error('Endpoint not found');
      const response = await apiClient.get(endpoint, {
        params: { id }
      });

      setSelectedItem(response.data);
    } catch (err) {
      setError(`Error fetching content details: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Reset selected item when changing content type
  useEffect(() => {
    setSelectedItem(null);
    setResults([]);
  }, [contentType]);

  // Render pagination controls
  const renderPagination = () => {
    if (totalPages <= 1) return null;
    
    return (
      <Pagination className="justify-content-center mt-3">
        <Pagination.Prev 
          onClick={() => searchContent(page - 1)}
          disabled={page === 1}
        />
        
        {page > 1 && <Pagination.Item onClick={() => searchContent(1)}>1</Pagination.Item>}
        {page > 2 && <Pagination.Ellipsis />}
        
        {page > 1 && <Pagination.Item onClick={() => searchContent(page - 1)}>{page - 1}</Pagination.Item>}
        <Pagination.Item active>{page}</Pagination.Item>
        {page < totalPages && <Pagination.Item onClick={() => searchContent(page + 1)}>{page + 1}</Pagination.Item>}
        
        {page < totalPages - 1 && <Pagination.Ellipsis />}
        {page < totalPages && <Pagination.Item onClick={() => searchContent(totalPages)}>{totalPages}</Pagination.Item>}
        
        <Pagination.Next 
          onClick={() => searchContent(page + 1)}
          disabled={page === totalPages}
        />
      </Pagination>
    );
  };

  // Format date string
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  // Render content item details
  const renderContentDetails = () => {
    if (!selectedItem) return null;

    let details;

    switch (contentType) {
      case 'articles':
        details = (
          <>
            <div className="d-flex align-items-center mb-3">
              <i className="fas fa-newspaper text-primary me-3 fs-2"></i>
              <div>
                <h3 className="mb-1">{selectedItem.title}</h3>
                <small className="text-muted">Published: {formatDate(selectedItem.created)}</small>
              </div>
            </div>
            {selectedItem.summary && <p className="lead text-muted">{selectedItem.summary}</p>}
            {selectedItem.body && <div className="content-body" dangerouslySetInnerHTML={{ __html: selectedItem.body }} />}
          </>
        );
        break;

      case 'blogs':
        details = (
          <>
            <div className="d-flex align-items-center mb-3">
              <i className="fas fa-blog text-success me-3 fs-2"></i>
              <div>
                <h3 className="mb-1">{selectedItem.title}</h3>
                <small className="text-muted">Published: {formatDate(selectedItem.created)} | Author: {selectedItem.author || 'Unknown'}</small>
              </div>
            </div>
            {selectedItem.summary && <p className="lead text-muted">{selectedItem.summary}</p>}
            {selectedItem.body && <div className="content-body" dangerouslySetInnerHTML={{ __html: selectedItem.body }} />}
          </>
        );
        break;

      case 'courses':
        details = (
          <>
            <div className="d-flex align-items-center mb-3">
              <i className="fas fa-graduation-cap text-info me-3 fs-2"></i>
              <div>
                <h3 className="mb-1">{selectedItem.title}</h3>
                <Badge bg="primary" className="mb-2">{selectedItem.type || 'Course'}</Badge>
              </div>
            </div>
            <p className="lead text-muted">{selectedItem.summary}</p>
            {selectedItem.description && <div className="content-body" dangerouslySetInnerHTML={{ __html: selectedItem.description }} />}
            {selectedItem.link && (
              <Button
                variant="primary"
                href={selectedItem.link}
                target="_blank"
                className="mt-3"
                style={{ background: 'linear-gradient(45deg, #667eea, #764ba2)', border: 'none' }}
              >
                <i className="fas fa-external-link-alt me-2"></i>
                Access Course
              </Button>
            )}
          </>
        );
        break;

      case 'events':
        details = (
          <>
            <div className="d-flex align-items-center mb-3">
              <i className="fas fa-calendar-alt text-warning me-3 fs-2"></i>
              <div>
                <h3 className="mb-1">{selectedItem.title}</h3>
                <small className="text-muted">
                  {formatDate(selectedItem.startDate)}
                  {selectedItem.endDate && ` - ${formatDate(selectedItem.endDate)}`}
                </small>
              </div>
            </div>
            <p><strong>Location:</strong> {selectedItem.location || 'Online'}</p>
            {selectedItem.description && <div className="content-body" dangerouslySetInnerHTML={{ __html: selectedItem.description }} />}
            {selectedItem.registrationLink && (
              <Button
                variant="primary"
                href={selectedItem.registrationLink}
                target="_blank"
                className="mt-3"
                style={{ background: 'linear-gradient(45deg, #667eea, #764ba2)', border: 'none' }}
              >
                <i className="fas fa-user-plus me-2"></i>
                Register for Event
              </Button>
            )}
          </>
        );
        break;

      case 'documents':
        details = (
          <>
            <div className="d-flex align-items-center mb-3">
              <i className="fas fa-file-alt text-secondary me-3 fs-2"></i>
              <div>
                <h3 className="mb-1">{selectedItem.title}</h3>
                <small className="text-muted">Published: {formatDate(selectedItem.created)}</small>
              </div>
            </div>
            {selectedItem.description && <p className="lead text-muted">{selectedItem.description}</p>}
            {selectedItem.fileUrl && (
              <Button
                variant="primary"
                href={selectedItem.fileUrl}
                target="_blank"
                className="mt-3"
                style={{ background: 'linear-gradient(45deg, #667eea, #764ba2)', border: 'none' }}
              >
                <i className="fas fa-download me-2"></i>
                Download Document
              </Button>
            )}
          </>
        );
        break;

      case 'offices':
        details = (
          <>
            <div className="d-flex align-items-center mb-3">
              <i className="fas fa-building text-danger me-3 fs-2"></i>
              <div>
                <h3 className="mb-1">{selectedItem.title}</h3>
              </div>
            </div>
            <Row>
              <Col md={6}>
                <p><i className="fas fa-map-marker-alt me-2 text-muted"></i><strong>Address:</strong> {selectedItem.address || 'N/A'}</p>
                <p><i className="fas fa-phone me-2 text-muted"></i><strong>Phone:</strong> {selectedItem.phone || 'N/A'}</p>
              </Col>
              <Col md={6}>
                <p><i className="fas fa-envelope me-2 text-muted"></i><strong>Email:</strong> {selectedItem.email || 'N/A'}</p>
                {selectedItem.hours && <p><i className="fas fa-clock me-2 text-muted"></i><strong>Hours:</strong> {selectedItem.hours}</p>}
              </Col>
            </Row>
            {selectedItem.description && <div className="content-body" dangerouslySetInnerHTML={{ __html: selectedItem.description }} />}
            {selectedItem.website && (
              <Button
                variant="primary"
                href={selectedItem.website}
                target="_blank"
                className="mt-3"
                style={{ background: 'linear-gradient(45deg, #667eea, #764ba2)', border: 'none' }}
              >
                <i className="fas fa-external-link-alt me-2"></i>
                Visit Website
              </Button>
            )}
          </>
        );
        break;

      default:
        details = <p>No details available</p>;
    }

    return (
      <Card className="shadow-lg border-0 mt-4" style={{ background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}>
        <Card.Header className="bg-gradient-primary text-white border-0">
          <div className="d-flex align-items-center justify-content-between">
            <h4 className="mb-0">
              <i className="fas fa-info-circle me-2"></i>
              Content Details
            </h4>
            <Badge bg="light" text="dark" className="fs-6">
              {contentTypes.find(type => type.value === contentType)?.label}
            </Badge>
          </div>
        </Card.Header>
        <Card.Body className="p-4">
          {details}
        </Card.Body>
        <Card.Footer className="bg-light border-0">
          <Button
            variant="outline-secondary"
            onClick={() => setSelectedItem(null)}
            className="w-100"
          >
            <i className="fas fa-arrow-left me-2"></i>
            Back to Results
          </Button>
        </Card.Footer>
      </Card>
    );
  };

  // Render node tree recursively
  const renderNodeTree = (nodes, level = 0) => {
    if (!nodes || nodes.length === 0) {
      return (
        <Alert variant="info" className={level === 0 ? '' : 'ms-4'}>
          {level === 0
            ? (contentType === 'offices' && !searchQuery.trim() && !loading
                ? "Loading offices..."
                : "No results found. Try a different search term.")
            : "No child nodes."}
        </Alert>
      );
    }
    return (
      <ListGroup className={level > 0 ? 'ms-4' : ''}>
        {nodes.map((item, idx) => {
          const hasChildren = item.hasChildren || (nodeMap[item.id] && nodeMap[item.id].length > 0);
          const expanded = expandedNodes[item.id];
          return (
            <ListGroup.Item key={item.id} className="d-flex align-items-center">
              <div style={{ flex: 1 }}>
                <span style={{ fontWeight: 'bold' }}>{item.title}</span>
                {item.summary && <span className="ms-2 text-muted">{item.summary.substring(0, 60)}...</span>}
              </div>
              {hasChildren && (
                <Button
                  variant="outline-secondary"
                  size="sm"
                  className="me-2"
                  onClick={async () => {
                    setExpandedNodes(prev => ({ ...prev, [item.id]: !expanded }));
                    if (!expanded && !nodeMap[item.id]) {
                      await fetchNodeChildren(item.id);
                    }
                  }}
                  aria-label={expanded ? 'Collapse' : 'Expand'}
                >
                  {expanded ? '-' : '+'}
                </Button>
              )}
              <Button
                variant="primary"
                size="sm"
                onClick={() => viewContentDetails(item.id)}
              >
                View
              </Button>
              {expanded && nodeMap[item.id] && (
                <div style={{ width: '100%' }}>
                  {renderNodeTree(nodeMap[item.id], level + 1)}
                </div>
              )}
            </ListGroup.Item>
          );
        })}
      </ListGroup>
    );
  };

  // Fetch resource details if selectedResource prop is provided
  useEffect(() => {
    if (selectedResource) {
      setLoading(true);
      setError(null);
      const endpointKey = 'sba_content_resource_details';
      if (!endpoints || !endpoints[endpointKey]) {
        setError('Resource details endpoint not found');
        setLoading(false);
        return;
      }
      apiClient.get(endpoints[endpointKey], {
        params: { id: selectedResource }
      })
        .then(response => {
          setSelectedItem(response.data);
          setLoading(false);
        })
        .catch(err => {
          setError(`Unable to load resource: ${err.message}`);
          setLoading(false);
        });
    } else {
      setSelectedItem(null);
    }
  }, [selectedResource, endpoints]);

  return (
    <Container fluid className="sba-content-explorer py-4" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', minHeight: '100vh' }}>
      {/* Modern Header */}
      <div className="text-center mb-5">
        <h1 className="display-4 text-white fw-bold mb-3" style={{ textShadow: '2px 2px 4px rgba(0,0,0,0.3)' }}>
          SBA Content Explorer
        </h1>
        <p className="lead text-white-50">Discover SBA resources, articles, courses, and more</p>
      </div>

      {/* Resource Status Section - Modern Design */}
      <Row className="mb-4">
        <Col lg={12}>
          <Card className="shadow-lg border-0" style={{ background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}>
            <Card.Header className="bg-gradient-primary text-white border-0">
              <div className="d-flex align-items-center">
                <i className="fas fa-server me-2"></i>
                <h5 className="mb-0">System Resources</h5>
              </div>
            </Card.Header>
            <Card.Body>
              <Row>
                <Col md={6}>
                  <div className="d-flex align-items-center p-3 rounded" style={{ background: 'rgba(0,123,255,0.1)' }}>
                    <div className={`status-indicator me-3 ${resourceStatus.flask.status === 'online' ? 'bg-success' : 'bg-danger'}`}></div>
                    <div>
                      <span className="fw-bold">Flask Server</span>
                      <Badge bg={resourceStatus.flask.status === 'online' ? 'success' : 'danger'} className="ms-2">
                        {resourceStatus.flask.status}
                      </Badge>
                    </div>
                  </div>
                </Col>
                <Col md={6}>
                  <div className="d-flex align-items-center p-3 rounded" style={{ background: 'rgba(40,167,69,0.1)' }}>
                    <div className={`status-indicator me-3 ${resourceStatus.chromadb.status === 'online' ? 'bg-success' : 'bg-danger'}`}></div>
                    <div>
                      <span className="fw-bold">ChromaDB</span>
                      <Badge bg={resourceStatus.chromadb.status === 'online' ? 'success' : 'danger'} className="ms-2">
                        {resourceStatus.chromadb.status}
                      </Badge>
                    </div>
                  </div>
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Main Content */}
      <Row>
        <Col lg={12}>
          {selectedItem ? (
            renderContentDetails()
          ) : (
            <Card className="shadow-lg border-0" style={{ background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(10px)' }}>
              <Card.Header className="bg-gradient-secondary text-white border-0">
                <div className="d-flex align-items-center justify-content-between">
                  <div className="d-flex align-items-center">
                    <i className="fas fa-search me-2"></i>
                    <h4 className="mb-0">Explore SBA Content</h4>
                  </div>
                  <Badge bg="light" text="dark" className="fs-6">
                    {contentTypes.find(type => type.value === contentType)?.label}
                  </Badge>
                </div>
              </Card.Header>
              <Card.Body className="p-4">
                <Form onSubmit={handleSearch}>
                  <Row className="mb-4">
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label className="fw-bold text-muted">Content Type</Form.Label>
                        <Form.Select
                          value={contentType}
                          onChange={(e) => setContentType(e.target.value)}
                          className="form-control-lg border-0 shadow-sm"
                          style={{ background: 'rgba(255,255,255,0.8)' }}
                        >
                          {contentTypes.map(type => (
                            <option key={type.value} value={type.value}>
                              {type.label}
                            </option>
                          ))}
                        </Form.Select>
                      </Form.Group>
                    </Col>
                    <Col md={8}>
                      <Form.Group>
                        <Form.Label className="fw-bold text-muted">Search Query</Form.Label>
                        <InputGroup className="input-group-lg">
                          <Form.Control
                            type="text"
                            placeholder={`Search SBA ${contentType}...`}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="border-0 shadow-sm"
                            style={{ background: 'rgba(255,255,255,0.8)' }}
                          />
                          <Button
                            variant="primary"
                            type="submit"
                            disabled={loading || (!searchQuery.trim() && contentType !== 'offices')}
                            className="px-4"
                            style={{ background: 'linear-gradient(45deg, #667eea, #764ba2)', border: 'none' }}
                          >
                            {loading ? (
                              <Spinner animation="border" size="sm" className="me-2" />
                            ) : (
                              <i className="fas fa-search me-2"></i>
                            )}
                            {loading ? 'Searching...' : 'Search'}
                          </Button>
                        </InputGroup>
                      </Form.Group>
                    </Col>
                  </Row>
                </Form>

                {error && (
                  <Alert variant="danger" className="border-0 shadow-sm">
                    <i className="fas fa-exclamation-triangle me-2"></i>
                    {error}
                  </Alert>
                )}

                {loading ? (
                  <div className="text-center py-5">
                    <div className="spinner-border text-primary" style={{ width: '3rem', height: '3rem' }} role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-3 text-muted">Discovering SBA content...</p>
                  </div>
                ) : (
                  <div className="results-container">
                    {renderNodeTree(results)}
                  </div>
                )}
                {renderPagination()}
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>

      <style jsx>{`
        .bg-gradient-primary {
          background: linear-gradient(45deg, #667eea, #764ba2);
        }
        .bg-gradient-secondary {
          background: linear-gradient(45deg, #f093fb, #f5576c);
        }
        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
        .card {
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .card:hover {
          transform: translateY(-5px);
          box-shadow: 0 15px 35px rgba(0,0,0,0.1) !important;
        }
        .btn {
          transition: all 0.3s ease;
        }
        .btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .form-control:focus, .form-select:focus {
          border-color: #667eea;
          box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
      `}</style>
    </Container>
  );
};

export default SBAContentExplorer;
