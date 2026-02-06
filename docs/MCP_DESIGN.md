# VALLORYS - MCP (Model Context Protocol) Design

## Vue d'ensemble des MCP Servers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VALLORYS MCP ECOSYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │  CRM          │  │  DVF/Market   │  │  Estimator    │  │  ArgGen     │  │
│  │  Connector    │  │  Data         │  │               │  │             │  │
│  │               │  │               │  │               │  │             │  │
│  │  - pull_lead  │  │  - get_price  │  │  - estimate   │  │  - generate │  │
│  │  - pull_prop  │  │  - get_stats  │  │  - explain    │  │  - script   │  │
│  │  - push_rep   │  │  - get_comps  │  │  - validate   │  │  - checklist│  │
│  │  - webhooks   │  │  - get_trends │  │               │  │  - template │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  └─────────────┘  │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐  │
│  │  Objection    │  │  Analytics    │  │  PDF/Report   │  │  Template   │  │
│  │  Coach        │  │               │  │  Builder      │  │  Store      │  │
│  │               │  │               │  │               │  │             │  │
│  │  - respond    │  │  - track      │  │  - generate   │  │  - search   │  │
│  │  - suggest    │  │  - aggregate  │  │  - customize  │  │  - store    │  │
│  │  - log_usage  │  │  - export     │  │  - send       │  │  - retrieve │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  └─────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## MCP 1: CRM Connector

### Metadata
| Champ | Valeur |
|-------|--------|
| **name** | `vallorys-crm-connector` |
| **version** | `1.0.0` |
| **description** | Connexion bidirectionnelle avec les CRM immobiliers |
| **auth** | OAuth2 per-tenant |
| **rate_limit** | 100 req/min/tenant |
| **pii_rules** | Données transitent, pas de stockage permanent |

### Tools

#### `pull_lead`
Récupère les informations d'un lead/contact depuis le CRM.

```json
{
  "name": "pull_lead",
  "description": "Récupère un lead depuis le CRM connecté",
  "inputSchema": {
    "type": "object",
    "properties": {
      "crm_type": {
        "type": "string",
        "enum": ["hubspot", "pipedrive", "generic"],
        "description": "Type de CRM"
      },
      "lead_id": {
        "type": "string",
        "description": "ID du lead dans le CRM"
      },
      "include_history": {
        "type": "boolean",
        "default": false,
        "description": "Inclure l'historique des interactions"
      }
    },
    "required": ["crm_type", "lead_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "seller": {
        "$ref": "#/definitions/SellerProfile"
      },
      "history": {
        "type": "array",
        "items": { "$ref": "#/definitions/Interaction" }
      },
      "appointments": {
        "type": "array",
        "items": { "$ref": "#/definitions/Appointment" }
      }
    }
  }
}
```

#### `pull_property`
Récupère les informations d'un bien depuis le CRM.

```json
{
  "name": "pull_property",
  "description": "Récupère les informations d'un bien immobilier",
  "inputSchema": {
    "type": "object",
    "properties": {
      "crm_type": { "type": "string", "enum": ["hubspot", "pipedrive", "generic"] },
      "property_id": { "type": "string" },
      "include_photos": { "type": "boolean", "default": false }
    },
    "required": ["crm_type", "property_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "property": { "$ref": "#/definitions/PropertyProfile" },
      "photos_urls": { "type": "array", "items": { "type": "string", "format": "uri" } }
    }
  }
}
```

#### `push_report`
Envoie un rapport d'estimation vers le CRM.

```json
{
  "name": "push_report",
  "description": "Pousse le rapport d'estimation vers le CRM",
  "inputSchema": {
    "type": "object",
    "properties": {
      "crm_type": { "type": "string", "enum": ["hubspot", "pipedrive", "generic"] },
      "lead_id": { "type": "string" },
      "property_id": { "type": "string" },
      "valuation": { "$ref": "#/definitions/ValuationResult" },
      "report_url": { "type": "string", "format": "uri" },
      "create_task": { "type": "boolean", "default": true }
    },
    "required": ["crm_type", "lead_id", "valuation"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "success": { "type": "boolean" },
      "crm_record_id": { "type": "string" },
      "task_id": { "type": "string" }
    }
  }
}
```

