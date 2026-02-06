# VALLORYS CRM Plugin

Plugin d'estimation immobilière IA pour CRM.

## Installation

```bash
pip install -e .
```

## Démarrage

```bash
# Avec Docker
docker compose up

# Sans Docker (dev)
uvicorn vallorys.main:app --reload
```

## API Endpoints

- `POST /v1/valuation/run` - Estimation
- `POST /v1/fieldpack/generate` - Pack terrain
- `POST /v1/objection/respond` - Coach objections
- `GET /v1/analytics/dashboard` - Dashboard
