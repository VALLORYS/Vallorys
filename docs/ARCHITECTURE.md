# VALLORYS CRM Plugin - Architecture Globale

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VALLORYS PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   CRM       │    │  External   │    │   Mobile    │    │  Dashboard  │  │
│  │  Systems    │    │   APIs      │    │    App      │    │    Web      │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │         │
│         ▼                  ▼                  ▼                  ▼         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API GATEWAY                                   │   │
│  │              (Auth, Rate Limiting, Routing)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐       │
│  │   CRM       │           │ Estimation  │           │   GenAI     │       │
│  │  Adapter    │           │   Engine    │           │  Service    │       │
│  │  Service    │           │   Service   │           │             │       │
│  └──────┬──────┘           └──────┬──────┘           └──────┬──────┘       │
│         │                         │                         │              │
│         │    ┌────────────────────┼────────────────────┐    │              │
│         │    │                    │                    │    │              │
│         ▼    ▼                    ▼                    ▼    ▼              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         MCP LAYER                                    │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │  CRM    │ │  DVF/   │ │Estimator│ │ArgGen  │ │Objection│       │   │
│  │  │Connector│ │ Market  │ │  Tool   │ │  Tool  │ │ Coach   │       │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │   │
│  │       │           │           │           │           │             │   │
│  │  ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐       │   │
│  │  │Analytics│ │  PDF    │ │Template │ │ Scorer  │ │ Logger  │       │   │
│  │  │  Tool   │ │ Builder │ │ Store   │ │  Tool   │ │  Tool   │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐            │
│         ▼                          ▼                          ▼            │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐       │
│  │ PostgreSQL  │           │    Redis    │           │   S3/Minio  │       │
│  │  (Primary)  │           │(Cache/Queue)│           │  (Reports)  │       │
│  └─────────────┘           └─────────────┘           └─────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Choix Techniques

### Backend: Python + FastAPI

**Justification:**
1. **Écosystème ML/AI mature** - NumPy, Pandas pour les calculs de pondération
2. **Async natif** - Performance pour les appels API externes (CRM, DVF)
3. **Type hints** - Pydantic pour validation stricte des schémas
4. **OpenAPI auto-généré** - Documentation API automatique
5. **Communauté active** - Facilité de recrutement et maintenance

### Base de données

| Composant | Technologie | Usage |
|-----------|-------------|-------|
| Primary DB | PostgreSQL 15+ | Données métier, tenants, estimations |
| Cache | Redis 7+ | Sessions, cache prix/m², rate limiting |
| Queue | Redis + BullMQ | Jobs async (PDF, analytics) |
| Vector Store | pgvector | Templates & retrieval (optionnel V2) |

### Architecture Multi-tenant

```
┌─────────────────────────────────────────────────┐
│                  TENANT ISOLATION               │
├─────────────────────────────────────────────────┤
│  Strategy: Schema-per-tenant (PostgreSQL)       │
│                                                 │
│  tenant_001.properties                          │
│  tenant_001.valuations                          │
│  tenant_001.events                              │
│                                                 │
│  tenant_002.properties                          │
│  tenant_002.valuations                          │
│  tenant_002.events                              │
│                                                 │
│  public.tenants (metadata)                      │
│  public.users (cross-tenant admin)              │
└─────────────────────────────────────────────────┘
```

## Services Principaux

### 1. API Gateway (`services/gateway`)
- Authentification OAuth2 + JWT
- Rate limiting par tenant
- Routing vers services internes
- CORS, compression, logging

### 2. CRM Adapter Service (`services/crm-adapter`)
- Interface unifiée pour tous les CRM
- Adapters: HubSpot, Pipedrive, Generic REST
- Webhooks ingestion
- Mapping champs configurable

### 3. Estimation Engine (`services/estimation`)
- Calcul prix/m² pondéré
- Règles de plafonnement (clamp)
- Score de confiance
- Justification détaillée

### 4. GenAI Service (`services/genai`)
- Génération argumentaires
- Scripts RDV
- Checklists
- Templates objections

### 5. Analytics Service (`services/analytics`)
- Event tracking
- KPIs réseau
- Exports CSV/API

## Flux de données principal

```
CRM Webhook ──► CRM Adapter ──► Property Enrichment
                    │
                    ▼
              Market Data (DVF) ──► Estimation Engine
                                          │
                                          ▼
                                    Valuation Result
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
              Field Pack            PDF Report            Push to CRM
              Generator             Builder               (Results)
                    │
                    ▼
              Argumentaire + Script + Checklist + Templates
```

## Sécurité & RGPD

### Données personnelles
- **Minimisation**: Ne stocker que le nécessaire
- **Pseudonymisation**: IDs internes, pas d'emails en clair dans logs
- **Chiffrement**: AES-256 at rest, TLS 1.3 in transit
- **Purge automatique**: Configurable par tenant (défaut: 24 mois)
- **Audit trail**: Toutes les actions loggées avec tenant_id, user_id, timestamp

### Authentification
```
┌─────────────────────────────────────────────────┐
│              AUTH FLOW                          │
├─────────────────────────────────────────────────┤
│  1. CRM → OAuth2 authorize                      │
│  2. User consent                                │
│  3. Callback with code                          │
│  4. Exchange code → access_token + refresh      │
│  5. JWT signed with tenant-specific secret      │
│  6. RBAC: admin, manager, agent                 │
└─────────────────────────────────────────────────┘
```

## Observabilité

### Stack
- **Logs**: Structured JSON (OpenTelemetry)
- **Traces**: Jaeger/Tempo
- **Metrics**: Prometheus + Grafana
- **Alerting**: Alertmanager

### Logs format
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "service": "estimation",
  "tenant_id": "tenant_001",
  "trace_id": "abc123",
  "span_id": "def456",
  "message": "Valuation completed",
  "valuation_id": "val_xyz",
  "confidence": 0.85,
  "duration_ms": 1250
}
```

## Déploiement

### Environnements
| Env | Infra | Usage |
|-----|-------|-------|
| local | Docker Compose | Développement |
| staging | K8s (single node) | Tests intégration |
| production | K8s (HA) | Production multi-tenant |

### Scaling
- **Horizontal**: Services stateless, scale via replicas
- **Vertical**: Estimation engine peut nécessiter plus de RAM pour gros datasets
- **Cache**: Redis cluster pour haute dispo

## Performance

### Objectifs
| Métrique | Target | Mesure |
|----------|--------|--------|
| Estimation latency | < 10s | P95 |
| Field pack generation | < 15s | P95 |
| Objection response | < 3s | P95 |
| Availability | 99.9% | Monthly |

### Optimisations
1. Cache agressif des prix/m² par secteur (TTL: 24h)
2. Pré-calcul des agrégats DVF par code postal
3. Streaming pour génération de texte
4. Connection pooling PostgreSQL
