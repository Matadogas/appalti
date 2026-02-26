import Link from 'next/link'

/* ─── Sample Data ─────────────────────────────────────────────── */

const sampleBids = [
  {
    id: '1',
    title: 'Manhattan Bridge Deck Rehabilitation & Structural Steel Repairs',
    agency: 'NYC Department of Transportation',
    state: 'NY',
    city: 'New York',
    category: 'construction',
    status: 'active',
    dueDate: '2026-03-15',
    budget: 12500000,
    tags: ['structural steel', 'bridge work', 'concrete'],
    isUrgent: true,
  },
  {
    id: '2',
    title: 'Newark Airport Terminal B Electrical Systems Upgrade',
    agency: 'Port Authority of NY & NJ',
    state: 'NJ',
    city: 'Newark',
    category: 'engineering',
    status: 'active',
    dueDate: '2026-03-22',
    budget: 8200000,
    tags: ['electrical', 'HVAC', 'fire protection'],
    isUrgent: false,
  },
  {
    id: '3',
    title: 'Brooklyn Navy Yard Waterfront Infrastructure Development',
    agency: 'NYC Economic Development Corp',
    state: 'NY',
    city: 'Brooklyn',
    category: 'construction',
    status: 'active',
    dueDate: '2026-04-01',
    budget: 15100000,
    tags: ['marine construction', 'site work', 'utilities'],
    isUrgent: false,
  },
  {
    id: '4',
    title: 'NJ Turnpike Exit 14A Roadway Reconstruction Phase II',
    agency: 'NJ Department of Transportation',
    state: 'NJ',
    city: 'Jersey City',
    category: 'construction',
    status: 'active',
    dueDate: '2026-03-28',
    budget: 22300000,
    tags: ['roadway', 'paving', 'drainage', 'traffic signals'],
    isUrgent: true,
  },
  {
    id: '5',
    title: 'Queens Central Library HVAC Modernization & Controls',
    agency: 'NYC Dept of Design & Construction',
    state: 'NY',
    city: 'Queens',
    category: 'facilities',
    status: 'active',
    dueDate: '2026-04-10',
    budget: 3800000,
    tags: ['HVAC', 'building automation', 'mechanical'],
    isUrgent: false,
  },
  {
    id: '6',
    title: 'Hoboken Waterfront Seawall Repair & Flood Mitigation',
    agency: 'City of Hoboken',
    state: 'NJ',
    city: 'Hoboken',
    category: 'construction',
    status: 'active',
    dueDate: '2026-03-18',
    budget: 6700000,
    tags: ['marine', 'concrete', 'flood control'],
    isUrgent: true,
  },
]

const stats = [
  { value: '2,400+', label: 'Active Bids', icon: 'clipboard' },
  { value: '47', label: 'Sources Monitored', icon: 'radar' },
  { value: 'NY & NJ', label: 'Full Coverage', icon: 'map' },
  { value: '$3.2B+', label: 'In Opportunities', icon: 'dollar' },
]

const features = [
  {
    title: 'Smart Filters',
    description: 'Filter by trade, location, budget range, and deadline. Find exactly the bids that match your capabilities.',
    icon: 'filter',
  },
  {
    title: 'AI Summaries',
    description: 'Every bid is analyzed and summarized by AI. Know the requirements, bonding needs, and key dates at a glance.',
    icon: 'brain',
  },
  {
    title: 'Daily Email Digests',
    description: 'Get new matching opportunities delivered to your inbox every morning. Never miss a deadline again.',
    icon: 'mail',
  },
  {
    title: 'Real-Time Updates',
    description: 'Bids are scraped from government portals multiple times daily. See new opportunities within hours of posting.',
    icon: 'refresh',
  },
]

const steps = [
  {
    number: '01',
    title: 'We Aggregate',
    description: 'Our scrapers monitor 47+ government procurement portals across New York and New Jersey around the clock.',
  },
  {
    number: '02',
    title: 'AI Enriches',
    description: 'Every bid is analyzed by AI to extract trade requirements, deadlines, bonding needs, and key contacts.',
  },
  {
    number: '03',
    title: 'You Win',
    description: 'Browse, filter, and get alerts for bids matching your trade. Respond faster and win more contracts.',
  },
]

/* ─── Helper Functions ────────────────────────────────────────── */

