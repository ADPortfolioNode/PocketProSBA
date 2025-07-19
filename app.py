#!/usr/bin/env python3
"""
Minimal PocketPro SBA Assistant - Render.com Compatible
Optimized for deployment without ChromaDB dependencies
"""



import os
import logging
import time
import json
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import datetime
from flask_socketio import SocketIO, emit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    from flask import Flask
    from flask_cors import CORS
    from flask_socketio import SocketIO

    app = Flask(__name__)
    CORS(app)
    render_env = os.environ.get('RENDER', None)
    render_service = os.environ.get('RENDER_SERVICE_ID', None)
    render_external_url = os.environ.get('RENDER_EXTERNAL_URL', None)
    if render_env or render_service or render_external_url:
        import eventlet
        eventlet.monkey_patch()
        socketio = SocketIO(app, cors_allowed_origins="*")
    else:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

    # Additional app setup here (routes, etc.)

    return app, socketio

app, socketio = create_app()


# Configure uploads folder
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'frontend', 'uploads'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure uploads directory exists

# Serve React build as static files for all non-API routes
from flask import send_from_directory

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

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

@app.route('/health', methods=['GET'])
def simple_health_check():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'success': True
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint with SBA knowledge"""
    try:
        data = request.get_json()
        
        # Accept message parameter from frontend or query parameter from minimal_app
        message = data.get('message', data.get('query', ''))
        user_name = data.get('userName', 'Guest')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Track session and personalize response
        session_id = request.cookies.get('session_id', str(uuid.uuid4()))
        
        # System message handling
        if message.startswith("SYSTEM:"):
            response = f"Session started for {user_name}. Welcome to the SBA Assistant!"
            resp = jsonify({
                'response': response,
                'timestamp': time.time(),
                'sessionId': session_id
            })
            resp.set_cookie('session_id', session_id, max_age=3600, httponly=True)
            return resp
        
        # Simple keyword-based responses for SBA queries with personalization
        response = generate_sba_response(message, user_name)
        
        resp = jsonify({
            'response': response,
            'timestamp': time.time(),
            'sources': get_relevant_sources(message)
        })
        resp.set_cookie('session_id', session_id, max_age=3600, httponly=True)
        return resp
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500

def generate_sba_response(message, user_name='Guest'):
    """Generate personalized response based on SBA knowledge"""
    message_lower = message.lower()
    personal_greeting = f"{user_name}, " if user_name and user_name != 'Guest' else ""
    
    # Greeting and introduction queries
    if any(keyword in message_lower for keyword in ['hello', 'hi ', 'hey', 'greetings', 'howdy']):
        return f"Hello {user_name}! I'm your SBA Assistant. How can I help you today with SBA programs and resources?"
    
    # Personal questions
    if any(keyword in message_lower for keyword in ['who are you', 'what can you do', 'your name']):
        return f"I'm your SBA Assistant, {user_name}! I can help you with information about SBA loans, grants, programs, and resources for small businesses. What would you like to know about?"
    
    # 7(a) Loans
    if any(keyword in message_lower for keyword in ['7a', '7(a)', 'loan', 'financing']):
        return f"{personal_greeting}The SBA 7(a) loan program is the most common SBA loan program. Here are the key details:\n\n**Loan Amount**: Up to $5,000,000\n**Uses**: Working capital, equipment purchase, real estate, business acquisition\n**Terms**: Up to 25 years for real estate, 10 years for equipment, 7 years for working capital\n**Down Payment**: Typically 10-15%\n\n**Benefits**:\n- Lower down payments than conventional loans\n- Longer repayment terms\n- Competitive interest rates\n- No prepayment penalties"
    # 7(a) Loans
    if any(keyword in message_lower for keyword in ['7a', '7(a)', 'loan', 'financing']):
        return f"""{personal_greeting}The SBA 7(a) loan program is the most common SBA loan program. Here are the key details:

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
        # RAG-like response: dynamically list available programs and resources
        programs = SBA_RESOURCES.get('programs', [])
        resources = SBA_RESOURCES.get('resources', [])
        program_lines = '\n'.join([
            f"• {p['name']}: {p['description']} (Max: {p['max_amount']})" for p in programs
        ])
        resource_lines = '\n'.join([
            f"• {r['name']}: {r['description']}" for r in resources
        ])
        return f"Here are the latest SBA programs and resources available to you:\n\nSBA Loan Programs:\n{program_lines}\n\nBusiness Resources:\n{resource_lines}\n\nWhat specific area would you like to learn more about?"

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

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """Document upload endpoint"""
    try:
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file part in the request'
            }), 400
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No selected file'
            }), 400
        
        # Save the file to the uploads folder
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Get file stats
        stats = os.stat(file_path)
        size_bytes = stats.st_size
        modified_timestamp = stats.st_mtime
        
        # Get file extension
        file_ext = Path(filename).suffix[1:].lower() if '.' in filename else ""
        
        # Determine number of pages (mock for now)
        pages = 1
        if file_ext.lower() in ['pdf', 'docx']:
            # Simulate document with multiple pages
            pages = max(1, size_bytes // 5000)
        
        # Create document metadata
        document = {
            'filename': filename,
            'path': file_path,
            'size': size_bytes,
            'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modified_timestamp)),
            'type': file_ext,
            'pages': pages
        }
        
        return jsonify({
            'success': True,
            'message': f'File {filename} uploaded successfully',
            'document': document
        })
        
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

@app.route('/api/uploads', methods=['GET'])
def list_uploads():
    """List uploaded documents"""
    try:
        # Get list of files in the uploads directory
        files = [f for f in os.listdir(UPLOAD_FOLDER) if os.path.isfile(os.path.join(UPLOAD_FOLDER, f))]
        
        return jsonify({
            'uploads': files,
            'count': len(files)
        })
        
    except Exception as e:
        logger.error(f"Uploads listing error: {str(e)}")
        return jsonify({'error': f'Failed to list uploads: {str(e)}'}), 500

@app.route('/api/documents/list', methods=['GET'])
def list_documents():
    """List documents in the uploads folder"""
    try:
        documents = []
        
        # Check if uploads folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            return jsonify({
                'success': True,
                'documents': documents
            })
        
        # List files in the uploads folder
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                # Get file stats
                stats = os.stat(file_path)
                size_bytes = stats.st_size
                modified_timestamp = stats.st_mtime
                
                # Get file extension
                file_ext = Path(filename).suffix[1:].lower() if '.' in filename else ""
                
                # Determine number of pages (mock for now)
                pages = 1
                if file_ext.lower() in ['pdf', 'docx']:
                    # Simulate document with multiple pages
                    pages = max(1, size_bytes // 5000)
                
                documents.append({
                    'filename': filename,
                    'path': file_path,
                    'size': size_bytes,
                    'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(modified_timestamp)),
                    'type': file_ext,
                    'pages': pages
                })
        
        return jsonify({
            'success': True,
            'documents': documents
        })
        
    except Exception as e:
        logger.error(f"Document listing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with config mode display"""
    # Determine config mode
    render_env = os.environ.get('RENDER', None)
    render_service = os.environ.get('RENDER_SERVICE_ID', None)
    render_external_url = os.environ.get('RENDER_EXTERNAL_URL', None)
    port = os.environ.get('PORT', '5000')
    if render_env or render_service or render_external_url:
        config_mode = 'render'
    else:
        config_mode = 'local'
    return jsonify({
        'name': 'PocketPro SBA Assistant API',
        'version': '1.0.0',
        'status': 'running',
        'config_mode': config_mode,
        'port': port,
        'render_service_id': render_service,
        'render_external_url': render_external_url,
        'endpoints': {
            'health': '/api/health',
            'chat': '/api/chat',
            'programs': '/api/programs',
            'resources': '/api/resources',
            'search': '/api/search',
            'uploads': '/api/uploads',
            'documents': '/api/documents/list'
        }
    })

@app.route('/api/health', methods=['GET'])
def api_health():
    try:
        return jsonify({
            "status": "ok",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "service": "PocketProSBA"
        }), 200
    except Exception as e:
        logger.error(f"/api/health error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['HEAD'])
def api_health_head():
    try:
        return ('', 200)
    except Exception as e:
        logger.error(f"/api/health HEAD error: {str(e)}", exc_info=True)
        return ('', 500)

@app.route('/api/registry', methods=['GET'])
def api_registry():
    try:
        return jsonify({
            "health": "/api/health",
            "chat": "/api/chat",
            "programs": "/api/programs",
            "resources": "/api/resources",
            "documents": "/api/documents/list",
            "upload": "/api/documents/upload",
            "search": "/api/search",
            "uploads": "/api/uploads"
        })
    except Exception as e:
        logger.error(f"/api/registry error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Example WebSocket event
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('server_response', {'data': 'Connected to backend WebSocket!'})

@socketio.on('chat')
def handle_chat(data):
    print(f'Received chat message: {data}')
    emit('server_response', {'data': f"Echo: {data}"})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    print(f'Received message: {data}')
    emit('server_response', {'data': f'Server received: {data}'})

if __name__ == '__main__':
    # Conditional config for local vs. Render.com
    render_env = os.environ.get('RENDER', None)
    render_service = os.environ.get('RENDER_SERVICE_ID', None)
    render_external_url = os.environ.get('RENDER_EXTERNAL_URL', None)
    port = int(os.environ.get('PORT', 5000))
    if render_env or render_service or render_external_url:
        print(f"[CONFIG MODE] Render.com detected. Service ID: {render_service}, External URL: {render_external_url}, Port: {port}")
    else:
        print(f"[CONFIG MODE] Local development detected. Port: {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
