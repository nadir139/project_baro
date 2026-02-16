import { NextRequest, NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase";

// GET /api/clients - List all clients
export async function GET() {
  const supabase = createAdminClient();

  const { data, error } = await supabase
    .from("clients")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ clients: data });
}

// POST /api/clients - Create a new client
export async function POST(request: NextRequest) {
  const supabase = createAdminClient();
  const body = await request.json();

  const { data: client, error: clientError } = await supabase
    .from("clients")
    .insert({
      client_id: body.client_id,
      company_name: body.company_name,
      sector: body.sector,
      agent_name: body.agent_name || "Marco",
      owner_name: body.owner_name,
      owner_email: body.owner_email,
      owner_phone: body.owner_phone,
      plan: body.plan || "standard",
      whatsapp_enabled: body.whatsapp_enabled ?? true,
      email_enabled: body.email_enabled ?? true,
      voice_enabled: body.voice_enabled ?? false,
    })
    .select()
    .single();

  if (clientError) {
    return NextResponse.json({ error: clientError.message }, { status: 400 });
  }

  // Create default config
  const { error: configError } = await supabase
    .from("client_configs")
    .insert({
      client_id: body.client_id,
      company_description: body.company_description || "",
      products_services: body.products_services || "",
      unique_selling_points: body.unique_selling_points || "",
      target_customers: body.target_customers || "",
      price_range: body.price_range || "",
      crm_provider: body.crm_provider || null,
      calendar_provider: body.calendar_provider || "calcom",
      privacy_policy_url: body.privacy_policy_url || "",
    });

  if (configError) {
    return NextResponse.json({ error: configError.message }, { status: 400 });
  }

  return NextResponse.json({ client }, { status: 201 });
}
