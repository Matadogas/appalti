'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import {
  getAllTenders,
  getUniqueSources,
  getTotalCount,
  getScrapedAt,
} from '@/lib/data'

/* ─── Data ───────────────────────────────────────────────────── */

const allBids = getAllTenders()
const allSources = getUniqueSources()
const totalCount = getTotalCount()
const scrapedAt = getScrapedAt()

/* ─── Helpers ─────────────────────────────────────────────────── */

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null
  const diff = new Date(dateStr).getTime() - new Date().getTime()
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

function sourceColor(source: string): string {
  if (source.includes('Port Authority')) return 'bg-violet-500/20 text-violet-300 border-violet-500/30'
  if (source.includes('PASSPort')) return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
  if (source.includes('OGS')) return 'bg-rose-500/20 text-rose-300 border-rose-500/30'
  return 'bg-slate-500/20 text-slate-300 border-slate-500/30'
}

function sourceAbbrev(source: string): string {
  if (source.includes('Port Authority')) return 'PANYNJ'
  if (source.includes('PASSPort')) return 'PASSPort'
  if (source.includes('OGS')) return 'NYS OGS'
  return source.slice(0, 8)
}

function truncate(str: string, len: number): string {
  if (str.length <= len) return str
  return str.slice(0, len).replace(/\s+\S*$/, '') + '...'
}

function formatRelativeTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return `${days}d ago`
}

type SortOption = 'deadline' | 'newest' | 'alpha'

/* ─── Page ────────────────────────────────────────────────────── */

