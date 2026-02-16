export interface Client {
  id: string;
  client_id: string;
  company_name: string;
  sector: string | null;
  agent_name: string;
  owner_name: string | null;
  owner_email: string | null;
  owner_phone: string | null;
  plan: string;
  monthly_fee_eur: number;
  whatsapp_enabled: boolean;
  email_enabled: boolean;
  voice_enabled: boolean;
  openclaw_port: number | null;
  voice_port: number | null;
  twilio_phone: string | null;
  domain: string | null;
  is_active: boolean;
  onboarded_at: string | null;
  created_at: string;
}

export interface Lead {
  id: string;
  client_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  company: string | null;
  role: string | null;
  source: string;
  channel: "whatsapp" | "email" | "phone" | "web_form" | "manual";
  status:
    | "new"
    | "contacted"
    | "qualifying"
    | "qualified"
    | "booked"
    | "won"
    | "lost"
    | "cold";
  qualification_score: number;
  qualification_data: Record<string, unknown>;
  notes: string;
  tags: string[];
  first_contact_at: string | null;
  last_contact_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  client_id: string;
  lead_id: string | null;
  role: "agent" | "lead" | "system";
  content: string;
  channel: "whatsapp" | "email" | "phone" | "web_form" | "manual";
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface Call {
  id: string;
  client_id: string;
  lead_id: string | null;
  phone_number: string;
  direction: "inbound" | "outbound";
  status: string;
  transcript: string | null;
  summary: string | null;
  duration_seconds: number;
  cost_eur: number;
  created_at: string;
  ended_at: string | null;
}

export interface Booking {
  id: string;
  client_id: string;
  lead_id: string | null;
  scheduled_at: string;
  duration_minutes: number;
  meeting_type: string;
  meeting_url: string | null;
  status: "confirmed" | "rescheduled" | "cancelled" | "completed" | "no_show";
  notes: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_leads: number;
  hot_leads: number;
  warm_leads: number;
  cold_leads: number;
  booked_today: number;
  calls_today: number;
  leads_today: number;
  avg_response_time: number | null;
  conversion_rate: number;
}
