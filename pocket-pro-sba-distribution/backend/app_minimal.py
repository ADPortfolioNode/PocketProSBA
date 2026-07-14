import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'PocketPro SBA Minimal',
        'version': '1.0.0'
    })

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """API health check endpoint"""
    return health_check()

@app.route('/api/sba/resources', methods=['GET'])
def get_sba_resources():
    """Get SBA programs and resources data"""
    try:
        # SBA Program data and descriptions
        sba_programs = [
            {
                'id': 'loans',
                'name': 'SBA Loans',
                'description': 'Small business loan programs with competitive terms',
                'icon': '💰',
                'detailedDescription': '''
                    The SBA offers a variety of loan programs designed to meet the financing needs of small businesses.
                    These include 7(a) loans (the SBA's primary lending program), 504 loans (for major fixed assets),
                    microloans (for small amounts), and disaster loans (for businesses affected by declared disasters).
                ''',
                'url': 'https://www.sba.gov/funding-programs/loans'
            },
            {
                'id': 'contracting',
                'name': 'Government Contracting',
                'description': 'Help small businesses win federal contracts',
                'icon': '📝',
                'detailedDescription': '''
                    The federal government aims to award at least 23% of all federal contracting dollars to small businesses.
                    The SBA offers certification programs such as 8(a) Business Development, HUBZone, Women-Owned Small Business (WOSB),
                    and Service-Disabled Veteran-Owned Small Business (SDVOSB) to help small businesses compete for contracts.
                ''',
                'url': 'https://www.sba.gov/federal-contracting'
            }
        ]

        return jsonify({
            'sba_programs': sba_programs,
            'message': 'Minimal backend is running'
        })

    except Exception as e:
        logger.error(f"Error getting SBA resources: {str(e)}")
        return jsonify({'error': f'Failed to get SBA resources: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting minimal backend on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)
