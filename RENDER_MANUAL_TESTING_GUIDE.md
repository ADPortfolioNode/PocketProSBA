# PocketPro:SBA Manual Testing Guide for Render.com

This guide provides detailed steps for manually testing specific features of PocketPro:SBA after deployment to Render.com.

## Prerequisites

- PocketPro:SBA deployed to Render.com using the provided configuration
- A valid Google Gemini API key configured in the environment variables
- A web browser to access the application
- Sample documents for testing (PDF, TXT, DOCX)

## Testing Health and Status Endpoints

1. **Health Check Endpoint**
   - Access: `https://your-backend-name.onrender.com/health`
   - Expected result: Status 200 with JSON response indicating "healthy"

2. **API Info Endpoint**
   - Access: `https://your-backend-name.onrender.com/api/info`
   - Expected result: JSON response with version, status, and endpoint information

## Testing Core Chat Functionality

1. **Basic Chat**
   - Access the frontend: `https://your-frontend-name.onrender.com`
   - Enter a simple greeting: "Hello, who are you?"
   - Expected result: Bot responds with an introduction to PocketPro:SBA

2. **Question Answering**
   - Ask a business-related question: "What are SBA loans?"
   - Expected result: Bot responds with information about SBA loans

3. **Follow-up Questions**
   - Ask a follow-up: "What are the eligibility requirements?"
   - Expected result: Bot maintains context and provides relevant information

## Testing Document Handling

1. **Document Upload**
   - Use the upload button/interface
   - Select a small PDF or TXT file (<1MB)
   - Expected result: Success message, document appears in the list

2. **Document Querying**
   - Ask a question about the uploaded document
   - Expected result: Response incorporates information from the document

3. **Error Handling**
   - Try uploading an unsupported file format
   - Expected result: Appropriate error message without crashing

## Testing Fallback Mechanisms

1. **Vector Store Fallback**
   - Upload a document and ask a question
   - Check backend logs (in Render dashboard)
   - Expected result: If ChromaDB is unavailable, logs should show fallback to SimpleVectorStore

2. **Graceful Degradation**
   - Try complex queries that might require unavailable dependencies
   - Expected result: Simplified but functional responses

## Performance Testing

1. **Cold Start**
   - Wait for the application to go idle (15+ minutes on free tier)
   - Access the application again
   - Measure time to first response
   - Expected result: Application should start within 30-60 seconds

2. **Concurrent Users**
   - Open multiple browser tabs with the application
   - Send requests simultaneously
   - Expected result: All requests should be handled, though performance may degrade

## User Experience Testing

1. **Mobile Responsiveness**
   - Access the application from a mobile device or use browser dev tools to simulate
   - Test chat, document upload, and navigation
   - Expected result: Interface should be usable on small screens

2. **Error Messages**
   - Intentionally trigger errors (bad queries, upload failures)
   - Expected result: User-friendly error messages, not technical errors

## Security Testing

1. **API Key Protection**
   - Check browser dev tools Network tab
   - Expected result: API key should not be visible in any requests

2. **Input Validation**
   - Try entering potentially harmful inputs (very long text, code snippets, etc.)
   - Expected result: Proper handling without security issues

## Troubleshooting Guide

### Issue: Backend Service Fails to Start
- Check build logs for compilation errors
- Verify environment variables are set correctly
- Try rebuilding with manual deployment instead of Blueprint

### Issue: Frontend Cannot Connect to Backend
- Check CORS settings
- Verify REACT_APP_BACKEND_URL is set correctly
- Check network requests in browser dev tools

### Issue: Document Upload Fails
- Check storage permissions
- Verify upload directory exists
- Check file size limits

### Issue: Chat Not Responding
- Verify Gemini API key is valid
- Check WebSocket connections
- Look for errors in browser console

## Reporting Issues

When reporting issues, please include:
1. Specific error messages
2. Steps to reproduce
3. URL of the affected service
4. Screenshots if available
5. Relevant logs from the Render dashboard
