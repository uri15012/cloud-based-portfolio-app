# Stock Portfolio API

A production-ready RESTful API for managing a personal stock portfolio, built with **Spring Boot 3**, **MySQL 8**, and deployed via **Docker** and **Kubernetes**. The project includes a full **CI/CD pipeline** powered by GitHub Actions with automated pytest integration tests on every push to `main`.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Running with Docker Compose](#running-with-docker-compose)
- [Deploying to Kubernetes](#deploying-to-kubernetes)
- [CI/CD Pipeline](#cicd-pipeline)
- [Integration Tests](#integration-tests)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Java 17 |
| Framework | Spring Boot 3.2 |
| Persistence | Spring Data JPA + Hibernate |
| Database | MySQL 8.3 |
| Build Tool | Maven 3.9 |
| Containerisation | Docker (multi-stage build) |
| Orchestration | Kubernetes (Deployment, Service, HPA, PVC) |
| CI/CD | GitHub Actions |
| Integration Tests | Python 3.12 + pytest + requests |

---

## Project Structure

```
stock-portfolio/
│
├── src/main/java/com/portfolio/
│   ├── StockPortfolioApplication.java   # Entry point
│   ├── entity/Stock.java                # JPA entity (symbol, quantity, buyPrice)
│   ├── repository/StockRepository.java  # Spring Data JPA repository
│   ├── service/StockService.java        # Business logic + error handling
│   └── controller/StockController.java  # REST controller — all CRUD endpoints
│
├── src/main/resources/
│   └── application.properties           # Datasource config via env variables
│
├── k8s/
│   ├── configmap.yml                    # Non-sensitive DB config
│   ├── secret.yml                       # Base64-encoded credentials
│   ├── mysql-deployment.yml             # MySQL PVC + Deployment + headless Service
│   ├── app-deployment.yml               # App Deployment + LoadBalancer Service
│   └── hpa.yml                          # HorizontalPodAutoscaler (min 1, max 3)
│
├── tests/
│   ├── test_api.py                      # 16 pytest integration tests
│   └── requirements.txt                 # pytest, requests
│
├── .github/workflows/
│   └── ci.yml                           # GitHub Actions CI/CD pipeline
│
├── Dockerfile                           # Multi-stage build (Maven → JRE)
└── docker-compose.yml                   # Local dev stack (app + MySQL)
```

---

## Architecture

### Local / Docker Compose

```
  Developer Machine
  ┌──────────────────────────────────────────────┐
  │                                              │
  │   docker-compose up --build                  │
  │                                              │
  │   ┌──────────────────┐   depends_on (health) │
  │   │  app container   │ ──────────────────┐   │
  │   │  Spring Boot     │                   │   │
  │   │  :8080           │                   ▼   │
  │   └────────┬─────────┘     ┌─────────────────┤
  │            │ JDBC           │  db container   │
  │            └───────────────▶│  MySQL 8.3      │
  │                             │  :3306          │
  │                             │  mysql_data vol │
  │                             └─────────────────┤
  │                                              │
  │   localhost:8080/api/stocks ◀── curl / client │
  └──────────────────────────────────────────────┘
```

### Kubernetes Cluster

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  Kubernetes Cluster                                             │
  │                                                                 │
  │  ┌──────────────────────────────────────────────────────────┐  │
  │  │  stock-portfolio-service  (LoadBalancer : 80 → 8080)     │  │
  │  └───────────────────────┬──────────────────────────────────┘  │
  │                          │ routes traffic                       │
  │            ┌─────────────▼──────────────┐                      │
  │            │  stock-portfolio-app        │ ◀── HPA (1–3 pods)  │
  │            │  Deployment                 │     CPU  ≥ 70%       │
  │            │                            │     Mem  ≥ 80%       │
  │            │  pod-1  pod-2  pod-3        │                      │
  │            │  Spring Boot :8080          │                      │
  │            └──────────────┬─────────────┘                      │
  │                           │ JDBC (via headless DNS)             │
  │            ┌──────────────▼─────────────┐                      │
  │            │  mysql-service (headless)   │                      │
  │            └──────────────┬─────────────┘                      │
  │                           │                                     │
  │            ┌──────────────▼─────────────┐                      │
  │            │  mysql  Deployment (×1)     │                      │
  │            │  strategy: Recreate         │                      │
  │            │  MySQL 8.3 :3306            │                      │
  │            └──────────────┬─────────────┘                      │
  │                           │ mounts                              │
  │            ┌──────────────▼─────────────┐                      │
  │            │  mysql-pvc  (1 Gi RWO)      │                      │
  │            └────────────────────────────┘                      │
  │                                                                 │
  │  ┌────────────────────┐   ┌──────────────────────────────────┐ │
  │  │  ConfigMap         │   │  Secret                          │ │
  │  │  DB_HOST / PORT    │   │  DB_PASSWORD                     │ │
  │  │  DB_NAME / USER    │   │  MYSQL_ROOT_PASSWORD             │ │
  │  └────────────────────┘   └──────────────────────────────────┘ │
  └─────────────────────────────────────────────────────────────────┘
```

### CI/CD Pipeline

```
  git push → main
       │
       ▼
  ┌─────────────────────────────────────────┐
  │  Job 1: build-and-test                  │
  │                                         │
  │  [MySQL service container]              │
  │        │                                │
  │  1. Checkout code                       │
  │  2. Setup Java 17 (Temurin) + Maven     │
  │  3. mvn package -DskipTests             │
  │  4. java -jar app.jar &  (background)   │
  │  5. Health-check loop (curl, 20 × 3s)   │
  │  6. Setup Python 3.12                   │
  │  7. pip install -r tests/requirements   │
  │  8. pytest tests/ -v ──────────────┐    │
  │                                    │    │
  │     PASS ──────────────────────────┘    │
  │     FAIL → upload app.log artifact      │
  └──────────────────┬──────────────────────┘
                     │ needs (on success only)
                     ▼
  ┌─────────────────────────────────────────┐
  │  Job 2: docker-build                    │
  │                                         │
  │  1. Checkout code                       │
  │  2. Setup Docker Buildx                 │
  │  3. docker build  (GHA layer cache)     │
  │     → cloudbasedportfolioapplication-   │
  │       app:latest                        │
  └─────────────────────────────────────────┘
```

---

## API Endpoints

Base path: `/api/stocks`

| Method | Path | Description | Request Body | Success Response |
|--------|------|-------------|--------------|-----------------|
| `GET` | `/api/stocks` | List all stocks | — | `200 OK` — JSON array |
| `GET` | `/api/stocks/{id}` | Get a stock by ID | — | `200 OK` — stock object |
| `POST` | `/api/stocks` | Add a new stock | `{ symbol, quantity, buyPrice }` | `201 Created` — created object |
| `PUT` | `/api/stocks/{id}` | Update a stock | `{ symbol, quantity, buyPrice }` | `200 OK` — updated object |
| `DELETE` | `/api/stocks/{id}` | Delete a stock | — | `204 No Content` |

**Error responses:** `404 Not Found` when a requested `id` does not exist.

### Example Request & Response

```bash
# Create a stock
curl -X POST http://localhost:8080/api/stocks \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","quantity":10,"buyPrice":175.50}'

# Response — 201 Created
{
  "id": 1,
  "symbol": "AAPL",
  "quantity": 10,
  "buyPrice": 175.50
}
```

---

## Running with Docker Compose

### Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd stock-portfolio

# 2. Build and start both containers
docker compose up --build

# 3. The API is available at:
#    http://localhost:8080/api/stocks

# 4. Stop and remove containers + network
docker compose down

# Remove persisted MySQL data as well
docker compose down -v
```

The `app` container waits for a **MySQL health check** to pass before starting, so the database is always ready before the application connects.

### Environment Variables

All variables have sensible defaults in `docker-compose.yml`. Override them at run-time if needed:

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `db` | MySQL hostname |
| `DB_PORT` | `3306` | MySQL port |
| `DB_NAME` | `portfolio` | Database name |
| `DB_USER` | `root` | Database user |
| `DB_PASSWORD` | `secret` | Database password |

---

## Deploying to Kubernetes

### Prerequisites

- A running Kubernetes cluster (e.g. Docker Desktop, minikube, GKE, EKS)
- `kubectl` configured to point at your cluster
- The Docker image built and available to the cluster

### 1. Build and load the image

```bash
# Build the image
docker build -t cloudbasedportfolioapplication-app:latest .

# If using minikube, load it directly into the cluster
minikube image load cloudbasedportfolioapplication-app:latest
```

### 2. Update credentials (optional)

The default passwords in `k8s/secret.yml` are base64-encoded `secret`. Replace them with your own:

```bash
echo -n 'your-new-password' | base64
# Paste the output into k8s/secret.yml
```

### 3. Apply all manifests

```bash
# Apply in dependency order
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secret.yml
kubectl apply -f k8s/mysql-deployment.yml
kubectl apply -f k8s/app-deployment.yml
kubectl apply -f k8s/hpa.yml

# Or apply the entire folder at once
kubectl apply -f k8s/
```

### 4. Verify the deployment

```bash
# Watch pods come up
kubectl get pods --watch

# Check rollout status
kubectl rollout status deployment/mysql
kubectl rollout status deployment/stock-portfolio-app

# View the assigned LoadBalancer address
kubectl get service stock-portfolio-service
```

### 5. Watch the autoscaler

```bash
kubectl get hpa stock-portfolio-hpa --watch
```

The HPA scales the app **between 1 and 3 replicas**, adding a pod when average CPU exceeds **70%** or memory exceeds **80%**, with a 30-second scale-up stabilisation window and a 120-second scale-down window to prevent flapping.

### 6. Tear down

```bash
kubectl delete -f k8s/
```

---

## CI/CD Pipeline

The pipeline is defined in `.github/workflows/ci.yml` and triggers on every push to `main`.

### Job 1 — Build & Integration Tests

| Step | Detail |
|---|---|
| MySQL service container | Spun up automatically by GitHub Actions before any step runs; health-checked via `mysqladmin ping` |
| Java 17 setup | Temurin distribution; Maven dependency cache enabled |
| Maven build | `mvn package -DskipTests` — produces an executable JAR |
| App startup | JAR launched as a background process with `ddl-auto=create` so the schema is freshly generated |
| Readiness check | `curl` loop — polls `/api/stocks` up to 20 times (60 s timeout) before failing and uploading the Spring Boot log as a downloadable artifact |
| Python 3.12 setup | pip dependency cache enabled |
| pytest | 16 integration tests run against the live API with `-v --tb=short` |

### Job 2 — Docker Build *(runs only if Job 1 passes)*

| Step | Detail |
|---|---|
| Docker Buildx | Multi-platform builder setup |
| Image build | Full multi-stage Dockerfile build; GitHub Actions layer cache (`type=gha`) keeps repeat builds fast |

> The Docker image is **not pushed** to a registry in this pipeline. To enable that, add `docker/login-action` and set `push: true` in the `build-push-action` step.

---

## Integration Tests

Tests live in `tests/test_api.py` and cover all five endpoints across **16 test cases**.

```
tests/test_api.py

  TestListStocks    (3 tests)
  ├── returns HTTP 200
  ├── response is a JSON array
  └── a newly created stock appears in the list

  TestAddStock      (4 tests)
  ├── returns HTTP 201
  ├── response body contains a generated id
  ├── all fields are persisted correctly
  └── multiple stocks receive unique ids

  TestGetStockById  (3 tests)
  ├── returns HTTP 200 for a known id
  ├── returned data matches what was saved
  └── unknown id returns HTTP 404

  TestUpdateStock   (3 tests)
  ├── returns HTTP 200
  ├── changes are visible on a subsequent GET
  └── unknown id returns HTTP 404

  TestDeleteStock   (4 tests — including negative paths)
  ├── returns HTTP 204
  ├── deleted stock returns 404 on GET
  ├── deleted stock is absent from GET all
  └── unknown id returns HTTP 404
```

Each test that creates data cleans up after itself in a `try/finally` block, so tests are fully isolated and order-independent.

### Running tests locally

```bash
# Start the app first (Docker Compose or bare Java)
docker compose up -d

# Install dependencies and run
pip install -r tests/requirements.txt
pytest tests/ -v
```

Override the base URL if your app runs on a different host or port:

```bash
API_BASE_URL=http://localhost:9090/api/stocks pytest tests/ -v
```
