"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { createBrowserClient } from "@/lib/supabase";
import type { Lead, Conversation, Call, Booking } from "@/lib/types";
import Link from "next/link";

export default function LeadDetailPage() {
  const params = useParams();
  const leadId = params.id as string;

  const [lead, setLead] = useState<Lead | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [calls, setCalls] = useState<Call[]>([]);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);

  const supabase = createBrowserClient();

  useEffect(() => {
    loadLeadData();
    setupRealtime();
  }, [leadId]);

  async function loadLeadData() {
    setLoading(true);

    const [leadRes, convRes, callsRes, bookingsRes] = await Promise.all([
      supabase.from("leads").select("*").eq("id", leadId).single(),
      supabase
        .from("conversations")
        .select("*")
        .eq("lead_id", leadId)
        .order("created_at", { ascending: true }),
      supabase
        .from("calls")
        .select("*")
        .eq("lead_id", leadId)
        .order("created_at", { ascending: false }),
      supabase
        .from("bookings")
        .select("*")
        .eq("lead_id", leadId)
        .order("scheduled_at", { ascending: false }),
    ]);

    if (leadRes.data) setLead(leadRes.data);
    if (convRes.data) setConversations(convRes.data);
    if (callsRes.data) setCalls(callsRes.data);
    if (bookingsRes.data) setBookings(bookingsRes.data);

    setLoading(false);
  }

  function setupRealtime() {
    const channel = supabase
      .channel(`lead-${leadId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "conversations",
          filter: `lead_id=eq.${leadId}`,
        },
        (payload) => {
          setConversations((prev) => [...prev, payload.new as Conversation]);
        }
      )
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "leads",
          filter: `id=eq.${leadId}`,
        },
        (payload) => {
          setLead(payload.new as Lead);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Caricamento...</div>
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Lead non trovato</div>
      </div>
    );
  }

  const scoreColor =
    lead.qualification_score >= 70
      ? "text-red-600"
      : lead.qualification_score >= 40
        ? "text-yellow-600"
        : "text-gray-500";

  const scoreLabel =
    lead.qualification_score >= 70
      ? "HOT"
      : lead.qualification_score >= 40
        ? "WARM"
        : "COLD";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <Link
            href="/dashboard"
            className="text-blue-600 hover:text-blue-800 text-sm mb-2 inline-block"
          >
            &larr; Torna alla Dashboard
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{lead.name}</h1>
              <p className="text-gray-500">
                {lead.company || "Azienda non specificata"} &middot;{" "}
                {lead.channel}
              </p>
            </div>
            <div className="text-right">
              <div className={`text-3xl font-bold ${scoreColor}`}>
                {lead.qualification_score}/100
              </div>
              <div className={`text-sm font-semibold ${scoreColor}`}>
                {scoreLabel}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 grid lg:grid-cols-3 gap-8">
        {/* Left: Lead Info + Calls + Bookings */}
        <div className="space-y-6">
          {/* Contact Info */}
          <div className="bg-white rounded-xl border p-6">
            <h2 className="font-semibold mb-4">Informazioni Contatto</h2>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Email</dt>
                <dd className="font-medium">{lead.email || "—"}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Telefono</dt>
                <dd className="font-medium">{lead.phone || "—"}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Ruolo</dt>
                <dd className="font-medium">{lead.role || "—"}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Fonte</dt>
                <dd className="font-medium">{lead.source}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Status</dt>
                <dd>
                  <span className="inline-flex px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    {lead.status}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Creato il</dt>
                <dd className="font-medium">
                  {new Date(lead.created_at).toLocaleString("it-IT")}
                </dd>
              </div>
            </dl>
          </div>

          {/* Qualification Data */}
          {lead.qualification_data &&
            Object.keys(lead.qualification_data).length > 0 && (
              <div className="bg-white rounded-xl border p-6">
                <h2 className="font-semibold mb-4">Qualificazione BANT</h2>
                <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                  {JSON.stringify(lead.qualification_data, null, 2)}
                </pre>
              </div>
            )}

          {/* Calls */}
          {calls.length > 0 && (
            <div className="bg-white rounded-xl border p-6">
              <h2 className="font-semibold mb-4">
                Chiamate ({calls.length})
              </h2>
              <div className="space-y-3">
                {calls.map((call) => (
                  <div key={call.id} className="border rounded-lg p-3 text-sm">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium">
                        {call.direction === "inbound"
                          ? "In arrivo"
                          : "In uscita"}
                      </span>
                      <span className="text-gray-500">
                        {call.duration_seconds}s
                      </span>
                    </div>
                    {call.summary && (
                      <p className="text-gray-600 text-xs">{call.summary}</p>
                    )}
                    <div className="text-xs text-gray-400 mt-1">
                      {new Date(call.created_at).toLocaleString("it-IT")}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Bookings */}
          {bookings.length > 0 && (
            <div className="bg-white rounded-xl border p-6">
              <h2 className="font-semibold mb-4">
                Appuntamenti ({bookings.length})
              </h2>
              <div className="space-y-3">
                {bookings.map((booking) => (
                  <div
                    key={booking.id}
                    className="border rounded-lg p-3 text-sm"
                  >
                    <div className="font-medium">
                      {new Date(booking.scheduled_at).toLocaleString("it-IT")}
                    </div>
                    <div className="text-gray-500">
                      {booking.duration_minutes} min &middot;{" "}
                      {booking.meeting_type} &middot; {booking.status}
                    </div>
                    {booking.meeting_url && (
                      <a
                        href={booking.meeting_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 text-xs hover:underline"
                      >
                        Link alla call
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: Conversation Timeline */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border p-6">
            <h2 className="font-semibold mb-4">
              Conversazione ({conversations.length} messaggi)
            </h2>
            <div className="space-y-4 max-h-[70vh] overflow-y-auto">
              {conversations.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "agent" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[75%] rounded-lg px-4 py-3 ${
                      msg.role === "agent"
                        ? "bg-blue-600 text-white"
                        : msg.role === "system"
                          ? "bg-gray-100 text-gray-500 text-xs italic"
                          : "bg-gray-100 text-gray-900"
                    }`}
                  >
                    <div className="text-sm whitespace-pre-wrap">
                      {msg.content}
                    </div>
                    <div
                      className={`text-xs mt-1 ${
                        msg.role === "agent"
                          ? "text-blue-200"
                          : "text-gray-400"
                      }`}
                    >
                      {msg.channel} &middot;{" "}
                      {new Date(msg.created_at).toLocaleTimeString("it-IT", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                  </div>
                </div>
              ))}
              {conversations.length === 0 && (
                <div className="text-center text-gray-400 py-8">
                  Nessun messaggio ancora. La conversazione apparira qui in
                  tempo reale.
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
