-- VALLORYS Database Initialization
-- Creates initial schema and extensions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema for default tenant (development)
CREATE SCHEMA IF NOT EXISTS tenant_default;

-- Tenants table (public schema)
CREATE TABLE IF NOT EXISTS public.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    schema_name VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table (public schema, cross-tenant admins)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tenant_id UUID REFERENCES public.tenants(id),
    role VARCHAR(50) NOT NULL DEFAULT 'agent',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_tenant ON public.users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- Insert default tenant for development
INSERT INTO public.tenants (name, slug, schema_name)
VALUES ('Development', 'dev', 'tenant_default')
ON CONFLICT (slug) DO NOTHING;

-- Set search path for tenant schema
SET search_path TO tenant_default, public;

-- Properties table (per-tenant)
CREATE TABLE IF NOT EXISTS tenant_default.properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255),
    address JSONB NOT NULL,
    property_type VARCHAR(50) NOT NULL,
    surface_living NUMERIC(10, 2) NOT NULL,
    surface_land NUMERIC(10, 2),
    rooms INTEGER,
    bedrooms INTEGER,
    bathrooms INTEGER,
    floor INTEGER,
    floors_total INTEGER,
    construction_year INTEGER,
    dpe_rating VARCHAR(10),
    ges_rating VARCHAR(10),
    condition JSONB,
    amenities JSONB,
    environment JSONB,
    renovation JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sellers table (per-tenant)
CREATE TABLE IF NOT EXISTS tenant_default.sellers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255),
    seller_type VARCHAR(50),
    urgency VARCHAR(50),
    motivation TEXT,
    price_expectation NUMERIC(12, 2),
    previous_estimates JSONB DEFAULT '[]',
    objections_history JSONB DEFAULT '[]',
    personality_hints VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Valuations table (per-tenant)
CREATE TABLE IF NOT EXISTS tenant_default.valuations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES tenant_default.properties(id),
    seller_id UUID REFERENCES tenant_default.sellers(id),
    range_low NUMERIC(12, 2) NOT NULL,
    range_high NUMERIC(12, 2) NOT NULL,
    price_point_recommended NUMERIC(12, 2) NOT NULL,
    confidence_score NUMERIC(5, 4) NOT NULL,
    confidence_level VARCHAR(20) NOT NULL,
    margin_percent NUMERIC(5, 2) NOT NULL,
    base_price_sqm_used NUMERIC(10, 2) NOT NULL,
    adjustments JSONB DEFAULT '[]',
    justification JSONB,
    risk_factors JSONB DEFAULT '[]',
    market_context JSONB,
    data_completeness NUMERIC(5, 4),
    methodology_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Field packs table (per-tenant)
CREATE TABLE IF NOT EXISTS tenant_default.fieldpacks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    valuation_id UUID REFERENCES tenant_default.valuations(id),
    argumentaire JSONB,
    script_rdv JSONB,
    checklist JSONB,
    templates JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Objection events table (per-tenant)
CREATE TABLE IF NOT EXISTS tenant_default.objection_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    valuation_id UUID REFERENCES tenant_default.valuations(id),
    objection_text TEXT NOT NULL,
    objection_category VARCHAR(50),
    response_used VARCHAR(20),
    outcome VARCHAR(50),
    agent_feedback VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Analytics events table (per-tenant)
CREATE TABLE IF NOT EXISTS tenant_default.events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    entity_type VARCHAR(50),
    user_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for tenant schema
CREATE INDEX IF NOT EXISTS idx_properties_external ON tenant_default.properties(external_id);
CREATE INDEX IF NOT EXISTS idx_valuations_property ON tenant_default.valuations(property_id);
CREATE INDEX IF NOT EXISTS idx_valuations_created ON tenant_default.valuations(created_at);
CREATE INDEX IF NOT EXISTS idx_events_type ON tenant_default.events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created ON tenant_default.events(created_at);

-- Grant permissions
GRANT ALL ON SCHEMA tenant_default TO vallorys;
GRANT ALL ON ALL TABLES IN SCHEMA tenant_default TO vallorys;
GRANT ALL ON ALL SEQUENCES IN SCHEMA tenant_default TO vallorys;
