# RENDER.COM DEPLOYMENT STRATEGY
# Rust Compilation Issue Workaround

## PROBLEM IDENTIFIED:
Render.com build failing due to Rust compilation errors when installing chromadb.
Error: "Read-only file system (os error 30)" - maturin/cargo build fails.

## SOLUTION: MINIMAL DEPLOYMENT APPROACH

### Phase 1: Get Core App Running (Current Focus)
✅ Use requirements-render-minimal.txt
✅ Excludes packages that require Rust compilation:
   - chromadb (temporarily removed)
   - sentence-transformers (heavy dependency)

### Phase 2: Add ChromaDB Later (Future Enhancement)
- Once core app is deployed and stable
- Explore alternatives:
  1. Use Render.com's native PostgreSQL with pgvector
  2. Use external ChromaDB service
  3. Try different vector database (Pinecone, Weaviate)

## FILES UPDATED:
📝 requirements-render-minimal.txt - Created minimal dependency list
📝 render.yaml - Updated to use minimal requirements

## APP BEHAVIOR WITH MINIMAL SETUP:
✅ Flask API will start successfully
✅ Health endpoints will work
✅ Basic LLM functionality will work (Google Gemini)
✅ Document upload endpoints exist but ChromaDB operations return graceful errors
✅ App logs will show "ChromaDB not available - skipping..." for vector operations

## BENEFITS:
- App deploys successfully on Render.com
- Core functionality works
- No Rust compilation issues
- Can add vector database functionality later
- Faster builds and deployments

## NEXT STEPS:
1. Deploy with minimal requirements
2. Verify basic functionality
3. Gradually add more features once stable
