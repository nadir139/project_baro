import { NextRequest, NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase";

// POST /api/voice-activate - Provision a Twilio number and activate voice for a client
export async function POST(request: NextRequest) {
  const supabase = createAdminClient();

  let body: Record<string, string>;
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const clientId = body.client_id;

  if (!clientId) {
    return NextResponse.json(
      { success: false, error: "client_id is required" },
      { status: 400 }
    );
  }

  const twilioSid = process.env.TWILIO_ACCOUNT_SID;
  const twilioToken = process.env.TWILIO_AUTH_TOKEN;

  if (!twilioSid || !twilioToken) {
    return NextResponse.json(
      {
        success: false,
        error: "Twilio credentials not configured on server",
      },
      { status: 500 }
    );
  }

  try {
    // Step 1: Search for available Italian numbers
    const searchUrl = `https://api.twilio.com/2010-04-01/Accounts/${twilioSid}/AvailablePhoneNumbers/IT/Local.json?PageSize=1`;
    const authHeader =
      "Basic " + Buffer.from(`${twilioSid}:${twilioToken}`).toString("base64");

    const searchRes = await fetch(searchUrl, {
      headers: { Authorization: authHeader },
    });

    if (!searchRes.ok) {
      return NextResponse.json(
        {
          success: false,
          error: "Failed to search Twilio numbers. Check credentials.",
        },
        { status: 500 }
      );
    }

    const searchData = await searchRes.json();
    const available = searchData.available_phone_numbers;

    if (!available || available.length === 0) {
      return NextResponse.json(
        {
          success: false,
          error:
            "No Italian phone numbers available in Twilio. Try a different region or number type.",
        },
        { status: 404 }
      );
    }

    const phoneNumber = available[0].phone_number;

    // Step 2: Purchase the number
    const purchaseUrl = `https://api.twilio.com/2010-04-01/Accounts/${twilioSid}/IncomingPhoneNumbers.json`;

    // Get client domain for webhook URL
    const { data: clientData } = await supabase
      .from("clients")
      .select("domain")
      .eq("client_id", clientId)
      .single();

    const domain = clientData?.domain || "localhost";
    const voiceUrl = `https://${domain}/voice/incoming`;
    const statusUrl = `https://${domain}/voice/status`;

    const purchaseRes = await fetch(purchaseUrl, {
      method: "POST",
      headers: {
        Authorization: authHeader,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        PhoneNumber: phoneNumber,
        VoiceUrl: voiceUrl,
        VoiceMethod: "POST",
        StatusCallback: statusUrl,
        StatusCallbackMethod: "POST",
        FriendlyName: `SpeedLead-${clientId}`,
      }),
    });

    if (!purchaseRes.ok) {
      const errorData = await purchaseRes.json();
      return NextResponse.json(
        {
          success: false,
          error: `Failed to purchase number: ${errorData.message || "Unknown error"}`,
        },
        { status: 500 }
      );
    }

    const purchaseData = await purchaseRes.json();

    // Step 3: Update client record
    await supabase
      .from("clients")
      .update({
        voice_enabled: true,
        twilio_phone: purchaseData.phone_number,
      })
      .eq("client_id", clientId);

    return NextResponse.json({
      success: true,
      phone_number: purchaseData.phone_number,
      sid: purchaseData.sid,
      message: `Voice activated for ${clientId} with number ${purchaseData.phone_number}`,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json(
      { success: false, error: message },
      { status: 500 }
    );
  }
}
