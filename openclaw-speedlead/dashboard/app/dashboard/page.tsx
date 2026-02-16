"use client";

import { useEffect, useState } from "react";
import { createBrowserClient } from "@/lib/supabase";
import type { Lead, DashboardStats } from "@/lib/types";
import Link from "next/link";

const STATUS_COLORS: Record<string, string> = {
  new: "bg-blue-100 text-blue-800",
  contacted: "bg-yellow-100 text-yellow-800",
  qualifying: "bg-orange-100 text-orange-800",
  qualified: "bg-green-100 text-green-800",
  booked: "bg-purple-100 text-purple-800",
  won: "bg-emerald-100 text-emerald-800",
  lost: "bg-red-100 text-red-800",
  cold: "bg-gray-100 text-gray-800",
};

const CHANNEL_ICONS: Record<string, string> = {
  whatsapp: "WA",
  email: "EM",
  phone: "PH",
  web_form: "WF",
  manual: "MN",
};

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 70
      ? "bg-red-100 text-red-700 border-red-200"
      : score >= 40
        ? "bg-yellow-100 text-yellow-700 border-yellow-200"
        : "bg-gray-100 text-gray-600 border-gray-200";
  const label = score >= 70 ? "HOT" : score >= 40 ? "WARM" : "COLD";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${color}`}>
      {label} {score}
    </span>
  );
}

export default function DashboardPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [voiceActivating, setVoiceActivating] = useState(false);

  const supabase = createBrowserClient();

  useEffect(() => {
    loadData();
    setupRealtime();
  }, []);

  async function loadData() {
    setLoading(true);

    // Load leads
    const { data: leadsData } = await supabase
      .from("leads")
      .select("*")
      .order("created_at", { ascending: false })
      .limit(50);

    if (leadsData) setLeads(leadsData);

    // Load stats
    const res = await fetch("/api/leads?stats=true");
    if (res.ok) {
      const data = await res.json();
      setStats(data.stats);
    }

    setLoading(false);
  }

  function setupRealtime() {
    const channel = supabase
      .channel("leads-realtime")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "leads" },
        (payload) => {
          if (payload.eventType === "INSERT") {
            setLeads((prev) => [payload.new as Lead, ...prev]);
          } else if (payload.eventType === "UPDATE") {
            setLeads((prev) =>
              prev.map((l) =>
                l.id === (payload.new as Lead).id ? (payload.new as Lead) : l
              )
            );
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }

  async function activateVoice() {
    setVoiceActivating(true);
    try {
      const res = await fetch("/api/voice-activate", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        alert(`Voce attivata! Numero: ${data.phone_number}`);
      } else {
        alert(`Errore: ${data.error}`);
      }
    } catch {
      alert("Errore nell'attivazione voce");
    }
    setVoiceActivating(false);
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500 text-lg">Caricamento...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              SpeedLead AI Dashboard
            </h1>
            <p className="text-sm text-gray-500">Gestione lead in tempo reale</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={activateVoice}
              disabled={voiceActivating}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-purple-700 transition disabled:opacity-50"
            >
              {voiceActivating ? "Attivando..." : "Attiva Voce"}
            </button>
            <button
              onClick={loadData}
              className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition"
            >
              Aggiorna
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
            <StatCard label="Lead Oggi" value={stats.leads_today} />
            <StatCard
              label="Lead HOT"
              value={stats.hot_leads}
              color="text-red-600"
            />
            <StatCard
              label="Lead WARM"
              value={stats.warm_leads}
              color="text-yellow-600"
            />
            <StatCard label="Appuntamenti Oggi" value={stats.booked_today} />
            <StatCard
              label="Tasso Conversione"
              value={`${stats.conversion_rate}%`}
              color="text-green-600"
            />
          </div>
        )}

        {/* Lead List */}
        <div className="bg-white rounded-xl border shadow-sm">
          <div className="px-6 py-4 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold">Lead Recenti</h2>
            <span className="text-sm text-gray-500">
              {leads.length} lead totali
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-sm text-gray-500">
                  <th className="px-6 py-3 font-medium">Lead</th>
                  <th className="px-6 py-3 font-medium">Azienda</th>
                  <th className="px-6 py-3 font-medium">Canale</th>
                  <th className="px-6 py-3 font-medium">Score</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">Data</th>
                  <th className="px-6 py-3 font-medium"></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {leads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">
                        {lead.name}
                      </div>
                      <div className="text-sm text-gray-500">
                        {lead.email || lead.phone || "—"}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {lead.company || "—"}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100">
                        {CHANNEL_ICONS[lead.channel] || lead.channel}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <ScoreBadge score={lead.qualification_score} />
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[lead.status] || "bg-gray-100"}`}
                      >
                        {lead.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(lead.created_at).toLocaleDateString("it-IT", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/dashboard/leads/${lead.id}`}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        Dettaglio
                      </Link>
                    </td>
                  </tr>
                ))}
                {leads.length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-6 py-12 text-center text-gray-400"
                    >
                      Nessun lead ancora. I lead appariranno qui in tempo reale.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

function StatCard({
  label,
  value,
  color = "text-gray-900",
}: {
  label: string;
  value: number | string;
  color?: string;
}) {
  return (
    <div className="bg-white rounded-xl border p-4">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
