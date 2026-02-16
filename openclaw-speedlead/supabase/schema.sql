-- ═══════════════════════════════════════════════════════════════
-- SpeedLead AI - Supabase Database Schema
-- Multi-tenant B2B lead management for Italian companies
-- ═══════════════════════════════════════════════════════════════

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- ─── ENUM TYPES ──────────────────────────────────────────────

CREATE TYPE lead_status AS ENUM (
    'new',
    'contacted',
    'qualifying',
    'qualified',
    'booked',
    'won',
    'lost',
    'cold'
);

CREATE TYPE lead_channel AS ENUM (
    'whatsapp',
    'email',
    'phone',
    'web_form',
    'manual'
);

CREATE TYPE call_direction AS ENUM ('inbound', 'outbound');

CREATE TYPE call_status AS ENUM (
    'initiated',
    'ringing',
    'in_progress',
    'completed',
    'missed',
    'failed',
    'busy',
    'no_answer'
);

CREATE TYPE booking_status AS ENUM (
    'confirmed',
    'rescheduled',
    'cancelled',
    'completed',
    'no_show'
);

CREATE TYPE action_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled'
);

-- ─── CLIENTS (tenants) ──────────────────────────────────────

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id TEXT UNIQUE NOT NULL,  -- slug: "acme-srl"
    company_name TEXT NOT NULL,
    sector TEXT,
    agent_name TEXT DEFAULT 'Marco',
    owner_name TEXT,
    owner_email TEXT,
    owner_phone TEXT,

    -- Subscription
    plan TEXT DEFAULT 'standard',  -- 'standard', 'premium', 'enterprise'
    monthly_fee_eur NUMERIC(10,2) DEFAULT 690.00,
    setup_fee_eur NUMERIC(10,2) DEFAULT 1900.00,

    -- Channels
    whatsapp_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    voice_enabled BOOLEAN DEFAULT FALSE,

    -- Infrastructure
    openclaw_port INTEGER,
    voice_port INTEGER,
    twilio_phone TEXT,
    domain TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    onboarded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_clients_client_id ON clients(client_id);
CREATE INDEX idx_clients_is_active ON clients(is_active);

-- ─── CLIENT CONFIGS ──────────────────────────────────────────

CREATE TABLE client_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,

    -- Company info (injected into system prompt)
    company_description TEXT,
    products_services TEXT,
    unique_selling_points TEXT,
    target_customers TEXT,
    price_range TEXT,

    -- Working hours
    work_hours_start TIME DEFAULT '08:00',
    work_hours_end TIME DEFAULT '20:00',
    work_timezone TEXT DEFAULT 'Europe/Rome',
    work_days TEXT[] DEFAULT ARRAY['mon','tue','wed','thu','fri'],

    -- Qualification settings
    min_score_for_booking INTEGER DEFAULT 70,
    auto_book BOOLEAN DEFAULT TRUE,
    notify_owner_threshold INTEGER DEFAULT 60,

    -- Follow-up settings
    followup_enabled BOOLEAN DEFAULT TRUE,
    followup_delays_hours INTEGER[] DEFAULT ARRAY[2, 24, 72, 168],
    max_followup_attempts INTEGER DEFAULT 4,

    -- CRM integration
    crm_provider TEXT,  -- 'hubspot', 'zoho', 'teamsystem', null
    crm_config JSONB DEFAULT '{}'::JSONB,

    -- Calendar integration
    calendar_provider TEXT DEFAULT 'calcom',  -- 'calcom', 'google'
    calendar_config JSONB DEFAULT '{}'::JSONB,

    -- GDPR
    privacy_policy_url TEXT,
    dpa_signed BOOLEAN DEFAULT FALSE,
    data_retention_days INTEGER DEFAULT 365,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(client_id)
);

-- ─── LEADS ───────────────────────────────────────────────────

CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,

    -- Contact info
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    company TEXT,
    role TEXT,  -- Job title / role

    -- Lead data
    source TEXT DEFAULT 'web_form',  -- 'web_form', 'fair', 'referral', 'cold', 'email', 'phone'
    channel lead_channel DEFAULT 'whatsapp',
    status lead_status DEFAULT 'new',

    -- Qualification
    qualification_score INTEGER DEFAULT 0 CHECK (qualification_score >= 0 AND qualification_score <= 100),
    qualification_data JSONB DEFAULT '{}'::JSONB,
    -- BANT fields in qualification_data:
    -- { "budget": {"value": "10k-50k", "confirmed": true},
    --   "authority": {"is_decision_maker": true, "decision_maker_name": ""},
    --   "need": {"description": "...", "urgency": "high"},
    --   "timeline": {"deadline": "2026-03-01", "urgency": "high"} }

    -- Tracking
    notes TEXT DEFAULT '',
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Follow-up
    next_action TEXT,
    next_action_at TIMESTAMPTZ,
    followup_count INTEGER DEFAULT 0,

    -- Timestamps
    first_contact_at TIMESTAMPTZ,
    last_contact_at TIMESTAMPTZ,
    qualified_at TIMESTAMPTZ,
    converted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leads_client_id ON leads(client_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_phone ON leads(phone);
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_score ON leads(qualification_score DESC);
CREATE INDEX idx_leads_created ON leads(created_at DESC);
CREATE INDEX idx_leads_next_action ON leads(next_action_at) WHERE next_action_at IS NOT NULL;

-- ─── CONVERSATIONS ──────────────────────────────────────────

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,

    role TEXT NOT NULL CHECK (role IN ('agent', 'lead', 'system')),
    content TEXT NOT NULL,
    channel lead_channel NOT NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,
    -- For email: {"subject": "...", "message_id": "...", "to": "..."}
    -- For whatsapp: {"message_id": "...", "media_type": "..."}
    -- For phone: {"call_id": "...", "is_transcription": true}

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_client_id ON conversations(client_id);
CREATE INDEX idx_conversations_lead_id ON conversations(lead_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);
CREATE INDEX idx_conversations_channel ON conversations(channel);

-- ─── CALLS ──────────────────────────────────────────────────

CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,

    phone_number TEXT NOT NULL,
    direction call_direction NOT NULL,
    status call_status DEFAULT 'initiated',

    -- Recording & transcript
    transcript TEXT,
    summary TEXT,
    recording_url TEXT,

    -- Duration & cost
    duration_seconds INTEGER DEFAULT 0,
    cost_eur NUMERIC(10,4) DEFAULT 0,

    -- Twilio reference
    external_id TEXT,  -- Twilio CallSid

    created_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

CREATE INDEX idx_calls_client_id ON calls(client_id);
CREATE INDEX idx_calls_lead_id ON calls(lead_id);
CREATE INDEX idx_calls_phone ON calls(phone_number);
CREATE INDEX idx_calls_created ON calls(created_at DESC);

-- ─── BOOKINGS ───────────────────────────────────────────────

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,

    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    meeting_type TEXT DEFAULT 'video',  -- 'call', 'video', 'in_person'
    meeting_url TEXT,

    status booking_status DEFAULT 'confirmed',
    notes TEXT,

    -- External calendar reference
    external_id TEXT,  -- Cal.com or Google Calendar event ID

    -- Reminders
    reminder_24h_sent BOOLEAN DEFAULT FALSE,
    reminder_1h_sent BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_bookings_client_id ON bookings(client_id);
CREATE INDEX idx_bookings_lead_id ON bookings(lead_id);
CREATE INDEX idx_bookings_scheduled ON bookings(scheduled_at);
CREATE INDEX idx_bookings_status ON bookings(status);

-- ─── SCHEDULED ACTIONS ──────────────────────────────────────

CREATE TABLE scheduled_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,

    action_type TEXT NOT NULL,  -- 'followup_message', 'reminder', 'crm_sync'
    scheduled_at TIMESTAMPTZ NOT NULL,

    payload JSONB DEFAULT '{}'::JSONB,
    status action_status DEFAULT 'pending',

    executed_at TIMESTAMPTZ,
    result JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scheduled_client ON scheduled_actions(client_id);
CREATE INDEX idx_scheduled_due ON scheduled_actions(scheduled_at)
    WHERE status = 'pending';
CREATE INDEX idx_scheduled_status ON scheduled_actions(status);

-- ─── ANALYTICS / DAILY STATS ────────────────────────────────

CREATE TABLE daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id TEXT NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    stat_date DATE NOT NULL,

    leads_new INTEGER DEFAULT 0,
    leads_contacted INTEGER DEFAULT 0,
    leads_qualified INTEGER DEFAULT 0,
    leads_booked INTEGER DEFAULT 0,
    leads_won INTEGER DEFAULT 0,
    leads_lost INTEGER DEFAULT 0,

    calls_inbound INTEGER DEFAULT 0,
    calls_outbound INTEGER DEFAULT 0,
    calls_duration_seconds INTEGER DEFAULT 0,
    calls_cost_eur NUMERIC(10,4) DEFAULT 0,

    messages_sent INTEGER DEFAULT 0,
    messages_received INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    emails_received INTEGER DEFAULT 0,

    bookings_created INTEGER DEFAULT 0,
    bookings_completed INTEGER DEFAULT 0,
    bookings_no_show INTEGER DEFAULT 0,

    avg_response_time_seconds NUMERIC(10,2),
    avg_qualification_score NUMERIC(5,2),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(client_id, stat_date)
);

