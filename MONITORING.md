Local monitoring stack (Prometheus + Grafana)

Quick start

1. Ensure `prometheus.yml` exists at the repository root (already present).
2. Start the stack with Docker Compose:

```bash
docker compose up -d
```

3. Open Prometheus: http://localhost:9090
   - Check Targets: http://localhost:9090/targets (job: todo-app-local)
4. Open Grafana: http://localhost:3000 (admin/admin)
   - The Prometheus data source is auto-provisioned and the "To-Do App Overview" dashboard is auto-imported.

Notes
- If Prometheus can't reach your Flask app when running in Docker, use `host.docker.internal:5001` (macOS/Windows). If running Prometheus on the host, change `prometheus.yml` to target `127.0.0.1:5001`.
- To stop: `docker compose down`
