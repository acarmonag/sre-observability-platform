.PHONY: up down logs chaos-memory chaos-latency chaos-errors chaos-cpu chaos-reset \
        chaos-status load-test clean build ps health

APP_URL ?= http://localhost:8000

## ── Lifecycle ────────────────────────────────────────────────────────────────

up:
	@echo "Starting SRE Observability Platform..."
	docker compose up -d --build
	@echo ""
	@echo "Services available at:"
	@echo "  App:        http://localhost:8000"
	@echo "  App docs:   http://localhost:8000/docs"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3000  (admin/admin)"
	@echo "  Jaeger:     http://localhost:16686"
	@echo "  Loki:       http://localhost:3100"

down:
	docker compose down

clean:
	@echo "Removing all containers and volumes (destructive!)"
	docker compose down -v --remove-orphans
	docker image rm sre-observability-platform-app 2>/dev/null || true

build:
	docker compose build --no-cache

ps:
	docker compose ps

logs:
	docker compose logs -f app

logs-all:
	docker compose logs -f

## ── Health checks ────────────────────────────────────────────────────────────

health:
	@echo "Checking service health..."
	@echo "App:"; curl -sf $(APP_URL)/health | python3 -m json.tool || echo "  UNREACHABLE"
	@echo "Chaos status:"; curl -sf $(APP_URL)/chaos/status | python3 -m json.tool || echo "  UNREACHABLE"

## ── Chaos Engineering ────────────────────────────────────────────────────────

chaos-memory:
	@echo "Triggering memory leak simulation..."
	curl -sf -X POST $(APP_URL)/chaos/memory-leak | python3 -m json.tool

chaos-latency:
	@echo "Triggering latency spike (60s)..."
	curl -sf -X POST "$(APP_URL)/chaos/latency-spike?duration_seconds=60" | python3 -m json.tool

chaos-errors:
	@echo "Triggering 50% error rate (60s)..."
	curl -sf -X POST "$(APP_URL)/chaos/error-rate?duration_seconds=60" | python3 -m json.tool

chaos-cpu:
	@echo "Triggering CPU spike (30s)..."
	curl -sf -X POST "$(APP_URL)/chaos/cpu-spike?duration_seconds=30" | python3 -m json.tool

chaos-reset:
	@echo "Resetting all chaos modes..."
	curl -sf -X DELETE $(APP_URL)/chaos/reset | python3 -m json.tool

chaos-status:
	@echo "Current chaos status:"
	curl -sf $(APP_URL)/chaos/status | python3 -m json.tool

## ── Load Testing ─────────────────────────────────────────────────────────────

load-test:
	@echo "Running load test against all endpoints (Ctrl+C to stop)..."
	@echo "Sending ~2 req/s to each endpoint for 60 seconds..."
	@for i in $$(seq 1 120); do \
		curl -sf $(APP_URL)/orders > /dev/null & \
		curl -sf $(APP_URL)/products > /dev/null & \
		curl -sf $(APP_URL)/health > /dev/null & \
		curl -sf -X POST $(APP_URL)/orders \
			-H "Content-Type: application/json" \
			-d '{"customer_id":"load-test-user","items":[{"product_id":"prod-0001","quantity":1,"unit_price":1299.99}]}' \
			> /dev/null & \
		sleep 0.5; \
	done; wait
	@echo "Load test complete."

load-test-chaos:
	@echo "Running load test with all chaos modes enabled..."
	$(MAKE) chaos-memory
	$(MAKE) chaos-errors
	$(MAKE) chaos-latency
	$(MAKE) load-test
	$(MAKE) chaos-reset