CREATE INDEX idx_daily_stats_client ON daily_stats(client_id);
CREATE INDEX idx_daily_stats_date ON daily_stats(stat_date DESC);

-- ─── ROW LEVEL SECURITY ─────────────────────────────────────

-- Enable RLS on all tables
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE scheduled_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_stats ENABLE ROW LEVEL SECURITY;

-- Service role can access everything (for backend services)
CREATE POLICY "Service role full access" ON clients
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON client_configs
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON leads
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON conversations
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON calls
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON bookings
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON scheduled_actions
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON daily_stats
    FOR ALL USING (auth.role() = 'service_role');

-- Dashboard users can only see their own client data
-- (requires auth.users with client_id in metadata)
CREATE POLICY "Users see own client data" ON leads
    FOR SELECT USING (
        client_id = (auth.jwt() ->> 'client_id')
    );
CREATE POLICY "Users see own client data" ON conversations
    FOR SELECT USING (
        client_id = (auth.jwt() ->> 'client_id')
    );
CREATE POLICY "Users see own client data" ON calls
    FOR SELECT USING (
        client_id = (auth.jwt() ->> 'client_id')
    );
CREATE POLICY "Users see own client data" ON bookings
    FOR SELECT USING (
        client_id = (auth.jwt() ->> 'client_id')
    );
CREATE POLICY "Users see own client data" ON daily_stats
    FOR SELECT USING (
        client_id = (auth.jwt() ->> 'client_id')
    );

-- ─── REALTIME ───────────────────────────────────────────────

-- Enable realtime for live dashboard updates
ALTER PUBLICATION supabase_realtime ADD TABLE leads;
ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
ALTER PUBLICATION supabase_realtime ADD TABLE calls;
ALTER PUBLICATION supabase_realtime ADD TABLE bookings;

-- ─── FUNCTIONS ──────────────────────────────────────────────

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_client_configs_updated_at
    BEFORE UPDATE ON client_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_bookings_updated_at
    BEFORE UPDATE ON bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Update first_contact_at when lead status changes from 'new'
CREATE OR REPLACE FUNCTION update_lead_contact_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = 'new' AND NEW.status != 'new' AND NEW.first_contact_at IS NULL THEN
        NEW.first_contact_at = NOW();
    END IF;
    NEW.last_contact_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_lead_timestamps
    BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_lead_contact_timestamp();

-- Function to get dashboard stats for a client
CREATE OR REPLACE FUNCTION get_client_dashboard_stats(p_client_id TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_leads', (SELECT COUNT(*) FROM leads WHERE client_id = p_client_id),
        'hot_leads', (SELECT COUNT(*) FROM leads WHERE client_id = p_client_id AND qualification_score >= 70),
        'warm_leads', (SELECT COUNT(*) FROM leads WHERE client_id = p_client_id AND qualification_score BETWEEN 40 AND 69),
        'cold_leads', (SELECT COUNT(*) FROM leads WHERE client_id = p_client_id AND qualification_score < 40),
        'booked_today', (SELECT COUNT(*) FROM bookings WHERE client_id = p_client_id AND DATE(scheduled_at) = CURRENT_DATE),
        'calls_today', (SELECT COUNT(*) FROM calls WHERE client_id = p_client_id AND DATE(created_at) = CURRENT_DATE),
        'leads_today', (SELECT COUNT(*) FROM leads WHERE client_id = p_client_id AND DATE(created_at) = CURRENT_DATE),
        'avg_response_time', (
            SELECT AVG(EXTRACT(EPOCH FROM (first_contact_at - created_at)))
            FROM leads
            WHERE client_id = p_client_id AND first_contact_at IS NOT NULL
            AND created_at > NOW() - INTERVAL '30 days'
        ),
        'conversion_rate', (
            SELECT CASE
                WHEN COUNT(*) = 0 THEN 0
                ELSE ROUND(COUNT(*) FILTER (WHERE status IN ('booked', 'won'))::NUMERIC / COUNT(*)::NUMERIC * 100, 1)
            END
            FROM leads
            WHERE client_id = p_client_id
            AND created_at > NOW() - INTERVAL '30 days'
        )
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
