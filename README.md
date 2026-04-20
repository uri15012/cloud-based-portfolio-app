# Stock Portfolio API

A production-ready RESTful API for managing a personal stock portfolio, built with **Spring Boot 3**, **MySQL 8**, and deployed via **Docker**, **Kubernetes**, and **AWS ECS Fargate**. The project includes a full **CI/CD pipeline** powered by GitHub Actions that runs automated pytest integration tests, pushes a Docker image to Amazon ECR, and redeploys the ECS service on every push to `main`.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Running with Docker Compose](#running-with-docker-compose)
- [Deploying to Kubernetes](#deploying-to-kubernetes)
- [Deploying to AWS (ECS Fargate)](#deploying-to-aws-ecs-fargate)
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
| Cloud | AWS ECS Fargate + Amazon ECR |
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
  │  Job 2: deploy                          │
  │                                         │
  │  1. Checkout code                       │
  │  2. Configure AWS credentials           │
  │  3. Log in to Amazon ECR                │
  │  4. docker build --platform linux/amd64 │
  │     → ECR/cloud-portfolio-app:latest    │
  │     → ECR/cloud-portfolio-app:<sha>     │
  │     (GHA layer cache)                   │
  │  5. Render new task definition revision │
  │     (swap app image → :<sha>)           │
  │  6. Register task def + force-deploy    │
  │     ECS service                         │
  │  7. Wait for service stability          │
  └─────────────────────────────────────────┘
                     │
                     ▼
          ECS Fargate task replaced
          http://13.53.131.214:8080
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

## Deploying to AWS (ECS Fargate)

### Live deployment

| Resource | Value |
|---|---|
| Live app URL | **http://13.53.131.214:8080/api/stocks** |
| ECR repository | `336779059487.dkr.ecr.eu-north-1.amazonaws.com/cloud-portfolio-app` |
| ECS cluster | `cloud-portfolio-cluster` |
| ECS service | `cloud-portfolio-service` |
| Region | `eu-north-1` (Stockholm) |

### Architecture

The app runs as a **single Fargate task** containing two containers that share the same network namespace (identical to how Docker Compose links `app` and `db` via `localhost`):

```
  Internet
      │
      │  HTTP :8080
      ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  AWS ECS Fargate Task  (512 CPU / 1024 MB)                  │
  │                                                             │
  │  ┌──────────────────────────┐                               │
  │  │  app container           │  ◀── public IP (port 8080)   │
  │  │  Spring Boot :8080       │                               │
  │  │  image: ECR/cloud-       │                               │
  │  │    portfolio-app:latest  │                               │
  │  └────────────┬─────────────┘                               │
  │               │ JDBC → localhost:3306                        │
  │  ┌────────────▼─────────────┐                               │
  │  │  mysql container         │                               │
  │  │  MySQL 8.3 :3306         │                               │
  │  │  image: mysql:8.3        │                               │
  │  └──────────────────────────┘                               │
  │                                                             │
  │  Both containers log to CloudWatch: /ecs/cloud-portfolio-app│
  └─────────────────────────────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  AWS Infrastructure                                         │
  │                                                             │
  │  VPC (default)  →  public subnet  →  Security Group        │
  │                                      (TCP 8080 open)        │
  │                                                             │
  │  ECR  →  stores versioned Docker images (:latest + :SHA)   │
  │  CloudWatch Logs  →  /ecs/cloud-portfolio-app              │
  │  IAM  →  ecsTaskExecutionRole (ECR pull + CW logs)         │
  └─────────────────────────────────────────────────────────────┘
```

**Key design decisions:**

- **MySQL sidecar** — runs alongside the app in the same task so the app connects via `localhost:3306`, matching the docker-compose setup with no code changes. For a production workload, replacing this with Amazon RDS would give persistent storage across task restarts.
- **Public IP on the task** — sufficient for a portfolio app. A production setup would sit behind an Application Load Balancer for a stable DNS name and HTTPS termination.
- **awsvpc networking** — each task gets its own elastic network interface, so security group rules apply at the task level rather than the EC2 instance level.

### Re-deploying manually

```bash
# Build and push a new image
aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin \
  336779059487.dkr.ecr.eu-north-1.amazonaws.com

docker build --platform linux/amd64 \
  -t 336779059487.dkr.ecr.eu-north-1.amazonaws.com/cloud-portfolio-app:latest .

docker push 336779059487.dkr.ecr.eu-north-1.amazonaws.com/cloud-portfolio-app:latest

# Force a new deployment
aws ecs update-service \
  --cluster cloud-portfolio-cluster \
  --service cloud-portfolio-service \
  --force-new-deployment \
  --region eu-north-1
```

### Checking service health

```bash
# Service status
aws ecs describe-services \
  --cluster cloud-portfolio-cluster \
  --services cloud-portfolio-service \
  --region eu-north-1 \
  --query 'services[0].{status:status,running:runningCount,desired:desiredCount}'

# Live endpoint
curl http://13.53.131.214:8080/api/stocks
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

### Job 2 — Build, Push & Deploy to ECS *(runs only if Job 1 passes)*

| Step | Detail |
|---|---|
| AWS credentials | Configured via `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` repository secrets |
| ECR login | `aws-actions/amazon-ecr-login` — exchanges the IAM credentials for a short-lived Docker registry token |
| Docker Buildx | Multi-platform builder (`linux/amd64`) setup |
| Image build + push | Full multi-stage Dockerfile build; image pushed to ECR tagged as both `:latest` and `:<git-sha>`; GitHub Actions layer cache (`type=gha`) keeps repeat builds fast |
| Task definition update | Downloads the current `cloud-portfolio-task` definition and renders a new revision with the `:<git-sha>` image via `aws-actions/amazon-ecs-render-task-definition` |
| ECS deploy | Registers the new task definition revision and triggers a rolling replacement of the running task via `aws-actions/amazon-ecs-deploy-task-definition`; the job waits for service stability before completing |

**Required repository secrets:**

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM access key with ECR push + ECS deploy permissions |
| `AWS_SECRET_ACCESS_KEY` | Corresponding IAM secret key |

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