#### `listen_webhooks`
Configuration des webhooks CRM.

```json
{
  "name": "configure_webhook",
  "description": "Configure un webhook pour recevoir les events CRM",
  "inputSchema": {
    "type": "object",
    "properties": {
      "crm_type": { "type": "string" },
      "event_types": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["lead.created", "lead.updated", "property.created", "appointment.scheduled"]
        }
      },
      "callback_url": { "type": "string", "format": "uri" }
    },
    "required": ["crm_type", "event_types", "callback_url"]
  }
}
```

---

## MCP 2: DVF/Market Data

### Metadata
| Champ | Valeur |
|-------|--------|
| **name** | `vallorys-market-data` |
| **version** | `1.0.0` |
| **description** | Accès aux données de marché DVF et agrégats |
| **auth** | API Key interne |
| **rate_limit** | 500 req/min |
| **pii_rules** | Données anonymisées uniquement |
| **cache_ttl** | 24 heures |

### Tools

#### `get_price_per_sqm`
Prix au m² par secteur.

```json
{
  "name": "get_price_per_sqm",
  "description": "Récupère le prix/m² médian pour un secteur",
  "inputSchema": {
    "type": "object",
    "properties": {
      "citycode": {
        "type": "string",
        "pattern": "^[0-9]{5}$",
        "description": "Code INSEE de la commune"
      },
      "property_type": {
        "type": "string",
        "enum": ["maison", "appartement", "terrain"],
        "description": "Type de bien"
      },
      "radius_km": {
        "type": "number",
        "minimum": 0.5,
        "maximum": 20,
        "default": 5,
        "description": "Rayon de recherche en km"
      },
      "period_months": {
        "type": "integer",
        "minimum": 6,
        "maximum": 36,
        "default": 12,
        "description": "Période d'analyse en mois"
      }
    },
    "required": ["citycode", "property_type"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "median_price_sqm": { "type": "number" },
      "p10_price_sqm": { "type": "number" },
      "p90_price_sqm": { "type": "number" },
      "transaction_count": { "type": "integer" },
      "trend_12m_percent": { "type": "number" },
      "data_quality": {
        "type": "string",
        "enum": ["high", "medium", "low"]
      },
      "last_update": { "type": "string", "format": "date-time" }
    }
  }
}
```

#### `get_sector_stats`
Statistiques détaillées du secteur.

```json
{
  "name": "get_sector_stats",
  "description": "Statistiques détaillées du marché local",
  "inputSchema": {
    "type": "object",
    "properties": {
      "citycode": { "type": "string" },
      "property_type": { "type": "string", "enum": ["maison", "appartement"] }
    },
    "required": ["citycode"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "avg_surface": { "type": "number" },
      "avg_rooms": { "type": "number" },
      "avg_days_on_market": { "type": "integer" },
      "price_distribution": {
        "type": "object",
        "properties": {
          "deciles": { "type": "array", "items": { "type": "number" } }
        }
      },
      "dpe_distribution": {
        "type": "object",
        "additionalProperties": { "type": "number" }
      }
    }
  }
}
```

#### `get_comparable_sales`
Ventes comparables (agrégées, anonymisées).

```json
{
  "name": "get_comparable_sales",
  "description": "Récupère des ventes comparables agrégées",
  "inputSchema": {
    "type": "object",
    "properties": {
      "citycode": { "type": "string" },
      "property_type": { "type": "string" },
      "surface_min": { "type": "number" },
      "surface_max": { "type": "number" },
      "rooms_min": { "type": "integer" },
      "rooms_max": { "type": "integer" },
      "limit": { "type": "integer", "default": 10, "maximum": 50 }
    },
    "required": ["citycode", "property_type"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "comparables": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "sale_date": { "type": "string", "format": "date" },
            "price": { "type": "number" },
            "price_sqm": { "type": "number" },
            "surface": { "type": "number" },
            "rooms": { "type": "integer" },
            "distance_km": { "type": "number" }
          }
        }
      },
      "count": { "type": "integer" }
    }
  }
}
```

---

## MCP 3: Estimator

