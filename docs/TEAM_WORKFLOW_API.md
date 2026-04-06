# Team Workflow API Documentation

## Overview

The Team Workflow API provides endpoints for interacting with a world-class three-person development team that collaborates to solve issues. The team consists of:

- **Administrator**: Researches issues and gathers context
- **Developer**: Implements solutions
- **QA Engineer**: Validates implementations

All responses include the greeting "Hello deo! 🎯" to acknowledge the user.

## Base URL

```
Local Development: http://localhost:5000/api/team
Production: https://your-domain.com/api/team
```

## Authentication

Currently, no authentication is required. Future versions may implement user authentication.

## Endpoints

### Health Check

Check the health status of the team workflow service.

**Endpoint:** `GET /api/team/health`

**Response:**
```json
{
  "status": "healthy",
  "service": "team_workflow",
  "greeting": "Hello deo! 🎯",
  "active_tasks": 3,
  "message": "World-class development team ready to assist!"
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `500 Internal Server Error`: Service is unhealthy

---

### Submit Issue

Submit a new issue for the team to work on.

**Endpoint:** `POST /api/team/submit`

**Request Body:**
```json
{
  "issue_description": "Implement user authentication feature"
}
```

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "greeting": "Hello deo! 🎯",
  "message": "Issue submitted successfully. Team is ready to work!",
  "created_at": "2025-01-26T12:00:00.000Z"
}
```

**Status Codes:**
- `201 Created`: Issue submitted successfully
- `400 Bad Request`: Missing or invalid issue description
- `500 Internal Server Error`: Server error

**Validation:**
- `issue_description` is required and cannot be empty or whitespace

---

### Process Task

Process a task through the team workflow. This triggers the complete cycle of research → implementation → validation.

**Endpoint:** `POST /api/team/process/{task_id}`

**URL Parameters:**
- `task_id`: UUID of the task to process

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "iterations": 1,
  "validation_passed": true,
  "solution": "Implementation details...",
  "message": "Task processing completed",
  "updated_at": "2025-01-26T12:05:00.000Z",
  "completed_at": "2025-01-26T12:05:00.000Z"
}
```

**Status Values:**
- `pending`: Task submitted but not yet processed
- `researching`: Administrator is analyzing the issue
- `implementing`: Developer is creating a solution
- `validating`: QA is testing the implementation
- `completed`: Task successfully completed
- `failed`: Task failed after maximum iterations

**Status Codes:**
- `200 OK`: Task processed successfully
- `404 Not Found`: Task ID not found
- `500 Internal Server Error`: Processing error

---

### Get Task Status

Retrieve the current status of a task.

**Endpoint:** `GET /api/team/task/{task_id}`

**URL Parameters:**
- `task_id`: UUID of the task

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "iterations": 1,
  "validation_passed": true,
  "created_at": "2025-01-26T12:00:00.000Z",
  "updated_at": "2025-01-26T12:05:00.000Z",
  "completed_at": "2025-01-26T12:05:00.000Z",
  "message_count": 7
}
```

**Status Codes:**
- `200 OK`: Status retrieved successfully
- `404 Not Found`: Task ID not found
- `500 Internal Server Error`: Server error

---

### Get Conversation History

Retrieve the full conversation history between team members for a task.

**Endpoint:** `GET /api/team/task/{task_id}/history`

