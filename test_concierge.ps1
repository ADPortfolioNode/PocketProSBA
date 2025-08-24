# PowerShell script to test concierge functionality
Write-Host "=== Testing Concierge Functionality ==="

# Change to backend directory
Set-Location backend

# Run the simple test
python simple_test.py

# Test basic imports
Write-Host "`n=== Testing Basic Imports ==="
python -c "from assistants.concierge import Concierge; print('Concierge imported successfully')"

# Test instantiation
Write-Host "`n=== Testing Instantiation ==="
python -c "from assistants.concierge import Concierge; c = Concierge(); print('Concierge instantiated successfully')"

# Test message handling
Write-Host "`n=== Testing Message Handling ==="
python -c "
from assistants.concierge import Concierge
c = Concierge()
result = c.handle_message('Tell me about SBA loans', 'test-session-1')
print('Message handling completed')
print(f'Result: {result}')
"