### Metadata
| Champ | Valeur |
|-------|--------|
| **name** | `vallorys-estimator` |
| **version** | `1.0.0` |
| **description** | Moteur d'estimation immobilière |
| **auth** | JWT tenant |
| **rate_limit** | 50 req/min/tenant |
| **pii_rules** | Pas de stockage PII, logs anonymisés |

### Tools

#### `estimate_property`
Estimation complète d'un bien.

```json
{
  "name": "estimate_property",
  "description": "Génère une estimation complète avec fourchette et justification",
  "inputSchema": {
    "type": "object",
    "properties": {
      "property": { "$ref": "#/definitions/PropertyProfile" },
      "market_context": { "$ref": "#/definitions/MarketContext" },
      "seller_expectation": {
        "type": "number",
        "description": "Prix espéré par le vendeur (optionnel)"
      }
    },
    "required": ["property", "market_context"]
  },
  "outputSchema": {
    "$ref": "#/definitions/ValuationResult"
  }
}
```

#### `explain_valuation`
Explication détaillée d'une estimation.

```json
{
  "name": "explain_valuation",
  "description": "Génère une explication détaillée de l'estimation",
  "inputSchema": {
    "type": "object",
    "properties": {
      "valuation_id": { "type": "string" },
      "detail_level": {
        "type": "string",
        "enum": ["summary", "detailed", "technical"],
        "default": "detailed"
      }
    },
    "required": ["valuation_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "summary": { "type": "string" },
      "factors": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "name": { "type": "string" },
            "impact_percent": { "type": "number" },
            "direction": { "type": "string", "enum": ["positive", "negative", "neutral"] },
            "explanation": { "type": "string" }
          }
        }
      },
      "market_comparison": { "type": "string" },
      "risk_factors": { "type": "array", "items": { "type": "string" } }
    }
  }
}
```

#### `validate_inputs`
Validation des données d'entrée.

```json
{
  "name": "validate_inputs",
  "description": "Valide la cohérence des données du bien",
  "inputSchema": {
    "type": "object",
    "properties": {
      "property": { "$ref": "#/definitions/PropertyProfile" }
    },
    "required": ["property"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "is_valid": { "type": "boolean" },
      "warnings": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "field": { "type": "string" },
            "message": { "type": "string" },
            "severity": { "type": "string", "enum": ["info", "warning", "error"] }
          }
        }
      },
      "missing_fields": { "type": "array", "items": { "type": "string" } },
      "data_quality_score": { "type": "number", "minimum": 0, "maximum": 1 }
    }
  }
}
```

---

## MCP 4: Argument Generator

### Metadata
| Champ | Valeur |
|-------|--------|
| **name** | `vallorys-arggen` |
| **version** | `1.0.0` |
| **description** | Génération de contenu terrain (argumentaires, scripts, checklists) |
| **auth** | JWT tenant |
| **rate_limit** | 30 req/min/tenant |
| **pii_rules** | Données vendeur pseudonymisées dans les logs |

### Tools

#### `generate_argumentaire`
Argumentaire personnalisé.

```json
{
  "name": "generate_argumentaire",
  "description": "Génère un argumentaire adapté au profil vendeur et au bien",
  "inputSchema": {
    "type": "object",
    "properties": {
      "seller": { "$ref": "#/definitions/SellerProfile" },
      "property": { "$ref": "#/definitions/PropertyProfile" },
      "valuation": { "$ref": "#/definitions/ValuationResult" },
      "tone": {
        "type": "string",
        "enum": ["professional", "reassuring", "direct", "empathetic"],
        "default": "professional"
      },
      "focus_points": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Points à mettre en avant"
      }
    },
    "required": ["seller", "property", "valuation"]
  },
  "outputSchema": {
    "$ref": "#/definitions/FieldPackArgumentaire"
  }
}
```

#### `generate_rdv_script`
Script de rendez-vous dynamique.

```json
{
  "name": "generate_rdv_script",
  "description": "Génère un script minute par minute pour le RDV",
  "inputSchema": {
    "type": "object",
    "properties": {
      "seller": { "$ref": "#/definitions/SellerProfile" },
      "property": { "$ref": "#/definitions/PropertyProfile" },
      "valuation": { "$ref": "#/definitions/ValuationResult" },
      "rdv_duration_minutes": {
        "type": "integer",
        "default": 60,
        "minimum": 30,
        "maximum": 120
      },
      "objectives": {
        "type": "array",
        "items": { "type": "string" }
      }
    },
    "required": ["seller", "property", "valuation"]
  },
  "outputSchema": {
    "$ref": "#/definitions/FieldPackScript"
  }
}
```

