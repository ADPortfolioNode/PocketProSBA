import React, { useState, useEffect } from 'react';
import { Card, ListGroup, Form, Button, InputGroup, Spinner, Alert, Badge, Row, Col, Pagination } from 'react-bootstrap';
import { apiFetch } from '../apiClient';

const SBAContentExplorer = ({ selectedResource, endpoints }) => {
  const [contentType, setContentType] = useState('articles');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
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

  // Search SBA content using endpoint registry
  const searchContent = async (pageNum = 1) => {
    if (!searchQuery.trim() && contentType !== 'offices') return;
    
    setLoading(true);
    setError(null);
    
    try {
      const endpointKey = `sba_content_${contentType}`;
      if (!endpoints || !endpoints[endpointKey]) throw new Error('Endpoint not found');
      const response = await apiFetch(endpointKey, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        query: { query: searchQuery, page: pageNum }
      });
      
      setResults(response.items || []);
      setTotalPages(response.totalPages || 1);
      setPage(pageNum);
    } catch (err) {
      console.error('Error searching SBA content:', err);
      setError(`Unable to fetch SBA content: ${err.message}. This feature may not be fully implemented yet.`);
      setResults([]);
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
      const endpointKey = `sba_content_${contentType}_details`;
      if (!endpoints || !endpoints[endpointKey]) throw new Error('Endpoint not found');
      const response = await apiFetch(endpointKey, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        params: { id }
      });
      
      setSelectedItem(response);
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
            <h3>{selectedItem.title}</h3>
            <p className="text-muted">Published: {formatDate(selectedItem.created)}</p>
            {selectedItem.summary && <p className="lead">{selectedItem.summary}</p>}
            {selectedItem.body && <div dangerouslySetInnerHTML={{ __html: selectedItem.body }} />}
          </>
        );
        break;
        
      case 'blogs':
        details = (
          <>
            <h3>{selectedItem.title}</h3>
            <p className="text-muted">Published: {formatDate(selectedItem.created)} | Author: {selectedItem.author || 'Unknown'}</p>
            {selectedItem.summary && <p className="lead">{selectedItem.summary}</p>}
            {selectedItem.body && <div dangerouslySetInnerHTML={{ __html: selectedItem.body }} />}
          </>
        );
        break;
        
      case 'courses':
        details = (
          <>
            <h3>{selectedItem.title}</h3>
            <Badge bg="primary" className="mb-2">{selectedItem.type || 'Course'}</Badge>
            <p className="lead">{selectedItem.summary}</p>
            {selectedItem.description && <div dangerouslySetInnerHTML={{ __html: selectedItem.description }} />}
            {selectedItem.link && (
              <Button variant="primary" href={selectedItem.link} target="_blank" className="mt-3">
                Access Course
              </Button>
            )}
          </>
        );
        break;
        
      case 'events':
        details = (
          <>
            <h3>{selectedItem.title}</h3>
            <p className="text-muted">
              {formatDate(selectedItem.startDate)} 
              {selectedItem.endDate && ` - ${formatDate(selectedItem.endDate)}`}
            </p>
            <p><strong>Location:</strong> {selectedItem.location || 'Online'}</p>
            {selectedItem.description && <div dangerouslySetInnerHTML={{ __html: selectedItem.description }} />}
            {selectedItem.registrationLink && (
              <Button variant="primary" href={selectedItem.registrationLink} target="_blank" className="mt-3">
                Register for Event
              </Button>
            )}
          </>
        );
        break;
        
      case 'documents':
        details = (
          <>
            <h3>{selectedItem.title}</h3>
            <p className="text-muted">Published: {formatDate(selectedItem.created)}</p>
            {selectedItem.description && <p className="lead">{selectedItem.description}</p>}
            {selectedItem.fileUrl && (
              <Button variant="primary" href={selectedItem.fileUrl} target="_blank" className="mt-3">
                Download Document
              </Button>
            )}
          </>
        );
        break;
        
      case 'offices':
        details = (
          <>
            <h3>{selectedItem.title}</h3>
            <p><strong>Address:</strong> {selectedItem.address || 'N/A'}</p>
            <p><strong>Phone:</strong> {selectedItem.phone || 'N/A'}</p>
            <p><strong>Email:</strong> {selectedItem.email || 'N/A'}</p>
            {selectedItem.hours && <p><strong>Hours:</strong> {selectedItem.hours}</p>}
            {selectedItem.description && <div dangerouslySetInnerHTML={{ __html: selectedItem.description }} />}
            {selectedItem.website && (
              <Button variant="primary" href={selectedItem.website} target="_blank" className="mt-3">
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
      <Card className="mt-3">
        <Card.Body>
          {details}
        </Card.Body>
        <Card.Footer>
          <Button variant="secondary" onClick={() => setSelectedItem(null)}>
            Back to Results
          </Button>
        </Card.Footer>
      </Card>
    );
  };

  // Render content list
  const renderContentList = () => {
    if (results.length === 0) {
      return (
        <Alert variant="info">
          {contentType === 'offices' && !searchQuery.trim() && !loading
            ? "Loading offices..."
            : "No results found. Try a different search term."}
        </Alert>
      );
    }
    
    return (
      <ListGroup>
        {results.map((item, index) => (
          <ListGroup.Item 
            key={index}
            action
            onClick={() => viewContentDetails(item.id)}
            className="d-flex justify-content-between align-items-center"
          >
            <div>
              <h5 className="mb-1">{item.title}</h5>
              <p className="mb-1 text-muted">
                {item.created && `Published: ${formatDate(item.created)}`}
                {item.startDate && `Date: ${formatDate(item.startDate)}`}
              </p>
              {item.summary && <p className="mb-0">{item.summary.substring(0, 100)}...</p>}
            </div>
            <Badge bg="primary" pill>
              View
            </Badge>
          </ListGroup.Item>
        ))}
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
      apiFetch(endpointKey, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        params: { id: selectedResource }
      })
        .then(data => {
          setSelectedItem(data);
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
    <div className="sba-content-explorer">
      {selectedItem ? (
        <Card className="mb-4">
          <Card.Header>
            <h4>{selectedItem.title}</h4>
          </Card.Header>
          <Card.Body>
            <div>{selectedItem.description || selectedItem.summary || "No description available."}</div>
            {/* Add more details as needed */}
          </Card.Body>
        </Card>
      ) : (
        <Card>
          <Card.Header>
            <h4 className="mb-0">SBA Content Explorer</h4>
          </Card.Header>
          <Card.Body>
            {selectedItem ? (
              renderContentDetails()
            ) : (
              <>
                <Form onSubmit={handleSearch}>
                  <Row className="mb-3">
                    <Col md={4}>
                      <Form.Group>
                        <Form.Label>Content Type</Form.Label>
                        <Form.Select
                          value={contentType}
                          onChange={(e) => setContentType(e.target.value)}
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
                        <Form.Label>Search Query</Form.Label>
                        <InputGroup>
                          <Form.Control
                            type="text"
                            placeholder={`Search SBA ${contentType}...`}
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                          />
                          <Button 
                            variant="primary" 
                            type="submit"
                            disabled={loading || (!searchQuery.trim() && contentType !== 'offices')}
                          >
                            {loading ? <Spinner animation="border" size="sm" /> : 'Search'}
                          </Button>
                        </InputGroup>
                      </Form.Group>
                    </Col>
                  </Row>
                </Form>
                
                {error && <Alert variant="danger">{error}</Alert>}
                
                {loading ? (
                  <div className="text-center my-4">
                    <Spinner animation="border" />
                    <p className="mt-2">Loading results...</p>
                  </div>
                ) : (
                  renderContentList()
                )}
                
                {renderPagination()}
              </>
            )}
          </Card.Body>
        </Card>
      )}
    </div>
  );
};

export default SBAContentExplorer;