function formatBudget(amount: number): string {
  if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`
  if (amount >= 1000) return `$${(amount / 1000).toFixed(0)}K`
  return `$${amount}`
}

function daysUntil(dateStr: string): number {
  const diff = new Date(dateStr).getTime() - new Date('2026-02-26').getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function categoryColor(cat: string): string {
  const colors: Record<string, string> = {
    construction: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    engineering: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    facilities: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    other: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
  }
  return colors[cat] || colors.other
}

function stateColor(state: string): string {
  return state === 'NY'
    ? 'bg-blue-600/30 text-blue-200 border-blue-500/40'
    : 'bg-orange-600/30 text-orange-200 border-orange-500/40'
}

/* ─── Icon Components ─────────────────────────────────────────── */

function IconClipboard() {
  return (
    <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  )
}

function IconRadar() {
  return (
    <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.348 14.651a3.75 3.75 0 010-5.303m5.304 0a3.75 3.75 0 010 5.303m-7.425 2.122a6.75 6.75 0 010-9.546m9.546 0a6.75 6.75 0 010 9.546M5.106 18.894c-3.808-3.808-3.808-9.98 0-13.789m13.788 0c3.808 3.808 3.808 9.981 0 13.79M12 12h.008v.007H12V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
    </svg>
  )
}

function IconMap() {
  return (
    <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
    </svg>
  )
}

function IconDollar() {
  return (
    <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function IconFilter() {
  return (
    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 01-.659 1.591l-5.432 5.432a2.25 2.25 0 00-.659 1.591v2.927a2.25 2.25 0 01-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 00-.659-1.591L3.659 7.409A2.25 2.25 0 013 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0112 3z" />
    </svg>
  )
}

function IconBrain() {
  return (
    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
    </svg>
  )
}

function IconMail() {
  return (
    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
    </svg>
  )
}

function IconRefresh() {
  return (
    <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182M2.985 19.644l3.181-3.182" />
    </svg>
  )
}

function IconArrowRight() {
  return (
    <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
    </svg>
  )
}

function IconClock() {
  return (
    <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  )
}

function IconBuilding() {
  return (
    <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
    </svg>
  )
}

function IconBolt() {
  return (
    <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
      <path fillRule="evenodd" d="M14.615 1.595a.75.75 0 01.359.852L12.982 9.75h7.268a.75.75 0 01.548 1.262l-10.5 11.25a.75.75 0 01-1.272-.71l1.992-7.302H3.75a.75.75 0 01-.548-1.262l10.5-11.25a.75.75 0 01.913-.143z" clipRule="evenodd" />
    </svg>
  )
}

function StatIcon({ type }: { type: string }) {
  switch (type) {
    case 'clipboard': return <IconClipboard />
    case 'radar': return <IconRadar />
    case 'map': return <IconMap />
    case 'dollar': return <IconDollar />
    default: return null
  }
}

function FeatureIcon({ type }: { type: string }) {
  switch (type) {
    case 'filter': return <IconFilter />
    case 'brain': return <IconBrain />
    case 'mail': return <IconMail />
    case 'refresh': return <IconRefresh />
    default: return null
  }
}

/* ─── Page Component ──────────────────────────────────────────── */

export default function Home() {
  return (
    <div className="relative z-10">
      {/* ════════ NAVIGATION ════════ */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5" style={{ background: 'rgba(10, 15, 28, 0.85)', backdropFilter: 'blur(16px)' }}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#0a0f1c" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
              </svg>
            </div>
            <span className="text-lg font-semibold tracking-tight text-white">TriState<span className="text-amber-400">Bids</span></span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#bids" className="text-sm text-slate-400 hover:text-white transition-colors">Live Bids</a>
            <a href="#how" className="text-sm text-slate-400 hover:text-white transition-colors">How It Works</a>
            <a href="#features" className="text-sm text-slate-400 hover:text-white transition-colors">Features</a>
            <Link
              href="/tenders"
              className="text-sm font-medium px-5 py-2 rounded-lg bg-amber-500 text-slate-900 hover:bg-amber-400 transition-all hover:shadow-lg hover:shadow-amber-500/20"
            >
              Browse Bids
            </Link>
          </div>
        </div>
      </nav>

      {/* ════════ HERO ════════ */}
      <section className="bg-mesh-hero bg-grid relative overflow-hidden pt-32 pb-20 md:pt-40 md:pb-28">
        {/* Decorative diagonal line */}
        <div className="absolute top-0 right-0 w-1/2 h-full opacity-[0.03]" style={{ background: 'repeating-linear-gradient(-45deg, transparent, transparent 40px, #f59e0b 40px, #f59e0b 41px)' }} />

        <div className="max-w-7xl mx-auto px-6 relative">
          <div className="max-w-3xl">
            {/* Live badge */}
            <div className="animate-fade-in-up inline-flex items-center gap-2 px-4 py-1.5 rounded-full badge-shimmer border border-amber-500/20 mb-8">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-medium text-amber-300 tracking-wide uppercase">Live &mdash; Monitoring 47 sources</span>
            </div>

            <h1 className="animate-fade-in-up delay-100 text-5xl md:text-7xl font-bold leading-[1.05] tracking-tight mb-6" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
              Never Miss a<br />
              <span className="text-amber-400">Public Works</span><br />
              Bid Again
            </h1>

            <p className="animate-fade-in-up delay-200 text-lg md:text-xl text-slate-400 leading-relaxed mb-10 max-w-xl">
              We scrape every government procurement portal in New York and New Jersey so you don&apos;t have to. AI-enriched summaries, deadline alerts, and trade-specific filtering &mdash; all in one place.
            </p>

            <div className="animate-fade-in-up delay-300 flex flex-col sm:flex-row gap-4">
              <Link
                href="/tenders"
                className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-amber-500 text-slate-900 font-semibold text-base hover:bg-amber-400 transition-all hover:shadow-xl hover:shadow-amber-500/25 hover:-translate-y-0.5"
              >
                Browse Live Bids
                <IconArrowRight />
              </Link>
              <a
                href="#how"
                className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl border border-slate-600 text-slate-300 font-medium text-base hover:border-slate-400 hover:text-white transition-all"
              >
                How It Works
              </a>
            </div>
          </div>

          {/* Floating stat card (desktop) */}
          <div className="hidden lg:block absolute top-12 right-0 w-72 animate-fade-in delay-500">
            <div className="glass-card rounded-2xl p-5 animate-float">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <IconBolt />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Just posted</p>
                  <p className="text-sm font-medium text-white">12 minutes ago</p>
                </div>
              </div>
              <p className="text-sm font-medium text-slate-200 mb-2">Bronx River Greenway Extension &mdash; Phase III</p>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span className="flex items-center gap-1"><IconBuilding /> NYC Parks</span>
                <span className="text-amber-400 font-semibold">$4.2M</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════ STATS BAR ════════ */}
      <section className="relative border-y border-white/5 bg-mesh-dark">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-4">
            {stats.map((stat, i) => (
              <div
                key={stat.label}
                className={`animate-fade-in-up delay-${(i + 1) * 100} flex flex-col items-center text-center md:flex-row md:text-left md:items-center gap-3 md:gap-4`}
              >
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
                  <StatIcon type={stat.icon} />
                </div>
                <div>
                  <p className="text-2xl md:text-3xl font-bold text-white tracking-tight">{stat.value}</p>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════ LIVE BIDS ════════ */}
      <section id="bids" className="bg-mesh-hero bg-grid py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-6">
          <div className="animate-fade-in-up text-center mb-14">
            <p className="text-amber-400 font-semibold text-sm tracking-widest uppercase mb-3">Live Feed</p>
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
              Today&apos;s Opportunities
            </h2>
            <p className="text-slate-400 mt-4 max-w-lg mx-auto">
              Real bid opportunities currently available from government procurement portals across the tri-state area.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {sampleBids.map((bid, i) => {
              const days = daysUntil(bid.dueDate)
              return (
                <div
                  key={bid.id}
                  className={`animate-fade-in-up delay-${(i + 1) * 100} group glass-card rounded-2xl p-6 hover:border-amber-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-amber-500/5 cursor-pointer relative overflow-hidden`}
                >
                  {/* Urgent indicator */}
                  {bid.isUrgent && (
                    <div className="absolute top-0 right-0 px-3 py-1 bg-red-500/90 text-white text-[10px] font-bold uppercase tracking-wider rounded-bl-lg">
                      Urgent
                    </div>
                  )}

                  {/* Header: State badge + Budget */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-md text-xs font-bold border ${stateColor(bid.state)}`}>
                        {bid.state}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-md text-xs font-medium border ${categoryColor(bid.category)}`}>
                        {bid.category}
                      </span>
                    </div>
                    <span className="text-lg font-bold text-amber-400">{formatBudget(bid.budget)}</span>
                  </div>

                  {/* Title */}
                  <h3 className="text-base font-semibold text-white group-hover:text-amber-300 transition-colors mb-2 leading-snug pr-4">
                    {bid.title}
                  </h3>

                  {/* Agency + Location */}
                  <div className="flex items-center gap-3 text-xs text-slate-400 mb-3">
                    <span className="flex items-center gap-1">
                      <IconBuilding />
                      {bid.agency}
                    </span>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {bid.tags.map(tag => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-700/60 text-slate-300 border border-slate-600/40"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>

                  {/* Footer: Due date + CTA */}
                  <div className="flex items-center justify-between pt-3 border-t border-white/5">
                    <span className={`flex items-center gap-1.5 text-xs font-medium ${days <= 20 ? 'text-red-400' : 'text-slate-400'}`}>
                      <IconClock />
                      {days} days left
                    </span>
                    <span className="text-xs font-medium text-amber-400 group-hover:text-amber-300 flex items-center gap-1 transition-colors">
                      View Details
                      <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                      </svg>
                    </span>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="animate-fade-in-up delay-700 text-center mt-10">
            <Link
              href="/tenders"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 font-semibold hover:bg-amber-500/20 hover:border-amber-500/50 transition-all"
            >
              View All 2,400+ Opportunities
              <IconArrowRight />
            </Link>
          </div>
        </div>
      </section>

      {/* ════════ HOW IT WORKS ════════ */}
      <section id="how" className="bg-mesh-dark py-20 md:py-28 border-y border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="animate-fade-in-up text-center mb-16">
            <p className="text-amber-400 font-semibold text-sm tracking-widest uppercase mb-3">How It Works</p>
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
              From Portal to Your Inbox
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Connecting line (desktop) */}
            <div className="hidden md:block absolute top-16 left-[17%] right-[17%] h-px bg-gradient-to-r from-transparent via-amber-500/30 to-transparent" />

            {steps.map((step, i) => (
              <div
                key={step.number}
                className={`animate-fade-in-up delay-${(i + 1) * 200} text-center relative`}
              >
                <div className="w-14 h-14 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center mx-auto mb-6 relative z-10" style={{ background: 'var(--navy-950)' }}>
                  <span className="text-xl font-bold text-amber-400" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>{step.number}</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{step.title}</h3>
                <p className="text-slate-400 leading-relaxed max-w-xs mx-auto">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════ FEATURES ════════ */}
      <section id="features" className="bg-mesh-hero bg-grid py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-6">
          <div className="animate-fade-in-up text-center mb-14">
            <p className="text-amber-400 font-semibold text-sm tracking-widest uppercase mb-3">Features</p>
            <h2 className="text-3xl md:text-5xl font-bold tracking-tight" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
              Built for Contractors
            </h2>
            <p className="text-slate-400 mt-4 max-w-lg mx-auto">
              Every feature designed to help you find and win more government construction contracts.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className={`animate-fade-in-up delay-${(i + 1) * 100} group glass-card-light rounded-2xl p-8 hover:border-amber-500/20 transition-all duration-300`}
              >
                <div className="w-14 h-14 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-5 group-hover:bg-amber-500/20 group-hover:border-amber-500/30 transition-all">
                  <FeatureIcon type={feature.icon} />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
                <p className="text-slate-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════ CTA ════════ */}
      <section className="bg-mesh-dark py-20 md:py-28 border-t border-white/5">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <div className="animate-fade-in-up">
            <div className="w-16 h-16 rounded-2xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center mx-auto mb-8 animate-pulse-glow">
              <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="#fbbf24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
            </div>

            <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-4" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
              Start Finding Bids<br /><span className="text-amber-400">Today</span>
            </h2>
            <p className="text-slate-400 text-lg mb-10 max-w-md mx-auto">
              Join hundreds of contractors who never miss a government opportunity. Set up alerts in under 2 minutes.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 max-w-md mx-auto">
              <input
                type="email"
                placeholder="your@company.com"
                className="w-full sm:flex-1 px-5 py-3.5 rounded-xl bg-slate-800/80 border border-slate-600/50 text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all"
              />
              <button className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-amber-500 text-slate-900 font-semibold hover:bg-amber-400 transition-all hover:shadow-lg hover:shadow-amber-500/25 whitespace-nowrap">
                Get Started Free
              </button>
            </div>
            <p className="text-xs text-slate-500 mt-4">Free tier includes 50 bid views/month. No credit card required.</p>
          </div>
        </div>
      </section>

      {/* ════════ FOOTER ════════ */}
      <footer className="border-t border-white/5 py-12" style={{ background: 'var(--navy-950)' }}>
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-10">
            {/* Brand */}
            <div className="md:col-span-1">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-7 h-7 rounded-md bg-amber-500 flex items-center justify-center">
                  <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="#0a0f1c" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
                  </svg>
                </div>
                <span className="text-base font-semibold text-white">TriState<span className="text-amber-400">Bids</span></span>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">
                Aggregating public construction opportunities from NY &amp; NJ government portals.
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Product</h4>
              <ul className="space-y-2.5">
                <li><a href="#bids" className="text-sm text-slate-500 hover:text-white transition-colors">Live Bids</a></li>
                <li><a href="#features" className="text-sm text-slate-500 hover:text-white transition-colors">Features</a></li>
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">API Access</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Sources</h4>
              <ul className="space-y-2.5">
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">NYC PASSPort</a></li>
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">NYS OGS</a></li>
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">NJ Treasury</a></li>
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">NJDOT</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4">Company</h4>
              <ul className="space-y-2.5">
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">Contact</a></li>
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="text-sm text-slate-500 hover:text-white transition-colors">Terms of Service</a></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-white/5 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs text-slate-600">&copy; 2026 TriStateBids. All rights reserved.</p>
            <div className="flex items-center gap-1 text-xs text-slate-600">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              All systems operational
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
