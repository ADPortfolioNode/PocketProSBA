PocketPro SBA — RAG vector store notes

VECTOR_STORE
- Controls which vector store is used by the application.
- Default: `chromadb` (set via `VECTOR_STORE` environment variable).
- Options:
  - `chromadb` — connect to an external Chromadb instance (requires `chromadb` package or the REST server).
  - `memory` — use the local in-memory `SimpleVectorStore` fallback (works without extra packages).

Chromadb configuration
- CHROMADB_URL: optional; if provided, used to connect to a chromadb REST instance.
- CHROMADB_COLLECTION: optional; collection name to use (defaults to `pocketpro_documents`).

Dev / optional dependencies
- To enable Prometheus monitoring and Chromadb support install:

```bash
pip install -r requirements-dev.txt
```

Smoke tests (quick local checks)
- Run a small smoke test that imports the Flask app and calls endpoints via the test client:

```bash
python -c "import os; os.environ['VECTOR_STORE']='memory'; import importlib; import app; importlib.reload(app); from app import app; client = app.test_client(); print(client.get('/').get_json())"
```

- Or run the pytest unit tests for `SimpleVectorStore`:

```bash
pip install pytest
pytest -q
```

Running the app locally
- Development (memory store):

```bash
export VECTOR_STORE=memory
python app.py
```

- Production with Chromadb (if installed and configured):

```bash
export VECTOR_STORE=chromadb
export CHROMADB_URL=http://localhost:8000
python app.py
```

Notes
- The app tolerates missing optional packages (prometheus_client, chromadb). When absent, monitoring is disabled and Chromadb will fall back to `memory`.
- The file `app.py` contains a `SimpleVectorStore` implementation for quick tests and an optional `ChromadbService` wrapper for production-like setups.