**URL Parameters:**
- `task_id`: UUID of the task

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "greeting": "Hello deo! 🎯",
  "conversation": [
    {
      "id": "msg-001",
      "role": "administrator",
      "content": "Hello deo! 🎯 Team assembled and ready to work on your issue!",
      "timestamp": "2025-01-26T12:00:00.000Z",
      "metadata": {
        "type": "greeting"
      }
    },
    {
      "id": "msg-002",
      "role": "administrator",
      "content": "📋 **Administrator Research Report**...",
      "timestamp": "2025-01-26T12:01:00.000Z",
      "metadata": {
        "build_notes": "...",
        "error_analysis": "...",
        "iteration": 1
      }
    },
    {
      "id": "msg-003",
      "role": "developer",
      "content": "💻 **Developer Implementation Report**...",
      "timestamp": "2025-01-26T12:03:00.000Z",
      "metadata": {
        "implementation_complete": true,
        "iteration": 1
      }
    },
    {
      "id": "msg-004",
      "role": "qa",
      "content": "✅ **QA Validation Report**...",
      "timestamp": "2025-01-26T12:05:00.000Z",
      "metadata": {
        "validation_passed": true,
        "checks": {...}
      }
    }
  ],
  "message_count": 4
}
```

**Role Values:**
- `administrator`: Research and analysis messages
- `developer`: Implementation messages
- `qa`: Validation and testing messages

**Status Codes:**
- `200 OK`: History retrieved successfully
- `404 Not Found`: Task ID not found
- `500 Internal Server Error`: Server error

---

### List Tasks

Retrieve a list of all active tasks.

**Endpoint:** `GET /api/team/tasks`

**Response:**
```json
{
  "greeting": "Hello deo! 🎯",
  "tasks": [
    {
      "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "completed",
      "iterations": 1,
      "validation_passed": true,
      "issue_description": "Implement user authentication feature",
      "created_at": "2025-01-26T12:00:00.000Z",
      "updated_at": "2025-01-26T12:05:00.000Z"
    },
    {
      "task_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      "status": "implementing",
      "iterations": 1,
      "validation_passed": false,
      "issue_description": "Fix database connection issue...",
      "created_at": "2025-01-26T12:10:00.000Z",
      "updated_at": "2025-01-26T12:12:00.000Z"
    }
  ],
  "count": 2
}
```

**Status Codes:**
- `200 OK`: Tasks retrieved successfully
- `500 Internal Server Error`: Server error

---

## Workflow Examples

### Complete Workflow Example

```bash
# 1. Submit an issue
TASK_ID=$(curl -X POST http://localhost:5000/api/team/submit \
  -H "Content-Type: application/json" \
  -d '{"issue_description": "Implement password reset feature"}' \
  | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# 2. Check initial status
curl http://localhost:5000/api/team/task/$TASK_ID | jq

# 3. Process the task
curl -X POST http://localhost:5000/api/team/process/$TASK_ID | jq

# 4. Get conversation history
curl http://localhost:5000/api/team/task/$TASK_ID/history | jq

# 5. List all tasks
curl http://localhost:5000/api/team/tasks | jq
```

### Python Example

```python
import requests

# Submit issue
response = requests.post(
    'http://localhost:5000/api/team/submit',
    json={'issue_description': 'Add user profile page'}
)
task_id = response.json()['task_id']
print(f"Greeting: {response.json()['greeting']}")

# Process task
process_response = requests.post(
    f'http://localhost:5000/api/team/process/{task_id}'
)
result = process_response.json()
print(f"Status: {result['status']}")
print(f"Iterations: {result['iterations']}")

# Get conversation history
history_response = requests.get(
    f'http://localhost:5000/api/team/task/{task_id}/history'
)
conversation = history_response.json()['conversation']

for message in conversation:
    print(f"{message['role']}: {message['content'][:100]}...")
```

### JavaScript/Axios Example

```javascript
const axios = require('axios');

async function teamWorkflowExample() {
  // Submit issue
  const submitResponse = await axios.post(
    'http://localhost:5000/api/team/submit',
    { issue_description: 'Implement two-factor authentication' }
  );
  
  const taskId = submitResponse.data.task_id;
  console.log('Greeting:', submitResponse.data.greeting);
  
  // Process task
  const processResponse = await axios.post(
    `http://localhost:5000/api/team/process/${taskId}`
  );
  
  console.log('Status:', processResponse.data.status);
  console.log('Completed:', processResponse.data.validation_passed);
  
  // Get conversation history
  const historyResponse = await axios.get(
    `http://localhost:5000/api/team/task/${taskId}/history`
  );
  
  historyResponse.data.conversation.forEach(msg => {
    console.log(`[${msg.role}]: ${msg.content.substring(0, 100)}...`);
  });
}

teamWorkflowExample();
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

Common error scenarios:

- **400 Bad Request**: Missing or invalid input data
- **404 Not Found**: Task ID not found
- **500 Internal Server Error**: Server processing error

## Rate Limiting

Currently, no rate limiting is implemented. Future versions may add rate limiting to prevent abuse.

## Changelog

### Version 1.0.0 (2025-01-26)
- Initial release of Team Workflow API
- Three-role team system (Administrator, Developer, QA)
- Automated retry loop with max 5 iterations
- Codebase parsing for build notes
- Full conversation history tracking
- "Hello deo! 🎯" greeting integration

## Support

For questions or issues with the Team Workflow API:
1. Check this documentation
2. Review the conversation history for error details
3. Check application logs for debugging
4. Submit an issue in the repository

---

**Remember:** Hello deo! 🎯 The team is ready to help resolve your issues!
