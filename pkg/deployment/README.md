# Op AI Tools API Deployment Guide

This guide provides instructions for deploying and managing the op-ai-tools Python API using Docker Swarm.

## Prerequisites

- Docker with Swarm mode enabled
- SSH access to the target server (for remote deployments)
- Neon Postgres database (https://neon.tech)
- Environment configuration file (`.env`)

## Quick Start

### 1. Prepare your environment file

Copy the example and fill in your values:

```bash
cp .env.example prod.config.env
# Edit prod.config.env with your actual values
```

### 2. Deploy

#### Remote Deployment

Deploy the application to a remote server:

```bash
bash pkg/deployment/deploy-remotely.sh user@server-ip:/home/user/deployments/op-ai-tools /path/to/prod.config.env
```

**Example:**

```bash
bash pkg/deployment/deploy-remotely.sh bleu@192.168.1.100:/home/bleu/op-ai-tools-prod /home/bleu/op-ai-tools-prod.env
```

This command will:

1. Sync the repository to the remote server
2. Build Docker images for the API
3. Run database migrations on your Neon database
4. Seed initial data (categories)
5. Deploy the stack using Docker Swarm

#### Local Deployment

Deploy to your local machine:

```bash
bash pkg/deployment/deploy-remotely.sh - /path/to/local.env
```

## Environment Configuration

The environment file must include:

### Required Variables

- `PROJECT_PREFIX`: Unique identifier for this deployment
- `DATABASE_URL`: Neon Postgres connection string (get from https://console.neon.tech)
  - Format: `postgresql://user:password@host/database?sslmode=require`
- `FLASK_API_SECRET_KEY`: Secret key for Flask/Quart API
- `SECRET`: General application secret
- At least one AI service API key (OpenAI, Anthropic, Voyage, or Groq)

### Optional Variables

- `HONEYBADGER_API_KEY`: Error tracking
- `POSTHOG_API_KEY`: Analytics
- `AGORA_BEARER_TOKEN`: Agora data source
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: AWS/S3 access
- `API_PORT`: Port to expose API (default: 9090)
- `API_CPU_LIMIT`: CPU limit (default: 4)
- `API_MEMORY_LIMIT`: Memory limit (default: 4G)

See `.env.example` for a complete list.

## Operations

### View Logs

View recent logs from the API backend:

```bash
docker service logs <PROJECT_PREFIX>_api-backend --tail 100 --follow
```

**Example:**

```bash
docker service logs op-ai-tools-prod_api-backend --tail 100 --follow
```

### Access Container Shell

```bash
docker exec -it $(docker ps -q -f name=<PROJECT_PREFIX>_api-backend) bash
```

**Example:**

```bash
docker exec -it $(docker ps -q -f name=op-ai-tools-prod_api-backend) bash
```

### Run Data Sync Jobs

To manually sync data:

```bash
# Access the container
docker exec -it $(docker ps -q -f name=<PROJECT_PREFIX>_api-backend) bash

# Inside the container
cd /app
poetry run sync categories
poetry run sync topics
poetry run sync summaries
poetry run sync snapshot
poetry run sync agora
```

### Scale the API

```bash
docker service scale <PROJECT_PREFIX>_api-backend=<replicas>
```

**Example:**

```bash
docker service scale op-ai-tools-prod_api-backend=3
```

### Update the Deployment

To deploy a new version:

```bash
# Same command as initial deployment
bash pkg/deployment/deploy-remotely.sh user@server:/path /path/to/env
```

The deployment uses a rolling update strategy (start-first) to minimize downtime.

### Tear Down

```bash
bash pkg/deployment/manage.sh down --env-file /path/to/env --revision dummy
```

Or remotely:

```bash
ssh user@server "cd /path/to/deployment && bash pkg/deployment/manage.sh down --env-file /path/to/env --revision dummy"
```

## Architecture

The deployment consists of:

1. **Neon Postgres**: Managed PostgreSQL database (cloud-hosted)
2. **API Backend**: Python/Quart API (port 9090 by default)

The API includes:

- RESTful endpoints for chat/predictions
- Automated data sync cron jobs (every 6 hours)
- Monthly index updates
- Health checks and monitoring

## Monitoring

### Health Check

```bash
curl http://your-server:9090/
```

### Service Status

```bash
docker service ls
docker service ps <PROJECT_PREFIX>_api-backend
```

### Database Connection

```bash
# Connect to Neon Postgres using the DATABASE_URL
psql "$DATABASE_URL"

# Or from your local machine (get the URL from Neon console)
psql "postgresql://user:password@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require"
```

## Troubleshooting

### API won't start

1. Check logs: `docker service logs <PROJECT_PREFIX>_api-backend`
2. Verify environment variables are set correctly
3. Ensure Neon database is accessible (check DATABASE_URL)
4. Verify your Neon database allows connections from your server IP
5. Check if API keys are valid

### Database connection issues

1. Verify DATABASE_URL format is correct
2. Test connection: `psql "$DATABASE_URL"`
3. Check Neon console for connection limits or issues
4. Ensure `sslmode=require` is in your connection string

### Out of memory

1. Increase `API_MEMORY_LIMIT` in your env file
2. Check actual memory usage: `docker stats`
3. Scale down API replicas if needed
4. Consider upgrading your server resources

## Security Notes

- Always use strong passwords for `POSTGRES_PASSWORD`
- Keep your `.env` file secure and never commit it to git
- Use HTTPS/SSL in production (configure reverse proxy)
- Regularly update Docker images and dependencies
- Rotate API keys periodically

## Support

For issues or questions, please open an issue on GitHub.
