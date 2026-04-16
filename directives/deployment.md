# Directive: Deployment

## Goal
Deploy moments4u to production (cloud or VPS).

## Deployment Options

### Option A: Single VPS (MVP — <50 users)
**Cost: ~$20-40/month**

1. Provision a VPS (Hetzner CPX31: 4 vCPU, 8GB, ~$15/mo)
2. Install Docker + Docker Compose
3. Clone repo, set up `.env` with production values
4. `docker compose -f infra/docker-compose.prod.yml up -d`
5. Set up Nginx reverse proxy with Let's Encrypt SSL
6. Point domain DNS to VPS IP

### Option B: AWS (Scale — 50+ users)
**Cost: ~$173/month baseline**

| Service | Resource |
|---------|----------|
| App + Worker | ECS Fargate |
| Database | RDS PostgreSQL + pgvector |
| Cache/Queue | ElastiCache Redis |
| Storage | S3 + CloudFront |
| DNS | Route 53 |

## CI/CD Pipeline

### GitHub Actions
- **On PR**: Run tests (pytest + Jest)
- **On main merge**: Build Docker images → Push to ECR → Deploy to ECS

### Deployment steps
1. Build backend Docker image
2. Build frontend Docker image (Next.js standalone)
3. Push to container registry (ECR / Docker Hub)
4. Update ECS service (or `docker compose pull && up -d` for VPS)
5. Run database migrations: `alembic upgrade head`
6. Verify health check endpoint: `GET /api/v1/health`

## Tools/Scripts
- `infra/docker-compose.yml` — Local dev stack
- `infra/docker-compose.prod.yml` — Production overrides
- `infra/scripts/deploy.sh` — Deployment automation
- `infra/scripts/backup_db.sh` — Database backup
- `.github/workflows/deploy.yml` — CI/CD pipeline

## Environment Configuration
- **Development**: `.env` with local services (MinIO, local PostgreSQL)
- **Staging**: `.env.staging` with cloud services, test data
- **Production**: `.env.production` with production secrets (managed via AWS SSM / GH Secrets)

## Scaling Triggers
| Metric | Trigger | Action |
|--------|---------|--------|
| API p95 > 2s | Auto-scale ECS tasks | Add more containers |
| Worker queue depth > 100 | Scale workers | Add Celery worker instances |
| DB CPU > 80% | Vertical scale | Upgrade RDS instance class |
| Storage > 100GB | N/A | S3 scales automatically |

## Rollback
1. ECS: Redeploy previous task definition revision
2. VPS: `docker compose pull && docker compose up -d` with previous tag
3. Database: Alembic downgrade (`alembic downgrade -1`)

## Edge Cases
- **Migration failure**: Always test migrations on staging first. Keep `alembic downgrade` scripts.
- **Zero-downtime deploy**: ECS handles rolling updates. For VPS, use `--remove-orphans` with health checks.
- **S3 bucket not created**: infra setup script must create bucket with lifecycle policy.

## Learnings
- (Add learnings here as deployments happen)
