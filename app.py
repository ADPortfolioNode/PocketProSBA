#!/usr/bin/env python3
"""
Minimal PocketPro SBA Assistant - Render.com Compatible
Optimized for deployment without ChromaDB dependencies
"""

import os
import logging
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# SBA Resources mock data for demonstration
SBA_RESOURCES = {
    "programs": [
        {
            "id": "7a_loans",
            "name": "7(a) Loans",
            "description": "Most common SBA loan program for small businesses",
            "max_amount": "$5,000,000",
            "use_cases": ["Working capital", "Equipment purchase", "Real estate", "Business acquisition"]
        },
        {
            "id": "504_loans",
            "name": "504 Loans",
            "description": "Long-term financing for real estate and equipment",
            "max_amount": "$5,500,000",
            "use_cases": ["Real estate", "Equipment", "Machinery"]
        },
        {
            "id": "microloans",
            "name": "Microloans",
            "description": "Small loans for startups and small businesses",
            "max_amount": "$50,000",
            "use_cases": ["Working capital", "Inventory", "Equipment"]
        }
    ],
    "resources": [
        {
            "id": "score",
            "name": "SCORE Mentorship",
            "description": "Free business mentoring from experienced entrepreneurs",
            "website": "https://www.score.org"
        },
        {
            "id": "sbdc",
            "name": "Small Business Development Centers",
            "description": "Business consulting and training services",
            "website": "https://americassbdc.org"
        }
    ]
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'environment': os.environ.get('RENDER_SERVICE_NAME', 'local'),
        'python_version': '3.13',
        'features': {
            'chat': True,
            'rag': False,  # Disabled for minimal deployment
            'file_upload': False
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with SBA knowledge"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Simple keyword-based responses for SBA queries
        response = generate_sba_response(message)
        
        return jsonify({
            'response': response,
            'timestamp': time.time(),
            'sources': get_relevant_sources(message)
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500

def generate_sba_response(message):
    """Generate response based on SBA knowledge"""
    message_lower = message.lower()
    
    # 7(a) Loans
    if any(keyword in message_lower for keyword in ['7a', '7(a)', 'loan', 'financing']):
        return """The SBA 7(a) loan program is the most common SBA loan program. Here are the key details:

**Loan Amount**: Up to $5,000,000
**Uses**: Working capital, equipment purchase, real estate, business acquisition
**Terms**: Up to 25 years for real estate, 10 years for equipment, 7 years for working capital
**Down Payment**: Typically 10-15%

**Benefits**:
- Lower down payments than conventional loans
- Longer repayment terms
- Competitive interest rates
- No prepayment penalties

Would you like to know more about eligibility requirements or other SBA loan programs?"""
    
    # 504 Loans
    elif any(keyword in message_lower for keyword in ['504', 'real estate', 'equipment']):
        return """The SBA 504 loan program provides long-term financing for real estate and equipment:

**Loan Amount**: Up to $5,500,000
**Structure**: 50% conventional loan, 40% SBA debenture, 10% down payment
**Terms**: 10 or 20 years
**Uses**: Real estate, equipment, machinery

**Benefits**:
- Lower down payment (10%)
- Fixed interest rates
- Long-term financing
- Promotes economic development

This program is ideal for businesses looking to purchase or improve real estate or buy equipment."""
    
    # Microloans
    elif any(keyword in message_lower for keyword in ['microloan', 'small loan', 'startup']):
        return """SBA Microloans are perfect for startups and small businesses:

**Loan Amount**: Up to $50,000 (average $13,000)
**Terms**: Up to 6 years
**Uses**: Working capital, inventory, supplies, furniture, fixtures, machinery, equipment

**Benefits**:
- Smaller loan amounts
- Less stringent requirements
- Business counseling included
- Good for businesses that can't qualify for traditional loans

Microloans are provided through nonprofit intermediary lenders."""
    
    # SCORE
    elif any(keyword in message_lower for keyword in ['mentor', 'score', 'advice', 'guidance']):
        return """SCORE provides free business mentoring:

**What is SCORE?**
- Volunteer network of experienced entrepreneurs and business leaders
- Free, confidential business mentoring
- Workshops and resources

**Services**:
- One-on-one mentoring
- Business plan development
- Marketing guidance
- Financial planning assistance

**How to Connect**:
Visit score.org to find a mentor in your area. All services are completely free!"""
    
    # SBDC
    elif any(keyword in message_lower for keyword in ['sbdc', 'development center', 'consulting']):
        return """Small Business Development Centers (SBDCs) offer comprehensive business support:

**Services**:
- Business consulting
- Training programs
- Market research
- Export assistance
- Technology commercialization

**Benefits**:
- Free or low-cost services
- Experienced business advisors
- Specialized industry expertise
- Connected to local universities

Find your local SBDC at americassbdc.org."""
    
    # General SBA info
    elif any(keyword in message_lower for keyword in ['sba', 'small business administration']):
        return """The Small Business Administration (SBA) supports small businesses through:

**Loan Programs**:
- 7(a) Loans (most common)
- 504 Loans (real estate/equipment)
- Microloans (small amounts)

**Resources**:
- SCORE mentorship
- Small Business Development Centers
- Women's Business Centers

**Other Support**:
- Government contracting opportunities
- Disaster assistance
- Investment programs

How can I help you with your specific business needs?"""
    
    # Default response
    else:
        return """I'm here to help you with SBA programs and small business resources! I can provide information about:

• **SBA Loan Programs**: 7(a) loans, 504 loans, microloans
• **Business Resources**: SCORE mentorship, SBDCs, training programs
• **Funding Options**: Grants, investment programs, disaster assistance
• **Government Contracting**: Set-aside programs, certifications

What specific area would you like to learn more about?"""

def get_relevant_sources(message):
    """Get relevant sources based on message content"""
    sources = []
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['loan', '7a', '504', 'microloan']):
        sources.append({
            'title': 'SBA Loan Programs',
            'url': 'https://www.sba.gov/funding-programs/loans',
            'type': 'official'
        })
    
    if any(keyword in message_lower for keyword in ['score', 'mentor']):
        sources.append({
            'title': 'SCORE Mentorship',
            'url': 'https://www.score.org',
            'type': 'resource'
        })
    
    if any(keyword in message_lower for keyword in ['sbdc', 'development']):
        sources.append({
            'title': 'Small Business Development Centers',
            'url': 'https://americassbdc.org',
            'type': 'resource'
        })
    
    return sources

@app.route('/api/programs', methods=['GET'])
def get_programs():
    """Get SBA programs"""
    return jsonify(SBA_RESOURCES['programs'])

@app.route('/api/resources', methods=['GET'])
def get_resources():
    """Get SBA resources"""
    return jsonify(SBA_RESOURCES['resources'])

@app.route('/api/search', methods=['POST'])
def search():
    """Search SBA resources"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        results = []
        
        # Search programs
        for program in SBA_RESOURCES['programs']:
            if (query in program['name'].lower() or 
                query in program['description'].lower() or 
                any(query in use_case.lower() for use_case in program['use_cases'])):
                results.append({
                    'type': 'program',
                    'data': program
                })
        
        # Search resources
        for resource in SBA_RESOURCES['resources']:
            if (query in resource['name'].lower() or 
                query in resource['description'].lower()):
                results.append({
                    'type': 'resource',
                    'data': resource
                })
        
        return jsonify({
            'query': query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'name': 'PocketPro SBA Assistant API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/api/health',
            'chat': '/api/chat',
            'programs': '/api/programs',
            'resources': '/api/resources',
            'search': '/api/search'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
