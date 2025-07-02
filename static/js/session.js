/**
 * Session initialization module
 * Fetches available API endpoints and stores them for frontend use
 */

// Store for available endpoints
window.apiEndpoints = {};

/**
 * Initializes the session by fetching available endpoints
 * from the server and storing them for later use
 */
function initSession() {
    console.log('Initializing session and discovering endpoints...');
    
    fetch('/api/endpoints')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch endpoints');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Process and store endpoints
                data.endpoints.forEach(endpoint => {
                    window.apiEndpoints[endpoint.endpoint] = {
                        url: endpoint.url,
                        methods: endpoint.methods,
                        description: endpoint.description
                    };
                });
                
                console.log(`Successfully loaded ${data.count} API endpoints`);
                
                // Trigger event for other components to know endpoints are available
                const event = new CustomEvent('endpointsLoaded', { 
                    detail: { endpoints: window.apiEndpoints } 
                });
                document.dispatchEvent(event);
            }
        })
        .catch(error => {
            console.error('Error during session initialization:', error);
        });
}

// Initialize the session when the document is ready
document.addEventListener('DOMContentLoaded', initSession);

/**
 * Helper function to get endpoint information by name
 * @param {string} name - The endpoint name
 * @returns {object|null} - The endpoint information or null if not found
 */
function getEndpoint(name) {
    return window.apiEndpoints[name] || null;
}
