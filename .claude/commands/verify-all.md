Run a full verification of the Smart Price project.

Check all components:

1. **Backend health**: `curl -s http://localhost:8000/api/v1/health`
2. **Frontend build**: `cd frontend && npm run build`
3. **Backend tests**: `cd backend && python -m pytest tests/ -v --tb=short`
4. **Search SSE test (BY)**: `curl -s "http://localhost:8000/api/v1/live-search/stream?q=iPhone+16&region=BY"` — verify Onliner returns results
5. **Search SSE test (RU)**: `curl -s "http://localhost:8000/api/v1/live-search/stream?q=iPhone+16&region=RU"` — check Yandex/WB
6. **Parsers endpoint**: `curl -s http://localhost:8000/api/v1/parsers` — list registered marketplaces
7. **Frontend accessible**: `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/`

Report results with ✅/❌ for each check.
