'use client'

import { useState, useEffect } from 'react'
import { Tender, TenderCategory, TenderStatus } from '@/types/tender'
import { listTenders } from '@/lib/api'
import { TenderCard } from '@/components/TenderCard'
import { TenderFilters } from '@/components/TenderFilters'

export default function TendersPage() {
  const [tenders, setTenders] = useState<Tender[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [state, setState] = useState<string>('')
  const [category, setCategory] = useState<TenderCategory | undefined>()
  const [status, setStatus] = useState<TenderStatus | undefined>()

  useEffect(() => {
    loadTenders()
  }, [state, category, status])

  async function loadTenders() {
    try {
      setLoading(true)
      setError(null)
      const data = await listTenders({
        state: state || undefined,
        category,
        status,
        limit: 50,
      })
      setTenders(data)
    } catch (err) {
      setError('Failed to load tenders. Please try again.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Public Works Opportunities</h1>

      <TenderFilters
        state={state}
        category={category}
        status={status}
        onStateChange={setState}
        onCategoryChange={setCategory}
        onStatusChange={setStatus}
      />

      {loading && (
        <div className="text-center py-12">
          <p className="text-gray-600">Loading opportunities...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {!loading && !error && tenders.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-600">
            No opportunities found. Try adjusting your filters.
          </p>
        </div>
      )}

      {!loading && !error && tenders.length > 0 && (
        <div className="space-y-6">
          {tenders.map((tender) => (
            <TenderCard key={tender.id} tender={tender} />
          ))}
        </div>
      )}
    </div>
  )
}
