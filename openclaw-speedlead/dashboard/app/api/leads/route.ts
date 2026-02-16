import { NextRequest, NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase";

// GET /api/leads - List leads with optional stats
export async function GET(request: NextRequest) {
  const supabase = createAdminClient();
  const { searchParams } = new URL(request.url);

  const clientId = searchParams.get("client_id");
  const status = searchParams.get("status");
  const wantStats = searchParams.get("stats") === "true";
  const limit = parseInt(searchParams.get("limit") || "50");
  const offset = parseInt(searchParams.get("offset") || "0");

  // Build query
  let query = supabase
    .from("leads")
    .select("*", { count: "exact" })
    .order("created_at", { ascending: false })
    .range(offset, offset + limit - 1);

  if (clientId) {
    query = query.eq("client_id", clientId);
  }
  if (status) {
    query = query.eq("status", status);
  }

  const { data, count, error } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const response: Record<string, unknown> = {
    leads: data,
    total: count,
  };

  // Include stats if requested
  if (wantStats && clientId) {
    const { data: statsData } = await supabase.rpc(
      "get_client_dashboard_stats",
      { p_client_id: clientId }
    );
    response.stats = statsData;
  } else if (wantStats) {
    // Compute basic stats across all clients
    const now = new Date();
    const todayStart = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate()
    ).toISOString();

    const [hotRes, warmRes, todayRes, bookedRes] = await Promise.all([
      supabase
        .from("leads")
        .select("id", { count: "exact", head: true })
        .gte("qualification_score", 70),
      supabase
        .from("leads")
        .select("id", { count: "exact", head: true })
        .gte("qualification_score", 40)
        .lt("qualification_score", 70),
      supabase
        .from("leads")
        .select("id", { count: "exact", head: true })
        .gte("created_at", todayStart),
      supabase
        .from("bookings")
        .select("id", { count: "exact", head: true })
        .gte("scheduled_at", todayStart)
        .eq("status", "confirmed"),
    ]);

    response.stats = {
      total_leads: count || 0,
      hot_leads: hotRes.count || 0,
      warm_leads: warmRes.count || 0,
      cold_leads: (count || 0) - (hotRes.count || 0) - (warmRes.count || 0),
      leads_today: todayRes.count || 0,
      booked_today: bookedRes.count || 0,
      calls_today: 0,
      avg_response_time: null,
      conversion_rate: 0,
    };
  }

  return NextResponse.json(response);
}

// POST /api/leads - Create a new lead (used by dashboard manual entry)
export async function POST(request: NextRequest) {
  const supabase = createAdminClient();
  const body = await request.json();

  const { data, error } = await supabase
    .from("leads")
    .insert({
      client_id: body.client_id,
      name: body.name,
      email: body.email,
      phone: body.phone,
      company: body.company,
      source: body.source || "manual",
      channel: body.channel || "manual",
      notes: body.notes || "",
    })
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }

  return NextResponse.json({ lead: data }, { status: 201 });
}
