# Faultline

Faultline is an error-tracking and observability service for client and server applications. It ingests exception traces, groups recurring failures via deterministic fingerprinting, and provides automated root-cause analysis and patch proposals using Claude 3.5 Sonnet.

## Architecture

```mermaid
flowchart TD
    subgraph Client
        APP["Application Code"]
        SDK["Python SDK (faultline)"]
        APP -->|Exception| SDK
    end

    subgraph Ingestion
        SDK -->|"POST /api/v1/capture"| API["FastAPI Ingestion API"]
        CACHE[("Redis Key Cache")] <--> API
        API -->|"Queue Push"| QUEUE[("Redis Stream / Queue")]
        API -->|"202 Accepted"| SDK
    end

    subgraph Worker Pool
        QUEUE -->|"Batch Fetch"| WORKER["Ingestion Worker"]
        NORM["Fingerprint Normalizer"] <--> WORKER
        LLM["Claude Analysis Engine"] <--> WORKER
    end

    subgraph Persistence
        WORKER -->|"Bulk Insert"| DB[("PostgreSQL")]
        WORKER -->|"Event Broadcast"| WS["WebSocket Manager"]
    end

    subgraph Dashboard
        WS -->|"Live Feed"| UI["React Dashboard"]
        DB -->|"REST Queries"| UI
    end
```

## System Components

- Ingestion API: Asynchronous FastAPI service terminating inbound telemetry over HTTP. API keys are cached in Redis to minimize database read overhead. Validated payloads are enqueued to a Redis queue for processing.
- Clustering Engine: Normalizes stack traces by removing memory addresses, UUIDs, and timestamps, producing a canonical SHA-256 fingerprint for error deduplication.
- Analysis Engine: Queries the Claude 3.5 Sonnet API to extract the root cause, identify vulnerable lines, and format a unified remediation diff. When an API key is not present, a rule-based evaluation engine provides baseline diagnostics.
- PostgreSQL Storage: Stores projects, error groups (incidents), and raw event records. The events table schema supports range partitioning by date.
- Python SDK: Background worker thread with an unbounded queue that batches telemetry payloads without blocking the main runtime thread. Registers standard exception hooks and atexit cleanup handlers.
- Dashboard: React and Tailwind CSS application providing incident inspection, stack frame folding, breadcrumb timelines, and live WebSocket telemetry feeds.

## Project Structure

```
faultline/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Capture, Incidents, Projects, Analytics endpoints
│   │   ├── models/          # SQLAlchemy entity models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── services/        # Clustering, AI analysis, caching, queue, storage
│   │   ├── config.py        # Environment settings
│   │   ├── database.py      # Database session and connection setup
│   │   ├── main.py          # FastAPI application entrypoint
│   │   └── worker.py        # Asynchronous batch processing worker
│   ├── tests/               # Unit and integration test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── schema.sql           # PostgreSQL table definitions with partitioning
├── sdk/
│   └── python/
│       ├── faultline/       # SDK client, transport, decorators, breadcrumbs
│       ├── pyproject.toml
│       └── setup.py
├── frontend/
│   ├── src/
│   │   ├── components/      # UI components (stack trace viewer, metrics, charts)
│   │   ├── pages/           # Dashboard views
│   │   └── api/             # API client and WebSocket handler
│   ├── Dockerfile
│   └── vite.config.js
├── examples/
│   ├── simulate_traffic.py  # Telemetry load generator
│   └── demo_payment_service.py # Example FastAPI service integration
├── deploy/
│   ├── nginx.conf           # Reverse proxy configuration
│   ├── render.yaml          # Render deployment manifest
│   ├── ec2_setup.sh         # Ubuntu EC2 installation script
│   └── faultline.service    # Systemd unit file
└── docker-compose.yml
```

## Local Development Setup

### Docker Compose

```bash
docker compose up -d --build
```

Services:
- Frontend Dashboard: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### Standalone Mode

The backend automatically uses SQLite and an in-memory queue fallback when PostgreSQL and Redis instances are unreachable:

```bash
pip install -r backend/requirements.txt
pip install -e sdk/python
uvicorn backend.app.main:app --port 8000
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Dashboard is served at `http://localhost:5173`.

## Test Execution

Run the backend test suite:

```bash
python -m pytest backend/tests -v
```

## SDK Usage

```python
import faultline

faultline.init(
    api_key="fl_live_production_demo_key_99",
    endpoint="http://localhost:8000",
    environment="production",
    release="v1.0.0"
)

faultline.add_breadcrumb("Order verification", category="checkout")

@faultline.capture_exceptions(tags={"service": "checkout"})
def process_order(order_id: str):
    pass

try:
    charge_customer()
except Exception as exc:
    faultline.capture_exception(exc, tags={"criticality": "high"})
```

## Environment Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/faultline` |
| `REDIS_URL` | Redis server connection string | `redis://localhost:6379/0` |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude 3.5 Sonnet analysis | None (uses heuristic fallback) |
| `CLAUDE_MODEL` | Model identifier | `claude-3-5-sonnet-20241022` |
| `INGESTION_BATCH_SIZE`| Queue batch fetch size | `50` |
| `INGESTION_FLUSH_INTERVAL_MS` | Ingestion poll interval in ms | `200` |

## License

MIT
