# SRE Observability Platform

A production-grade FastAPI microservice with full **LGTM stack** observability and built-in **chaos engineering** endpoints. Designed as an SRE training environment where you can observe the effects of real failure modes — memory leaks, latency spikes, error injection, and CPU saturation — in a complete observability system.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SRE Observability Platform                   │
│                                                                     │
│  ┌──────────────┐  metrics   ┌─────────────────┐                   │
│  │   FastAPI    │ ─────────► │   Prometheus    │                   │
│  │   app:8000   │            │   :9090         │                   │
│  │              │  traces    └────────┬────────┘                   │
│  │  /orders     │ ─────────► ┌────────▼────────┐  dashboards      │
│  │  /products   │            │     Grafana      │ ◄──────────      │
│  │  /chaos/*    │  logs      │     :3000        │                   │
│  │  /health     │ ─────────► └────────┬────────┘                   │
│  │  /metrics    │  (stdout)           │ queries                    │
│  └──────┬───────┘            ┌────────▼────────┐                   │
│         │                    │      Loki        │                   │
│         │ OTLP gRPC          │      :3100       │                   │
│         │                    └─────────────────┘                   │
│         ▼                    ┌─────────────────┐                   │
│  ┌──────────────┐            │    Promtail     │                   │
│  │    Jaeger    │            │  (log shipper)  │                   │
│  │  UI: :16686  │            │  /var/lib/      │                   │
│  │  OTLP: :4317 │            │  docker/        │                   │
│  └──────────────┘            │  containers     │                   │
│                              └─────────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘

Data flows:
  Metrics:  app → Prometheus (scrape /metrics every 15s) → Grafana
  Logs:     app stdout → Docker → Promtail → Loki → Grafana
  Traces:   app → Jaeger (OTLP gRPC :4317) → Jaeger UI / Grafana
```

---

## Quickstart

```bash
git clone <repo-url> sre-observability-platform
cd sre-observability-platform

# Start everything
make up

# Or directly:
docker compose up -d --build
```

Wait ~20 seconds for all services to become healthy, then open:

| Service    | URL                        | Credentials     |
|------------|----------------------------|-----------------|
| App API    | http://localhost:8000/docs | —               |
| Grafana    | http://localhost:3000      | admin / admin   |
| Prometheus | http://localhost:9090      | —               |
| Jaeger UI  | http://localhost:16686     | —               |
| Loki       | http://localhost:3100      | —               |

---

## Endpoints

### Business API

| Method | Endpoint           | Description               | Latency       |
|--------|--------------------|---------------------------|---------------|
| GET    | /health            | Health check + uptime     | <5ms          |
| GET    | /metrics           | Prometheus metrics        | <5ms          |
| GET    | /orders            | List all orders           | 50–200ms      |
| POST   | /orders            | Create new order          | 100–300ms     |
| GET    | /orders/{id}       | Get order by ID           | 20–100ms      |
| GET    | /products          | List product catalog      | 30–150ms      |
| GET    | /products/{id}     | Get product by ID         | 10–50ms       |

### Chaos Engineering

| Method | Endpoint                  | Effect                                   |
|--------|---------------------------|------------------------------------------|
| POST   | /chaos/memory-leak        | Allocates ~1MB/2s until reset            |
| POST   | /chaos/latency-spike      | Adds 2–5s random latency for 60s         |
| POST   | /chaos/error-rate         | 50% of /orders return HTTP 500 for 60s   |
| POST   | /chaos/cpu-spike          | CPU-intensive loop for 30s               |
| DELETE | /chaos/reset              | Stops all active chaos modes             |
| GET    | /chaos/status             | Shows which modes are active             |

---

## Chaos Engineering

Each chaos mode injects a different real-world failure pattern. Use these to:
- Verify your alerts fire correctly
- See how observability data changes under failure
- Train incident response

### Trigger examples

```bash
# Memory leak — watch memory_usage_bytes climb in Grafana
make chaos-memory
# or: curl -X POST http://localhost:8000/chaos/memory-leak

# Latency spike — watch p99 latency spike on the dashboard
make chaos-latency
# or: curl -X POST "http://localhost:8000/chaos/latency-spike?duration_seconds=60"

# Error rate — watch error rate % alert fire
make chaos-errors
# or: curl -X POST "http://localhost:8000/chaos/error-rate?duration_seconds=60"

# CPU spike — watch process CPU usage surge
make chaos-cpu
# or: curl -X POST "http://localhost:8000/chaos/cpu-spike?duration_seconds=30"

# Reset everything
make chaos-reset
# or: curl -X DELETE http://localhost:8000/chaos/reset

# Check current status
make chaos-status
# or: curl http://localhost:8000/chaos/status
```

### Run a load test + chaos simultaneously

```bash
# In one terminal:
make load-test-chaos

# In another, watch in Grafana: http://localhost:3000
```

---

## Grafana Dashboards

Three pre-built dashboards are provisioned automatically at startup.

### 1. SRE Golden Signals (`/d/sre-golden-signals`)

The canonical SRE dashboard — shows all four Google SRE golden signals:

- **Traffic** — requests/second by endpoint (time series)
- **Errors** — error rate % with 5% threshold line (time series)
- **Latency** — p50 / p95 / p99 latency side by side (time series)
- **Saturation** — memory RSS usage (time series)
- **Requests by endpoint** — horizontal bar chart
- **Status code distribution** — donut pie chart
- **Active chaos modes** — stat panels (red = active)
- **Chaos history** — when each mode was active (time series)

### 2. Application Logs (`/d/sre-logs`)

- **All app logs** — full JSON log stream from Loki
- **Errors & Warnings** — filtered to WARNING/ERROR level
- **Log rate by level** — INFO / WARNING / ERROR rates over time
- **HTTP status distribution** — 2xx / 4xx / 5xx rates from log data

### 3. Trace Analysis (`/d/sre-traces`)

- **Latency heatmap** — request duration distribution over time
- **p99 latency by endpoint** — horizontal bar chart, sorted by slowest
- **Slowest endpoints table** — p50 / p95 / p99 per endpoint
- **Duration histogram** — bucket distribution for the last 5 minutes
- **Link to Jaeger UI** — for full trace waterfall exploration

---

## Alerting

Alerts are defined in `prometheus/alerts.yml` and fire into Grafana.

| Alert               | Condition                              | Severity | Action                             |
|---------------------|----------------------------------------|----------|------------------------------------|
| HighErrorRate       | Error rate > 5% for 2 minutes          | warning  | Check /chaos/status, check logs    |
| HighLatency         | p99 > 2s for 2 minutes                 | warning  | Check latency-spike chaos mode     |
| MemoryLeakDetected  | Memory grew >50MB in 5 minutes         | critical | Check memory-leak chaos mode       |
| ChaosModeActive     | Any chaos gauge > 0                    | info     | Informational — chaos is running   |
| ServiceDown         | app target unreachable for 1 minute    | critical | Check container status             |

View firing alerts at: http://localhost:9090/alerts

---

## Environment Variables

| Variable         | Default                   | Description                          |
|------------------|---------------------------|--------------------------------------|
| JAEGER_ENDPOINT  | http://jaeger:4317        | OTLP gRPC endpoint for trace export  |
| LOG_LEVEL        | INFO                      | Python logging level                 |
| APP_ENV          | development               | Environment tag on OTel resource     |

---

## Observability Metrics Reference

| Metric                              | Type      | Labels                           |
|-------------------------------------|-----------|----------------------------------|
| http_requests_total                 | counter   | method, endpoint, status_code    |
| http_request_duration_seconds       | histogram | method, endpoint                 |
| active_chaos_modes                  | gauge     | mode                             |
| memory_usage_bytes                  | gauge     | —                                |
| orders_created_total                | counter   | —                                |
| orders_processed_total              | counter   | —                                |

---

## Extending the Platform

### Add a new metric

```python
# In app/middleware/metrics.py
from prometheus_client import Counter
my_metric = Counter("my_metric_total", "Description", ["label1"])

# Use it in a router
my_metric.labels(label1="value").inc()
```

### Add a new chaos mode

1. Add state fields to `ChaosState` in `app/services/chaos_service.py`
2. Add activation method to `ChaosService`
3. Add endpoint to `app/routers/chaos.py`
4. Add gauge label to `app/middleware/metrics.py`

### Add a new dashboard

1. Create `grafana/provisioning/dashboards/my-dashboard.json`
2. `docker compose restart grafana` — it auto-provisions on startup

### Query tips

```promql
# Error rate over last 5 minutes
sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# p99 latency per endpoint
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))

# Memory growth rate
rate(memory_usage_bytes[5m])
```

---

## Makefile Targets

```
make up              Start all services (builds app image)
make down            Stop all services
make clean           Stop + remove all volumes (destructive)
make build           Rebuild app image from scratch
make logs            Follow app container logs
make logs-all        Follow all service logs
make health          Check app health + chaos status
make chaos-memory    Trigger memory leak
make chaos-latency   Trigger latency spike (60s)
make chaos-errors    Trigger 50% error rate (60s)
make chaos-cpu       Trigger CPU spike (30s)
make chaos-reset     Reset all chaos modes
make chaos-status    Show active chaos modes
make load-test       Send sustained load to all endpoints
make load-test-chaos Run load test with all chaos modes enabled
```