#### `generate_checklist`
Checklist pré-mandat.

```json
{
  "name": "generate_checklist",
  "description": "Génère une checklist pré-mandat personnalisée",
  "inputSchema": {
    "type": "object",
    "properties": {
      "property": { "$ref": "#/definitions/PropertyProfile" },
      "property_type": { "type": "string" },
      "include_photos_guide": { "type": "boolean", "default": true }
    },
    "required": ["property"]
  },
  "outputSchema": {
    "$ref": "#/definitions/FieldPackChecklist"
  }
}
```

#### `generate_templates`
Templates emails/SMS/objections.

```json
{
  "name": "generate_templates",
  "description": "Génère des templates de communication",
  "inputSchema": {
    "type": "object",
    "properties": {
      "template_type": {
        "type": "string",
        "enum": ["email_pre_rdv", "email_post_rdv", "sms_reminder", "objection_response", "follow_up"]
      },
      "seller": { "$ref": "#/definitions/SellerProfile" },
      "valuation": { "$ref": "#/definitions/ValuationResult" },
      "context": { "type": "string" }
    },
    "required": ["template_type"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "subject": { "type": "string" },
      "body": { "type": "string" },
      "variables": {
        "type": "array",
        "items": { "type": "string" }
      }
    }
  }
}
```

---

## MCP 5: Objection Coach

### Metadata
| Champ | Valeur |
|-------|--------|
| **name** | `vallorys-objection-coach` |
| **version** | `1.0.0` |
| **description** | Agent IA pour réponse aux objections en temps réel |
| **auth** | JWT tenant |
| **rate_limit** | 100 req/min/tenant (mode live) |
| **pii_rules** | Pas de stockage des conversations, stats agrégées uniquement |
| **latency_target** | < 3s P95 |

### Tools

#### `respond_to_objection`
Réponse à une objection en temps réel.

```json
{
  "name": "respond_to_objection",
  "description": "Génère une réponse à une objection vendeur",
  "inputSchema": {
    "type": "object",
    "properties": {
      "objection_text": {
        "type": "string",
        "maxLength": 500,
        "description": "L'objection du vendeur"
      },
      "objection_category": {
        "type": "string",
        "enum": [
          "price_too_low",
          "neighbor_sold_higher",
          "other_agency_estimate",
          "want_to_test_market",
          "not_urgent",
          "need_time_to_think",
          "commission_too_high",
          "dont_trust_estimates",
          "other"
        ]
      },
      "seller": { "$ref": "#/definitions/SellerProfile" },
      "valuation": { "$ref": "#/definitions/ValuationResult" },
      "conversation_history": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "role": { "type": "string", "enum": ["agent", "seller"] },
            "text": { "type": "string" }
          }
        },
        "maxItems": 10
      }
    },
    "required": ["objection_text"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "quick_response": {
        "type": "string",
        "description": "Réponse 10 secondes"
      },
      "detailed_response": {
        "type": "string",
        "description": "Réponse 45 secondes"
      },
      "follow_up_question": {
        "type": "string",
        "description": "Question pour reprendre la main"
      },
      "proof_point": {
        "type": "string",
        "description": "Preuve issue du rapport à citer"
      },
      "suggested_tone": {
        "type": "string",
        "enum": ["empathetic", "factual", "challenging", "reassuring"]
      },
      "objection_id": {
        "type": "string",
        "description": "ID pour tracking"
      }
    }
  }
}
```

#### `suggest_proactive`
Suggestions proactives.

```json
{
  "name": "suggest_proactive",
  "description": "Suggère des arguments proactifs basés sur le contexte",
  "inputSchema": {
    "type": "object",
    "properties": {
      "seller": { "$ref": "#/definitions/SellerProfile" },
      "valuation": { "$ref": "#/definitions/ValuationResult" },
      "current_phase": {
        "type": "string",
        "enum": ["discovery", "presentation", "objection_handling", "closing"]
      }
    },
    "required": ["current_phase"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "suggestions": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "trigger": { "type": "string" },
            "message": { "type": "string" },
            "priority": { "type": "string", "enum": ["high", "medium", "low"] }
          }
        }
      }
    }
  }
}
```

