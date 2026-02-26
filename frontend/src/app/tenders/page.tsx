'use client'

import { useState } from 'react'
import Link from 'next/link'

/* ─── Sample Data (static for demo) ──────────────────────────── */

const allBids = [
  {
    id: '1',
    title: 'Manhattan Bridge Deck Rehabilitation & Structural Steel Repairs',
    agency: 'NYC Department of Transportation',
    state: 'NY',
    city: 'New York',
    county: 'New York',
    category: 'construction',
    status: 'active',
    dueDate: '2026-03-15',
    publishDate: '2026-02-10',
    budget: 12500000,
    tags: ['structural steel', 'bridge work', 'concrete'],
    aiSummary: 'Major rehabilitation project for Manhattan Bridge deck including structural steel repairs, concrete resurfacing, and waterproofing. Pre-bid meeting required. Performance bond of 100% required.',
    documents: 3,
  },
  {
    id: '2',
    title: 'Newark Airport Terminal B Electrical Systems Upgrade',
    agency: 'Port Authority of NY & NJ',
    state: 'NJ',
    city: 'Newark',
    county: 'Essex',
    category: 'engineering',
    status: 'active',
    dueDate: '2026-03-22',
    publishDate: '2026-02-12',
    budget: 8200000,
    tags: ['electrical', 'HVAC', 'fire protection'],
    aiSummary: 'Complete electrical systems upgrade for Terminal B. Includes main switchgear replacement, emergency generator installation, fire alarm modernization, and HVAC controls integration.',
    documents: 5,
  },
  {
    id: '3',
    title: 'Brooklyn Navy Yard Waterfront Infrastructure Development',
    agency: 'NYC Economic Development Corp',
    state: 'NY',
    city: 'Brooklyn',
    county: 'Kings',
    category: 'construction',
    status: 'active',
    dueDate: '2026-04-01',
    publishDate: '2026-02-15',
    budget: 15100000,
    tags: ['marine construction', 'site work', 'utilities'],
    aiSummary: 'Waterfront infrastructure including bulkhead construction, utility relocation, stormwater management, and site grading. MWBE goals apply. Prevailing wage required.',
    documents: 8,
  },
  {
    id: '4',
    title: 'NJ Turnpike Exit 14A Roadway Reconstruction Phase II',
    agency: 'NJ Department of Transportation',
    state: 'NJ',
    city: 'Jersey City',
    county: 'Hudson',
    category: 'construction',
    status: 'active',
    dueDate: '2026-03-28',
    publishDate: '2026-02-08',
    budget: 22300000,
    tags: ['roadway', 'paving', 'drainage', 'traffic signals'],
    aiSummary: 'Phase II of Exit 14A reconstruction including full-depth pavement replacement, drainage improvements, traffic signal modernization, and ADA-compliant pedestrian facilities.',
    documents: 12,
  },
  {
    id: '5',
    title: 'Queens Central Library HVAC Modernization & Controls',
    agency: 'NYC Dept of Design & Construction',
    state: 'NY',
    city: 'Queens',
    county: 'Queens',
    category: 'facilities',
    status: 'active',
    dueDate: '2026-04-10',
    publishDate: '2026-02-20',
    budget: 3800000,
    tags: ['HVAC', 'building automation', 'mechanical'],
    aiSummary: 'HVAC system replacement and building automation upgrade for Queens Central Library. Includes chiller replacement, VAV box installation, and DDC controls.',
    documents: 4,
  },
  {
    id: '6',
    title: 'Hoboken Waterfront Seawall Repair & Flood Mitigation',
    agency: 'City of Hoboken',
    state: 'NJ',
    city: 'Hoboken',
    county: 'Hudson',
    category: 'construction',
    status: 'active',
    dueDate: '2026-03-18',
    publishDate: '2026-02-05',
    budget: 6700000,
    tags: ['marine', 'concrete', 'flood control'],
    aiSummary: 'Seawall reconstruction and flood mitigation along Hoboken waterfront. Includes sheet pile installation, concrete cap beam, and tide gate mechanisms.',
    documents: 6,
  },
  {
    id: '7',
    title: 'Yonkers Public School Roofing Replacement Program',
    agency: 'Yonkers Board of Education',
    state: 'NY',
    city: 'Yonkers',
    county: 'Westchester',
    category: 'facilities',
    status: 'active',
    dueDate: '2026-04-05',
    publishDate: '2026-02-18',
    budget: 5200000,
    tags: ['roofing', 'waterproofing', 'insulation'],
    aiSummary: 'Roof replacement at 4 elementary schools including tear-off, insulation, and TPO membrane installation. Work must be completed during summer break.',
    documents: 3,
  },
  {
    id: '8',
    title: 'Trenton Water Main Replacement - Phase IV Downtown',
    agency: 'City of Trenton Water Utility',
    state: 'NJ',
    city: 'Trenton',
    county: 'Mercer',
    category: 'construction',
    status: 'active',
    dueDate: '2026-03-25',
    publishDate: '2026-02-14',
    budget: 9400000,
    tags: ['water main', 'excavation', 'pipe installation'],
    aiSummary: 'Replacement of aging cast iron water mains with ductile iron pipe in downtown district. Approximately 12,000 LF of 8-inch and 12-inch main.',
    documents: 7,
  },
]

/* ─── Helpers ─────────────────────────────────────────────────── */