export default function TendersPage() {
  const [stateFilter, setStateFilter] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [sortBy, setSortBy] = useState<SortOption>('deadline')

  const filtered = useMemo(() => {
    let results = allBids.filter(bid => {
      if (stateFilter && bid.state !== stateFilter) return false
      if (categoryFilter && bid.category !== categoryFilter) return false
      if (sourceFilter && bid.source !== sourceFilter) return false
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        return (
          bid.title.toLowerCase().includes(q) ||
          bid.agency.toLowerCase().includes(q) ||
          bid.source.toLowerCase().includes(q) ||
          bid.description.toLowerCase().includes(q)
        )
      }
      return true
    })

    // Sort
    results.sort((a, b) => {
      if (sortBy === 'deadline') {
        if (!a.dueDate && !b.dueDate) return 0
        if (!a.dueDate) return 1
        if (!b.dueDate) return -1
        return a.dueDate.localeCompare(b.dueDate)
      }
      if (sortBy === 'newest') {
        if (!a.publishDate && !b.publishDate) return 0
        if (!a.publishDate) return 1
        if (!b.publishDate) return -1
        return b.publishDate.localeCompare(a.publishDate)
      }
      return a.title.localeCompare(b.title)
    })

    return results
  }, [stateFilter, categoryFilter, sourceFilter, searchQuery, sortBy])

  const activeFilters = [stateFilter, categoryFilter, sourceFilter, searchQuery].filter(Boolean).length

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
          <div className="flex items-center gap-4">
            <span className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              {totalCount} active bids &middot; Updated {formatRelativeTime(scrapedAt)}
            </span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 text-sm text-slate-500 mb-3">
            <Link href="/" className="hover:text-white transition-colors">Home</Link>
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
            <span className="text-slate-300">Browse Opportunities</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-2" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
            Browse Opportunities
          </h1>
          <p className="text-slate-400">
            {filtered.length} bid{filtered.length !== 1 ? 's' : ''}{activeFilters > 0 ? ' matching your filters' : ` from ${Object.keys(getUniqueSources()).length > 0 ? allSources.length : 3} government portals`}
          </p>
        </div>

        {/* Filters */}
        <div className="glass-card rounded-2xl p-5 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
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
            {/* Source */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">Source</label>
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-600/50 text-white text-sm focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all appearance-none cursor-pointer"
              >
                <option value="">All Sources</option>
                {allSources.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
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
                <option value="other">Other</option>
              </select>
            </div>
            {/* Sort */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5 uppercase tracking-wider">Sort</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="w-full px-4 py-2.5 rounded-lg bg-slate-800/80 border border-slate-600/50 text-white text-sm focus:outline-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/30 transition-all appearance-none cursor-pointer"
              >
                <option value="deadline">Nearest Deadline</option>
                <option value="newest">Newest First</option>
                <option value="alpha">Alphabetical</option>
              </select>
            </div>
            {/* Clear */}
            <div className="flex items-end">
              {activeFilters > 0 && (
                <button
                  onClick={() => { setStateFilter(''); setCategoryFilter(''); setSourceFilter(''); setSearchQuery('') }}
                  className="w-full px-4 py-2.5 rounded-lg border border-slate-600/50 text-slate-400 text-sm hover:text-white hover:border-slate-400 transition-all"
                >
                  Clear filters ({activeFilters})
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Bid List */}
        <div className="space-y-3">
          {filtered.map((bid) => {
            const days = daysUntil(bid.dueDate)
            const isUrgent = days !== null && days <= 7 && days >= 0
            const isPast = days !== null && days < 0

            return (
              <Link
                key={bid.id}
                href={`/tenders/${bid.id}`}
                className="group glass-card rounded-2xl p-5 md:p-6 hover:border-amber-500/25 transition-all duration-300 cursor-pointer block"
              >
                <div className="flex flex-col lg:flex-row lg:items-start gap-4">
                  {/* Main Content */}
                  <div className="flex-1 min-w-0">
                    {/* Top badges */}
                    <div className="flex flex-wrap items-center gap-2 mb-2.5">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border ${sourceColor(bid.source)}`}>
                        {sourceAbbrev(bid.source)}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-md text-xs font-medium border ${categoryColor(bid.category)}`}>
                        {categoryLabel(bid.category)}
                      </span>
                      {isUrgent && (
                        <span className="px-2.5 py-0.5 rounded-md text-xs font-bold bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse">
                          {days}d left
                        </span>
                      )}
                      {isPast && (
                        <span className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-500/20 text-slate-400 border border-slate-500/30">
                          Deadline passed
                        </span>
                      )}
                    </div>

                    {/* Title */}
                    <h2 className="text-base font-semibold text-white group-hover:text-amber-300 transition-colors mb-1.5 leading-snug">
                      {truncate(bid.title, 120)}
                    </h2>

                    {/* Agency + Source */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-400 mb-2">
                      <span className="flex items-center gap-1.5">
                        <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
                        </svg>
                        {truncate(bid.agency, 50)}
                      </span>
                      {bid.city && (
                        <span className="flex items-center gap-1.5">
                          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                          </svg>
                          {bid.city}, {bid.state}
                        </span>
                      )}
                    </div>

                    {/* Description preview */}
                    {bid.description && (
                      <p className="text-xs text-slate-500 line-clamp-1 mb-2">{bid.description}</p>
                    )}

                    {/* Metadata tags from rawRef */}
                    <div className="flex flex-wrap gap-1.5">
                      {bid.rawRef?.reference_number && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-700/60 text-slate-300 border border-slate-600/40">
                          {bid.rawRef.reference_number}
                        </span>
                      )}
                      {bid.rawRef?.epin && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-700/60 text-slate-300 border border-slate-600/40">
                          EPIN: {bid.rawRef.epin}
                        </span>
                      )}
                      {bid.rawRef?.bid_number && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-700/60 text-slate-300 border border-slate-600/40">
                          Bid #{bid.rawRef.bid_number}
                        </span>
                      )}
                      {bid.rawRef?.industry && (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-700/60 text-slate-300 border border-slate-600/40">
                          {bid.rawRef.industry}
                        </span>
                      )}
                      {bid.rawRef?.group_number && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-700/60 text-slate-300 border border-slate-600/40">
                          Group #{bid.rawRef.group_number}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Right sidebar */}
                  <div className="lg:w-44 flex-shrink-0 flex flex-row lg:flex-col items-start lg:items-end gap-3 lg:text-right">
                    {bid.dueDate && !isPast && (
                      <div>
                        <p className="text-xs text-slate-500 mb-0.5">Deadline</p>
                        <p className={`text-sm font-semibold ${isUrgent ? 'text-red-400' : 'text-white'}`}>
                          {new Date(bid.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </p>
                      </div>
                    )}
                    {bid.publishDate && (
                      <div>
                        <p className="text-xs text-slate-500 mb-0.5">Published</p>
                        <p className="text-sm text-slate-300">
                          {new Date(bid.publishDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                        </p>
                      </div>
                    )}
                    <span className="mt-auto px-4 py-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold group-hover:bg-amber-500/20 transition-all whitespace-nowrap flex items-center gap-1.5">
                      View Details
                      <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                      </svg>
                    </span>
                  </div>
                </div>
              </Link>
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
            <p className="text-slate-400 mb-4">Try adjusting your filters or search query.</p>
            <button
              onClick={() => { setStateFilter(''); setCategoryFilter(''); setSourceFilter(''); setSearchQuery('') }}
              className="text-sm text-amber-400 hover:text-amber-300 transition-colors"
            >
              Clear all filters
            </button>
          </div>
        )}

        {/* Results summary */}
        {filtered.length > 0 && (
          <div className="mt-8 text-center text-xs text-slate-600">
            Showing {filtered.length} of {totalCount} opportunities &middot; Data from {allSources.length} government portals
          </div>
        )}
      </div>
    </div>
  )
}
