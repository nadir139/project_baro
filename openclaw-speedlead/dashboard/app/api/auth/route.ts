import { NextRequest, NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase";

// POST /api/auth/signup - Create a new user for a client (admin only)
export async function POST(request: NextRequest) {
  const supabase = createAdminClient();
  const body = await request.json();

  const { email, password, full_name, client_id } = body;

  if (!email || !password || !client_id) {
    return NextResponse.json(
      { error: "email, password, and client_id are required" },
      { status: 400 }
    );
  }

  // Verify client exists
  const { data: client } = await supabase
    .from("clients")
    .select("client_id")
    .eq("client_id", client_id)
    .single();

  if (!client) {
    return NextResponse.json(
      { error: `Client '${client_id}' not found` },
      { status: 404 }
    );
  }

  // Create auth user with client_id in metadata
  const { data: authData, error: authError } =
    await supabase.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
      user_metadata: {
        full_name: full_name || "",
        client_id,
      },
    });

  if (authError) {
    return NextResponse.json({ error: authError.message }, { status: 400 });
  }

  return NextResponse.json(
    {
      user: {
        id: authData.user.id,
        email: authData.user.email,
        client_id,
      },
      message: `User created for client ${client_id}`,
    },
    { status: 201 }
  );
}