#### `log_objection_outcome`
Logging pour analytics.

```json
{
  "name": "log_objection_outcome",
  "description": "Log le résultat d'un traitement d'objection",
  "inputSchema": {
    "type": "object",
    "properties": {
      "objection_id": { "type": "string" },
      "response_used": {
        "type": "string",
        "enum": ["quick", "detailed", "custom", "none"]
      },
      "outcome": {
        "type": "string",
        "enum": ["objection_resolved", "objection_persists", "new_objection", "meeting_ended"]
      },
      "agent_feedback": {
        "type": "string",
        "enum": ["helpful", "not_helpful", "partially_helpful"]
      }
    },
    "required": ["objection_id", "outcome"]
  }
}
```

---

## MCP 6: Analytics

### Metadata
| Champ | Valeur |
|-------|--------|
| **name** | `vallorys-analytics` |
| **version** | `1.0.0` |
| **description** | Tracking et KPIs réseau |
| **auth** | JWT tenant (admin only for aggregates) |
| **rate_limit** | 200 req/min |
| **pii_rules** | Données agrégées uniquement, pas de PII en sortie |

### Tools

#### `track_event`
Tracking d'événements.

```json
{
  "name": "track_event",
  "description": "Enregistre un événement pour analytics",
  "inputSchema": {
    "type": "object",
    "properties": {
      "event_type": {
        "type": "string",
        "enum": [
          "valuation_created",
          "valuation_viewed",
          "fieldpack_generated",
          "rdv_scheduled",
          "rdv_completed",
          "mandate_signed",
          "sale_completed",
          "objection_handled"
        ]
      },
      "entity_id": { "type": "string" },
      "entity_type": { "type": "string" },
      "metadata": {
        "type": "object",
        "additionalProperties": true
      },
      "user_id": { "type": "string" }
    },
    "required": ["event_type"]
  }
}
```

#### `get_dashboard_metrics`
Métriques dashboard.

```json
{
  "name": "get_dashboard_metrics",
  "description": "Récupère les KPIs pour le dashboard",
  "inputSchema": {
    "type": "object",
    "properties": {
      "scope": {
        "type": "string",
        "enum": ["agent", "agency", "network"]
      },
      "period": {
        "type": "string",
        "enum": ["7d", "30d", "90d", "12m", "all"]
      },
      "metrics": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": [
            "valuation_count",
            "valuation_accuracy",
            "avg_decote",
            "mandate_conversion",
            "objection_frequency",
            "script_usage",
            "avg_rdv_duration"
          ]
        }
      }
    },
    "required": ["scope", "period"]
  },
  "outputSchema": {
    "$ref": "#/definitions/DashboardMetrics"
  }
}
```

#### `export_data`
Export de données.

```json
{
  "name": "export_data",
  "description": "Exporte les données en CSV ou JSON",
  "inputSchema": {
    "type": "object",
    "properties": {
      "data_type": {
        "type": "string",
        "enum": ["valuations", "events", "metrics", "objections"]
      },
      "format": {
        "type": "string",
        "enum": ["csv", "json"]
      },
      "filters": {
        "type": "object",
        "properties": {
          "date_from": { "type": "string", "format": "date" },
          "date_to": { "type": "string", "format": "date" },
          "agent_ids": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "required": ["data_type", "format"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "download_url": { "type": "string", "format": "uri" },
      "expires_at": { "type": "string", "format": "date-time" },
      "row_count": { "type": "integer" }
    }
  }
}
```

---

## MCP 7: PDF/Report Builder

### Metadata
| Champ | Valeur |
|-------|--------|
| **name** | `vallorys-report-builder` |
| **version** | `1.0.0` |
| **description** | Génération de rapports PDF |
| **auth** | JWT tenant |
| **rate_limit** | 20 req/min/tenant |
| **pii_rules** | Rapports contiennent PII, chiffrés au repos |

### Tools

#### `generate_report`
Génération de rapport PDF.

