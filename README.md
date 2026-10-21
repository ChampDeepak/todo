# Taskr — DevOps Capstone

A three-tier task tracker, built as the vehicle for a full DevOps pipeline:
containerised, tested in CI, scanned for vulnerabilities, provisioned with
Terraform, deployed to Kubernetes with Helm, and monitored with Prometheus and
Grafana.

## Demo walkthrough

https://github.com/user-attachments/assets/aa0b1660-b766-4a36-83b9-467120cefbce

Narrated, with subtitles burned in. One code change followed end to end: commit
and push, the CI pipeline with tests and a Trivy scan that blocks on HIGH or
CRITICAL findings, a Helm rollout across two replicas, a rollback, the Prometheus
and Grafana dashboards showing live request rate and latency, and finally
`terraform destroy` tearing the AWS environment down — fifteen resources
destroyed, then fifteen to add against the empty state, which is the proof it
rebuilds from this repository alone.

The player above is a downscaled copy that fits GitHub's upload limit. The
full-quality file is [`docs/screenshots/m10-demo.mp4`](docs/screenshots/m10-demo.mp4)
(7:45, 1920×1248), and the transcript is in [`captions.srt`](captions.srt).

---

**Repository:** <https://github.com/ChampDeepak/todo>
**CI pipeline:** <https://github.com/ChampDeepak/todo/actions>
**Latest green run:** <https://github.com/ChampDeepak/todo/actions/runs/38970270985>
**Presentation:** [docs/slides/slides.pdf](docs/slides/slides.pdf) — 10 slides
**Submission evidence:** [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md)

---

## What the application does

Taskr tracks tasks through a lifecycle. You can create a task with a title,
description, priority and due date; move it between `todo`, `in_progress` and
`done`; filter and search the list; and see live statistics including how many
tasks are overdue and what share of them are complete.

### Feature scope

- Create, view, edit and delete tasks
- Mark a task complete in one action
- Filter by status and priority, search by title
- Task priority (`low` / `medium` / `high`) and due dates
- Live statistics: totals per status, overdue count, completion rate
- Responsive UI

### API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness. Never touches the database. |
| `GET` | `/health/ready` | Readiness. Returns 503 while the database is unreachable. |
| `GET` | `/metrics` | Prometheus metrics. |
| `GET` | `/api/tasks` | List, with `status`, `priority`, `search`, `limit`, `offset`. |
| `GET` | `/api/tasks/stats` | Aggregate counts, computed in the database. |
| `GET` | `/api/tasks/{id}` | One task, 404 if absent. |
| `POST` | `/api/tasks` | Create. 201 on success, 422 on invalid input. |
| `PUT` | `/api/tasks/{id}` | Partial update; omitted fields are left alone. |
| `PATCH` | `/api/tasks/{id}/complete` | Mark done. |
| `DELETE` | `/api/tasks/{id}` | Delete. 204 on success. |

---

## Architecture

```
                 ┌──────────────┐
  browser  ──────▶   Ingress    │   (nginx-ingress in k8s / nginx in compose)
                 └──────┬───────┘
                   /    │    \_____ /api, /health
                  /     │           \
          ┌──────▼────┐ │      ┌─────▼──────┐      ┌────────────┐
          │ frontend  │ │      │  backend   │─────▶│ PostgreSQL │
          │ React+Vite│ │      │  FastAPI   │      │            │
          │  → nginx  │ │      │  uvicorn   │      └────────────┘
          └───────────┘ │      └─────┬──────┘
                        │            │ /metrics
                        │      ┌─────▼──────┐      ┌────────────┐
                        │      │ Prometheus │─────▶│  Grafana   │
                        │      └────────────┘      └────────────┘
```

Three processes, not one. The frontend, the API and the database scale,
deploy and fail independently.

**The frontend never knows the backend's address.** It calls `/api/...` as a
relative path, and whatever serves the frontend proxies that prefix onward:
Vite in development, nginx in the container image, the Kubernetes Ingress in
the cluster. Browser configuration is baked in at build time, so a hardcoded
API URL would mean rebuilding the image per environment and would break "build
once, promote the same artifact".

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, served by nginx |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, uvicorn |
| Database | PostgreSQL 16, schema managed by Alembic |
| Containers | Docker, multi-stage build, non-root |
| CI/CD | GitHub Actions → GitHub Container Registry |
| Security | Trivy, failing on HIGH/CRITICAL |
| Infrastructure | Terraform → AWS VPC + EKS |
| Orchestration | Kubernetes, Helm |
| Observability | Prometheus, Grafana |

---

## Running it

### Everything, with one command

```bash
docker compose up --build
```

Then open <http://localhost:3000>.

Host ports are 3000 (frontend), 8001 (API) and 5433 (Postgres). The two
non-obvious ones avoid a clash with another project on the development
machine; inside the compose network the services always reach each other on
their real ports via service names (`db:5432`, `backend:8000`).

### Backend alone, for development

```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8001
```

### Tests

```bash
cd backend && .venv/bin/pytest -v
```

32 tests. They need a PostgreSQL reachable at `localhost:5433` — the compose
stack provides it. The suite creates its own throwaway database, runs every
test inside a transaction, and rolls it back, so tests cannot leak state into
each other regardless of execution order.

### Kubernetes, locally

