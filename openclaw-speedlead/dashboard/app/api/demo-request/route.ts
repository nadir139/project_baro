import { NextRequest, NextResponse } from "next/server";
import { createBrowserClient } from "@/lib/supabase";

// POST /api/demo-request - Save demo request from landing page
export async function POST(request: NextRequest) {
  const supabase = createBrowserClient();
  const body = await request.json();

  const email = body.email?.trim();
  if (!email) {
    return NextResponse.json(
      { error: "Email is required" },
      { status: 400 }
    );
  }

  const { error } = await supabase.from("demo_requests").insert({
    email,
    company_name: body.company_name || null,
    name: body.name || null,
    phone: body.phone || null,
    message: body.message || null,
    source: body.source || "landing_page",
  });

  if (error) {
    return NextResponse.json(
      { error: "Errore nel salvataggio. Riprova." },
      { status: 500 }
    );
  }

  return NextResponse.json({
    success: true,
    message: "Grazie! Ti contatteremo entro 24 ore.",
  });
}
