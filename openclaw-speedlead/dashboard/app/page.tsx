import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <header className="bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 text-white">
        <nav className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-2xl font-bold">SpeedLead AI</div>
          <div className="flex gap-4 items-center">
            <a href="#features" className="hover:underline">
              Funzionalita
            </a>
            <a href="#pricing" className="hover:underline">
              Prezzi
            </a>
            <a href="#demo" className="hover:underline">
              Demo
            </a>
            <Link
              href="/dashboard"
              className="bg-white text-blue-900 px-4 py-2 rounded-lg font-semibold hover:bg-blue-50 transition"
            >
              Dashboard
            </Link>
          </div>
        </nav>

        <div className="max-w-7xl mx-auto px-6 py-24 text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Il tuo venditore AI
            <br />
            che non dorme mai
          </h1>
          <p className="text-xl md:text-2xl text-blue-100 mb-8 max-w-3xl mx-auto">
            Risponde su WhatsApp, Email e Telefono in italiano, 24/7. Qualifica
            lead e prenota appuntamenti automaticamente.
          </p>
          <div className="flex gap-4 justify-center">
            <a
              href="#demo"
              className="bg-white text-blue-900 px-8 py-4 rounded-lg text-lg font-bold hover:bg-blue-50 transition"
            >
              Prenota una Demo
            </a>
            <a
              href="#pricing"
              className="border-2 border-white text-white px-8 py-4 rounded-lg text-lg font-bold hover:bg-white/10 transition"
            >
              Vedi Prezzi
            </a>
          </div>
        </div>
      </header>

      {/* Stats */}
      <section className="bg-white py-12 border-b">
        <div className="max-w-7xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {[
            { value: "< 20s", label: "Tempo di risposta" },
            { value: "24/7", label: "Sempre attivo" },
            { value: "3x", label: "Lead convertiti in piu" },
            { value: "0.05EUR/min", label: "Costo voce" },
          ].map((stat) => (
            <div key={stat.label}>
              <div className="text-3xl font-bold text-blue-900">
                {stat.value}
              </div>
              <div className="text-gray-500 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">
            Come Funziona
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: "1. Lead Arriva",
                desc: "Da sito web, fiera, WhatsApp o telefono. SpeedLead riceve il contatto istantaneamente.",
                icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z",
              },
              {
                title: "2. Qualifica Automatica",
                desc: "L'AI contatta il lead in < 20 secondi, qualifica budget, urgenza e decisore con conversazione naturale.",
                icon: "M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
              },
              {
                title: "3. Appuntamento Fissato",
                desc: "Per i lead caldi, l'AI prenota automaticamente un appuntamento sul calendario e notifica il venditore.",
                icon: "M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5",
              },
            ].map((feature) => (
              <div
                key={feature.title}
                className="bg-white p-8 rounded-xl shadow-sm border"
              >
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <svg
                    className="w-6 h-6 text-blue-900"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d={feature.icon}
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Channels */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12">
            Tutti i Canali, Un Solo Agente
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                channel: "WhatsApp",
                desc: "Risposta immediata su WhatsApp Business. Conversazione naturale in italiano, follow-up automatici.",
                color: "bg-green-500",
              },
              {
                channel: "Email",
                desc: "Monitora la casella email, risponde ai lead con email professionali, invia preventivi e materiale.",
                color: "bg-blue-500",
              },
              {
                channel: "Telefono",
                desc: "Numero italiano +39, voce naturale AI. Riceve e fa chiamate, trascrive tutto automaticamente.",
                color: "bg-purple-500",
              },
            ].map((ch) => (
              <div
                key={ch.channel}
                className="text-center p-8 rounded-xl border"
              >
                <div
                  className={`w-16 h-16 ${ch.color} rounded-full mx-auto mb-4 flex items-center justify-center`}
                >
                  <span className="text-white text-2xl font-bold">
                    {ch.channel[0]}
                  </span>
                </div>
                <h3 className="text-xl font-bold mb-3">{ch.channel}</h3>
                <p className="text-gray-600">{ch.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-4">
            Prezzi Chiari, Nessuna Sorpresa
          </h2>
          <p className="text-center text-gray-500 mb-12 max-w-2xl mx-auto">
            Setup una tantum + canone mensile fisso. Nessun costo nascosto per
            messaggio.
          </p>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                name: "Starter",
                setup: "1.900",
                monthly: "490",
                features: [
                  "WhatsApp AI 24/7",
                  "Qualificazione automatica",
                  "Booking appuntamenti",
                  "Dashboard base",
                  "Supporto email",
                ],
              },
              {
                name: "Professional",
                setup: "1.900",
                monthly: "690",
                features: [
                  "Tutto in Starter +",
                  "Email AI automatica",
                  "CRM sync (HubSpot/Zoho)",
                  "Report settimanali",
                  "Supporto prioritario",
                ],
                popular: true,
              },
              {
                name: "Enterprise",
                setup: "2.900",
                monthly: "990",
                features: [
                  "Tutto in Professional +",
                  "Voce AI (telefono +39)",
                  "TeamSystem integration",
                  "Multi-agente",
                  "Account manager dedicato",
                ],
              },
            ].map((plan) => (
              <div
                key={plan.name}
                className={`bg-white rounded-xl p-8 border-2 ${
                  plan.popular
                    ? "border-blue-500 shadow-lg relative"
                    : "border-gray-200"
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-500 text-white text-sm px-4 py-1 rounded-full font-semibold">
                    Piu Popolare
                  </div>
                )}
                <h3 className="text-xl font-bold mb-2">{plan.name}</h3>
                <div className="mb-1">
                  <span className="text-sm text-gray-500">Setup: </span>
                  <span className="font-bold">EUR {plan.setup}</span>
                  <span className="text-sm text-gray-500"> una tantum</span>
                </div>
                <div className="mb-6">
                  <span className="text-4xl font-bold">EUR {plan.monthly}</span>
                  <span className="text-gray-500">/mese</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2">
                      <svg
                        className="w-5 h-5 text-green-500 shrink-0"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
                <a
                  href="#demo"
                  className={`block text-center py-3 rounded-lg font-semibold transition ${
                    plan.popular
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-gray-100 text-gray-900 hover:bg-gray-200"
                  }`}
                >
                  Prenota Demo
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Demo CTA */}
      <section id="demo" className="py-20 bg-blue-900 text-white">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Prova SpeedLead AI Gratis per 14 Giorni
          </h2>
          <p className="text-blue-200 mb-8 text-lg">
            Nessuna carta di credito richiesta. Setup in 24 ore. Risultati dal
            primo giorno.
          </p>
          <form className="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto">
            <input
              type="email"
              placeholder="La tua email aziendale"
              className="flex-1 px-4 py-3 rounded-lg text-gray-900"
            />
            <button
              type="submit"
              className="bg-white text-blue-900 px-8 py-3 rounded-lg font-bold hover:bg-blue-50 transition"
            >
              Inizia Ora
            </button>
          </form>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-6 grid md:grid-cols-4 gap-8">
          <div>
            <div className="text-white font-bold text-xl mb-4">
              SpeedLead AI
            </div>
            <p className="text-sm">
              Il venditore AI per aziende B2B italiane. Powered by OpenClaw.
            </p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Prodotto</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#features" className="hover:text-white">
                  Funzionalita
                </a>
              </li>
              <li>
                <a href="#pricing" className="hover:text-white">
                  Prezzi
                </a>
              </li>
              <li>
                <a href="#demo" className="hover:text-white">
                  Demo
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Legale</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#" className="hover:text-white">
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  Termini di Servizio
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white">
                  GDPR
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Contatti</h4>
            <ul className="space-y-2 text-sm">
              <li>info@speedlead.ai</li>
              <li>+39 02 1234567</li>
              <li>Milano, Italia</li>
            </ul>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 mt-8 pt-8 border-t border-gray-800 text-center text-sm">
          &copy; 2026 SpeedLead AI. Tutti i diritti riservati.
        </div>
      </footer>
    </div>
  );
}