function formatBudget(amount: number): string {
  if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`
  if (amount >= 1000) return `$${(amount / 1000).toFixed(0)}K`
  return `$${amount}`
}

function daysUntil(dateStr: string): number {
  const diff = new Date(dateStr).getTime() - new Date('2026-02-26').getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function categoryLabel(cat: string): string {
  const labels: Record<string, string> = {
    construction: 'Construction',
    engineering: 'Engineering',
    facilities: 'Facilities',
    other: 'Other',
  }
  return labels[cat] || cat
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

/* ─── Page ────────────────────────────────────────────────────── */

export default function TendersPage() {
  const [stateFilter, setStateFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')

  const filtered = allBids.filter(bid => {
    if (stateFilter && bid.state !== stateFilter) return false
    if (categoryFilter && bid.category !== categoryFilter) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return (
        bid.title.toLowerCase().includes(q) ||
        bid.agency.toLowerCase().includes(q) ||
        bid.tags.some(t => t.toLowerCase().includes(q))
      )
    }
    return true
  })

  return (
    <div className="relative z-10 min-h-screen">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-white/5" style={{ background: 'rgba(10, 15, 28, 0.92)', backdropFilter: 'blur(16px)' }}>
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-amber-500 flex items-center justify-center">
              <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#0a0f1c" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
              </svg>
            </div>
            <span className="text-lg font-semibold tracking-tight text-white">TriState<span className="text-amber-400">Bids</span></span>
          </Link>
          <div className="flex items-center gap-3">
            <span className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {allBids.length} active bids
            </span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-2" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
            Browse Opportunities
          </h1>
          <p className="text-slate-400">
            {filtered.length} bid{filtered.length !== 1 ? 's' : ''} matching your filters
          </p>
        </div>

        {/* Filters */}
        <div className="glass-card rounded-2xl p-5 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">Search</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title, agency, or trade..."
                className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-600/50 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all"
              />
            </div>
            {/* State */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">State</label>
              <select
                value={stateFilter}
                onChange={(e) => setStateFilter(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-600/50 text-white text-sm focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all appearance-none cursor-pointer"
              >
                <option value="">All States</option>
                <option value="NY">New York</option>
                <option value="NJ">New Jersey</option>
              </select>
            </div>
            {/* Category */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">Category</label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-600/50 text-white text-sm focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all appearance-none cursor-pointer"
              >
                <option value="">All Categories</option>
                <option value="construction">Construction</option>
                <option value="engineering">Engineering</option>
                <option value="facilities">Facilities</option>
              </select>
            </div>
          </div>
        </div>

        {/* Bid List */}
        <div className="space-y-4">
          {filtered.map((bid) => {
            const days = daysUntil(bid.dueDate)
            return (
              <div
                key={bid.id}
                className="group glass-card rounded-2xl p-6 hover:border-amber-500/25 transition-all duration-300 cursor-pointer"
              >
                <div className="flex flex-col lg:flex-row lg:items-start gap-5">
                  {/* Main Content */}
                  <div className="flex-1 min-w-0">
                    {/* Top badges */}
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      <span className={`px-2.5 py-0.5 rounded-md text-xs font-bold border ${stateColor(bid.state)}`}>
                        {bid.state}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-md text-xs font-medium border ${categoryColor(bid.category)}`}>
                        {categoryLabel(bid.category)}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                        Active
                      </span>
                      {days <= 20 && (
                        <span className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-red-500/20 text-red-300 border border-red-500/30">
                          {days}d left
                        </span>
                      )}
                    </div>

                    {/* Title */}
                    <h2 className="text-lg font-semibold text-white group-hover:text-amber-300 transition-colors mb-1.5 leading-snug">
                      {bid.title}
                    </h2>

                    {/* Agency + Location */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-400 mb-3">
                      <span className="flex items-center gap-1.5">
                        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                        </svg>
                        {bid.agency}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                        </svg>
                        {bid.city}, {bid.county} County
                      </span>
                    </div>

                    {/* AI Summary */}
                    <p className="text-sm text-slate-400 leading-relaxed mb-3 line-clamp-2">
                      {bid.aiSummary}
                    </p>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1.5">
                      {bid.tags.map(tag => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-700/60 text-slate-300 border border-slate-600/40"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Right sidebar: Budget + Meta */}
                  <div className="lg:w-48 flex-shrink-0 flex flex-row lg:flex-col items-start lg:items-end gap-4 lg:gap-3 lg:text-right">
                    <div>
                      <p className="text-2xl font-bold text-amber-400">{formatBudget(bid.budget)}</p>
                      <p className="text-xs text-slate-500">estimated budget</p>
                    </div>
                    <div className="flex flex-col items-start lg:items-end gap-1.5 text-xs text-slate-400">
                      <span className="flex items-center gap-1.5">
                        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
                        </svg>
                        Due: {new Date(bid.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                        </svg>
                        {bid.documents} documents
                      </span>
                    </div>
                    <button className="mt-1 px-4 py-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold hover:bg-amber-500/20 transition-all">
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-20">
            <div className="w-16 h-16 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto mb-4">
              <svg width="28" height="28" fill="none" viewBox="0 0 24 24" stroke="#64748b" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">No bids found</h3>
            <p className="text-slate-400">Try adjusting your filters or search query.</p>
          </div>
        )}
      </div>
    </div>
  )
}
