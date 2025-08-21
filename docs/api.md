# API Reference

This document provides a reference for the API endpoints available in the PocketPro:SBA Edition application.

## Base URL

The base URL for all API endpoints is `/api`.

## Authentication

Currently, there is no authentication required to access the API endpoints.

## Endpoints

### GET /api/info

Returns system information.

**Response:**

```json
{
  "service": "PocketPro:SBA Edition",
  "version": "1.0.0",
  "status": "operational",
  "rag_status": "available",
  "vector_store": "ChromaDB",
  "document_count": 100
}
```

### POST /api/decompose

Decomposes a user task into steps.

**Request Body:**

```json
{
  "message": "How do I apply for a small business loan?",
  "session_id": "12345"
}
```

**Response:**

```json
{
  "response": {
    "text": "I can help with that. Here are the steps to apply for a small business loan...",
    "sources": [],
    "timestamp": "2024-08-21T12:00:00.000Z"
  }
}
```

### POST /api/execute

Executes a decomposed task step.

**Request Body:**

```json
{
  "task": {
    "step_number": 1,
    "instruction": "Gather required documents.",
    "suggested_agent_type": "SearchAgent"
  }
}
```

**Response:**

```json
{
  "step_number": 1,
  "status": "completed",
  "result": "Here are the documents you need...",
  "sources": []
}
```

### POST /api/validate

Validates a step result.

**Request Body:**

```json
{
  "result": "Here are the documents you need...",
  "task": {
    "step_number": 1,
    "instruction": "Gather required documents.",
    "suggested_agent_type": "SearchAgent"
  }
}
```

**Response:**

```json
{
  "status": "PASS",
  "confidence": 0.9,
  "feedback": "Step result validated successfully"
}
```

### POST /api/query

Queries documents.

**Request Body:**

```json
{
  "query": "small business loan",
  "top_k": 5
}
```

**Response:**

```json
{
  "success": true,
  "query": "small business loan",
  "results": [
    {
      "id": "1",
      "content": "...",
      "metadata": {},
      "distance": 0.1,
      "relevance_score": 0.9
    }
  ],
  "count": 1
}
```

### GET /api/chat

Returns all chat messages.

**Response:**

```json
[
  {
    "id": 1,
    "user_id": "12345",
    "message": "Hello",
    "timestamp": "2024-08-21T12:00:00.000Z"
  }
]
```

### POST /api/chat

Creates a new chat message.

**Request Body:**

```json
{
  "user_id": "12345",
  "message": "Hello"
}
```

**Response:**

```json
{
  "id": 1,
  "user_id": "12345",
  "message": "Hello",
  "timestamp": "2024-08-21T12:00:00.000Z"
}
```

### PUT /api/chat/<message_id>

Updates a chat message.

**Request Body:**

```json
{
  "message": "Hello, world!"
}
```

**Response:**

```json
{
  "id": 1,
  "user_id": "12345",
  "message": "Hello, world!",
  "timestamp": "2024-08-21T12:00:00.000Z"
}
```