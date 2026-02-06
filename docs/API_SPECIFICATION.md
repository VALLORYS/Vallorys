# VALLORYS Plugin - API Specification

## Base URL
```
Production: https://api.vallorys.com/v1
Staging:    https://api-staging.vallorys.com/v1
Local:      http://localhost:8000/v1
```

## Authentication

### OAuth2 + JWT
```
Authorization: Bearer <jwt_token>
X-Tenant-ID: <tenant_id>
```

### JWT Claims
```json
{
  "sub": "user_123",
  "tenant_id": "tenant_abc",
  "role": "agent",
  "permissions": ["valuation:create", "fieldpack:generate"],
  "exp": 1705312800,
  "iat": 1705226400
}
```

---

## Endpoints

### Health & Status

#### `GET /health`
Health check endpoint.

**Response 200:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "dvf_api": "healthy"
  }
}
```

---

### Valuation

#### `POST /valuation/run`
Exécute une estimation complète.

**Request:**
```json
{
  "property": {
    "address": {
      "street": "15 rue de la Paix",
      "city": "Lyon",
      "citycode": "69001",
      "postal_code": "69001",
      "lat": 45.7676,
      "lng": 4.8344
    },
    "type": "appartement",
    "surface_living": 85,
    "rooms": 4,
    "bedrooms": 2,
    "bathrooms": 1,
    "floor": 3,
    "floors_total": 5,
    "construction_year": 1920,
    "dpe_rating": "D",
    "condition": {
      "global": "good",
      "windows": "double_glazing_recent",
      "electrical": "up_to_code"
    },
    "amenities": {
      "cellar": true,
      "balcony": true,
      "elevator": true
    },
    "environment": {
      "view": "pleasant",
      "noise_level": "moderate",
      "nearby_shops": true,
      "nearby_transport": true
    }
  },
  "seller": {
    "type": "owner_occupier",
    "urgency": "moderate",
    "price_expectation": 420000
  },
  "options": {
    "include_comparables": true,
    "include_detailed_justification": true
  }
}
```

**Response 200:**
```json
{
  "valuation_id": "val_a1b2c3d4",
  "created_at": "2024-01-15T10:30:00Z",
  "property_id": "prop_x1y2z3",
  "range_low": 365000,
  "range_high": 395000,
  "price_point_recommended": 379000,
  "confidence_score": 0.85,
  "confidence_level": "high",
  "margin_percent": 7,
  "base_price_sqm_used": 4250,
  "adjustments": [
    {
      "factor": "dpe_rating",
      "impact_percent": -3,
      "direction": "negative",
      "explanation": "DPE D : légère décote par rapport au marché (moyenne C)",
      "capped": false
    },
    {
      "factor": "floor_with_elevator",
      "impact_percent": 2,
      "direction": "positive",
      "explanation": "3ème étage avec ascenseur, étage recherché",
      "capped": false
    },
    {
      "factor": "condition_global",
      "impact_percent": 0,
      "direction": "neutral",
      "explanation": "Bon état général, dans la norme du marché",
      "capped": false
    },
    {
      "factor": "balcony",
      "impact_percent": 2,
      "direction": "positive",
      "explanation": "Balcon apprécié en centre-ville",
      "capped": false
    },
    {
      "factor": "location_premium",
      "impact_percent": 5,
      "direction": "positive",
      "explanation": "Secteur prisé Lyon 1er, proche commerces et transports",
      "capped": true
    }
  ],
  "justification": {
    "summary": "Appartement bien situé en centre-ville de Lyon avec des prestations dans la moyenne haute du marché. Le DPE D représente un léger handicap compensé par l'emplacement premium et les aménagements (balcon, cave).",
    "top_positive_factors": [
      "Emplacement Lyon 1er, secteur très recherché",
      "Étage intermédiaire avec ascenseur",
      "Balcon et cave"
    ],
    "top_negative_factors": [
      "DPE D nécessitant potentiellement des travaux de rénovation énergétique",
      "Immeuble ancien (1920) avec charges potentiellement élevées"
    ],
    "market_comparison": "Prix au m² estimé : 4 459 €/m² vs médiane secteur 4 250 €/m² (+5%). Justifié par les prestations."
  },
  "risk_factors": [
    {
      "type": "regulatory",
      "description": "DPE D : interdiction de location à partir de 2034 sans rénovation",
      "severity": "medium"
    }
  ],
  "market_context": {
    "median_price_sqm": 4250,
    "p10_price_sqm": 3500,
    "p90_price_sqm": 5200,
    "transaction_count": 156,
    "trend_12m_percent": 2.3
  },
  "data_completeness": 0.92,
  "methodology_version": "2.1.0"
}
```

**Response 422 (Validation Error):**
```json
{
  "error": "validation_error",
  "message": "Invalid property data",
  "details": [
    {
      "field": "property.surface_living",
      "message": "Surface must be greater than 0",
      "code": "invalid_value"
    }
  ]
}
```

---

#### `GET /valuation/{valuation_id}`
Récupère une estimation existante.

**Response 200:**
```json
{
  "valuation_id": "val_a1b2c3d4",
  "created_at": "2024-01-15T10:30:00Z",
  "...": "same as POST response"
}
```

---

#### `GET /valuation/{valuation_id}/explain`
Explication détaillée de l'estimation.

**Query params:**
- `detail_level`: `summary` | `detailed` | `technical` (default: `detailed`)

**Response 200:**
```json
{
  "valuation_id": "val_a1b2c3d4",
  "detail_level": "detailed",
  "explanation": {
    "methodology": "L'estimation utilise la méthode des comparables ajustée avec pondération des critères. Base : prix/m² médian du secteur sur 12 mois glissants.",
    "base_calculation": {
      "median_price_sqm": 4250,
      "surface": 85,
      "base_price": 361250,
      "formula": "4250 €/m² × 85 m² = 361 250 €"
    },
    "adjustments_breakdown": [
      {
        "factor": "location_premium",
        "weight": 0.25,
        "raw_impact_percent": 8,
        "capped_impact_percent": 5,
        "cap_reason": "Plafonnement localisation à +5% max",
        "calculation": "361 250 € × 5% = +18 062 €"
      }
    ],
    "final_calculation": {
      "base": 361250,
      "total_adjustments": 21750,
      "price_point": 379000,
      "range_margin": 0.07,
      "range_low": 365000,
      "range_high": 395000
    },
    "confidence_factors": {
      "data_quality": 0.90,
      "comparable_count": 0.85,
      "data_recency": 0.92,
      "final_score": 0.85
    }
  }
}
```

---

### Field Pack

#### `POST /fieldpack/generate`
Génère le pack terrain complet.

**Request:**
```json
{
  "valuation_id": "val_a1b2c3d4",
  "seller": {
    "type": "heir",
    "urgency": "moderate",
    "price_expectation": 420000,
    "personality_hints": "analytical",
    "previous_estimates": [
      {
        "source": "Agence X",
        "amount": 450000,
        "date": "2024-01-01"
      }
    ]
  },
  "generate": {
    "argumentaire": true,
    "script_rdv": true,
    "checklist": true,
    "templates": ["objection_response", "email_pre_rdv"]
  },
  "options": {
    "tone": "empathetic",
    "rdv_duration_minutes": 60
  }
}
```

**Response 200:**
```json
{
  "fieldpack_id": "fp_x1y2z3",
  "created_at": "2024-01-15T10:35:00Z",
  "valuation_id": "val_a1b2c3d4",

  "argumentaire": {
    "opening": "Je comprends que vendre un bien hérité peut être une décision chargée d'émotions. Mon rôle est de vous accompagner avec transparence et de vous donner toutes les clés pour prendre la meilleure décision.",
    "key_points": [
      {
        "point": "Estimation basée sur des données réelles",
        "argument": "Notre estimation s'appuie sur 156 ventes réalisées dans votre secteur ces 12 derniers mois. Ce n'est pas une estimation \"au doigt mouillé\", mais une analyse factuelle du marché.",
        "proof": "Prix médian constaté : 4 250 €/m² dans Lyon 1er"
      },
      {
        "point": "Écart avec l'estimation précédente",
        "argument": "L'estimation de l'Agence X à 450 000 € est 18% au-dessus du marché. Une telle surévaluation risque de rallonger significativement le délai de vente et de vous faire perdre des acquéreurs sérieux.",
        "proof": "Délai moyen de vente dans le secteur : 65 jours au prix marché, 120+ jours si surévalué de plus de 10%"
      },
      {
        "point": "Le bon prix pour une vente sereine",
        "argument": "À 379 000 €, votre bien se positionne dans la tranche haute du marché tout en restant attractif. C'est le prix qui génère le plus de visites qualifiées.",
        "proof": "Fourchette recommandée : 365 000 € - 395 000 €"
      }
    ],
    "closing": "Mon objectif est que vous vendiez dans les meilleures conditions, au meilleur prix réaliste. Je préfère vous donner un conseil honnête plutôt qu'un chiffre flatteur qui vous ferait perdre du temps."
  },

  "script_rdv": {
    "total_duration_minutes": 60,
    "phases": [
      {
        "phase": "Accueil & mise en confiance",
        "duration_minutes": 5,
        "timing": "0-5 min",
        "objectives": ["Créer un climat de confiance", "Montrer de l'empathie pour la situation"],
        "script": "Bonjour [Prénom], merci de me recevoir. Je sais que vendre un bien familial n'est jamais une décision facile. Avant de parler chiffres, j'aimerais comprendre votre situation et vos attentes.",
        "tips": ["Écouter activement", "Ne pas parler prix immédiatement"]
      },
      {
        "phase": "Découverte",
        "duration_minutes": 15,
        "timing": "5-20 min",
        "objectives": ["Comprendre le contexte de vente", "Identifier les vraies motivations"],
        "questions": [
          "Depuis quand êtes-vous propriétaire de ce bien ?",
          "Qu'est-ce qui vous a décidé à vendre maintenant ?",
          "Avez-vous un projet précis après la vente ?",
          "Y a-t-il d'autres héritiers impliqués dans cette décision ?"
        ],
        "script": "Pour vous donner le meilleur conseil possible, j'ai besoin de comprendre votre situation...",
        "tips": ["Prendre des notes", "Reformuler pour valider"]
      },
      {
        "phase": "Visite du bien",
        "duration_minutes": 15,
        "timing": "20-35 min",
        "objectives": ["Valider les informations", "Identifier points forts/faibles"],
        "script": "Visitons ensemble le bien. Pouvez-vous me montrer les derniers travaux réalisés ?",
        "checklist": ["Surface réelle", "État DPE", "Vue et luminosité", "Nuisances éventuelles"]
      },
      {
        "phase": "Présentation estimation",
        "duration_minutes": 15,
        "timing": "35-50 min",
        "objectives": ["Présenter l'estimation de façon pédagogique", "Anticiper les objections"],
        "script": "Passons à l'estimation. Je vais vous expliquer précisément comment nous arrivons à ce chiffre, étape par étape.",
        "key_moments": [
          "Montrer les comparables",
          "Expliquer les ajustements",
          "Comparer avec l'estimation précédente"
        ],
        "tips": ["Utiliser des visuels", "Laisser le silence après le prix"]
      },
      {
        "phase": "Traitement objections & closing",
        "duration_minutes": 10,
        "timing": "50-60 min",
        "objectives": ["Répondre aux objections", "Obtenir le mandat ou un RDV de suivi"],
        "common_objections": [
          "L'autre agence m'a dit plus",
          "Je veux tester le marché plus haut"
        ],
        "script": "Avez-vous des questions sur cette estimation ? Je comprends que le chiffre puisse vous surprendre...",
        "closing_options": [
          "Mandat exclusif avec garantie de résultat",
          "Test de 3 semaines au prix suggéré",
          "Second RDV avec les co-héritiers"
        ]
      }
    ]
  },

  "checklist": {
    "categories": [
      {
        "category": "Documents à récupérer",
        "items": [
          { "item": "Titre de propriété", "required": true, "note": "Original ou copie certifiée" },
          { "item": "Diagnostics techniques (DPE, amiante, plomb...)", "required": true },
          { "item": "Taxe foncière dernière année", "required": true },
          { "item": "Charges de copropriété (3 derniers appels)", "required": true },
          { "item": "PV des 3 dernières AG", "required": true },
          { "item": "Règlement de copropriété", "required": false }
        ]
      },
      {
        "category": "Points à vérifier sur place",
        "items": [
          { "item": "Surface réelle (mesurer si doute)", "required": true },
          { "item": "Conformité électrique", "required": true },
          { "item": "État des fenêtres et volets", "required": true },
          { "item": "Fonctionnement VMC/ventilation", "required": false },
          { "item": "État parties communes", "required": true }
        ]
      },
      {
        "category": "Photos à prendre",
        "items": [
          { "item": "Façade immeuble", "required": true },
          { "item": "Entrée/hall", "required": true },
          { "item": "Chaque pièce (2-3 angles)", "required": true },
          { "item": "Vue depuis fenêtres principales", "required": true },
          { "item": "Balcon/terrasse", "required": true },
          { "item": "Cave/parking si applicable", "required": false }
        ]
      },
      {
        "category": "Questions à poser",
        "items": [
          { "item": "Travaux votés en AG non encore réalisés ?", "required": true },
          { "item": "Litiges en cours dans la copropriété ?", "required": true },
          { "item": "Projets urbains à proximité ?", "required": false }
        ]
      }
    ]
  },

  "templates": {
    "objection_response": {
      "objection": "L'agence X m'a estimé à 450 000 €",
      "response_quick": "Je comprends. Permettez-moi de vous montrer précisément pourquoi notre estimation diffère et sur quelles données elle s'appuie.",
      "response_detailed": "L'écart de 70 000 € avec l'estimation de l'Agence X est significatif. Regardons ensemble les 156 ventes réelles dans votre secteur ces 12 derniers mois : le prix médian est de 4 250 €/m². À 450 000 €, votre bien serait affiché à 5 294 €/m², soit 24% au-dessus du marché. Les biens surévalués de plus de 15% restent en moyenne 4 mois de plus sur le marché et finissent souvent par se vendre en dessous du prix initial qu'ils auraient pu obtenir.",
      "follow_up_question": "Avez-vous demandé à l'Agence X sur quelles ventes comparables ils s'appuient ?"
    },
    "email_pre_rdv": {
      "subject": "Notre rendez-vous du [DATE] - Estimation de votre bien",
      "body": "Bonjour [Prénom],\n\nJe vous confirme notre rendez-vous le [DATE] à [HEURE] pour l'estimation de votre appartement situé [ADRESSE].\n\nPour que notre rencontre soit la plus productive possible, pourriez-vous préparer :\n- Le titre de propriété ou attestation notariée\n- Les diagnostics techniques existants\n- Les 3 derniers appels de charges\n\nJe prévois environ 1h pour la visite et la présentation de l'estimation.\n\nN'hésitez pas à me contacter si vous avez des questions d'ici là.\n\nBien cordialement,\n[SIGNATURE]"
    }
  }
}
```

---

### Objection Coach

#### `POST /objection/respond`
Réponse temps réel à une objection.

**Request:**
```json
{
  "objection_text": "Mon voisin a vendu son appartement 20% plus cher que votre estimation l'année dernière",
  "objection_category": "neighbor_sold_higher",
  "valuation_id": "val_a1b2c3d4",
  "conversation_history": [
    { "role": "agent", "text": "Voici mon estimation basée sur les données du marché..." },
    { "role": "seller", "text": "Mon voisin a vendu son appartement 20% plus cher que votre estimation l'année dernière" }
  ]
}
```

**Response 200:**
```json
{
  "objection_id": "obj_m1n2o3",
  "quick_response": "Intéressant ! Pouvez-vous me dire à quel étage et quelle surface ? Chaque bien a ses spécificités.",
  "detailed_response": "La vente de votre voisin est une référence intéressante, mais plusieurs facteurs peuvent expliquer la différence. Premièrement, le marché a évolué depuis l'année dernière (-2% sur le secteur). Deuxièmement, chaque bien est unique : l'étage, l'exposition, l'état intérieur, les travaux réalisés... Avez-vous des détails sur son appartement ? Était-il rénové ? À quel étage ? Cela nous permettrait de comparer objectivement.",
  "follow_up_question": "Savez-vous si votre voisin avait fait des travaux de rénovation avant la vente ?",
  "proof_point": "Notre estimation s'appuie sur 156 ventes dans votre secteur ces 12 derniers mois, pas sur un cas isolé. Prix médian constaté : 4 250 €/m².",
  "suggested_tone": "factual",
  "additional_tips": [
    "Ne pas dénigrer le voisin ou sa vente",
    "Ramener à des données objectives",
    "Proposer de vérifier ensemble s'il y a des informations publiques"
  ]
}
```

---

### CRM Webhooks

#### `POST /crm/webhook`
Réception des webhooks CRM.

**Headers:**
```
X-Webhook-Secret: <secret>
X-CRM-Type: hubspot
```

**Request (lead.created):**
```json
{
  "event_type": "lead.created",
  "timestamp": "2024-01-15T10:00:00Z",
  "crm_type": "hubspot",
  "data": {
    "lead_id": "lead_123",
    "contact": {
      "email": "vendeur@example.com",
      "first_name": "Jean",
      "last_name": "Dupont",
      "phone": "+33612345678"
    },
    "property": {
      "address": "15 rue de la Paix, 69001 Lyon",
      "type": "appartement",
      "surface": 85
    }
  }
}
```

**Response 200:**
```json
{
  "status": "processed",
  "actions_taken": [
    "lead_enriched",
    "valuation_queued"
  ],
  "valuation_id": "val_pending_xyz"
}
```

---

### Analytics

#### `GET /analytics/dashboard`
Métriques dashboard réseau.

**Query params:**
- `scope`: `agent` | `agency` | `network`
- `period`: `7d` | `30d` | `90d` | `12m`
- `agent_id`: (optionnel, si scope=agent)

**Response 200:**
```json
{
  "scope": "agency",
  "period": "30d",
  "generated_at": "2024-01-15T11:00:00Z",
  "metrics": {
    "valuations": {
      "total": 127,
      "by_type": {
        "maison": 45,
        "appartement": 82
      },
      "avg_confidence": 0.82
    },
    "accuracy": {
      "mae": 12500,
      "mape": 4.2,
      "within_range_percent": 78,
      "sample_size": 34,
      "note": "Basé sur les ventes finalisées avec prix connu"
    },
    "conversion": {
      "rdv_scheduled": 89,
      "mandates_signed": 42,
      "conversion_rate": 0.47
    },
    "pricing": {
      "avg_decote_vs_seller_expectation": -8.3,
      "avg_decote_vs_final_sale": -2.1
    },
    "objections": {
      "total_handled": 156,
      "top_categories": [
        { "category": "price_too_low", "count": 67, "resolution_rate": 0.72 },
        { "category": "neighbor_sold_higher", "count": 34, "resolution_rate": 0.68 },
        { "category": "other_agency_estimate", "count": 28, "resolution_rate": 0.75 }
      ]
    },
    "usage": {
      "fieldpack_generated": 98,
      "scripts_viewed": 156,
      "coach_sessions": 67,
      "avg_rdv_duration_minutes": 52
    }
  }
}
```

---

#### `POST /analytics/export`
Export des données.

**Request:**
```json
{
  "data_type": "valuations",
  "format": "csv",
  "filters": {
    "date_from": "2024-01-01",
    "date_to": "2024-01-31",
    "property_type": "appartement"
  }
}
```

**Response 200:**
```json
{
  "export_id": "exp_abc123",
  "status": "processing",
  "estimated_rows": 127,
  "callback_url": "/analytics/export/exp_abc123"
}
```

---

### Reports

#### `POST /reports/generate`
Génère un rapport PDF.

**Request:**
```json
{
  "valuation_id": "val_a1b2c3d4",
  "template": "detailed",
  "include_sections": ["summary", "property_details", "market_analysis", "methodology"],
  "branding": {
    "agency_name": "Immobilier Lyon Centre",
    "logo_url": "https://example.com/logo.png",
    "primary_color": "#1E40AF"
  }
}
```

**Response 202:**
```json
{
  "report_id": "rpt_xyz789",
  "status": "generating",
  "estimated_time_seconds": 30,
  "callback_url": "/reports/rpt_xyz789"
}
```

#### `GET /reports/{report_id}`
Récupère un rapport généré.

**Response 200:**
```json
{
  "report_id": "rpt_xyz789",
  "status": "ready",
  "download_url": "https://storage.vallorys.com/reports/rpt_xyz789.pdf",
  "expires_at": "2024-01-16T10:30:00Z",
  "page_count": 8,
  "generated_at": "2024-01-15T10:31:00Z"
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": {},
  "request_id": "req_abc123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 422 | Données d'entrée invalides |
| `not_found` | 404 | Ressource non trouvée |
| `unauthorized` | 401 | Token invalide ou expiré |
| `forbidden` | 403 | Permissions insuffisantes |
| `rate_limited` | 429 | Trop de requêtes |
| `internal_error` | 500 | Erreur serveur |
| `service_unavailable` | 503 | Service temporairement indisponible |
| `dvf_unavailable` | 503 | API DVF indisponible, fallback utilisé |

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/valuation/run` | 50 | 1 min |
| `/fieldpack/generate` | 30 | 1 min |
| `/objection/respond` | 100 | 1 min |
| `/analytics/*` | 200 | 1 min |
| `/crm/webhook` | 500 | 1 min |

**Headers de réponse:**
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705312860
```

---

## Webhooks Sortants

### Configuration
```json
{
  "webhook_url": "https://your-crm.com/webhook",
  "events": ["valuation.completed", "report.ready"],
  "secret": "whsec_xxx"
}
```

### Événements

#### `valuation.completed`
```json
{
  "event": "valuation.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "valuation_id": "val_a1b2c3d4",
    "property_id": "prop_x1y2z3",
    "range_low": 365000,
    "range_high": 395000,
    "confidence_level": "high"
  }
}
```

### Signature
```
X-Webhook-Signature: sha256=<HMAC-SHA256(payload, secret)>
```