```bash
kind create cluster --config k8s/kind-cluster.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.3/deploy/static/provider/kind/deploy.yaml
kind load docker-image todo-backend:latest todo-frontend:latest --name taskr
kubectl apply -f k8s/namespace.yaml
helm upgrade --install taskr ./helm --namespace taskr --wait
```

Then open <http://localhost:8080>.

### Monitoring

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values monitoring/kube-prometheus-stack-values.yaml
kubectl apply -f monitoring/servicemonitor.yaml
```

- Prometheus: <http://prometheus.localtest.me:8080>
- Grafana: <http://grafana.localtest.me:8080> (`admin` / `admin`)

### AWS infrastructure

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
# ... and when finished, ALWAYS:
terraform destroy
```

---

## The pipeline

Every push to `main` runs:

```
   test (ruff + pytest, real Postgres)  ─┐
                                         ├─▶  build → Trivy scan → push to GHCR
   build-frontend (npm ci + vite build) ─┘          (per image, in parallel)
```

Gates run cheapest-first. Tests take seconds; building and publishing two
images takes minutes. A failure in either gate means no image is built at all.

### Image tags are commit SHAs, never `latest`

```
ghcr.io/champdeepak/todo-backend:sha-d1fb04cebfcafba6ca0a9e52761b7363062d98a2
ghcr.io/champdeepak/todo-frontend:sha-d1fb04cebfcafba6ca0a9e52761b7363062d98a2
```

`latest` is a mutable label: two machines pulling it can be running different
code, and there is no previous `latest` to roll back to. With a SHA tag the
commit, the CI run, the image and the running pod all carry one identifier.
Deploying is `--set backend.image.tag=<sha>`; rolling back is the same command
with the previous SHA.

---

## Security scanning (Trivy)

Trivy scans the OS packages and application libraries inside each built image.
It runs **before** the push, so a failing image is never published. A HIGH or
CRITICAL finding **with an available fix** fails the job; unfixable findings
are reported but do not block, because a finding nobody can act on only
teaches people to switch the scanner off.

**What it found, and what we did.** On the backend image (`python:3.12-slim`)
Trivy reported no HIGH or CRITICAL vulnerability with an available fix. On the
frontend it reported **43 findings — 41 HIGH and 2 CRITICAL** — nearly all in
OpenSSL, because the base image `nginx:1.27-alpine` is built on Alpine 3.21 and
ships OpenSSL 3.3.3. The most serious was **CVE-2026-31789**, a CRITICAL heap
buffer overflow in OpenSSL, fixed upstream in 3.3.7. The pipeline blocked the
push. We moved the base image to `nginx:1.29-alpine` (Alpine 3.23, OpenSSL
3.5.6) and added `apk upgrade`, and the scan passed.

The lesson worth keeping: **the vulnerability was not in code we wrote.** It
was in a base image that had aged since it was published. That is the normal
case, and it is why the scan runs on every build rather than once at review.

---

## Repository layout

| Path | Contents |
|---|---|
| `backend/app/` | FastAPI application: config, database, models, schemas, routes |
| `backend/alembic/` | Database migrations |
| `backend/tests/` | 32 pytest tests against a real PostgreSQL |
| `frontend/` | React + Vite source, `nginx.conf`, multi-stage `Dockerfile` |
| `.github/workflows/` | CI pipeline |
| `terraform/` | AWS VPC and EKS cluster |
| `k8s/` | Namespace and the kind cluster definition |
| `helm/` | Helm chart: deployments, services, ingress, secret |
| `monitoring/` | Prometheus/Grafana values and the ServiceMonitor |
| `docs/` | Screenshot tracker and submission evidence |

---

## Deliberate shortcuts

Every one of these is a conscious trade, not an oversight.

| Shortcut | Why | What production would do |
|---|---|---|
| Terraform state is local | An S3 + DynamoDB backend costs setup time | Remote backend, so state is shared and applies serialise |
| EKS nodes in public subnets | A NAT Gateway costs ~$32/month and minutes per apply | Private subnets, NAT for egress, load balancers only in public |
| PostgreSQL runs in the cluster | Simpler to demonstrate | Amazon RDS — backups, failover and patching become someone else's full-time job |
| Migrations run in the app entrypoint | One less moving part | A separate migration Job that must complete before the Deployment rolls, so N replicas do not race |
| Database password in `values.yaml` | Demo only | External Secrets Operator or AWS Secrets Manager |
| `apk upgrade` in the Dockerfile | Patches packages fixed after the base image was built | Same, plus automated base image bumps (Renovate/Dependabot) |
| Grafana password is `admin` | Demo only | SSO, or a generated secret |

---

## Things verified, not assumed

- 32 tests pass against real PostgreSQL, and pass with a deliberately broken
  `DATABASE_URL`, proving the suite is genuinely isolated from it.
- `docker compose up --build` starts all three services healthy; the API was
  exercised end to end through the nginx proxy (201 on create, data read back).
- Both container images run as non-root — verified with `id` inside the running
  containers (`uid=1001`, `uid=101`), not inferred from the Dockerfile.
- The frontend image contains no Node binary — verified with `which node`.
- `terraform init`, `validate` and `fmt` all pass.
- Five pods Running in Kubernetes with replicas spread across two worker nodes;
  the app was exercised through the Ingress on port 8080.