```json
{
  "name": "generate_report",
  "description": "Génère un rapport PDF d'estimation",
  "inputSchema": {
    "type": "object",
    "properties": {
      "valuation_id": { "type": "string" },
      "template": {
        "type": "string",
        "enum": ["standard", "detailed", "executive", "custom"],
        "default": "standard"
      },
      "include_sections": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["summary", "property_details", "market_analysis", "comparables", "methodology", "appendix"]
        }
      },
      "branding": {
        "type": "object",
        "properties": {
          "logo_url": { "type": "string", "format": "uri" },
          "primary_color": { "type": "string", "pattern": "^#[0-9A-Fa-f]{6}$" },
          "agency_name": { "type": "string" }
        }
      }
    },
    "required": ["valuation_id"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "report_id": { "type": "string" },
      "download_url": { "type": "string", "format": "uri" },
      "expires_at": { "type": "string", "format": "date-time" },
      "page_count": { "type": "integer" }
    }
  }
}
```

---

## Définitions communes (Schemas)

```json
{
  "definitions": {
    "PropertyProfile": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "address": {
          "type": "object",
          "properties": {
            "street": { "type": "string" },
            "city": { "type": "string" },
            "citycode": { "type": "string", "pattern": "^[0-9]{5}$" },
            "postal_code": { "type": "string" },
            "lat": { "type": "number" },
            "lng": { "type": "number" }
          },
          "required": ["city", "citycode"]
        },
        "type": { "type": "string", "enum": ["maison", "appartement", "terrain", "immeuble"] },
        "surface_living": { "type": "number", "minimum": 1 },
        "surface_land": { "type": "number" },
        "rooms": { "type": "integer", "minimum": 1 },
        "bedrooms": { "type": "integer" },
        "bathrooms": { "type": "integer" },
        "floor": { "type": "integer" },
        "floors_total": { "type": "integer" },
        "construction_year": { "type": "integer" },
        "dpe_rating": { "type": "string", "enum": ["A", "B", "C", "D", "E", "F", "G", "unknown"] },
        "ges_rating": { "type": "string", "enum": ["A", "B", "C", "D", "E", "F", "G", "unknown"] },
        "condition": {
          "type": "object",
          "properties": {
            "global": { "type": "string", "enum": ["excellent", "good", "average", "poor", "to_renovate"] },
            "roof": { "type": "string", "enum": ["excellent", "good", "average", "poor", "to_replace"] },
            "windows": { "type": "string", "enum": ["double_glazing_recent", "double_glazing_old", "single_glazing"] },
            "heating": { "type": "string", "enum": ["recent", "functional", "to_replace"] },
            "electrical": { "type": "string", "enum": ["up_to_code", "functional", "to_renovate"] },
            "plumbing": { "type": "string", "enum": ["recent", "functional", "to_renovate"] }
          }
        },
        "renovation": {
          "type": "object",
          "properties": {
            "last_major_renovation_year": { "type": "integer" },
            "estimated_work_budget": { "type": "number" },
            "work_description": { "type": "string" }
          }
        },
        "amenities": {
          "type": "object",
          "properties": {
            "garage": { "type": "boolean" },
            "parking_spots": { "type": "integer" },
            "cellar": { "type": "boolean" },
            "pool": { "type": "boolean" },
            "terrace": { "type": "boolean" },
            "balcony": { "type": "boolean" },
            "garden": { "type": "boolean" },
            "elevator": { "type": "boolean" },
            "fireplace": { "type": "boolean" }
          }
        },
        "environment": {
          "type": "object",
          "properties": {
            "view": { "type": "string", "enum": ["exceptional", "pleasant", "ordinary", "obstructed"] },
            "noise_level": { "type": "string", "enum": ["very_quiet", "quiet", "moderate", "noisy"] },
            "nearby_shops": { "type": "boolean" },
            "nearby_transport": { "type": "boolean" },
            "nearby_schools": { "type": "boolean" }
          }
        }
      },
      "required": ["address", "type", "surface_living"]
    },

    "SellerProfile": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "type": {
          "type": "string",
          "enum": ["owner_occupier", "investor", "heir", "divorcing", "relocating", "other"]
        },
        "urgency": { "type": "string", "enum": ["urgent", "moderate", "no_rush", "unknown"] },
        "motivation": { "type": "string" },
        "price_expectation": { "type": "number" },
        "previous_estimates": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "source": { "type": "string" },
              "amount": { "type": "number" },
              "date": { "type": "string", "format": "date" }
            }
          }
        },
        "objections_history": {
          "type": "array",
          "items": { "type": "string" }
        },
        "personality_hints": {
          "type": "string",
          "enum": ["analytical", "expressive", "driver", "amiable", "unknown"]
        }
      }
    },

    "MarketContext": {
      "type": "object",
      "properties": {
        "median_price_sqm": { "type": "number" },
        "p10_price_sqm": { "type": "number" },
        "p90_price_sqm": { "type": "number" },
        "transaction_count": { "type": "integer" },
        "trend_12m_percent": { "type": "number" },
        "avg_days_on_market": { "type": "integer" },
        "supply_demand_ratio": { "type": "number" },
        "data_quality": { "type": "string", "enum": ["high", "medium", "low"] }
      },
      "required": ["median_price_sqm"]
    },

    "ValuationResult": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "property_id": { "type": "string" },
        "range_low": { "type": "number" },
        "range_high": { "type": "number" },
        "price_point_recommended": { "type": "number" },
        "confidence_score": { "type": "number", "minimum": 0, "maximum": 1 },
        "confidence_level": { "type": "string", "enum": ["high", "medium", "low"] },
        "margin_percent": { "type": "number" },
        "base_price_sqm_used": { "type": "number" },
        "adjustments": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "factor": { "type": "string" },
              "impact_percent": { "type": "number" },
              "direction": { "type": "string", "enum": ["positive", "negative"] },
              "explanation": { "type": "string" },
              "capped": { "type": "boolean" }
            }
          }
        },
        "justification": {
          "type": "object",
          "properties": {
            "summary": { "type": "string" },
            "top_positive_factors": { "type": "array", "items": { "type": "string" } },
            "top_negative_factors": { "type": "array", "items": { "type": "string" } },
            "market_comparison": { "type": "string" }
          }
        },
        "risk_factors": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "type": { "type": "string" },
              "description": { "type": "string" },
              "severity": { "type": "string", "enum": ["low", "medium", "high"] }
            }
          }
        },
        "data_completeness": { "type": "number", "minimum": 0, "maximum": 1 },
        "methodology_version": { "type": "string" }
      },
      "required": ["range_low", "range_high", "confidence_score"]
    },

    "DashboardMetrics": {
      "type": "object",
      "properties": {
        "period": { "type": "string" },
        "scope": { "type": "string" },
        "valuation_count": { "type": "integer" },
        "valuation_accuracy": {
          "type": "object",
          "properties": {
            "mae": { "type": "number" },
            "mape": { "type": "number" },
            "sample_size": { "type": "integer" }
          }
        },
        "avg_decote_percent": { "type": "number" },
        "mandate_conversion_rate": { "type": "number" },
        "top_objections": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "category": { "type": "string" },
              "count": { "type": "integer" },
              "resolution_rate": { "type": "number" }
            }
          }
        },
        "script_usage_rate": { "type": "number" },
        "avg_rdv_duration_minutes": { "type": "number" }
      }
    }
  }
}
```

---

## Permissions et Sécurité MCP

| MCP Server | Roles autorisés | PII Access | Audit Required |
|------------|-----------------|------------|----------------|
| CRM Connector | admin, manager, agent | Yes | Yes |
| DVF/Market Data | all | No | No |
| Estimator | admin, manager, agent | Yes (indirect) | Yes |
| Argument Generator | admin, manager, agent | Yes | Yes |
| Objection Coach | agent | Yes (session only) | Yes |
| Analytics | admin, manager | Aggregated only | Yes |
| Report Builder | admin, manager, agent | Yes | Yes |

---

## Flux d'intégration MCP

```
Agent Request
     │
     ▼
┌─────────────┐
│  MCP Host   │ (Claude Code / Custom Agent)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│            MCP Protocol Layer                   │
│  - Tool discovery                               │
│  - Schema validation                            │
│  - Permission check                             │
│  - Rate limiting                                │
└──────────────────────┬──────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ MCP Server 1│ │ MCP Server 2│ │ MCP Server N│
└─────────────┘ └─────────────┘ └─────────────┘
```
