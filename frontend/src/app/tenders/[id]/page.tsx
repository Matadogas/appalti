import Link from 'next/link'
import { notFound } from 'next/navigation'
import {
  getAllTenderIds,
  getTenderById,
  getSimilarTenders,
  getScrapedAt,
  getTotalCount,
  getSourceCounts,
} from '@/lib/data'
import type { Tender } from '@/lib/data'

/* ─── Static Generation ──────────────────────────────────────── */

export async function generateStaticParams() {
  return getAllTenderIds().map(id => ({ id }))
}

/* ─── Helpers ─────────────────────────────────────────────────── */

function daysUntil(dateStr: string | null): number | null {
  if (!dateStr) return null
  const diff = new Date(dateStr).getTime() - new Date().getTime()
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

function categoryLabel(cat: string): string {
  return cat.charAt(0).toUpperCase() + cat.slice(1)
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

function sourceDescription(source: string): string {
  if (source.includes('Port Authority')) return 'Port Authority of NY & NJ Bonfire Procurement Portal'
  if (source.includes('PASSPort')) return 'NYC Procurement and Sourcing Solutions Portal'
  if (source.includes('OGS')) return 'New York State Office of General Services'
  return source
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

function getReferenceId(tender: Tender): string | null {
  return (
    tender.rawRef?.reference_number ||
    tender.rawRef?.epin ||
    tender.rawRef?.bid_number ||
    null
  )
}

function getMetadataItems(tender: Tender): { label: string; value: string }[] {
  const items: { label: string; value: string }[] = []

  if (tender.rawRef?.reference_number) items.push({ label: 'Reference #', value: tender.rawRef.reference_number })
  if (tender.rawRef?.epin) items.push({ label: 'EPIN', value: tender.rawRef.epin })
  if (tender.rawRef?.bid_number) items.push({ label: 'Bid #', value: tender.rawRef.bid_number })
  if (tender.rawRef?.group_number) items.push({ label: 'Group #', value: tender.rawRef.group_number })
  if (tender.rawRef?.industry) items.push({ label: 'Industry', value: tender.rawRef.industry })
  if (tender.rawRef?.program) items.push({ label: 'Program', value: tender.rawRef.program })
  if (tender.rawRef?.rfx_status) items.push({ label: 'RFx Status', value: tender.rawRef.rfx_status })
  if (tender.rawRef?.bonfire_id) items.push({ label: 'Portal ID', value: tender.rawRef.bonfire_id })
  if (tender.rawRef?.bid_opening_date) items.push({ label: 'Bid Opening', value: tender.rawRef.bid_opening_date })

  return items
}

/* ─── Page Component ──────────────────────────────────────────── */

export default async function TenderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const tender = getTenderById(id)

  if (!tender) {
    notFound()
  }

  const similar = getSimilarTenders(tender, 4)
  const days = daysUntil(tender.dueDate)
  const isUrgent = days !== null && days <= 7 && days >= 0
  const isPast = days !== null && days < 0
  const referenceId = getReferenceId(tender)
  const metadata = getMetadataItems(tender)
  const scrapedAt = getScrapedAt()

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
            <Link
              href="/tenders"
              className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-1.5"
            >
              <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              All Bids
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero / Header */}
      <section className="bg-mesh-hero bg-grid pt-8 pb-10 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-sm text-slate-500 mb-6">
            <Link href="/" className="hover:text-white transition-colors">Home</Link>
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
            <Link href="/tenders" className="hover:text-white transition-colors">Opportunities</Link>
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
            <span className="text-slate-300 truncate max-w-xs">{truncate(tender.title, 40)}</span>
          </div>

          {/* Badges */}
          <div className="flex flex-wrap items-center gap-2.5 mb-5">
            <span className={`px-3 py-1 rounded-lg text-xs font-semibold border ${sourceColor(tender.source)}`}>
              {sourceAbbrev(tender.source)}
            </span>
            <span className={`px-3 py-1 rounded-lg text-xs font-medium border ${categoryColor(tender.category)}`}>
              {categoryLabel(tender.category)}
            </span>
            <span className="px-3 py-1 rounded-lg text-xs font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
              {tender.status === 'active' ? 'Active' : tender.status}
            </span>
            {isUrgent && (
              <span className="px-3 py-1 rounded-lg text-xs font-bold bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse">
                {days} days remaining
              </span>
            )}
            {isPast && (
              <span className="px-3 py-1 rounded-lg text-xs font-medium bg-slate-500/20 text-slate-400 border border-slate-500/30">
                Deadline passed
              </span>
            )}
          </div>

          {/* Title */}
          <h1 className="text-2xl md:text-4xl font-bold leading-snug tracking-tight mb-4 max-w-4xl" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
            {tender.title}
          </h1>

          {/* Agency + Location row */}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-400">
            <span className="flex items-center gap-2">
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
              </svg>
              {tender.agency}
            </span>
            {tender.city && (
              <span className="flex items-center gap-2">
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                </svg>
                {tender.city}, {tender.state}
              </span>
            )}
            {referenceId && (
              <span className="flex items-center gap-2 font-mono text-xs text-slate-500">
                <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 8.25h15m-16.5 7.5h15m-1.8-13.5l-3.9 19.5m-2.1-19.5l-3.9 19.5" />
                </svg>
                {referenceId}
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* ── Main Column ── */}
          <div className="lg:col-span-2 space-y-8">
            {/* AI Summary placeholder */}
            <div className="glass-card rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500/60 via-amber-400/30 to-transparent" />
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center">
                  <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#fbbf24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">AI Analysis</h3>
                  <p className="text-xs text-slate-500">Powered by TriStateBids AI</p>
                </div>
              </div>
              {tender.description ? (
                <p className="text-sm text-slate-300 leading-relaxed">{tender.description}</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-slate-400 leading-relaxed">
                    This {categoryLabel(tender.category).toLowerCase()} opportunity is posted by <span className="text-white font-medium">{tender.agency}</span>{' '}
                    via the <span className="text-white font-medium">{tender.source}</span> procurement portal.
                    {tender.dueDate && !isPast && (
                      <> The submission deadline is <span className="text-amber-400 font-medium">{new Date(tender.dueDate).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span>.</>
                    )}
                  </p>
                  <p className="text-xs text-slate-500 italic">Full AI-powered analysis is available with TriStateBids Pro. Includes scope breakdown, trade requirements, bonding needs, and compliance checklist.</p>
                </div>
              )}
            </div>

            {/* Key Details */}
            {metadata.length > 0 && (
              <div className="glass-card rounded-2xl p-6">
                <h3 className="text-sm font-semibold text-white mb-5 flex items-center gap-2">
                  <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
                  </svg>
                  Procurement Details
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {metadata.map(({ label, value }) => (
                    <div key={label} className="flex flex-col gap-0.5">
                      <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">{label}</span>
                      <span className="text-sm text-white font-mono">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Source Portal Card */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                </svg>
                Source Portal
              </h3>
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 border ${sourceColor(tender.source)}`}>
                  <span className="text-xs font-bold">{sourceAbbrev(tender.source).slice(0, 3)}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white mb-0.5">{tender.source}</p>
                  <p className="text-xs text-slate-500 mb-3">{sourceDescription(tender.source)}</p>
                  <a
                    href={tender.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-semibold hover:bg-amber-500/20 hover:border-amber-500/50 transition-all"
                  >
                    View on Portal
                    <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                    </svg>
                  </a>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-white/5">
                <p className="text-[11px] text-slate-600 font-mono break-all">{tender.sourceUrl}</p>
              </div>
            </div>

            {/* Disclaimer */}
            <div className="rounded-xl p-4 border border-slate-700/50 bg-slate-800/30">
              <p className="text-xs text-slate-500 leading-relaxed">
                <span className="text-slate-400 font-semibold">Disclaimer:</span> This information is aggregated from publicly available government procurement portals and is provided for informational purposes. Always verify details directly with the issuing agency before submitting a bid. TriStateBids is not responsible for inaccuracies in source data.
              </p>
            </div>
          </div>

          {/* ── Sidebar ── */}
          <div className="space-y-6">
            {/* Timeline Card */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-white mb-5 flex items-center gap-2">
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Timeline
              </h3>
              <div className="space-y-5">
                {tender.publishDate && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-emerald-500 border-2 border-emerald-500/30" />
                      <div className="w-px h-full bg-slate-700 mt-1" />
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 mb-0.5">Published</p>
                      <p className="text-sm font-medium text-white">
                        {new Date(tender.publishDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-3 h-3 rounded-full bg-cyan-500 border-2 border-cyan-500/30" />
                    <div className="w-px h-full bg-slate-700 mt-1" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-0.5">Data collected</p>
                    <p className="text-sm font-medium text-white">{formatRelativeTime(scrapedAt)}</p>
                  </div>
                </div>

                {tender.dueDate && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className={`w-3 h-3 rounded-full ${isUrgent ? 'bg-red-500 animate-pulse' : isPast ? 'bg-slate-500' : 'bg-amber-500'} border-2 ${isUrgent ? 'border-red-500/30' : isPast ? 'border-slate-500/30' : 'border-amber-500/30'}`} />
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 mb-0.5">
                        {isPast ? 'Deadline (passed)' : 'Deadline'}
                      </p>
                      <p className={`text-sm font-medium ${isUrgent ? 'text-red-400' : isPast ? 'text-slate-400' : 'text-white'}`}>
                        {new Date(tender.dueDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                      </p>
                      {days !== null && !isPast && (
                        <p className={`text-xs mt-0.5 font-semibold ${isUrgent ? 'text-red-400' : 'text-amber-400'}`}>
                          {days} day{days !== 1 ? 's' : ''} remaining
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {!tender.dueDate && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-slate-600 border-2 border-slate-600/30" />
                    </div>
                    <div>
                      <p className="text-xs text-slate-500 mb-0.5">Deadline</p>
                      <p className="text-sm text-slate-400">Open / Continuous</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Facts */}
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-white mb-5 flex items-center gap-2">
                <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                </svg>
                Quick Facts
              </h3>
              <div className="space-y-3.5">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500">State</span>
                  <span className="text-sm text-white font-medium">{tender.state === 'NY' ? 'New York' : 'New Jersey'}</span>
                </div>
                {tender.city && (
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500">City</span>
                    <span className="text-sm text-white">{tender.city}</span>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500">Category</span>
                  <span className={`px-2.5 py-0.5 rounded-md text-xs font-medium border ${categoryColor(tender.category)}`}>
                    {categoryLabel(tender.category)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500">Source</span>
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-semibold border ${sourceColor(tender.source)}`}>
                    {sourceAbbrev(tender.source)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-500">Status</span>
                  <span className="px-2.5 py-0.5 rounded-md text-xs font-medium bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                    Active
                  </span>
                </div>
              </div>
            </div>

            {/* CTA Card */}
            <div className="rounded-2xl p-6 border border-amber-500/20 bg-gradient-to-br from-amber-500/5 to-transparent">
              <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/25 flex items-center justify-center mb-4">
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="#fbbf24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
                </svg>
              </div>
              <h4 className="text-sm font-semibold text-white mb-2">Get Alerts for Similar Bids</h4>
              <p className="text-xs text-slate-400 mb-4 leading-relaxed">
                Never miss a {categoryLabel(tender.category).toLowerCase()} opportunity from {truncate(tender.agency, 30)}. Set up instant email alerts.
              </p>
              <button className="w-full px-4 py-2.5 rounded-lg bg-amber-500 text-slate-900 text-sm font-semibold hover:bg-amber-400 transition-all hover:shadow-lg hover:shadow-amber-500/20">
                Set Up Alerts
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ══ Similar Opportunities ══ */}
      {similar.length > 0 && (
        <section className="max-w-7xl mx-auto px-6 pb-16">
          <div className="border-t border-white/5 pt-12">
            <h2 className="text-xl font-bold tracking-tight mb-6" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
              Similar Opportunities
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {similar.map(s => {
                const sDays = daysUntil(s.dueDate)
                return (
                  <Link
                    key={s.id}
                    href={`/tenders/${s.id}`}
                    className="group glass-card rounded-xl p-5 hover:border-amber-500/25 transition-all"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${sourceColor(s.source)}`}>
                        {sourceAbbrev(s.source)}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium border ${categoryColor(s.category)}`}>
                        {categoryLabel(s.category)}
                      </span>
                    </div>
                    <h3 className="text-sm font-medium text-white group-hover:text-amber-300 transition-colors mb-1 leading-snug">
                      {truncate(s.title, 90)}
                    </h3>
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{truncate(s.agency, 35)}</span>
                      {sDays !== null && sDays >= 0 && (
                        <span className={sDays <= 7 ? 'text-red-400 font-medium' : ''}>{sDays}d left</span>
                      )}
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        </section>
      )}

      {/* Footer bar */}
      <footer className="border-t border-white/5 py-6" style={{ background: 'var(--navy-950)' }}>
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-600">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Data from {getTotalCount()} opportunities across {Object.keys(getSourceCounts()).length} portals
          </div>
          <Link href="/tenders" className="text-xs text-amber-400 hover:text-amber-300 transition-colors flex items-center gap-1">
            Browse all opportunities
            <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>
      </footer>
    </div>
  )
}
