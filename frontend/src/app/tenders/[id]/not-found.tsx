import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="relative z-10 min-h-screen flex items-center justify-center">
      <div className="text-center px-6">
        <div className="w-20 h-20 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto mb-6">
          <svg width="36" height="36" fill="none" viewBox="0 0 24 24" stroke="#64748b" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-white mb-2" style={{ fontFamily: 'var(--font-dm-serif), Georgia, serif' }}>
          Opportunity Not Found
        </h1>
        <p className="text-slate-400 mb-8 max-w-md mx-auto">
          This bid opportunity may have been removed or the URL may be incorrect.
        </p>
        <Link
          href="/tenders"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-amber-500 text-slate-900 font-semibold hover:bg-amber-400 transition-all"
        >
          Browse All Opportunities
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </Link>
      </div>
    </div>
  )
}
