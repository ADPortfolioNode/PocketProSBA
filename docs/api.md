# API Reference

This document provides a reference for the backend API endpoints.

## Base URL

The base URL for the API is `/api`.

## Endpoints

### 1. GET /api/info

Retrieves system information about the PocketPro SBA service.

- **Method:** `GET`
- **Description:** Returns the service name, version, and status.
- **Response:**

```json
{
  "service": "PocketPro SBA",
  "version": "1.0.0",
  "status": "running"
}
```

### 2. POST /api/decompose

Decomposes a user task into actionable steps.

- **Method:** `POST`
- **Description:** Takes a user message and an optional session ID, and returns a decomposed task.
- **Request Body:**

```json
{
  "message": "string",
  "session_id": "string" (optional)
}
```

- **Response:**

```json
{
  "response": "string"
}
```

### 3. POST /api/execute

Executes a decomposed task step.

- **Method:** `POST`
- **Description:** Takes a task object and executes the specified step.
- **Request Body:**

```json
{
  "task": { /* object representing the task step */ }
}
```

- **Response:**

```json
{
  "result": { /* object representing the result of the execution */ }
}
```

### 4. POST /api/validate

Validates the result of a task step.

- **Method:** `POST`
- **Description:** Takes a result and a task object, and returns a validation status.
- **Request Body:**

```json
{
  "result": "string",
  "task": { /* object representing the task step */ }
}
```

- **Response:**

```json
{
  "validation": "string"
}
```

### 5. POST /api/query

Queries documents based on a given query.

- **Method:** `POST`
- **Description:** Searches for relevant documents based on the query and returns the top K results.
- **Request Body:**

```json
{
  "query": "string",
  "top_k": "integer" (optional, default: 5, max: 20)
}
```

- **Response:**

```json
{
  "results": [ /* array of document objects */ ]
}
```

### 6. GET /api/chat/

Retrieves all chat messages.

- **Method:** `GET`
- **Description:** Returns a list of all chat messages.
- **Response:**

```json
[
  {
    "id": "integer",
    "user_id": "string",
    "message": "string",
    "timestamp": "string"
  }
]
```

### 7. POST /api/chat/

Creates a new chat message.

- **Method:** `POST`
- **Description:** Adds a new chat message to the system.
- **Request Body:**

```json
{
  "user_id": "string",
  "message": "string"
}
```

- **Response:**

```json
{
  "id": "integer",
  "user_id": "string",
  "message": "string",
  "timestamp": "string"
}
```

### 8. PUT /api/chat/<int:message_id>

Updates an existing chat message.

- **Method:** `PUT`
- **Description:** Updates the content of a specific chat message by its ID.
- **URL Parameters:**
  - `message_id`: The ID of the message to update.
- **Request Body:**

```json
{
  "message": "string"
}
```

- **Response:**

```json
{
  "id": "integer",
  "user_id": "string",
  "message": "string",
  "timestamp": "string"
}
```
